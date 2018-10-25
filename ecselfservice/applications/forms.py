from flask import current_app
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, NoneOf
from wtforms import ValidationError
from ..db import (
    get_applications,
    get_events,
)


class AppNameForm(FlaskForm):
    app_name = StringField('AppName',
        validators=[
            DataRequired(),
            Length(1, 64),
            Regexp('^[a-z][a-z0-9_]{3,}$', 0,
               'name must be lowercased ascii characters that start with a letter followed by letters, numbers or underscores'
            ),
        ],
    )
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(AppNameForm, self).__init__(*args, **kwargs)

    def validate_app_name(self, field):
        app_by_name = next(get_applications(app_name=field.data), None)
        if app_by_name is not None:
            raise ValidationError('application name has already been taken')


class EventForm(FlaskForm):
    app_name = StringField('AppName',
        validators=[DataRequired()]
    )
    event_name = StringField('EventName',
        validators=[
            DataRequired(),
            Length(1, 64),
            Regexp('^[a-z][a-z0-9_]{3,}$', 0,
               'name must be lowercased ascii characters that start with a letter followed by letters, numbers or underscores'
            ),
        ],
    )
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)

    def validate(self):
        if not super(EventForm, self).validate():
            return False
        application = next(get_applications(app_name=self.app_name.data), None)
        if application:
            event = next(get_events(app_name=application.name, event_name=self.event_name.data), None)
            if not event:
                return True
            else:
                self.event_name.errors.append('event name already exists')
                return False
        else:
            self.event_name.errors.append('the parent application does not exist')
            return False
