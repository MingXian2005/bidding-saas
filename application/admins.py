import os
from application import app, db, socketio
from application.models import Users, Timer, Initials, Bid, Client, AuctionInfo, AuctionImage
from flask_login import current_user, login_required
from functools import wraps
from flask import render_template, request, flash, redirect, url_for, abort
from application.forms import RegistrationForm, TimerForm, InitialsForm, NewTimerForm, NewTimerForm2, AuctionInfoForm, AuctionImageForm
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.utils import secure_filename

scheduler = BackgroundScheduler()
scheduler.start()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not (current_user.is_admin or current_user.sys_admin):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

import string

def generate_display_name():
    # Get all display names already used
    existing_names = {u.display_name for u in Users.query.all() if u.display_name}
    for letter in string.ascii_uppercase:
        name = f"Company {letter}"
        if name not in existing_names:
            return name
    raise Exception("Ran out of company names!")

@app.route('/admin')
@app.route('/admin/')
@login_required
@admin_required

def admin():
    if current_user.is_blocked:
        return redirect(url_for('blocked'))
    return render_template('admin.html', title="Admin Homepage")

@app.route('/admin/register', methods=['GET', 'POST'])
@login_required
@admin_required

def admin_register():
    if current_user.is_blocked:
        return redirect(url_for('blocked'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        display_name = form.display_name.data
        IdentificationKey = form.IdentificationKey.data
        password = form.password.data
        
        # Check if IdentificationKey already exists
        existing_user = Users.query.filter_by(IdentificationKey=IdentificationKey).first()
        if existing_user:
            flash('IdentificationKey already exists. Please choose a different one.', 'danger')
            return render_template('register.html', form=form, title="Admin Registration")

        new_user = Users(
        IdentificationKey=IdentificationKey,
        display_name=display_name,  # assign anonymous name
        )
        new_user.client_id = current_user.client_id 
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully!', 'success')
        return redirect(url_for('admin_register'))
    return render_template('register.html', form=form, title="Admin Registration")


@app.route('/admin/page', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_page():
    if current_user.is_blocked:
        return redirect(url_for('blocked'))
    
    form = TimerForm()
        
    return render_template('admin_page.html', form=form, title="Admin Page")


@app.route('/admin/page/start', methods=['POST'])
@login_required
@admin_required
def admin_start_auction():
    if current_user.is_blocked:
        return redirect(url_for('blocked'))
    
    # You can get duration from a form or use a default
    duration = int(request.form.get('duration', 5))  # default 5 minutes if not provided
    # extra_duration = int(request.form.get('extra_duration', 5))  # default 5 minutes if not provided
    # total_extra_duration = extra_duration + duration
    end_time = datetime.now(ZoneInfo("Asia/Singapore")) + timedelta(minutes=duration)
    # force_end_time = datetime.now(ZoneInfo("Asia/Singapore")) + timedelta(minutes=total_extra_duration)
    force_end_time = datetime.now(ZoneInfo("Asia/Singapore")) + timedelta(minutes=10000000)
    start_time = datetime.now(ZoneInfo("Asia/Singapore"))
    print("admin timer setting")
    print(end_time, 'end time')
    print(force_end_time, 'force end time')
    # Remove old timers
    # Timer.query.delete()
    Timer.query.filter_by(client_id=current_user.client_id).delete()
    db.session.commit()
    # timer = Timer(end_time=end_time, force_end_time=force_end_time, start_time=start_time)
    timer = Timer(
        end_time=end_time,
        force_end_time=force_end_time,
        start_time=start_time,
        client_id=current_user.client_id
    )
    db.session.add(timer)
    db.session.commit()
    flash(f'Auction timer set for {duration} minutes.', 'success')
    return redirect(url_for('admin_page'))

@app.route('/admin/init', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_init():
    if current_user.is_blocked:
        return redirect(url_for('blocked'))
    
    form = InitialsForm()
    return render_template('admin_init.html', form=form, title="Admin Init")

@app.route('/admin/init/post', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_init_post():
    if current_user.is_blocked:
        return redirect(url_for('blocked'))
    
    form = InitialsForm()
    if form.validate_on_submit():
        StartingBid = form.StartingBid.data
        BidDecrement = form.BidDecrement.data
        MaxBidPercentage = form.MaxBidPercentage.data

        # Initials.query.delete()
        Initials.query.filter_by(client_id=current_user.client_id).delete()
        db.session.commit()

        new_initials = Initials(
            StartingBid=StartingBid,
            BidDecrement=BidDecrement,
            MaxBidPercentage=MaxBidPercentage,
            client_id=current_user.client_id
        )
        db.session.add(new_initials)
        db.session.commit()

        socketio.emit(
            'initials_updated',
            {
                'StartingBid': StartingBid,
                'BidDecrement': BidDecrement,
                'MaxBidPercentage': float(MaxBidPercentage)
            },
            room=f'client_{current_user.client_id}'
        )

        flash('New initials set successfully!', 'success')
        return redirect(url_for('admin_init'))
    
    return render_template('admin_init.html', form=form, title="Admin Init")

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    if current_user.is_blocked:
        return redirect(url_for('blocked'))
    
    # users = Users.query.filter_by(sys_admin=False).all()
    users = Users.query.filter_by(client_id=current_user.client_id, sys_admin=False, is_admin = False).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/<int:user_id>/toggle_block', methods=['POST'])
@login_required
@admin_required
def toggle_block_user(user_id):
    user = Users.query.get_or_404(user_id)
    user.is_blocked = not user.is_blocked
    db.session.commit()
    status = 'blocked' if user.is_blocked else 'unblocked'
    flash(f'User {user.display_name} is now {status}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/start', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_start():
    if current_user.is_blocked:
        return redirect(url_for('blocked'))
    
    form = NewTimerForm()
    if form.validate_on_submit():
        start_time = form.start_time.data
        duration = form.duration.data
        # extra_duration = form.extra_duration.data
        # total_extra_duration = extra_duration + duration
        start_time = start_time.replace(tzinfo=ZoneInfo("Asia/Singapore"))
        end_time = start_time + timedelta(minutes=duration)
        # force_end_time = start_time + timedelta(minutes=total_extra_duration)
        force_end_time = datetime.now(ZoneInfo("Asia/Singapore")) + timedelta(minutes=10000000)
        print(start_time)
        print(end_time)
        print(force_end_time)
        print(datetime.now(ZoneInfo("Asia/Singapore")))


        # Remove old timers
        Timer.query.filter_by(client_id=current_user.client_id).delete()
        db.session.commit()

        # timer = Timer(start_time=start_time, end_time=end_time, force_end_time=force_end_time)
        timer = Timer(
            end_time=end_time,
            force_end_time=force_end_time,
            start_time=start_time,
            client_id=current_user.client_id
        )
        db.session.add(timer)
        db.session.commit()
        flash(f'Auction timer set.', 'success')
        return redirect(url_for('admin_start'))
    return render_template('admin_start.html', form=form, title="Admin Start")

@app.route('/admin/rm', methods=['GET'])
@login_required
@admin_required
def admin_rm():
    if current_user.is_blocked:
        return redirect(url_for('blocked'))
    
    # bids = Bid.query.order_by(Bid.timestamp.desc()).all()
    bids = Bid.query.filter_by(client_id=current_user.client_id).order_by(Bid.timestamp.desc()).all()
    return render_template('admin_rm.html', bids=bids, title="Remove Bids")

@app.route('/admin/rm/<int:bid_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_bid(bid_id):
    bid = Bid.query.get_or_404(bid_id)
    db.session.delete(bid)
    db.session.commit()
    flash(f'Bid {bid_id} has been deleted.', 'success')
    return redirect(url_for('admin_rm'))


def emit_auction_start():
    print("Auction start time reached! Emitting event to clients.")
    socketio.emit('auction_started', {'message': 'Auction has started!'})

@app.route('/admin/close', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_close():
    if current_user.is_blocked:
        return redirect(url_for('blocked'))
    
    form = NewTimerForm2()
    if form.validate_on_submit():
        start_time = form.start_time.data
        duration = form.duration.data
        start_time = start_time.replace(tzinfo=ZoneInfo("Asia/Singapore"))
        end_time = start_time + timedelta(minutes=duration)
        force_end_time = datetime.now(ZoneInfo("Asia/Singapore")) + timedelta(minutes=10000000)

        Timer.query.filter_by(client_id=current_user.client_id).delete()
        db.session.commit()

        # timer = Timer(start_time=start_time, end_time=end_time, force_end_time=force_end_time)
        timer = Timer(
            end_time=end_time,
            force_end_time=force_end_time,
            start_time=start_time,
            client_id=current_user.client_id
        )
        db.session.add(timer)
        db.session.commit()

        # Emit timer update immediately to refresh clients after setting time
        socketio.emit('timer_updated', {
            'start_time': timer.start_time.isoformat(),
            'end_time': timer.end_time.isoformat()
        })

        # Also emit a 'refresh_page' event so clients can reload immediately
        socketio.emit('refresh_page', {})

        # Clear existing scheduled jobs
        scheduler.remove_all_jobs()

        # Schedule auction start event
        scheduler.add_job(
            func=emit_auction_start,
            trigger='date',
            run_date=start_time.astimezone(ZoneInfo("UTC")),
            id='auction_start_job'
        )

        flash(f'Auction timer set.', 'success')
        return redirect(url_for('admin_close'))
    return render_template('admin_close.html', form=form, title="Admin Close")

@app.route('/admin/aucinfo', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_info():
    if current_user.is_blocked:
        return redirect(url_for('blocked'))

    # Instantiate both forms with prefixes
    info_form = AuctionInfoForm(prefix='info')
    image_form = AuctionImageForm(prefix='image')

    # Get existing auction info for this client
    aucinfo = AuctionInfo.query.filter_by(client_id=current_user.client_id).first()

    # Pre-fill info form if data exists
    if aucinfo and request.method == 'GET':
        info_form.title.data = aucinfo.title
        info_form.address.data = aucinfo.address

    # Handle Info form submission
    if info_form.validate_on_submit() and info_form.submit.data:
        if aucinfo:
            aucinfo.title = info_form.title.data
            aucinfo.address = info_form.address.data
        else:
            aucinfo = AuctionInfo(
                title=info_form.title.data,
                address=info_form.address.data,
                client_id=current_user.client_id
            )
            db.session.add(aucinfo)

        db.session.commit()
        socketio.emit(
            'auction_info_updated',
            {'title': aucinfo.title, 'address': aucinfo.address},
            room=f'client_{current_user.client_id}'
        )
        flash("Auction info saved successfully!", "success")
        return redirect(url_for('admin_info'))

    # Handle Image form submission
    elif image_form.validate_on_submit() and image_form.submit.data:
        image_file = image_form.image.data
        if image_file:
            filename = secure_filename(image_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save the new file to disk
            image_file.save(file_path)

            # Get the existing image record for this client
            old_image = AuctionImage.query.filter_by(client_id=current_user.client_id).first()

            if old_image:
                # Optional: remove the old file from disk if it exists
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image.image_filename)
                try:
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except Exception as e:
                    print(f"Failed to remove old image: {e}")

                # Update the existing database record
                old_image.image_filename = filename
            else:
                # No previous image, create a new record
                old_image = AuctionImage(image_filename=filename, client_id=current_user.client_id)
                db.session.add(old_image)

            db.session.commit()

            flash("Auction image uploaded successfully!", "success")

            # Update clients in real-time
            socketio.emit(
                'auction_images_updated',
                {
                    'images': [
                        img.image_filename for img in AuctionImage.query.filter_by(client_id=current_user.client_id).all()
                    ]
                },
                room=f'client_{current_user.client_id}'
            )

        return redirect(url_for('admin_info'))

    return render_template(
        'admin_info.html',
        info_form=info_form,
        image_form=image_form,
        aucinfo=aucinfo,
        title="Auction Info"
    )

@app.route('/admin_reset', methods=['GET', 'POST'])
@login_required
def admin_reset():
    if not current_user.is_admin:
        flash('Only admins can access this page.', 'danger')
        return redirect(url_for('bid'))

    if request.method == 'POST':
        # Delete all bids and timers for this client
        Bid.query.filter_by(client_id=current_user.client_id).delete()
        Timer.query.filter_by(client_id=current_user.client_id).delete()
        db.session.commit()
        flash('All bids and auction timer have been reset.', 'success')
        return redirect(url_for('admin_reset'))

    return render_template('admin_reset.html')
