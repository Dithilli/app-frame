from flask import current_app as app
from flask_login import UserMixin, AnonymousUserMixin
import arrow
import ulid
from arrow.parser import ParserError
from datetime import datetime
from . import login_manager
import random
import string


def gen_state():
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in range(32))


class Permission:
    UNAUTHORIZED = 1
    READ = 2
    WRITE = 4
    ADMIN = 8


class User(UserMixin):
    """
    information regarding the authenticated user
    """
    def __init__(self, user_id, avatar, roles, teams):
        self.id = user_id
        self.user_id = self.id
        self.avatar = avatar
        self.roles = roles or []
        self.teams = teams or []
        self.last_seen = datetime.utcnow()

    def can(self, perm):
        """
        if the user has a specific permission
        """
        for role in self.roles:
            if role == perm:
                return True
        return False

    def is_administrator(self):
        """
        if the user is an admin
        """
        return self.can(Permission.ADMIN)

    def has_read_access(self):
        """
        if the user has the ability to read
        """
        return self.can(Permission.READ)

    def has_write_access(self):
        """
        if the user has the ability to write
        """
        return self.can(Permission.WRITE)

    def ping(self):
        """
        sets the last user interaction time
        """
        self.last_seen = datetime.utcnow()


class AnonymousUser(AnonymousUserMixin):
    """
    if a user hasnt logged in yet they are considered "anonymouse"
    """
    def __init__(self):
        self.user_id = "anonymous"
        self.state = gen_state()

    def can(self, permissions):
        """
        if the user has a specific permission
        anonymous users always returns False
        """
        return False

    def is_administrator(self):
        """
        if the user is an admin
        """
        return self.can(Permission.ADMIN)

    def has_read_access(self):
        """
        if the user has the ability to read
        """
        return self.can(Permission.READ)

    def has_write_access(self):
        """
        if the user has the ability to write
        """
        return self.can(Permission.WRITE)


login_manager.anonymous_user = AnonymousUser


def get_date(millis):
    try:
        date = arrow.get(millis)
    except ParserError:
        app.logger.exception("error parsing datetime value=[{}]"
                             .format(millis))
        raise
    except ValueError:
        # if attempting to parse a long fails, then it will
        # fall back to attempt to extract the milliseconds
        sec, ms = divmod(millis, 1000)
        # since the values are millisecond truncated
        # pad the right of the value with 6 zeros
        date = \
            arrow.get(sec).replace(microseconds=int('{:<06d}'.format(ms)))
    return date


class Application(object):
    """
    The top level application/service that describes an event stream
    """
    def __init__(self, identifier, name, created_by, created_on):
        if created_on is None:
            created_on = arrow.utcnow()
        self.created_on = get_date(created_on)

        if identifier is None:
            self.identifier = \
                ulid.from_timestamp(self.created_on.datetime).str
        else:
            self.identifier = identifier

        self.id = self.identifier
        self.name = name
        self.created_by = created_by
        self.events = []
        self.type = 'application'

    def add_events(self, events):
        """
        a function that adds events to an application
        """
        self.events = events

    @staticmethod
    def parse(data):
        """
        parses application data from dictionary object
        TODO will be replaced by avro parser
        """
        if isinstance(data, Application):
            return data
        else:
            return Application(
                identifier=data['id'],
                name=data['name'],
                created_by=data['created_by'],
                created_on=data['created_on']
            )

    def serialize(self):
        return {
            'id': self.identifier,
            'type': 'application',
            'name': self.name,
            'created_by': self.created_by,
            'created_on': int(round(self.created_on.float_timestamp * 1000)),
        }


class Event(object):
    """
    An event that belongs to an application
    """
    def __init__(self, identifier, name, created_by, created_on,
                 parent_app_id):
        if created_on is None:
            created_on = arrow.utcnow()
        self.created_on = get_date(created_on)

        if identifier is None:
            self.identifier = \
                ulid.from_timestamp(self.created_on.datetime).str
        else:
            self.identifier = identifier

        self.id = self.identifier
        self.name = name
        self.created_by = created_by
        self.parent_app_id = parent_app_id
        self.parent_app = None
        self.type = 'event'

    def set_parent(self, parent_application):
        """
        sets the parent application for the event
        """
        self.parent_app_id = parent_application.identifier
        self.parent_app = parent_application
        return self

    @staticmethod
    def parse(data):
        """
        parses event data from dictionary object
        TODO will be replaced by avro parser
        """
        if isinstance(data, Event):
            return data
        else:
            return Event(
                identifier=data['id'],
                name=data['name'],
                created_by=data['created_by'],
                created_on=data['created_on'],
                parent_app_id=data['parent_id']
            )

    def serialize(self):
        return {
            'id': self.identifier,
            'type': 'event',
            'parent_id': self.parent_app.identifier if self.parent_app is not None else self.parent_app_id,
            'name': self.name,
            'created_by': self.created_by,
            'created_on': int(round(self.created_on.float_timestamp * 1000)),
        }
