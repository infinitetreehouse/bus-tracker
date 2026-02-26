from datetime import datetime

from sqlalchemy import func, select

from bustracker.models.school import School
from bustracker.models.user import User
from bustracker.models.user_school import UserSchool


"""
Tests
-DONE Non school email

Gate #1
-DONE School email that doesn't match user email, no google_sub yet

-DONE School email that matches user but inactive, no google_sub yet

-DONE School email that matches inactive user with active school assignments

-DONE Repeat using google_sub, same email, inactive user

-DONE Repeat using google_sub, different email, inactive user

Gate #2
-DONE School email that matches active user but no assigned schools

-DONE School email that matches active user but inactive schools only

-DONE Repeat using google_sub, same email, no assigned schools

-DONE Repeat using google_sub, different email, no assigned schools

Gate #3
-DONE School email that matches active user with one active school
    -DONE Confirn google_sub, name, last login are set

-DONE School email that matches active user with multiple active/inactive schools
    -DONE Confirn google_sub, name, last login are set

-DONE Repeat using google_sub but force different email, confirm email updated

-DONE Repeat using email but force google_sub to be different, should fail

-DONE Repeat but force user email to be uppercase

-DONE Force change to duplicate email after matching sub, should fail
"""

MSG_NO_USER = (
    "You signed in with Google, but you don't have a user account in the "
    "Bus Tracker app. Please contact your administrator."
)

MSG_INACTIVE_USER = (
    "You signed in with Google, but your user account is not active in the "
    "Bus Tracker app. Please contact your administrator."
)

MSG_NO_SCHOOLS = (
    "You have an active user account in the Bus Tracker app, but you don't "
    "have access to any schools yet. Please contact your administrator."
)

MSG_SUB_MISMATCH = (
    "You signed in with Google, but your account could not be verified. "
    "Please contact your administrator."
)


def _norm_email(email):
    if email is None:
        return None
    return str(email).strip().lower()


def _get_active_school_count(db, user_id):
    stmt = (
        select(func.count())
        .select_from(UserSchool)
        .join(School, School.id == UserSchool.school_id)
        .where(UserSchool.user_id == user_id)
        .where(School.is_active == True)
    )
    return int(db.execute(stmt).scalar() or 0)


def sync_user_from_google_claims(db, claims):
    """
    Gate logic:
      1) user exists
      2) user is active
      3) user has at least one active school via user_schools -> schools

    Identity strategy:
      - require non-empty sub
      - try lookup by sub first
      - if not found, lookup by email
      - if found by sub and email differs, update email
      - if found by email and google_sub missing, set it
      - if found by email and google_sub exists but differs, block

    Returns: (user_id, error_message_or_none)
    """
    email = _norm_email(claims.get('email'))

    # OIDC sub should be a stable unique ID that stays the same even if a user's
    # email changes (while using the same account), see Google documentation:
    # https://developers.google.com/identity/openid-connect/openid-connect
    sub = claims.get('sub')
    sub = None if sub is None else str(sub).strip()

    if sub is None or sub == '':
        return None, MSG_SUB_MISMATCH

    full_name = claims.get('name')
    given_name = claims.get('given_name')
    family_name = claims.get('family_name')

    if email is None or email == '':
        return None, MSG_NO_USER

    # 1) Try by sub first
    # TODO: Consider handling edge case where google_sub has leading/trailing
    # whitespace (could cause sub-first lookup miss; fix by trimming on write or
    # one-time DB cleanup)
    stmt = select(User).where(User.google_sub == sub)
    user = db.execute(stmt).scalar_one_or_none()

    found_by = 'sub' if user is not None else None

    # 2) Fallback: try by email
    if user is None:
        stmt = select(User).where(func.lower(User.email) == email)
        user = db.execute(stmt).scalar_one_or_none()
        found_by = 'email' if user is not None else None

    # print(found_by)

    # Gate #1
    if user is None:
        return None, MSG_NO_USER

    # Gate #2
    if not bool(user.is_active):
        return None, MSG_INACTIVE_USER

    # Gate #3
    active_school_count = _get_active_school_count(db, user.id)
    if active_school_count <= 0:
        return None, MSG_NO_SCHOOLS

    # Normalize existing sub (trim)
    existing_sub = user.google_sub
    existing_sub = None if existing_sub is None else str(existing_sub).strip()

    # Identity binding / updates
    if found_by == 'sub':
        # If email changed, update it
        if _norm_email(user.email) != email:
            user.email = email

    elif found_by == 'email':
        # If user has never been bound to google_sub, bind now
        if existing_sub is None or existing_sub == '':
            user.google_sub = sub
        else:
            # If already bound, must match
            if existing_sub != sub:
                return None, MSG_SUB_MISMATCH

    # Update profile fields + last login
    user.full_name = full_name
    user.given_name = given_name
    user.family_name = family_name
    user.last_login_at_utc = datetime.utcnow()

    return user.id, None


def get_user_allowed_schools(db, user_id):
    """
    Returns rows of:
      (school_id, short_name, long_name, timezone)
    Only active schools.
    """
    stmt = (
        select(School.id, School.short_name, School.long_name, School.timezone)
        .select_from(UserSchool)
        .join(School, School.id == UserSchool.school_id)
        .where(UserSchool.user_id == user_id)
        .where(School.is_active == True)
        .order_by(School.short_name.asc())
    )
    return db.execute(stmt).all()
