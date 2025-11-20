from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from flask_login import LoginManager
from flask_socketio import SocketIO
from dotenv import load_dotenv
from sqlalchemy import text

    # Load .env variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # For flash messages

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
socketio = SocketIO(app, async_mode='eventlet')

with app.app_context():
    from .models import Users, Bid, Timer, Initials
    db.drop_all()
    db.create_all()

    # Create admin user
    if not Users.query.filter_by(IdentificationKey='admin').first():
        admin = Users(IdentificationKey='admin', is_admin=True, display_name='Administrator')
        admin.set_password('admin')
        db.session.add(admin)

    # db.session.execute(text("SET TIME ZONE 'Asia/Singapore';"))
    db.session.commit()
    print('Created Database!')

#run the file routes.py
from application import routes1, admins