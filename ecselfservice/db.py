from flask import (
    app,
    current_app,
)
import ulid
import json
import requests
from threading import Lock
from .models import (
    Permission,
    User,
    Application,
    Event,
)
from .signer import sign
from .errors import (
    SSBaseDataError,
    AppAlreadyExistsError,
    EventParentNotFoundError,
    EventAlreadyExists,
    InvalidDataInstanceType,
    map_error,
)


class ECMGRClient(object):

    def __init__(self, app_secret, base_url, conn_timeout=3.05,
                 read_timeout=5):

        self.secret = app_secret
        # removes trailing slash from base url if it exists
        self._base_url = base_url.rstrip('//')
        self._conn_timeout = conn_timeout
        self._read_timeout = read_timeout
        self._session = requests.Session()

    def get_app(self, app_name):
        pass

    def create_app(self, app):
        url_path = 'v1/a/apps/{}'.format(app.name)
        url = '/'.join([self._base_url, url_path])

        payload = json.dumps({'createdBy': app.created_by})

        sig = sign("POST", url_path, payload, [], self.secret)

        headers = {
            'Authorization': 'Bearer {sig}'.format(sig=sig),
            'Content-Type': 'application/json'
        }

        res = self._session.post(
            url,
            headers=headers,
            data=payload,
            timeout=(self._conn_timeout, self._read_timeout)
        )

        if res.status_code == requests.codes.ok:
            response = res.json()
            return Application(
                response['id'],
                response['name'],
                response['createdBy'],
                response['createdOn']
            )
        else:
            # raises error
            self._handle_api_error(res)
            return app

    def create_event(self, event):
        app = event.parent_app
        url_path = 'v1/a/apps/{}/events/{}'.format(app.name, event.name)
        url = '/'.join([self._base_url, url_path])

        payload = json.dumps({'createdBy': event.created_by})

        sig = sign("POST", url_path, payload, [], self.secret)

        headers = {
            'Authorization': 'Bearer {sig}'.format(sig=sig),
            'Content-Type': 'application/json'
        }

        res = self._session.post(
            url,
            headers=headers,
            data=payload,
            timeout=(self._conn_timeout, self._read_timeout)
        )

        if res.status_code == requests.codes.ok:
            response = res.json()

            event_id = ulid.new().str
            new_event = Event(
                event_id,
                response['name'],
                response['createdBy'],
                response['createdOn'],
                None
            )
            new_event.set_parent(app)

            return new_event
        else:
            # raises error
            self._handle_api_error(res)
            return event

    def get_events(self, app):
        app_name = app.name if hasattr(app, 'name') else app['name'] if 'name' in app else app
        url_path = 'v1/a/apps/{}/events'.format(app_name)
        url = '/'.join([self._base_url, url_path])
        payload = b''

        sig = sign("GET", url_path, payload, [],
                   self.secret)

        headers = {
            'Authorization': 'Bearer {sig}'.format(sig=sig),
            'Content-Type': 'application/json'
        }

        res = self._session.get(
            url,
            headers=headers,
            timeout=(self._conn_timeout, self._read_timeout)
        )

        if res.status_code == requests.codes.ok:
            response = res.json()
            for event in response['events']:
                # TODO: change when event generates ulid ID
                ulid_str = ulid.new().str
                yield Event(
                    ulid_str,
                    event['name'],
                    event['createdBy'],
                    event['createdOn'],
                    response['app']['id']
                )
        else:
            # raises error
            self._handle_api_error(res)
            return []

    def get_event(self, app_name, event_name):
        pass

    def get_apps(self):
        url_path = 'v1/a/apps'
        url = '/'.join([self._base_url, url_path])
        payload = b''

        sig = sign("GET", url_path, payload, [],
                          self.secret)

        headers = {
            'Authorization': 'Bearer {sig}'.format(sig=sig),
            'Content-Type': 'application/json'
        }

        res = self._session.get(
            url,
            headers=headers,
            timeout=(self._conn_timeout, self._read_timeout)
        )

        if res.status_code == requests.codes.ok:
            result = res.json()
            for app in result:
                yield Application(
                    app['id'],
                    app['name'],
                    app['createdBy'],
                    app['createdOn']
                )
        else:
            # raises error
            self._handle_api_error(res)
            return []

    @classmethod
    def _handle_api_error(cls, res):
        '''
        handles api specific errors from eventcollector
        '''
        raise map_error(res)

    def close(self):
        '''
        closes request session if defined
        '''
        if self._session is not None:
            self._session.close()


def ecmgr_client():
    return ECMGRClient(
        app_secret=current_app.config['EVENTCOLLECTOR_SECRET'],
        base_url=current_app.config['EVENTCOLLECTOR_URL'],
    )


