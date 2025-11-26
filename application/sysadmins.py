from application import app, db, socketio
from application.models import Users, Timer, Initials, Bid, Client
from flask_login import current_user, login_required
from functools import wraps
from flask import render_template, request, flash, redirect, url_for, abort
from application.forms import SysAdminRegistrationForm, TimerForm, InitialsForm, NewTimerForm, NewTimerForm2
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler


scheduler = BackgroundScheduler()
scheduler.start()

def sysadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not current_user.sys_admin:
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

@app.route('/sysadmin')
@login_required
@sysadmin_required
def sysadmin():
    return render_template('sysadmin.html')

@app.route('/sysadmin/register', methods=['GET', 'POST'])
@login_required
@sysadmin_required
def sysadmin_register():
    form = SysAdminRegistrationForm()
    
    # Populate existing clients
    form.client_id.choices = [(0, '--- Select Existing Client ---')] + \
        [(c.id, c.name) for c in Client.query.order_by(Client.name).all()]

    if form.validate_on_submit():
        display_name = form.display_name.data
        IdentificationKey = form.IdentificationKey.data
        password = form.password.data
        client_id = None

        # Check if IdentificationKey exists
        if Users.query.filter_by(IdentificationKey=IdentificationKey).first():
            flash('IdentificationKey already exists.', 'danger')
            return render_template('sysregister.html', form=form)

        # Create new client if provided
        if form.new_client_name.data:
            new_client = Client(name=form.new_client_name.data)
            db.session.add(new_client)
            db.session.commit()
            client_id = new_client.id
        elif form.client_id.data != 0:
            client_id = form.client_id.data
        else:
            flash('Select or create a client.', 'danger')
            return render_template('sysregister.html', form=form)

        # Create admin user
        new_user = Users(
            display_name=display_name,
            IdentificationKey=IdentificationKey,
            is_admin=True,
            client_id=client_id
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Admin registered successfully!', 'success')
        return redirect(url_for('sysadmin_register'))

    return render_template('sysregister.html', form=form)

@app.route('/sysadmin/users')
@login_required
@sysadmin_required
def sysadmin_users():
    users = Users.query.filter_by(sys_admin=False).all()
    return render_template('sysadmin_users.html', users=users)

@app.route('/sysadmin/users/<int:user_id>/toggle_block', methods=['POST'])
@login_required
@sysadmin_required
def toggle_block_admin(user_id):
    user = Users.query.get_or_404(user_id)
    user.is_blocked = not user.is_blocked
    db.session.commit()
    status = 'blocked' if user.is_blocked else 'unblocked'
    flash(f'User {user.display_name} is now {status}.', 'success')
    return redirect(url_for('sysadmin_users'))

@app.route('/sysadmin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@sysadmin_required
def delete_user_admin(user_id):
    user = Users.query.get_or_404(user_id)

    if user.sys_admin:
        flash("You cannot delete a system admin account!", "danger")
        return redirect(url_for('sysadmin_users'))

    db.session.delete(user)
    db.session.commit()

    flash(f'User {user.display_name} has been deleted.', 'success')
    return redirect(url_for('sysadmin_users'))

