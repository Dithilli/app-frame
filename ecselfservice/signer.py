from base64 import b64encode, b64decode
import hashlib
import hmac
import six

ON_NEW_LINE = '\n'


def sign(method, url, payload, items, app_secret):
    encoded_payload = hash_and_b64encode(payload)
    encoded_req_str = hash_and_b64encode(build_req_str(method, url,
                                                       encoded_payload))
    if items is None:
        items = []
    return compute_signature(items, app_secret, encoded_req_str)


def hash_and_b64encode(value):
    return b64encode(hashlib.sha256(utf8(value)).digest())


def utf8(value):
    if isinstance(value, six.text_type):
        return value.encode('utf-8')
    return value


def build_req_str(method, url, encoded_payload):
    if not url.startswith("/"):
        url = "/{url}".format(url=url)
    return ON_NEW_LINE.join([method, url, encoded_payload.decode()])


def compute_signature(items, app_secret, encoded_req_str):
    if items is None:
        items = []
    req_str_with_app_name = ON_NEW_LINE.\
        join(items + [encoded_req_str.decode()])
    sig = hmac.new(b64decode(app_secret),
                   utf8(req_str_with_app_name), hashlib.sha256).digest()
    return b64encode(sig).decode()
