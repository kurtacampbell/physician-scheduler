# schedulers/base_scheduler.py

from abc import ABC, abstractmethod

class Scheduler(ABC):

    def __init__(self, physicians, dates):
        self.physicians = physicians  # List of Physician objects
        self.dates = dates  # List of DateAssignment objects
        self.total_dates = len(dates)
        self.total_available_dates = 0  # Will be calculated
        self.type = None  # Will be set by the subclass

    @abstractmethod
    def assign_dates(self):
        pass
