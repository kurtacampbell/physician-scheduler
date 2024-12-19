import pytest
from datetime import date
from models.physician import Physician

@pytest.fixture
def physician():
    """Create a basic physician for testing"""
    return Physician(name="Physician A")

@pytest.fixture
def physician_with_night_block():
    """Create a physician with a night block"""
    physician = Physician(name="Physician B")
    blocked_date = date(2023, 10, 15)
    physician.blocked_dates = {blocked_date: ['Night']}
    return physician

@pytest.fixture
def physician_with_all_types_block():
    """Create a physician with a block for all types"""
    physician = Physician(name="Physician B")
    blocked_date = date(2023, 10, 15)
    physician.blocked_dates = {blocked_date: ['Night', 'Weekend', 'Holiday']}
    return physician

@pytest.fixture
def physician_with_empty_block():
    """Create a physician with an empty block"""
    physician = Physician(name="Physician B")
    blocked_date = date(2023, 10, 15)
    physician.blocked_dates = {blocked_date: []}
    return physician

def test_physician_initialization(physician):
    assert physician.name == "Physician A"
    assert physician.blocked_dates == {}
    assert physician.assigned_dates == []

def test_is_available_no_block(physician):
    test_date = date(2023, 10, 15)
    assert physician.is_available(test_date) is True
    assert physician.is_available(test_date, 'Night') is True
    assert physician.is_available(test_date, 'Weekend') is True
    assert physician.is_available(test_date, 'Holiday') is True

def test_is_available_with_night_block(physician_with_night_block):
    blocked_date = date(2023, 10, 15)
    assert physician_with_night_block.is_available(blocked_date) is False
    assert physician_with_night_block.is_available(blocked_date, 'Night') is False
    assert physician_with_night_block.is_available(blocked_date, 'Weekend') is True
    assert physician_with_night_block.is_available(blocked_date, 'Holiday') is True

def test_is_available_with_all_types_block(physician_with_all_types_block):
    blocked_date = date(2023, 10, 15)
    assert physician_with_all_types_block.is_available(blocked_date) is False
    assert physician_with_all_types_block.is_available(blocked_date, 'Night') is False
    assert physician_with_all_types_block.is_available(blocked_date, 'Weekend') is False
    assert physician_with_all_types_block.is_available(blocked_date, 'Holiday') is False

def test_is_available_with_empty_block(physician_with_empty_block):
    blocked_date = date(2023, 10, 15)
    assert physician_with_empty_block.is_available(blocked_date) is False
    assert physician_with_empty_block.is_available(blocked_date, 'Night') is False
    assert physician_with_empty_block.is_available(blocked_date, 'Weekend') is False
    assert physician_with_empty_block.is_available(blocked_date, 'Holiday') is False

def test_assign_date(physician):
    class MockDateAssignment:
        def __init__(self, date_val):
            self.date = date_val
            self.type = 'Night'
    
    date_assignment = MockDateAssignment(date(2023, 10, 15))
    physician.assign_date(date_assignment)
    assert len(physician.assigned_dates) == 1
    assert physician.assigned_dates[0].date == date(2023, 10, 15)

def test_get_last_assignment_date(physician):
    class MockDateAssignment:
        def __init__(self, date_val, type_val):
            self.date = date_val
            self.type = type_val
    
    # Add some assignments
    assignments = [
        MockDateAssignment(date(2023, 10, 1), 'Night'),
        MockDateAssignment(date(2023, 10, 15), 'Weekend'),
        MockDateAssignment(date(2023, 10, 30), 'Night')
    ]
    
    for assignment in assignments:
        physician.assign_date(assignment)
    
    assert physician.get_last_assignment_date('Night') == date(2023, 10, 30)
    assert physician.get_last_assignment_date('Weekend') == date(2023, 10, 15)
    assert physician.get_last_assignment_date('Holiday') is None

def test_get_days_since_last_assignment(physician):
    class MockDateAssignment:
        def __init__(self, date_val, type_val):
            self.date = date_val
            self.type = type_val
        
        def get_date(self):
            return self.date
    
    # Create a list of dates
    dates = [
        MockDateAssignment(date(2023, 10, i), 'Night') 
        for i in range(1, 31)
    ]
    
    # Assign one date to the physician
    physician.assign_date(dates[0])  # Assigns Oct 1
    
    # Check days since last assignment for Oct 15
    current_date = dates[14]  # Oct 15
    days = physician.get_days_since_last_assignment(dates, current_date, 'Night')
    assert days == 14

    # Check for assignment type with no history
    days = physician.get_days_since_last_assignment(dates, current_date, 'Weekend')
    assert days == float('inf')

def test_add_blocked_dates_single_range(physician):
    """Test adding a single blocked date range"""
    blocked_dates = [{
        'start': '2025-01-01',
        'end': '2025-01-03',
        'type': ['Night']
    }]
    
    physician.add_blocked_dates(blocked_dates)
    
    # Check each date in range
    assert physician.is_available(date(2025, 1, 1), 'Night') is False
    assert physician.is_available(date(2025, 1, 2), 'Night') is False
    assert physician.is_available(date(2025, 1, 3), 'Night') is False
    
    # Check that other types are still available
    assert physician.is_available(date(2025, 1, 1), 'Weekend') is True
    assert physician.is_available(date(2025, 1, 1), 'Holiday') is True

def test_add_blocked_dates_multiple_types(physician):
    """Test blocking multiple assignment types"""
    blocked_dates = [{
        'start': '2025-01-01',
        'end': '2025-01-01',
        'type': ['Night', 'Weekend']
    }]
    
    physician.add_blocked_dates(blocked_dates)
    
    assert physician.is_available(date(2025, 1, 1), 'Night') is False
    assert physician.is_available(date(2025, 1, 1), 'Weekend') is False
    assert physician.is_available(date(2025, 1, 1), 'Holiday') is True

def test_add_blocked_dates_no_type(physician):
    """Test blocking without specifying types (should block all types)"""
    blocked_dates = [{
        'start': '2025-01-01',
        'end': '2025-01-01'
    }]
    
    physician.add_blocked_dates(blocked_dates)
    
    # When no type is specified, all types should be blocked
    assert physician.is_available(date(2025, 1, 1)) is False
    assert physician.is_available(date(2025, 1, 1), 'Night') is False
    assert physician.is_available(date(2025, 1, 1), 'Weekend') is False
    assert physician.is_available(date(2025, 1, 1), 'Holiday') is False

def test_add_blocked_dates_multiple_ranges(physician):
    """Test adding multiple blocked date ranges"""
    blocked_dates = [
        {
            'start': '2025-01-01',
            'end': '2025-01-03',
            'type': ['Night']
        },
        {
            'start': '2025-01-15',
            'end': '2025-01-17',
            'type': ['Weekend']
        }
    ]
    
    physician.add_blocked_dates(blocked_dates)
    
    # Check first range
    assert physician.is_available(date(2025, 1, 1), 'Night') is False
    assert physician.is_available(date(2025, 1, 1), 'Weekend') is True
    
    # Check second range
    assert physician.is_available(date(2025, 1, 15), 'Night') is True
    assert physician.is_available(date(2025, 1, 15), 'Weekend') is False