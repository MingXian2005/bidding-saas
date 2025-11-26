from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField, DateTimeField, SelectField
from wtforms.validators import InputRequired, Length, NumberRange
from wtforms.validators import DataRequired, Optional

class RegistrationForm(FlaskForm):
    IdentificationKey = StringField('Identification Key', validators=[InputRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=120)])
    display_name = StringField('Display Name', validators=[InputRequired(), Length(min=1, max=80)])
    submit = SubmitField('Register')

class SysAdminRegistrationForm(FlaskForm):
    display_name = StringField('Display Name', validators=[DataRequired()])
    IdentificationKey = StringField('Identification Key', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    
    # For assigning a client
    client_id = SelectField('Assign Client', coerce=int, validators=[Optional()])
    
    # Or create a new client
    new_client_name = StringField('Or Create New Client', validators=[Optional()])
    
    submit = SubmitField('Register Admin')

class BidForm(FlaskForm):
    amount = FloatField('Bid Amount (RM)', validators=[InputRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Place Bid')


class LoginForm(FlaskForm):
    display_name = StringField('Company Name', 
            validators=[InputRequired()], render_kw={"placeholder": "Company Name"})
    password = PasswordField("Password",
            validators=[InputRequired()], render_kw={"placeholder": "Password"})
    
    submit = SubmitField('Login')


class TimerForm(FlaskForm):
    duration = IntegerField('Auction Duration (minutes)', validators=[InputRequired(), NumberRange(min=1)])
    # extra_duration = IntegerField('Extra Auction Duration (minutes)', validators=[InputRequired(), NumberRange(min=1)])
    submit = SubmitField('Set Timer')

class NewTimerForm(FlaskForm):
    start_time = DateTimeField('Start Time', format='%Y-%m-%d %H:%M:%S', validators=[InputRequired()], render_kw={"placeholder": "%Y-%m-%d %H:%M:%S, 24hrs"})
    duration = IntegerField('Auction Duration (minutes)', validators=[InputRequired(), NumberRange(min=1)])
    # extra_duration = IntegerField('Extra Auction Duration (minutes)', validators=[InputRequired(), NumberRange(min=1)])
    submit = SubmitField('Set Timer')

class NewTimerForm2(FlaskForm):
    start_time = DateTimeField('Start Time', format='%Y-%m-%d %H:%M:%S', validators=[InputRequired()], render_kw={"placeholder": "%Y-%m-%d %H:%M:%S, 24hrs"})
    duration = IntegerField('Auction Duration (minutes)', validators=[InputRequired(), NumberRange(min=1)])
    # force_end_time = DateTimeField('End Time', format='%Y-%m-%d %H:%M:%S', validators=[InputRequired()], render_kw={"placeholder": "%Y-%m-%d %H:%M:%S, 24hrs"})
    submit = SubmitField('Set Timer')



class InitialsForm(FlaskForm):
    StartingBid = FloatField('Starting Bid ($)', validators=[InputRequired()])
    BidDecrement = FloatField('Next Bid Decrement($)', validators=[InputRequired()])
    submit = SubmitField('Confirm')
