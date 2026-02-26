import os

from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, g, redirect, render_template, session, url_for

from bustracker.auth import init_oauth, oauth
from bustracker.auth_service import (
    MSG_NO_SCHOOLS,
    get_user_allowed_schools,
    sync_user_from_google_claims,
)
from bustracker.auth_utils import login_required
from bustracker.config import DevConfig, ProdConfig
from bustracker.db import get_session, init_engine, ping_db
from bustracker.models.user import User
from bustracker.ui_demo_data import (
    get_demo_bus_run_edit_view,
    get_demo_bus_run_view,
    get_demo_home_options,
)


def _norm_str(val):
    if val is None:
        return None
    val = str(val).strip()
    if val == '':
        return None
    return val


def _build_compact_user_display_name(user):
    given_name = _norm_str(user.given_name)
    family_name = _norm_str(user.family_name)
    email = _norm_str(user.email)

    if given_name is not None and family_name is not None:
        return given_name + ' ' + family_name[0] + '.'

    if email is not None:
        return email

    return 'Unknown User'


def _get_current_user(db, user_id):
    if user_id is None:
        return None
    return db.get(User, user_id)


def _format_date_mmddyyyy(val):
    if val is None:
        return ''

    # Accept date/datetime objects
    if hasattr(val, 'strftime'):
        return val.strftime('%m/%d/%Y')

    s = str(val).strip()

    # Accept ISO date strings like "2026-02-25"
    try:
        d = datetime.strptime(s, '%Y-%m-%d')
        return d.strftime('%m/%d/%Y')
    except ValueError:
        pass

    # If it’s not parseable, just return it as-is (better than crashing)
    return s


