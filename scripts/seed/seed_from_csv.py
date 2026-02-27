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
from bustracker.models.bus import Bus
from bustracker.models.school import School
from bustracker.models.school_bus import SchoolBus
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
TRUNCATE TABLE school_buses;
TRUNCATE TABLE buses;
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
    allowed = {
        'schools',
        'users',
        'user_schools',
        'buses',
        'school_buses',
    }

    if '--only' not in argv:
        return ['schools', 'buses', 'school_buses', 'users', 'user_schools']

    i = argv.index('--only')
    if i == len(argv) - 1:
        msg = '--only requires a value (schools, buses, school_buses, users, '
        msg += 'user_schools)'
        raise ValueError(msg)

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


def _parse_bool_0_1(raw, context, field_name='is_active'):
    if raw is None or str(raw).strip() == '':
        msg = context + ': ' + field_name + ' is required (use 1 or 0)'
        raise ValueError(msg)

    val = str(raw).strip()
    if val == '1':
        return True
    if val == '0':
        return False

    msg = context + ': invalid ' + field_name + ' (use 1 or 0), got: ' + val
    raise ValueError(msg)


def _require_str(raw, context, field_name):
    if raw is None:
        raise ValueError(context + ': ' + field_name + ' is required')

    val = str(raw).strip()
    if val == '':
        raise ValueError(context + ': ' + field_name + ' is required')

    return val


def _parse_int_required(raw, context, field_name):
    val = _require_str(raw, context, field_name)

    try:
        return int(val)
    except Exception:
        msg = context + ': invalid ' + field_name + ' (must be int), got: ' + val
        raise ValueError(msg)


def _validate_hex_color(val, context):
    if not val.startswith('#') or len(val) != 7:
        msg = context + ': invalid hex_color (expected #RRGGBB), got: ' + val
        raise ValueError(msg)


def upsert_schools(session, csv_path):
    rows = _read_csv_rows(
        csv_path,
        required_headers=['short_name', 'long_name', 'timezone', 'is_active']
    )

    inserted = 0
    updated = 0

    for r in rows:
        short_name = _require_str(r.get('short_name'), 'schools.csv', 'short_name')
        long_name = _require_str(r.get('long_name'), 'schools.csv', 'long_name')
        timezone = _require_str(r.get('timezone'), 'schools.csv', 'timezone')
        is_active = _parse_bool_0_1(r.get('is_active'), 'schools.csv')

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
        email = _require_str(r.get('email'), 'users.csv', 'email')
        is_active = _parse_bool_0_1(r.get('is_active'), 'users.csv')

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
        user_email = _require_str(
            r.get('user_email'),
            'user_schools.csv',
            'user_email'
        )
        school_short_name = _require_str(
            r.get('school_short_name'),
            'user_schools.csv',
            'school_short_name'
        )

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


def upsert_buses(session, csv_path):
    rows = _read_csv_rows(
        csv_path,
        required_headers=['bus_code', 'is_active']
    )

    inserted = 0
    updated = 0

    for r in rows:
        bus_code = _require_str(r.get('bus_code'), 'buses.csv', 'bus_code')
        is_active = _parse_bool_0_1(r.get('is_active'), 'buses.csv')

        existing = session.execute(
            select(Bus).where(Bus.bus_code == bus_code)
        ).scalar_one_or_none()

        if existing is None:
            b = Bus(
                bus_code=bus_code,
                is_active=is_active
            )
            session.add(b)
            inserted += 1
            continue

        changed = False

        if existing.is_active != is_active:
            existing.is_active = is_active
            changed = True

        if changed:
            updated += 1

    return {'inserted': inserted, 'updated': updated, 'rows': len(rows)}


def upsert_school_buses(session, csv_path):
    rows = _read_csv_rows(
        csv_path,
        required_headers=[
            'school_short_name',
            'bus_code',
            'display_name',
            'color_name',
            'hex_color',
            'sort_order',
            'driver_name',
            'is_sped',
            'is_active',
        ]
    )

    inserted = 0
    updated = 0

    for r in rows:
        school_short_name = _require_str(
            r.get('school_short_name'),
            'school_buses.csv',
            'school_short_name'
        )
        bus_code = _require_str(
            r.get('bus_code'),
            'school_buses.csv',
            'bus_code'
        )

        display_name = _require_str(
            r.get('display_name'),
            'school_buses.csv',
            'display_name'
        )
        color_name = _require_str(
            r.get('color_name'),
            'school_buses.csv',
            'color_name'
        )
        hex_color = _require_str(
            r.get('hex_color'),
            'school_buses.csv',
            'hex_color'
        )
        _validate_hex_color(hex_color, 'school_buses.csv')

        sort_order = _parse_int_required(
            r.get('sort_order'),
            'school_buses.csv',
            'sort_order'
        )

        driver_name = _require_str(
            r.get('driver_name'),
            'school_buses.csv',
            'driver_name'
        )

        is_sped = _parse_bool_0_1(
            r.get('is_sped'),
            'school_buses.csv',
            field_name='is_sped'
        )

        is_active = _parse_bool_0_1(
            r.get('is_active'),
            'school_buses.csv'
        )

        school = session.execute(
            select(School).where(School.short_name == school_short_name)
        ).scalar_one_or_none()

        if school is None:
            msg = (
                'school_buses.csv: school not found for short_name: '
                + school_short_name
            )
            raise ValueError(msg)

        bus = session.execute(
            select(Bus).where(Bus.bus_code == bus_code)
        ).scalar_one_or_none()

        if bus is None:
            msg = 'school_buses.csv: bus not found for bus_code: ' + bus_code
            raise ValueError(msg)

        # Updated 2/27/2026 to allow the same bus to be used multiple times with
        # different display_names in order to distinguish between AM/PM
        
        # existing = session.execute(
        #     select(SchoolBus).where(
        #         SchoolBus.school_id == school.id,
        #         SchoolBus.bus_id == bus.id
        #     )
        # ).scalar_one_or_none()

        existing = session.execute(
            select(SchoolBus).where(
                SchoolBus.school_id == school.id,
                SchoolBus.display_name == display_name
            )
        ).scalar_one_or_none()

        if existing is None:
            sb = SchoolBus(
                school_id=school.id,
                bus_id=bus.id,
                display_name=display_name,
                color_name=color_name,
                hex_color=hex_color,
                sort_order=sort_order,
                driver_name=driver_name,
                is_sped=is_sped,
                is_active=is_active
            )
            session.add(sb)
            inserted += 1
            continue

        changed = False

        # Updated 2/27/2026 to update bus_id since display_name is replacing it
        # as part of the natural key
        
        # if existing.display_name != display_name:
        #     existing.display_name = display_name
        #     changed = True

        if existing.bus_id != bus.id:
            existing.bus_id = bus.id
            changed = True

        if existing.color_name != color_name:
            existing.color_name = color_name
            changed = True

        if existing.hex_color != hex_color:
            existing.hex_color = hex_color
            changed = True

        if existing.sort_order != sort_order:
            existing.sort_order = sort_order
            changed = True

        if existing.driver_name != driver_name:
            existing.driver_name = driver_name
            changed = True

        if existing.is_sped != is_sped:
            existing.is_sped = is_sped
            changed = True

        if existing.is_active != is_active:
            existing.is_active = is_active
            changed = True

        if changed:
            updated += 1

    return {'inserted': inserted, 'updated': updated, 'rows': len(rows)}


def main():
    only = _parse_only_arg(sys.argv)

    # Run from repo root: python scripts/seed/seed_from_csv.py
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    seed_data_dir = os.path.join(repo_root, 'scripts', 'seed', 'data')

    users_csv = os.path.join(seed_data_dir, 'users.csv')
    schools_csv = os.path.join(seed_data_dir, 'schools.csv')
    user_schools_csv = os.path.join(seed_data_dir, 'user_schools.csv')
    buses_csv = os.path.join(seed_data_dir, 'buses.csv')
    school_buses_csv = os.path.join(seed_data_dir, 'school_buses.csv')

    cfg = _get_cfg()

    engine = create_engine(cfg.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)

    session = Session()

    try:
        schools_result = None
        buses_result = None
        school_buses_result = None
        users_result = None
        user_schools_result = None

        if 'schools' in only:
            schools_result = upsert_schools(session, schools_csv)

        if 'buses' in only:
            buses_result = upsert_buses(session, buses_csv)

        if 'school_buses' in only:
            school_buses_result = upsert_school_buses(
                session,
                school_buses_csv
            )

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

    if buses_result is not None:
        print('Buses: inserted=%s updated=%s rows=%s' % (
            buses_result['inserted'],
            buses_result['updated'],
            buses_result['rows']
        ))

    if school_buses_result is not None:
        print('SchoolBuses: inserted=%s updated=%s rows=%s' % (
            school_buses_result['inserted'],
            school_buses_result['updated'],
            school_buses_result['rows']
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
