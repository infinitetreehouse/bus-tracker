# 1) stdlib
import csv
import os
import sys

# 2) third-party
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

# 3) app
import bustracker.models
from bustracker.config import DevConfig, ProdConfig
from bustracker.models.school import School
from bustracker.models.user import User
from bustracker.models.user_school import UserSchool


"""
Tests:
-DONE Smoke test initial load, should work.

-DONE User emails have different cases + leading/trailing spaces (same spelling)
in users.csv & user_schools.csv, should still match, saved stripped and lower

-DONE School short_names have different cases in schools.csv & user_schools.csv,
should fail... DOES NOT FAIL, BUT OK

-DONE Any value other than 1 or 0 for is_active fails

-DONE Blank/empty white space for required fields fails

-DONE Missing required header fails

-DONE Duplicate emails in users.csv just runs back-to-back updates

-DONE Loading user_schools.csv before the user or school is added fails

-DONE If any row fails, the entire update is rolled back... SEEMS TO WORK

-DONE Updates (e.g., changing is_active from 1 to 0) are successful

-----

python -m scripts.seed.seed_from_csv

SQL commands to help with testing:

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE user_schools;
TRUNCATE TABLE users;
TRUNCATE TABLE schools;
SET FOREIGN_KEY_CHECKS = 1;
"""

def _get_cfg():
    load_dotenv()

    env = os.getenv('FLASK_ENV', 'development').lower()
    if env == 'production':
        return ProdConfig()
    return DevConfig()


def _parse_only_arg(argv):
    # --only schools
    # --only schools,users
    allowed = {'schools', 'users', 'user_schools'}

    if '--only' not in argv:
        return ['schools', 'users', 'user_schools']

    i = argv.index('--only')
    if i == len(argv) - 1:
        raise ValueError('--only requires a value (schools, users, user_schools)')

    raw = argv[i + 1]
    parts = [p.strip() for p in raw.split(',') if p.strip() != '']

    if len(parts) == 0:
        raise ValueError('--only requires at least one value')

    for p in parts:
        if p not in allowed:
            raise ValueError('invalid --only value: ' + p)

    return parts


def _read_csv_rows(csv_path, required_headers):
    if not os.path.exists(csv_path):
        raise ValueError('csv file not found: ' + csv_path)

    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        missing = [h for h in required_headers if h not in headers]
        if missing:
            msg = 'missing required headers in %s: %s' % (
                csv_path,
                ', '.join(missing)
            )
            raise ValueError(msg)

        rows = []
        for row in reader:
            # Keep raw row structure, but strip whitespace on string values
            cleaned = {}
            for k, v in row.items():
                if v is None:
                    cleaned[k] = None
                else:
                    cleaned[k] = str(v).strip()
            rows.append(cleaned)

        return rows


def _parse_bool_0_1(raw, context):
    if raw is None or str(raw).strip() == '':
        raise ValueError(context + ': is_active is required (use 1 or 0)')

    val = str(raw).strip()
    if val == '1':
        return True
    if val == '0':
        return False

    raise ValueError(context + ': invalid is_active (use 1 or 0), got: ' + val)


def upsert_schools(session, csv_path):
    rows = _read_csv_rows(
        csv_path,
        required_headers=['short_name', 'long_name', 'timezone', 'is_active']
    )

    inserted = 0
    updated = 0

    for r in rows:
        short_name = r['short_name']
        long_name = r['long_name']
        timezone = r['timezone']
        is_active = _parse_bool_0_1(r.get('is_active'), 'schools.csv')

        if short_name is None or short_name == '':
            raise ValueError('schools.csv: short_name is required')
        if long_name is None or long_name == '':
            raise ValueError('schools.csv: long_name is required')
        if timezone is None or timezone == '':
            raise ValueError('schools.csv: timezone is required')

        existing = session.execute(
            select(School).where(School.short_name == short_name)
        ).scalar_one_or_none()

        if existing is None:
            s = School(
                short_name=short_name,
                long_name=long_name,
                timezone=timezone,
                is_active=is_active
            )
            session.add(s)
            inserted += 1
            continue

        # Update only fields we control via CSV
        changed = False

        if existing.long_name != long_name:
            existing.long_name = long_name
            changed = True

        if existing.timezone != timezone:
            existing.timezone = timezone
            changed = True

        if existing.is_active != is_active:
            existing.is_active = is_active
            changed = True

        if changed:
            updated += 1

    return {'inserted': inserted, 'updated': updated, 'rows': len(rows)}


