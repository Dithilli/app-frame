import requests
from flask import (
    Blueprint,
    redirect,
    request,
    session,
    flash,
    url_for,
    render_template,
    current_app as app,
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)
from ..decorators import (
    ssl_required,
)
from ..db import (
    get_user,
    get_user_by_login,
)
from .. import login_manager
bp = Blueprint('auth', __name__, url_prefix='/auth')


@login_manager.unauthorized_handler
def unauthorized():
    if current_user.is_authenticated:
        app.logger.warn("{user} attempted to access an unauthorized page"
                        .format(user=current_user.user_id))
        return render_template('unauthorized.html')
    else:
        return redirect(url_for('index'))


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_login(user_id)


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()


@bp.route('/login/')
def login():
    """
    login endpoint
    """
    # TODO: replace me with loginmanager
    # if session['state'] == request.args.get('state'):
    return redirect(
        "https://github.com/login/oauth/authorize"
        "?client_id={client_id}"
        "&state={state}"
        "&allow_signup=false"
        .format(
            client_id=app.config['GITHUB_CLIENT_ID'],
            state=request.args.get('state')
        )
        # "&scope=read:org"
    )
    # return redirect('/')


@bp.route('/callback/', methods=['GET', 'POST'])
def callback():
    """
    request that is called from github oauth
    """
    # if request.args.get('state') != session['state']:
    #     app.logger.error(
    #         "cb state '{}' != session state '{}'"
    #         .format(
    #             request.args.get('state'),
    #             session['state']
    #         )
    #     )
    #     return '', 404

    if 'code' in request.args:
        payload = {
            'client_id': app.config['GITHUB_CLIENT_ID'],
            'client_secret': app.config['GITHUB_CLIENT_SECRET'],
            'code': request.args['code']
        }
        resp = requests.post(
            app.config['TOKEN_URL'],
            params=payload,
            headers={'Accept': 'application/json'}
        )
        if not resp.ok:
            try:
                resp.raise_for_status()
            except Exception:
                app.logger.exception('auth failure')
            return 'failed to authenticate', 500

        data = resp.json()
        if 'access_token' in data:
            session['access_token'] = data['access_token']

            user = get_user(data['access_token'])
            if user is None:
                app.logger.error('user is none!')
                return '', 404

            login_user(user, remember=False, force=True)
            index_url = "{}{}".format(app.config.get('BASE_URL'), url_for('index'))

            return redirect(index_url)

        app.logger.error("github didn't return an access token")
        return '', 404
    return '', 404


@bp.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    index_url = "{}{}".format(app.config.get('BASE_URL'), url_for('index'))
    return redirect(index_url)