def generate_secure_token(num_bytes=32):
    from secrets import token_bytes
    from base64 import b64encode
    return b64encode(token_bytes(num_bytes)).decode()


def run_graphql_query(query, access_token=None, **kwargs):
    """
    A simple function to use requests.post to make the API call.
    Note the json= section.
    """
    headers = {'Accept': 'application/json'}
    auth = None
    if access_token:
        headers["Authorization"] = "token {}".format(access_token)
        auth = (None, access_token)

    resp = requests.post(
        current_app.config['GRAPHQL_URL'],
        json={'query': query, **kwargs},
        headers=headers,
        auth=auth
    )
    if resp.ok:
        return resp.json()
    else:
        raise Exception("Query Failure: code=[{}]"
                        .format(resp.status_code))


def _github_self_query(access_token):
    """
    github self query to git login name and avatar
    TODO: fix support for read:org to return if user is part of
          required org
    """
    graphql_query = """
    query {
      self: viewer {
        login
        avatar: avatarUrl(size: 30)
        #query($required_org: String!) {
        #org: organization(login: $required_org){
        #  login
        #}
      }
    }
    """
    variables = {
        # 'required_org': ORG
    }
    data = run_graphql_query(graphql_query, access_token, variables=variables)
    return data['data']['self']


def _github_user_teams_query(user_login):
    """
    returns the following structure
    case class Member(login: String, name: String)
    case class Members(member_role: String, member_url: String, member: Member)
    case class TeamMemberships(total: Int, members: List[Members])
    case class TeamMembership(team_name: String, team_slug: String,
                              team_description: Option[String],
                              team_memberships: TeamMemberships)
    case class UserMemberships(login: String, teams: Map[String,
                               Option[TeamMembership]])
    case class QueryResult(user_memberships: UserMemberships)
    """
    def subteam_query(team):
        """
        determine if user belongs to team
        """
        return \
            "{team_alias}: team(slug: \"{team_name}\") {{ ...teamMembership }}"\
            .format(team_alias=team.replace("-", "_"), team_name=team)

    subteam_queries = list(subteam_query(team) for team in
                           current_app.config['EVENTCOLLECTOR_TEAMS'])
    user_teams = "\n".join(subteam_queries)

    query = """
        query ($org: String!, $user: String!) {
          user_memberships: user(login: $user) {
            avatar: avatarUrl(size: 30)
            teams: organization(login: $org){
              %s
            }
          }
        }
        """ % user_teams

    fragments = """
        fragment teamMembership on Team {
          team_name: name
          team_slug: slug
          team_description: description
          team_memberships: members(first: 100, query: $user){
            total: totalCount
            members: edges{
              member_role: role
              member_url: memberAccessUrl
              member: node {
                login
                name
              }
            }
          }
        }
        """
    graphql_query = query + fragments
    variables = {
        'org': current_app.config['ORG'],
        'user': user_login,
    }
    data = run_graphql_query(graphql_query, None, variables=variables)
    return data['data']['user_memberships']


def determine_user_memberships(login, data):
    def has_login(m):
        return m['member']['login'] == login

    def filter_non_empty(f):
        return len(list(f)) > 0

    for key, value in (data['teams'] or {}).items():
        yield {
            'name': value['team_name'],
            'id': value['team_slug'],
            'is_member':
                value['team_memberships']['total'] > 0 and \
                filter_non_empty(filter(has_login,
                                        value['team_memberships']['members']))
        }


def get_roles_for_login(user_login, memberships):
    """
    returns an iterator of memberships for a given login
    """
    active_memberships = \
        list(i for i in memberships if i['is_member'] is True)

    if len(active_memberships) <= 0:
        yield Permission.UNAUTHORIZED
    else:
        yield Permission.READ
        for i in memberships:
            if i['id'] == current_app.config['EVENTCOLLECTOR_WRITER'] and i['is_member'] is True:
                yield Permission.WRITE

        # # TODO: add support for whitelist admins
        # for user in WHITELISTED_ADMINS:
        #     if user == user_login:
        #         yield Permission.WRITE
        #         yield Permission.ADMIN


def get_user_by_login(user_id):
    try:
        # NOTE: for testing
        # user_id = "jkachmar"

        user_teams = _github_user_teams_query(user_id)
        memberships = list(determine_user_memberships(user_id, user_teams))
        user_avatar = user_teams['avatar']
        roles = list(r for r in get_roles_for_login(user_id, memberships))
        return User(user_id=user_id, avatar=user_avatar, roles=roles, teams=memberships)
    except Exception:
        current_app.logger.exception("error getting roles for login")
        return None