def upsert_users(session, csv_path):
    rows = _read_csv_rows(csv_path, required_headers=['email', 'is_active'])

    inserted = 0
    updated = 0

    for r in rows:
        email = r['email']
        is_active = _parse_bool_0_1(r.get('is_active'), 'users.csv')

        if email is None or email == '':
            raise ValueError('users.csv: email is required')

        email = email.lower()

        existing = session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if existing is None:
            u = User(
                email=email,
                is_active=is_active
            )
            session.add(u)
            inserted += 1
            continue

        changed = False

        if existing.is_active != is_active:
            existing.is_active = is_active
            changed = True

        if changed:
            updated += 1

    return {'inserted': inserted, 'updated': updated, 'rows': len(rows)}


def upsert_user_schools(session, csv_path):
    rows = _read_csv_rows(
        csv_path,
        required_headers=['user_email', 'school_short_name']
    )

    inserted = 0

    for r in rows:
        user_email = r['user_email']
        school_short_name = r['school_short_name']

        if user_email is None or user_email == '':
            raise ValueError('user_schools.csv: user_email is required')
        if school_short_name is None or school_short_name == '':
            raise ValueError('user_schools.csv: school_short_name is required')

        user_email = user_email.lower()

        user = session.execute(
            select(User).where(User.email == user_email)
        ).scalar_one_or_none()

        if user is None:
            msg = 'user_schools.csv: user not found for email: ' + user_email
            raise ValueError(msg)

        school = session.execute(
            select(School).where(School.short_name == school_short_name)
        ).scalar_one_or_none()

        if school is None:
            msg = (
                'user_schools.csv: school not found for short_name: '
                + school_short_name
            )
            raise ValueError(msg)

        existing = session.execute(
            select(UserSchool).where(
                UserSchool.user_id == user.id,
                UserSchool.school_id == school.id
            )
        ).scalar_one_or_none()

        if existing is None:
            link = UserSchool(
                user_id=user.id,
                school_id=school.id
            )
            session.add(link)
            inserted += 1

    return {'inserted': inserted, 'rows': len(rows)}


def main():
    only = _parse_only_arg(sys.argv)
    
    # Run from repo root: python scripts/seed/seed_from_csv.py
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    seed_data_dir = os.path.join(repo_root, 'scripts', 'seed', 'data')

    users_csv = os.path.join(seed_data_dir, 'users.csv')
    schools_csv = os.path.join(seed_data_dir, 'schools.csv')
    user_schools_csv = os.path.join(seed_data_dir, 'user_schools.csv')
    
    # Doesn't exist, just for testing
    # test_csv = os.path.join(seed_data_dir, 'test.csv')

    cfg = _get_cfg()

    engine = create_engine(cfg.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)

    session = Session()

    try:
        # Seed schools first, then users, then user_schools
        schools_result = None
        users_result = None
        user_schools_result = None

        if 'schools' in only:
            schools_result = upsert_schools(session, schools_csv)

        if 'users' in only:
            users_result = upsert_users(session, users_csv)

        if 'user_schools' in only:
            user_schools_result = upsert_user_schools(session, user_schools_csv)

        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()

    print('Seed complete.')

    if schools_result is not None:
        print('Schools: inserted=%s updated=%s rows=%s' % (
            schools_result['inserted'],
            schools_result['updated'],
            schools_result['rows']
        ))

    if users_result is not None:
        print('Users: inserted=%s updated=%s rows=%s' % (
            users_result['inserted'],
            users_result['updated'],
            users_result['rows']
        ))

    if user_schools_result is not None:
        print('UserSchools: inserted=%s rows=%s' % (
            user_schools_result['inserted'],
            user_schools_result['rows']
        ))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('seed failed: %s' % str(e))
        sys.exit(1)
