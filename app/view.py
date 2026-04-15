from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, URL

# -------------------------------
# 1. Register Form
# -------------------------------
class RegisterForm(FlaskForm):
    fullname = StringField("Full Name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[DataRequired()])
    
    password = PasswordField("Password", validators=[
        DataRequired(), 
        Length(min=6, max=150)
    ])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    
    receiveMail = BooleanField("Receive Emails", validators=[Optional()]) # BooleanField badanaa Optional ayaa la dhigaa
    termsCondition = BooleanField("Terms & Conditions", validators=[DataRequired()])
    submit = SubmitField("Create Account")

# -------------------------------
# 2. Login Form
# -------------------------------
class LoginForm(FlaskForm):
    login_id = StringField('Login ID', validators=[
        DataRequired(), 
        Length(min=3, max=64)
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

# -------------------------------
# 3. Settings Data Form
# -------------------------------
class SettingsDataForm(FlaskForm):
    group_name = StringField("Group Name", validators=[
        DataRequired(), 
        Length(min=2, max=255)
    ])
    system_name = StringField("System Name", validators=[
        Optional(), 
        Length(max=255)
    ])
    address = StringField("Address", validators=[
        DataRequired(), 
        Length(max=255)
    ])
    
    short_desc = TextAreaField("Short Description", validators=[Optional()])
    long_desc = TextAreaField("Long Description", validators=[Optional()])
    success_desc = TextAreaField("Success Description", validators=[Optional()])

    head_image = FileField("Header Image", validators=[
        Optional(), 
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    image_success = FileField("Success Image", validators=[
        Optional(), 
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    about_image = FileField("About Image", validators=[
        Optional(), 
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])

    video_url = StringField("Video URL", validators=[Optional(), URL()])

    phone1 = StringField("Phone 1", validators=[DataRequired(), Length(max=15)])
    phone2 = StringField("Phone 2", validators=[Optional(), Length(max=15)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=100)])

    facebook = StringField("Facebook", validators=[Optional(), Length(max=255)])
    twitter = StringField("Twitter", validators=[Optional(), Length(max=255)])
    instagram = StringField("Instagram", validators=[Optional(), Length(max=255)])
    dribbble = StringField("Dribbble", validators=[Optional(), Length(max=255)])

    logo = FileField("Main Logo", validators=[
        Optional(), 
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    logo2 = FileField("Secondary Logo", validators=[
        Optional(), 
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])

    submit = SubmitField("Save Settings")

# -------------------------------
# 4. Forgot Password Forms
# -------------------------------
class ForgotPasswordForm(FlaskForm):
    email = StringField("Email Address", validators=[
        DataRequired(message="Email is required."), 
        Email(message="Invalid email address.")
    ])
    submit = SubmitField("Send OTP")

class VerifyOTPForm(FlaskForm):
    otp_code = StringField('OTP Code', validators=[
        DataRequired(), 
        Length(min=6, max=6, message="OTP must be 6 digits.")
    ])
    submit = SubmitField("Validate")

class ForgotPasswordChangeForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[
        DataRequired(), 
        Length(min=8, max=150)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('new_password', message="Passwords must match.")
    ])
    submit = SubmitField('Save Changes')





    