def create_app():
    # Load .env for local dev (harmless in prod if .env not present)
    load_dotenv()

    app = Flask(__name__)
    
    app.jinja_env.filters['mmddyyyy'] = _format_date_mmddyyyy

    env = os.getenv('FLASK_ENV', 'development').lower()
    cfg = ProdConfig() if env == 'production' else DevConfig()

    app.config['SECRET_KEY'] = cfg.SECRET_KEY
    app.config['APP_BASE_URL'] = cfg.APP_BASE_URL
    app.config['GOOGLE_OAUTH_CLIENT_ID'] = cfg.GOOGLE_OAUTH_CLIENT_ID
    app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = cfg.GOOGLE_OAUTH_CLIENT_SECRET
    app.config['GOOGLE_OAUTH_REDIRECT_URI'] = cfg.GOOGLE_OAUTH_REDIRECT_URI

    init_engine(cfg.SQLALCHEMY_DATABASE_URI)

    # OAuth (Google OIDC)
    init_oauth(app)

    @app.before_request
    def open_db_session():
        g.db = get_session()

    @app.teardown_request
    def close_db_session(exc):
        db = getattr(g, 'db', None)
        if db is None:
            return

        try:
            if exc is None:
                db.commit()
            else:
                db.rollback()
        finally:
            db.close()

    @app.context_processor
    def inject_template_globals():
        user_id = session.get('user_id')
        current_user_display_name = None

        if user_id is not None:
            user = _get_current_user(g.db, user_id)
            if user is not None:
                current_user_display_name = _build_compact_user_display_name(user)

        return {
            'is_logged_in': bool(user_id is not None),
            'current_user_display_name': current_user_display_name,
        }

    @app.get('/health')
    @login_required
    def health():
        try:
            ping_db()
        except Exception:
            return 'database error', 500
        return 'ok', 200

    @app.get('/')
    def public_landing():
        if session.get('user_id') is not None:
            return redirect(url_for('home'))

        return render_template('public_landing.html')

    @app.get('/login')
    def login():
        # If a protected route sent the user here, keep that destination
        if not session.get('next_url'):
            session['next_url'] = url_for('home')

        redirect_uri = app.config['GOOGLE_OAUTH_REDIRECT_URI']
        return oauth.google.authorize_redirect(redirect_uri)

    @app.get('/logged-out')
    def logged_out():
        return render_template('logged_out.html')

    @app.get('/logout')
    def logout():
        session.clear()
        return redirect(url_for('logged_out'))

    @app.get('/oauth/callback')
    def oauth_callback():
        token = oauth.google.authorize_access_token()

        userinfo = token.get('userinfo')
        if userinfo is None:
            userinfo = oauth.google.parse_id_token(token)

        user_id, err = sync_user_from_google_claims(g.db, userinfo)
        if err is not None:
            # Defensive: ensure we never commit on auth failure.
            g.db.rollback()
            return (
                render_template(
                    'message.html',
                    page_title='Access Denied',
                    heading='Access Denied',
                    message=err,
                    primary_action_label='Back to Sign In',
                    primary_action_url=url_for('login'),
                    secondary_action_label='Back to Home',
                    secondary_action_url=url_for('public_landing'),
                ),
                403
            )

        next_url = session.get('next_url', url_for('home'))

        session.clear()
        session['user_id'] = user_id

        return redirect(next_url)

    @app.get('/home')
    @login_required
    def home():
        user_id = session.get('user_id')

        schools = get_user_allowed_schools(g.db, user_id)
        if not schools:
            return (
                render_template(
                    'message.html',
                    page_title='Access Denied',
                    heading='Access Denied',
                    message=MSG_NO_SCHOOLS,
                    primary_action_label='Log Out',
                    primary_action_url=url_for('logout'),
                    secondary_action_label='Back to Home',
                    secondary_action_url=url_for('public_landing'),
                ),
                403
            )

        school_options = []
        for r in schools:
            school_options.append({
                'id': int(r.id),
                'short_name': str(r.short_name),
                'long_name': str(r.long_name),
                'timezone': str(r.timezone),
            })
        
        # For the "Your school(s)" list
        school_short_names_display = ', '.join(
            [s['short_name'] for s in school_options]
        )

        demo = get_demo_home_options()

        return render_template(
            'home.html',
            page_title='Bus Tracker Home',
            school_options=school_options,
            school_short_names_display=school_short_names_display,
            run_type_options=demo['run_type_options'],
            bus_options=demo['bus_options'],
            default_run_type_code=demo['default_run_type_code'],
            default_date_iso=demo['default_date_iso'],
        )

    @app.post('/bus-runs')
    @login_required
    def create_or_open_bus_run():
        # Placeholder for Phase 1 route skeleton.
        # Later this will validate form input, create/fetch bus_run, and redirect.
        return (
            render_template(
                'message.html',
                page_title='Not Implemented Yet',
                heading='Track Buses Coming Soon',
                message=(
                    'The /bus-runs POST route is wired up, but the create/find '
                    'bus_run logic is not implemented yet.'
                ),
                primary_action_label='Back to Home',
                primary_action_url=url_for('home'),
            ),
            501
        )

    @app.get('/bus-runs/<bus_run_public_id>')
    @login_required
    def view_bus_run(bus_run_public_id):
        # Placeholder for Phase 1 route skeleton.
        # Later this will load the run + statuses and enforce school access.
        view_data = get_demo_bus_run_view(bus_run_public_id)

        return render_template(
            'bus_run.html',
            page_title='Bus Run',
            bus_run_public_id=view_data['bus_run_public_id'],
            school_name=view_data['school_name'],
            run_date=view_data['run_date'],
            run_type_label=view_data['run_type_label'],
            show_buses_rolling=view_data['show_buses_rolling'],
            tiles=view_data['tiles'],
        )

    @app.get('/bus-runs/<bus_run_public_id>/edit')
    @login_required
    def edit_bus_run(bus_run_public_id):
        # Placeholder for Phase 1 route skeleton.
        # Later this will load the run + current bus selection for editing.
        view_data = get_demo_bus_run_edit_view(bus_run_public_id)

        return render_template(
            'bus_run_edit.html',
            page_title='Edit Bus Run',
            bus_run_public_id=view_data['bus_run_public_id'],
            school_name=view_data['school_name'],
            run_date=view_data['run_date'],
            run_type_label=view_data['run_type_label'],
            bus_options=view_data['bus_options'],
        )

    return app
