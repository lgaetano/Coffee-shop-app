import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen
from .env import auth0_domain, algorithm, api_audience

AUTH0_DOMAIN = auth0_domain
ALGORITHMS = algorithm
API_AUDIENCE = api_audience

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header
# Source: https://github.com/udacity/FSND/blob/master/BasicFlaskAuth/app.py
def get_token_auth_header():
    ''' Retrieve access token from authorization header. '''
    
    # Check if authorization header exists
    if "Authorization" not in request.headers:
        raise AuthError({
                'code': 'authorization_header_missing',
                'description': 'Unable to parse authentication token.'
            }, 401)

    auth_header = request.headers['Authorization']
    header_parts = auth_header.split(" ")

    if len(header_parts) != 2:
        raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 401)
    # Confirm "bearer" token
    elif header_parts[0].lower() != "bearer":
        raise AuthError({
                'code': 'invalid_header',
                'description': 'Authorization header must be a bearer token.'
            }, 401)

    return header_parts[1]

# Source: https://github.com/udacity/FSND/blob/master/BasicFlaskAuth/app.py
def check_permissions(permission, payload):
    ''' Check user permissions. '''
    # Check for permissions array in JWT
    if 'permissions' not in payload:
        raise AuthError({
                'code': 'invalid_claims',
                'description': 'Permission not included in JWT.'
            }, 400)

    # Check if user has permission 
    if permission not in payload['permissions']:
        raise AuthError({
                'code': 'unauthorized',
                'description': 'Permission not found.'
            }, 403)
    
    return True

'''
!!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
# Source: https://github.com/udacity/FSND/blob/master/BasicFlaskAuth/app.py
def verify_decode_jwt(token):
    ''' Method to decode jwt token. '''
    # Get public key from AUTH0
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    
    # Get data in header
    unverified_header = jwt.get_unverified_header(token)
    
    # Choose key
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            # Use key to validate jwt
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)

        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)

    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)

# Source: https://github.com/udacity/FSND/blob/master/BasicFlaskAuth/app.py
def requires_auth(permission=''):
    ''' Decorator to require authorization. '''
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except Exception as e:
                print('ERROR: ', str(e))
                abort(403)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator