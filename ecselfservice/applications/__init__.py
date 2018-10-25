from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    url_for,
    current_app,
)
from flask_login import (
    login_required,
    current_user,
)
from ..decorators import (
    admin_required,
    read_required,
    write_required,
    permission_required,
    ssl_required,
)
from ..db import (
    get_application_event_data,
    add_application,
    add_event,
    get_events,
    get_applications,
    generate_secure_token,
)
from ..models import (
    Application,
    Event,
)
from ..errors import SSBaseError
from .forms import AppNameForm, EventForm

PREFIX = 'applications'
bp = Blueprint(PREFIX, __name__, url_prefix='/%s' % PREFIX)


@bp.route('/')
@login_required
@read_required
def applications():
    apps = get_application_event_data()
    data = {'apps': apps}

    return render_template('%s/list-applications.html' % PREFIX, **data)


@bp.route('/<string:app_name>/view/')
@login_required
@read_required
def application(app_name):
    apps = get_application_event_data(app_name=app_name)
    if len(apps) == 0:
        return f'{app_name} not found', 404

    data = {'app': apps[0]}
    return render_template('%s/new-application.html' % PREFIX, **data)


@bp.route('/success/')
def success():
    data = {
        'app_name': 'your_new_app',
        'secure_token': 'ImicxwyxoodZSuf1WO4QVrw6IZfWXT7L80AMdGV4f2A=',
    }
    return render_template('%s/created-application.html' % PREFIX, **data)


@bp.route('/new/', methods=['GET', 'POST'])
@login_required
@write_required
def application_new():
    data = {'app': None}
    form = AppNameForm()
    if form.validate_on_submit():
        app_name = form.app_name.data
        created_by = current_user.user_id
        application = Application(name=app_name,
                                  created_by=created_by,
                                  identifier=None, created_on=None)
        try:
            secure_token = generate_secure_token()
            add_application(application, secure_token)
            data['secure_token'] = secure_token
            data['app'] = application
            current_app.logger.info(f'type=[new_application] app_name=[{app_name}] created_by=[{created_by}]')
        except SSBaseError:
            current_app.logger.exception('type=[new_application_validation_failure] app_name=[{app_name}] created_by=[{created_by}]')
        except Exception:
            current_app.logger.exception('type=[new_application_failure] app_name=[{app_name}] created_by=[{created_by}]')

    data['form'] = form
    return render_template('%s/new-application.html' % PREFIX, **data)


@bp.route('/events/')
@login_required
@read_required
def events_all():
    return redirect(url_for('applications.events'))


@bp.route('/events/all/')
@login_required
@read_required
def events():
    apps = get_application_event_data()
    data = {'apps': apps}
    return render_template('%s/list-events.html' % PREFIX, **data)


@bp.route('/<string:app_name>/events/')
@login_required
@read_required
def application_events(app_name):
    apps = get_application_event_data(app_name=app_name)
    if len(apps) == 0:
        return f'{app_name} not found', 404

    data = {'apps': apps, 'current_app': app_name}
    return render_template('%s/list-events.html' % PREFIX, **data)


@bp.route('/<string:app_name>/events/new/', methods=['GET', 'POST'])
@login_required
@read_required
def application_event_new(app_name):
    data = {}
    app = next(get_applications(app_name=app_name), None)
    if not app:
        # the app being requested no longer exists
        return redirect(url_for('applications.applications'))

    form = EventForm()
    form.app_name.data = app.name

    if form.validate_on_submit():
        event_name = form.event_name.data
        created_by = current_user.user_id
        new_event = Event(name=event_name,
                          created_by=created_by,
                          parent_app_id=app.identifier,
                          identifier=None,
                          created_on=None)
        new_event.set_parent(app)
        try:
            add_event(new_event)
            current_app.logger.info(f'type=[new_event] app_name=[{app.name}] event_name=[{event_name}] created_by=[{created_by}]')
            return redirect(url_for('applications.application_events', app_name=app.name))
        except SSBaseError:
            current_app.logger.exception('type=[new_event_validation_failure] app_name=[{app_name}] event_name=[{event_name}] created_by=[{created_by}]')
        except Exception:
            current_app.logger.exception('type=[new_event_failure] app_name=[{app_name}] event_name=[{event_name}] created_by=[{created_by}]')

    data['form'] = form
    return render_template('%s/new-event.html' % PREFIX, **data)