def get_user(access_token):
    try:
        # [IO] get user information from self query
        gh_user_data = _github_self_query(access_token)
        user_id = gh_user_data['login']
        avatar = gh_user_data['avatar']
    except Exception:
        current_app.logger.exception("error querying self user")
        return None

    return get_user_by_login(user_id)


_topic_data = None


def get_applications(app_name=None):
    # apps = _get_or_update_data()
    client = ecmgr_client()
    apps = client.get_apps()
    for app in apps:
        if app_name is None:
            yield app
            events = ecmgr_client().get_events(app)
            for event in events:
                yield event
        else:
            if isinstance(app, Application):
                if app.name == app_name:
                    yield app


def deserialize_apps():
    mappings = {}
    DATA = get_applications()
    for e in sorted(DATA, key=lambda i: (i.type, i.id)):
        if e.type == 'event':
            event = Event.parse(e)
            event.set_parent(mappings['apps'][event.parent_app_id])
            mappings.setdefault('events', {})\
                .setdefault(event.parent_app_id, []).append(event)
        elif e.type == 'application':
            application = Application.parse(e)
            mappings.setdefault('apps', {})[application.identifier] = application

    apps = mappings['apps'] if 'apps' in mappings else {}
    for app_id, application in sorted(apps.items(), reverse=True):
        events = mappings['events'] if 'events' in mappings else {}
        sorted_events = sorted(events.get(app_id, []),
                               key=lambda e: e.identifier, reverse=True)
        application.add_events(list(sorted_events))
        yield application

_lock = Lock()

def _get_or_update_data(item_to_append=None):
    with _lock:
        # HACK: YES I KNOW! global is evil
        global _topic_data
        if _topic_data is None:
            _topic_data = list(deserialize_apps())

        if item_to_append is not None:
            # throws exception
            _append_application_data(item_to_append, _topic_data)
            _topic_data.sort(key=lambda e: e.identifier, reverse=True)

        return _topic_data


def _append_application_data(item, data):
    try:
        if isinstance(item, Application):
            def _find_app_by_name(a):
                return a.name == item.name

            # search the instances to see if the app name already exists
            found_app = next(filter(_find_app_by_name, data), None)
            if found_app:
                raise AppAlreadyExistsError('attempting to add an application '
                                            'that already exists',
                                            app_name=item.name)
            data.append(item)
        elif isinstance(item, Event):
            # locate the event's parent application
            # determine if event doesnt already exist
            # add event if found parent app and event DNE
            parent_id, parent_name = \
                (item.parent_app.identifier, item.parent_app.name) if \
                item.parent_app else \
                (item.parent_app_id, None)

            def _find_app_by_identifier(a):
                return a.identifier == parent_id

            def _find_event_by_name(e):
                return e.name == item.name

            # before adding, ensure the parent app exists
            found_app = next(filter(_find_app_by_identifier, data), None)
            if not found_app:
                raise \
                    EventParentNotFoundError('attempt to add event to a '
                                             'parent application that does '
                                             'not exist',
                                             app_name=parent_name or parent_id,
                                             event_name=item.name)

            # before adding the event, ensure it doesnt already exist
            event = next(filter(_find_event_by_name, found_app.events), None)
            if event:
                raise EventAlreadyExists('attempt to add event '
                                         'that already exists',
                                         app_name=parent_name or parent_id,
                                         event_name=item.name)
            # append the event
            found_app.events.append(item)
            found_app.events.sort(key=lambda k: k.identifier, reverse=True)
        else:
            raise InvalidDataInstanceType('attempt to add an unexpected type.'
                                          'expects Application or Event but '
                                          'received %s' % item.__class__)
    except SSBaseDataError:
        raise
    except Exception:
        current_app.logger.exception('unexpected error while appending data')
        raise


def add_event(event):
    """
    attempt to add an event to it's parent app
    raises SSBaseError
    """
    client = ecmgr_client()
    item = client.create_event(event)
    _get_or_update_data(item_to_append=item)


def add_application(app, secure_token):
    """
    attempt to add a new application
    raises SSBaseError
    """
    client = ecmgr_client()
    item = client.create_app(app)
    _get_or_update_data(
        item_to_append=item
    )


def get_events(app_name=None, event_name=None):
    for app in get_applications(app_name=app_name):
        for event in app.events:
            if event_name is None:
                yield event
            else:
                if event.name == event_name:
                    yield event


def get_application_event_data(app_name=None):
    apps = _get_or_update_data()
    if app_name is None:
        return apps

    def filter_by_app_name(application):
        return application.name == app_name

    return list(filter(filter_by_app_name, apps))
