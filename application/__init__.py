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
    from .models import Users, Bid, Timer, Initials, Client
    db.drop_all()
    db.create_all()

    # ✅ 1. Default Sysadmin
    if not Users.query.filter_by(sys_admin=True).first():
        sysadmin = Users(
            IdentificationKey="Advancedata Network",
            sys_admin=True,
            display_name="sysadmin"
        )
        sysadmin.set_password("sysadv")
        db.session.add(sysadmin)
        print("Created default Sysadmin")

    # ✅ 2. Default Client
    default_client = Client.query.filter_by(name="Default Client").first()
    if not default_client:
        default_client = Client(name="Default Client")
        db.session.add(default_client)
        db.session.commit()  # commit to generate client.id
        print("Created default Client")

    # ✅ 3. Default User under client
    if not Users.query.filter_by(IdentificationKey="admin").first():
        client_user = Users(
            IdentificationKey="admin",
            is_admin=True,
            display_name="Administrator",
            client_id=default_client.id
        )
        client_user.set_password("admin")
        db.session.add(client_user)
        print("Created default client user")

    db.session.commit()
    print('Created Database!')

#run the file routes.py
# from application import routes1, admins