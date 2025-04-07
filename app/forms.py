'''
Forms related to user registration and login
'''

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms import validators as val


class RegistrationForm(FlaskForm):
    '''
    form to register a new user
    '''
    username = StringField(
        'Username', validators=[val.DataRequired(),
                                val.Length(min=4, max=30,
                                           message='Must be between 4 and 30 characters.')]
    )
    email = StringField(
        'Email', validators=[val.DataRequired(),
                             val.Length(
                                 min=6, max=40, message='Must be between 6 and 40 characters.'),
                             val.Email(message='Invalid email address.')]
    )
    password = PasswordField(
        'Password', validators=[val.DataRequired(),
                                val.Length(min=6, max=40, message='Must be between 6 and 40 characters.')]
    )
    confirm = PasswordField(
        'Confirm Password',
        [val.DataRequired(),
         val.EqualTo('password', message='Passwords must match exactly')]
    )


class LoginForm(FlaskForm):
    '''
    form to login an existing user
    '''
    username = StringField('Username', [val.DataRequired()])
    password = PasswordField('Password', [val.DataRequired()])


class ForgotPasswordForm(FlaskForm):
    '''
    form for a user who forgot their password
    '''
    email = StringField(
        'Email', validators=[val.DataRequired(),
                             val.Length(min=6, max=40),
                             val.Email(message='Invalid email address.')]
    )
