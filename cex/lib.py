"""Library interface"""

import requests

__all__ = [
    'Cex',
    'CexError',
    'RequestError',
    'ResponseError',
    'NotFoundError',
    'ServerError',
    'JSONError'
]

class CexError(Exception):
    """Base class for all errors"""

class RequestError(CexError):
    """An error occurred while handling the request"""

class ResponseError(CexError):
    """There was a client or server error"""

class NotFoundError(ResponseError):
    """Compiler not found"""

class ServerError(ResponseError):
    """The API service is having issues"""

class JSONError(CexError):
    """Couldn't decode the text into json"""

class Cex:
    """Compiler Explorer API consumer"""
    def __init__(self, host='https://godbolt.org'):
        self.set_host(host)

    def set_host(self, host):
        """Set a Compiler Explorer host"""
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
                'filters': {
                    'execute': execute
                },
            }
        }

        if language:
            payload['lang'] = language

        if cflags:
            payload['options']['userArguments'] = cflags

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
