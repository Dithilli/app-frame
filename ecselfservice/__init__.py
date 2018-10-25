import os
from flask import (
    Flask,
    render_template,
    current_app,
)
from .config import Config
from flask_login import (
    LoginManager,
    current_user,
)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.url_map.strict_slashes = False
    # app.register_error_handler(403, unauthorized)
    config = Config()
    config.init_app(app)
    app.config.from_object(config)

    login_manager.init_app(app)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from .applications import bp as applications_bp
    app.register_blueprint(applications_bp)

    app.add_url_rule('/', endpoint='index')

    return app
