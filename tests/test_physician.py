import unittest
from datetime import date
from models.physician import Physician

class TestPhysician(unittest.TestCase):

    def setUp(self):
        # Set up a Physician object for testing
        self.physician = Physician(name="Dr. Smith")

    def test_is_available_no_block(self):
        # Test when there are no blocked dates
        test_date = date(2023, 10, 15)
        self.assertTrue(self.physician.is_available(test_date))

    def test_is_available_with_block(self):
        # Test when the date is blocked
        blocked_date = date(2023, 10, 15)
        self.physician.blocked_dates.add(blocked_date)
        self.assertFalse(self.physician.is_available(blocked_date))

    def test_is_available_with_specific_block(self):
        # Test when the date is blocked for a specific assignment type
        blocked_date = date(2023, 10, 15)
        self.physician.blocked_dates = {blocked_date: ['Night']}
        self.assertFalse(self.physician.is_available(blocked_date, 'Night'))
        self.assertTrue(self.physician.is_available(blocked_date, 'Weekend'))

    def test_is_available_no_specific_type(self):
        # Test when no specific assignment type is provided
        blocked_date = date(2023, 10, 15)
        self.physician.blocked_dates = {blocked_date: []}
        self.assertFalse(self.physician.is_available(blocked_date))

if __name__ == '__main__':
    unittest.main() 