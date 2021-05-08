import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen

AUTH0_DOMAIN = 'lgaetano.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'drinks'

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

'''
@DONE? implement get_token_auth_header() method
    X it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    X it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    X return the token part of the header
'''
def get_token_auth_header(token):
    ''' Retrieve access token from authorization header. '''
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
    elif header_parts[0].lower() != "bearer":
        raise AuthError({
                'code': 'invalid_header',
                'description': 'Authorization header must be a bearer token.'
            }, 401)

    return header_parts[1]


'''
@DONE implement check_permissions(permission, payload) method
'''
def check_permissions(permission, payload):
    ''' Check permissions. '''
    if 'permissions' not in payload:
        raise AuthError({
                'code': 'invalid_claims',
                'description': 'Permission not included in JWT.'
            }, 400)
            
    if permission not in payload['permissions']:
        raise AuthError({
                'code': 'unauthorized',
                'description': 'Permission not found.'
            }, 403)
    
    return True

'''
@DONE implement verify_decode_jwt(token) method
    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
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

'''
@DONE implement @requires_auth(permission) decorator method
'''
def requires_auth(permission=''):
    ''' Decorator to require authorization. '''
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except:
                abort(401)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator