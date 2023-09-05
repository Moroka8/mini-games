from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class SignForm(FlaskForm):
    username = StringField('Create username', validators=[DataRequired()])
    password = PasswordField('Create password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class StakeForm(FlaskForm):
    stake = StringField('Stake',validators=[DataRequired()])
    submit = SubmitField('Start')

class Stake1Form(FlaskForm):
    stake1 = StringField('Stake',validators=[DataRequired()])

class CaseForm(FlaskForm):
    open_case = SubmitField("Open")

class LoginChangeForm(FlaskForm):
    login = StringField('Write new login',validators=[DataRequired()])
    submit = SubmitField('Change')

class PasswordChangeForm(FlaskForm):
    old_pass = PasswordField('Write your old password',validators=[DataRequired()])
    new_pass = PasswordField('Write your new password',validators=[DataRequired()])
    repeat_pass = PasswordField('Repeat your new password',validators=[DataRequired()])
    submit = SubmitField('Change')

