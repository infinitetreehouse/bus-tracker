from authlib.integrations.flask_client import OAuth


oauth = OAuth()


def init_oauth(app):
    oauth.init_app(app)

    oauth.register(
        name='google',
        server_metadata_url=(
            'https://accounts.google.com/.well-known/openid-configuration'
        ),
        client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
        client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
        client_kwargs={
            'scope': 'openid email profile',
        },
    )
