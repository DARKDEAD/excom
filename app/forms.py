from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, InputRequired, Length


class LoginForm(FlaskForm):
    mail = StringField("mail", [InputRequired(), Email()])
    password = PasswordField(
            "password",
            [InputRequired(), Length(min=6, message="Минимальная пароля 6 знаков")],
    )
