"""Test Date Expansion Module

This module contains unit tests for the date expansion functionality in the scheduling system.
It tests the expansion of date ranges into individual date assignments for nights, weekends,
and holidays.
"""

from datetime import date, timedelta
import pytest
from input_processing.config_loader import ConfigLoader

@pytest.fixture
def config_loader():
    """Create a ConfigLoader instance with empty config data for testing."""
    sample_config = {
        "dates": {
            "assignement_range": [],  # Empty list for date ranges to expand
            "holidays": []            # Empty list for holidays
        }
    }
    return ConfigLoader(sample_config)

def test_basic_weekday_nights(config_loader):
    """Test that weekdays are correctly expanded into night shifts"""
    range_data = [{
        "start": "2025-01-06",  # Monday
        "end": "2025-01-09"     # Thursday
    }]
    
    assignments = config_loader._expand_date_range(range_data, [])
    
    # Should have 4 night shifts (Mon-Thu)
    assert len(assignments) == 4
    
    nights = [a for a in assignments if a.type == 'Night']
    assert len(nights) == 4
    
    # Verify each night shift starts at 5 PM and ends at 8 AM next day
    for night in nights:
        assert night.start_datetime.hour == 17
        assert night.end_datetime.hour == 8
        assert night.end_datetime.date() == night.date + timedelta(days=1)

def test_weekend_creation(config_loader):
    """Test that weekends are correctly created"""
    range_data = [{
        "start": "2025-01-03",  # Friday
        "end": "2025-01-05"     # Sunday
    }]
    
    assignments = config_loader._expand_date_range(range_data, [])
    
    # Should have just one weekend assignment
    assert len(assignments) == 1
    weekend = assignments[0]
    
    # Verify weekend properties
    assert weekend.type == 'Weekend'
    assert weekend.date.strftime('%A') == 'Friday'
    assert weekend.start_datetime.hour == 17  # 5 PM Friday
    assert weekend.end_datetime.hour == 8     # 8 AM Monday
    assert weekend.end_datetime.date() == date(2025, 1, 6)

def test_full_week_expansion(config_loader):
    """Test expansion of a full week including weekend"""
    range_data = [{
        "start": "2025-01-06",  # Monday
        "end": "2025-01-12"     # Sunday
    }]
    
    assignments = config_loader._expand_date_range(range_data, [])
    
    # Should have 4 night shifts (Mon-Thu) and 1 weekend (Fri-Sun)
    assert len(assignments) == 5
    
    nights = [a for a in assignments if a.type == 'Night']
    weekends = [a for a in assignments if a.type == 'Weekend']
    
    assert len(nights) == 4
    assert len(weekends) == 1

def test_partial_week_with_weekend(config_loader):
    """Test expansion of partial week including weekend days"""
    range_data = [{
        "start": "2025-01-02",  # Thursday
        "end": "2025-01-05"     # Sunday
    }]
    
    assignments = config_loader._expand_date_range(range_data, [])
    
    # Should have 1 night shift (Thu) and 1 weekend (Fri-Sun)
    assert len(assignments) == 2
    
    night = next(a for a in assignments if a.type == 'Night')
    weekend = next(a for a in assignments if a.type == 'Weekend')
    
    assert night.date == date(2025, 1, 2)
    assert weekend.date == date(2025, 1, 3)

def test_multiple_weeks(config_loader):
    """Test expansion of multiple weeks"""
    range_data = [{
        "start": "2025-01-06",  # Monday week 1
        "end": "2025-01-19"     # Sunday week 2
    }]
    
    assignments = config_loader._expand_date_range(range_data, [])
    
    # Should have 8 night shifts (Mon-Thu both weeks) and 2 weekends
    assert len(assignments) == 10
    
    nights = [a for a in assignments if a.type == 'Night']
    weekends = [a for a in assignments if a.type == 'Weekend']
    
    assert len(nights) == 8
    assert len(weekends) == 2 