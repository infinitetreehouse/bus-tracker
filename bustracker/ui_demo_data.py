from datetime import date


def get_demo_home_options():
    """
    Placeholder form data for /home.
    Later replace with DB-driven queries based on:
      - current user
      - selected school
      - active buses
      - run_types table
    """
    return {
        'run_type_options': [
            {'code': 'arrival', 'label': 'Arrival'},
            {'code': 'dismissal', 'label': 'Dismissal'},
        ],
        'bus_options': [
            {'code': 'purple', 'label': 'Purple Bus'},
            {'code': 'green', 'label': 'Green Bus'},
            {'code': 'blue', 'label': 'Blue Bus'},
            {'code': 'red', 'label': 'Red Bus'},
            {'code': 'yellow', 'label': 'Yellow Bus'},
        ],
        'default_run_type_code': 'arrival',
        'default_date_iso': date.today().isoformat(),
    }


def get_demo_bus_run_view(bus_run_public_id):
    """
    Placeholder page data for /bus-runs/<public_id>.
    Later replace with bus_run + bus_run_statuses query results.
    """
    return {
        'bus_run_public_id': str(bus_run_public_id),
        'school_name': 'Example Elementary',
        'run_date': date.today().isoformat(),
        'run_type_label': 'Arrival',
        'show_buses_rolling': False,
        'tiles': [
            {
                'bus_label': 'Purple Bus',
                'check_in_time': '7:08 AM',
                'student_count': 22,
                'departure_time': '',
                'status_label': 'Checked in',
            },
            {
                'bus_label': 'Green Bus',
                'check_in_time': '',
                'student_count': '',
                'departure_time': '',
                'status_label': 'Waiting',
            },
            {
                'bus_label': 'Blue Bus',
                'check_in_time': '7:14 AM',
                'student_count': 17,
                'departure_time': '',
                'status_label': 'Checked in',
            },
            {
                'bus_label': 'Red Bus',
                'check_in_time': '',
                'student_count': '',
                'departure_time': '',
                'status_label': 'Waiting',
            },
        ],
    }


def get_demo_bus_run_edit_view(bus_run_public_id):
    """
    Placeholder page data for /bus-runs/<public_id>/edit.
    Later replace with real run + current included buses.
    """
    return {
        'bus_run_public_id': str(bus_run_public_id),
        'school_name': 'Example Elementary',
        'run_date': date.today().isoformat(),
        'run_type_label': 'Arrival',
        'bus_options': [
            {'code': 'purple', 'label': 'Purple Bus', 'checked': True},
            {'code': 'green', 'label': 'Green Bus', 'checked': True},
            {'code': 'blue', 'label': 'Blue Bus', 'checked': True},
            {'code': 'red', 'label': 'Red Bus', 'checked': False},
            {'code': 'yellow', 'label': 'Yellow Bus', 'checked': False},
        ],
    }
