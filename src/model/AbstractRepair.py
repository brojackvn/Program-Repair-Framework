import abc

class AbstractRepair():
    def __init__(self):
        pass

    @abc.abstractmethod
    def load_model(self):
        pass
    
    @abc.abstractmethod
    def generate_patch(self):
        pass

    @abc.abstractmethod
    def decode_patch(self):
        pass