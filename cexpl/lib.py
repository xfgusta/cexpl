"""Library interface"""

import requests

__all__ = [
    'Cexpl',
    'CexplError',
    'RequestError',
    'ResponseError',
    'NotFoundError',
    'ServerError',
    'JSONError'
]

class CexplError(Exception):
    """Base class for all errors"""

class RequestError(CexplError):
    """An error occurred while handling the request"""

class ResponseError(CexplError):
    """There was a client or server error"""

class NotFoundError(ResponseError):
    """Compiler not found"""

class ServerError(ResponseError):
    """The API service is having issues"""

class JSONError(CexplError):
    """Couldn't decode the text into json"""

class Cexpl:
    """Compiler Explorer API consumer"""
    def __init__(self, host='https://godbolt.org'):
        self.set_host(host)

    def set_host(self, host):
        """Set a Compiler Explorer host"""
        if not host.lower().startswith(('http://', 'https://')):
            host = f'http://{host}'
        self._host = host
        self._api = f'{self._host}/api'

    def get_host(self):
        """Get the current Compiler Explorer host"""
        return self._host

    def get_languages(self, fields=None):
        """Return a list of languages"""
        url = f'{self._api}/languages'

        # to see all the available fields, you can GET /api/languages?fields=all
        if fields:
            fields = ','.join(fields)

        return _request('GET', url, params={'fields': fields})

    def get_compilers(self, name=None, fields=None):
        """Returns a list of compilers"""
        url = f'{self._api}/compilers'

        if name:
            url += f'/{name}'

        # to see all the available fields, you can GET /api/compilers?fields=all
        if fields:
            fields = ','.join(fields)

        return _request('GET', url, params={'fields': fields})

    def compile_src(
        self,
        src,
        compiler,
        language=None,
        cflags=None,
        args=None,
        stdin=None,
        skip_asm=False,
        execute=False
    ):
        """Perform a compilation"""
        url = f'{self._api}/compiler/{compiler}/compile'

        payload = {
            'source': src,
            'options': {
                'compilerOptions': {
                    'skipAsm': skip_asm
                },
                'executeParameters': {
                },
                'filters': {
                    'execute': execute
                },
            }
        }

        if language:
            payload['lang'] = language

        if cflags:
            payload['options']['userArguments'] = cflags

        if args:
            payload['options']['executeParameters']['args'] = args

        if stdin:
            payload['options']['executeParameters']['stdin'] = stdin

        return _request('POST', url, json=payload)

    def generate_short_link(
        self,
        src,
        compiler,
        language=None,
        cflags=None,
        args=None,
        stdin=None,
        execute=False
    ):
        """Save the given state to a shortlink"""
        url = f'{self._api}/shortener'

        session = {
            'id': 1,
            'source': src,
            'compilers': [
                {
                    'id': compiler,
                }
            ]
        }

        if execute:
            executor = {
                'compiler': {
                    'id': compiler
                }
            }

            if args:
                executor['arguments'] = args

            if stdin:
                executor['stdin'] = stdin

            session['executors'] = [executor]

        if language:
            session['language'] = language

        if cflags:
            session['compilers'][0]['options'] = cflags
            if execute:
                session['executors'][0]['compiler']['options'] = cflags

        payload = {
            'sessions': [
                session
            ]
        }

        return _request('POST', url, json=payload)

def _request(method, url, **kwargs):
    """Make a request to the API"""
    try:
        response = requests.request(
            method,
            url,
            headers={'Accept': 'application/json'},
            **kwargs
        )
    except requests.RequestException as error:
        raise RequestError from error

    code = response.status_code
    if code == 404:
        raise NotFoundError
    if code == 505:
        raise ServerError

    if not response.ok:
        raise ResponseError

    try:
        return response.json()
    except requests.JSONDecodeError as error:
        raise JSONError from error
