import os
from flask_dotenv import DotEnv


class Config:
    """
    configuration that is shared throughout the application
    """
    SSL = True
    BASE_URL = 'https://ecselfservice.ngrok.io'
    SECRET_KEY = os.environ.get('SESSION_SECRET_KEY', 'dev')
    EVENTCOLLECTOR_WRITER = 'eventcollectorowner'
    # EVENTCOLLECTOR_READER = 'wework-engineering'
    EVENTCOLLECTOR_READER = 'data-engineering'
    EVENTCOLLECTOR_TEAMS = {
        EVENTCOLLECTOR_WRITER,
        EVENTCOLLECTOR_READER,
    }
    ORG = 'WeConnect'
    GRAPHQL_URL = 'https://api.github.com/graphql'
    TOKEN_URL = 'https://github.com/login/oauth/access_token'
    GH_REST_TEAMS_URL = 'https://github.com/login/oauth/access_token'
    # EVENTCOLLECTOR_SECRET = os.environ.get('EVENTCOLLECTOR_SECRET')
    # EVENTCOLLECTOR_URL = os.environ.get('EVENTCOLLECTOR_URL')
    # GITHUB_CLIENT_ID = ''
    # GITHUB_CLIENT_SECRET = ''

    @classmethod
    def init_app(self, app):
        """
        initializes the application secrets through a ".env" file
        """
        env = DotEnv()
        env.init_app(app, verbose_mode=True)
