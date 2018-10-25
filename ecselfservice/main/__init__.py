from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from ..decorators import (
    ssl_required,
)
bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    data = {}
    return render_template('index.html', **data)


@bp.route('/unauthorized/')
def unauthorized():
    data = {}
    return render_template('unauthorized.html', **data)
