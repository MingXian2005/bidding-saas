from application import app, db, socketio
from application.models import Users, Timer, Initials, Bid
from flask_login import current_user, login_required
from functools import wraps
from flask import render_template, request, flash, redirect, url_for, abort
from application.forms import RegistrationForm, TimerForm, InitialsForm, NewTimerForm, NewTimerForm2
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not current_user.is_admin:
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
    return render_template('admin.html', title="Admin Homepage")

@app.route('/admin/register', methods=['GET', 'POST'])
@login_required
@admin_required

def admin_register():
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
        display_name=display_name  # assign anonymous name
        )
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
    form = TimerForm()
    # timer = Timer.query.order_by(Timer.id.desc()).first()

    # if timer:
    #     if timer.end_time:
    #         timer.end_time = timer.end_time.replace(tzinfo=ZoneInfo('UTC'))
    #         timer.end_time = timer.end_time.astimezone(ZoneInfo("Asia/Singapore"))
    # # No need for `else: timer.end_time = None`

    # if timer:
    #     if timer.force_end_time:
    #         timer.force_end_time = timer.force_end_time.replace(tzinfo=ZoneInfo('UTC'))
    #         timer.force_end_time = timer.force_end_time.astimezone(ZoneInfo("Asia/Singapore"))

    # if form.validate_on_submit():
    #     duration = form.duration.data  # duration in minutes
    #     extra_duration = form.extra_duration.data
    #     end_time = datetime.now(ZoneInfo("Asia/Singapore")) + timedelta(minutes=duration)
    #     force_end_time = end_time + timedelta(minutes=extra_duration)

    #     print("admin timer setting")
    #     print(end_time, 'end time')
    #     print(force_end_time, 'force end time')

    #     # Remove old timers if you want only one active
    #     Timer.query.delete()
    #     db.session.commit()

    #     timer = Timer(end_time=end_time, force_end_time=force_end_time)
    #     db.session.add(timer)
    #     db.session.commit()
    #     flash(f'Auction timer set for {duration} minutes and force ends after an additional {extra_duration}.', 'success')
    #     return redirect(url_for('admin_page'))
        
    return render_template('admin_page.html', form=form, title="Admin Page")


@app.route('/admin/page/start', methods=['POST'])
@login_required
@admin_required
def admin_start_auction():
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
    Timer.query.delete()
    db.session.commit()
    timer = Timer(end_time=end_time, force_end_time=force_end_time, start_time=start_time)
    db.session.add(timer)
    db.session.commit()
    flash(f'Auction timer set for {duration} minutes.', 'success')
    return redirect(url_for('admin_page'))

@app.route('/admin/init', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_init():
    form = InitialsForm()
    return render_template('admin_init.html', form=form, title="Admin Init")

@app.route('/admin/init/post', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_init_post():
    form = InitialsForm()
    if form.validate_on_submit():
        StartingBid = form.StartingBid.data
        BidDecrement = form.BidDecrement.data
        Initials.query.delete()
        db.session.commit()
        new_initials = Initials(StartingBid=StartingBid, BidDecrement=BidDecrement)
        db.session.add(new_initials)
        db.session.commit()
        flash('New initials set successfully!', 'success')
        return redirect(url_for('admin_init'))
    return render_template('admin_init.html', form=form, title="Admin Init")

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = Users.query.all()
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
        Timer.query.delete()
        db.session.commit()

        timer = Timer(start_time=start_time, end_time=end_time, force_end_time=force_end_time)
        db.session.add(timer)
        db.session.commit()
        flash(f'Auction timer set.', 'success')
        return redirect(url_for('admin_start'))
    return render_template('admin_start.html', form=form, title="Admin Start")

@app.route('/admin/rm', methods=['GET'])
@login_required
@admin_required
def admin_rm():
    bids = Bid.query.order_by(Bid.timestamp.desc()).all()
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
    form = NewTimerForm2()
    if form.validate_on_submit():
        start_time = form.start_time.data
        duration = form.duration.data
        start_time = start_time.replace(tzinfo=ZoneInfo("Asia/Singapore"))
        end_time = start_time + timedelta(minutes=duration)
        force_end_time = datetime.now(ZoneInfo("Asia/Singapore")) + timedelta(minutes=10000000)

        Timer.query.delete()
        db.session.commit()

        timer = Timer(start_time=start_time, end_time=end_time, force_end_time=force_end_time)
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
