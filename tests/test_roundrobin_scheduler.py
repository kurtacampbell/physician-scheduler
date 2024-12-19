from datetime import date
import pytest
from models.physician import Physician
from models.date_assignment import DateAssignment
from schedulers.roundrobin_scheduler import RoundRobinScheduler

@pytest.fixture
def physicians():
    return [
        Physician("Dr. Smith"),
        Physician("Dr. Jones"),
        Physician("Dr. Williams")
    ]

@pytest.fixture
def dates():
    return [
        DateAssignment(date(2024, 1, i), "Night") for i in range(1, 8)
    ]

@pytest.fixture
def basic_scheduler(physicians, dates):
    return RoundRobinScheduler(physicians, dates, "Night")

@pytest.fixture
def blocked_physician():
    return Physician("Dr. Smith", {date(2024, 1, 1): []})

def test_initialization(basic_scheduler):
    """Test if scheduler initializes correctly"""
    assert len(basic_scheduler.physicians) == 3
    assert len(basic_scheduler.dates) == 7
    assert basic_scheduler.type == "Night"
    assert basic_scheduler.constraints == []

def test_basic_assignment(basic_scheduler):
    """Test if scheduler assigns all dates"""
    basic_scheduler.assign_dates()
    
    # Check all dates are assigned
    assert all(date.assigned_physician is not None for date in basic_scheduler.dates)
    
    # Check distribution is roughly even
    assignments = {}
    for date in basic_scheduler.dates:
        physician = date.assigned_physician.name
        assignments[physician] = assignments.get(physician, 0) + 1
    
    # With 7 dates and 3 physicians, each should have 2 or 3 assignments
    assert all(2 <= count <= 3 for count in assignments.values())

def test_constraint_same_physician():
    """Test constraint preventing same physician from working consecutive days"""
    physicians = [Physician("Dr. Smith"), Physician("Dr. Jones")]
    dates = [DateAssignment(date(2024, 1, i), "Night") for i in range(1, 4)]
    
    constraints = [{
        "physician1": "Any",
        "physician2": "Any",
        "distance": 1  # Cannot work consecutive days
    }]
    
    scheduler = RoundRobinScheduler(physicians, dates, "Night", constraints)
    scheduler.assign_dates()
    
    # Check no physician works consecutive days
    for i in range(len(dates) - 1):
        assert dates[i].assigned_physician != dates[i + 1].assigned_physician

def test_constraint_different_physicians():
    """Test constraint between specific physicians"""
    physicians = [Physician("Dr. Smith"), Physician("Dr. Jones"), Physician("Dr. Williams")]
    dates = [DateAssignment(date(2024, 1, i), "Night") for i in range(1, 4)]
    
    constraints = [{
        "physician1": "Dr. Smith",
        "physician2": "Dr. Jones",
        "distance": 1  # Cannot work within 1 day of each other
    }]
    
    scheduler = RoundRobinScheduler(physicians, dates, "Night", constraints)
    scheduler.assign_dates()
    
    # Check Dr. Smith and Dr. Jones don't work within 1 day of each other
    for i in range(len(dates)):
        for j in range(max(0, i-1), min(len(dates), i+2)):
            if i != j:
                if dates[i].assigned_physician.name == "Dr. Smith":
                    assert dates[j].assigned_physician.name != "Dr. Jones"
                elif dates[i].assigned_physician.name == "Dr. Jones":
                    assert dates[j].assigned_physician.name != "Dr. Smith"

def test_no_available_physician(blocked_physician):
    """Test exception when no physician is available"""
    physicians = [blocked_physician]
    dates = [DateAssignment(date(2024, 1, 1), "Night")]
    
    scheduler = RoundRobinScheduler(physicians, dates, "Night")

    # Check if the blocked physician is available, should not be.
    assert blocked_physician.is_available(dates[0].date) is False

    with pytest.raises(Exception) as exc_info:
        print(scheduler.dates[0].assigned_physician.name) if scheduler.dates[0].assigned_physician is not None else print("None")
        scheduler.assign_dates()
        print(scheduler.dates[0].assigned_physician.name) if scheduler.dates[0].assigned_physician is not None else print("None")
    assert str(exc_info.value).startswith("No available physician")

def test_fairness_over_time(basic_scheduler):
    """Test if assignments are distributed fairly over time"""
    basic_scheduler.assign_dates()
    
    # Check assignments are evenly distributed throughout the period
    first_half = basic_scheduler.dates[:3]
    second_half = basic_scheduler.dates[3:]
    
    # Count assignments in each half
    first_half_counts = {}
    second_half_counts = {}
    
    for date in first_half:
        physician = date.assigned_physician.name
        first_half_counts[physician] = first_half_counts.get(physician, 0) + 1
        
    for date in second_half:
        physician = date.assigned_physician.name
        second_half_counts[physician] = second_half_counts.get(physician, 0) + 1
    
    # Each physician should have assignments in both halves
    assert set(first_half_counts.keys()) == set(second_half_counts.keys()) 