import abc

class AbstractModel():
    def __init__(self):
        pass

    @abc.abstractmethod
    def load_model(self):
        pass
    
    @abc.abstractmethod
    def generate_patch(self):
        pass