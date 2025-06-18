import abc

class AbstractRepair(abc.ABC):
    @abc.abstractmethod
    def __init__(self):
        """Initialize with parsed arguments."""
        pass

    @abc.abstractmethod
    def repair(self):
        """Run the full repair process."""
        pass
