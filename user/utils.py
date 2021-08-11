from HelpingHearts.settings import blackListedTokens
from datetime import datetime, timedelta
import jwt
from django.conf import settings


def generate_access_token(user):

    access_token_payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow()
    }
    access_token = jwt.encode(access_token_payload, settings.SECRET_KEY, algorithm='HS256').decode('utf-8')
    if access_token in blackListedTokens:
        blackListedTokens.discard(access_token)
    return access_token


def generate_refresh_token(user):
    refresh_token_payload = {
        'user.id': user.id,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    refresh_token = jwt.encode(refresh_token_payload, settings.REFRESH_SECRET_KEY, algorithm='HS256').decode('utf-8')
    if refresh_token in blackListedTokens:
        blackListedTokens.discard(refresh_token)
    return refresh_token
