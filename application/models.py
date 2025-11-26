from application import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from zoneinfo import ZoneInfo


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore")))
    users = db.relationship('Users', backref='client', lazy=True)

class Users(db.Model, UserMixin):
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)  # nullable=True for sys_admin
    id = db.Column(db.Integer, primary_key=True)
    IdentificationKey = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    sys_admin = db.Column(db.Boolean, default=False)
    display_name = db.Column(db.String(80), unique=True)  
    is_blocked = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(
        db.DateTime(timezone=True), 
        default=lambda: datetime.now(ZoneInfo("Asia/Singapore")) 
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # foreign key to Users
    user = db.relationship('Users', backref=db.backref('bids', lazy=True))       # relationship to Users

    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    client = db.relationship('Client', backref=db.backref('bids', lazy=True))

class Timer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    end_time = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore")), nullable=False) 
    force_end_time = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore"))) 
    start_time = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore"))) 

    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    client = db.relationship('Client', backref=db.backref('timers', lazy=True))

class Initials(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    StartingBid = db.Column(db.Float, nullable=False)
    BidDecrement = db.Column(db.Float, nullable=False)

    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    client = db.relationship('Client', backref=db.backref('initials', lazy=True))

class AuctionInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
