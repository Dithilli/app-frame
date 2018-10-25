"""
custom exceptions
"""


class SSBaseError(Exception):
    """
    base exception for all self service exceptions
    """
    pass


class SSBaseDataError(SSBaseError):
    """
    base exception for interaction with in
    memory data representation
    """
    pass


class InvalidDataInstanceType(SSBaseDataError):
    """
    error that describes when attempting to add
    an unexpected type
    must be an Application or an Event
    """
    def __init__(self, *args, **kwargs):
        super(InvalidDataInstanceType, self).__init__(*args, **kwargs)


class AppAlreadyExistsError(SSBaseDataError):
    """
    error that describes when attempting to add an
    application that already exists
    """
    def __init__(self, *args, **kwargs):
        self.app_name = kwargs.pop('app_name') if \
            'app_name' in kwargs else None
        self.event_name = kwargs.pop('event_name') if \
            'event_name' in kwargs else None
        super(AppAlreadyExistsError, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f"AppAlreadyExistsError(app_name={self.app_name}, event_name={self.event_name})"

    def __str__(self):
        return f"{self.message} app_name=[{self.app_name}] event_name=[{self.event_name}]"


class EventParentNotFoundError(SSBaseDataError):
    """
    error that describes when attempting to add an
    event to an application that does not exist
    """
    def __init__(self, *args, **kwargs):
        self.app_name = kwargs.pop('app_name') if \
            'app_name' in kwargs else None
        self.event_name = kwargs.pop('event_name') if \
            'event_name' in kwargs else None
        super(EventParentNotFoundError, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f"EventParentNotFoundError(app_name={self.app_name}, event_name={self.event_name})"

    def __str__(self):
        return f"{self.message} app_name=[{self.app_name}] event_name=[{self.event_name}]"


class EventAlreadyExists(SSBaseDataError):
    """
    error that describes when attempting to add an
    event to an application where the event already
    exists
    """
    def __init__(self, *args, **kwargs):
        self.app_name = kwargs.pop('app_name') if \
            'app_name' in kwargs else None
        self.event_name = kwargs.pop('event_name') if \
            'event_name' in kwargs else None
        super(EventAlreadyExists, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f"EventAlreadyExists(app_name={self.app_name}, event_name={self.event_name})"

    def __str__(self):
        return f"{self.message} app_name=[{self.app_name}] event_name=[{self.event_name}]"


class ECMGRAPIError(SSBaseError):
    '''
    Unexpected api error response
    '''
    def __init__(self, message):
        super(ECMGRAPIError, self).__init__()
        self.message = message


class InvalidEventError(SSBaseError):
    '''
    Error indicates a serialization error where the
    dict supplied cannot be converted to valid avro bytes
    '''
    def __init__(self, validation_errors, event):
        message = \
            'Invalid event: {event}, validation errors: {validation_errors}'\
            .format(event=event, validation_errors=validation_errors)
        super(InvalidEventError, self).__init__(self, message)


class SchemaEvolutionError(SSBaseError):
    '''
    Error indicates a schema registration error
    '''
    def __init__(self, message, errors):
        self.message = message
        self.errors = errors
        super(SchemaEvolutionError, self).__init__(message)

    def __str__(self):
        return "{message}: errors: {errors}"\
            .format(message=self.message,
                    errors=', '.join(self.errors))


def map_error(resp):
    '''
    Error mapper that maps error based on attributes
    '''
    def _handle_evolution(resp_dict):
        if 'detail' not in resp_dict:
            return None

        fmt_str = "title=[{title}] field=[{field}] detail=[{detail}]"
        errors = list(fmt_str.format(title=err["title"],
                                     field=err["fieldName"],
                                     detail=err['detail'])
                      for err in resp_dict["errors"])
        return SchemaEvolutionError(resp_dict['detail'], errors)

    def _handle_default(resp_dict):
        if 'detail' not in resp_dict:
            return None

        return ECMGRAPIError(resp_dict['detail'])

    # add specific type handlers here
    error_map = {
        'https://eventcollector.we.co/v1/errors#schema-evolution-error':
            _handle_evolution,
    }

    json_dict = resp.json()
    if 'type' in json_dict:
        error_type = json_dict['type']
        handler = error_map.get(error_type)
        if handler is None:
            handler = _handle_default
        err = handler(json_dict)
        if err:
            return err

    # fallback handler for unexpected situations
    return ECMGRAPIError('Unknown API response: {res}'.format(res=resp))
