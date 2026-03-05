from abc import ABC, abstractmethod
class base_fix(ABC):

    def __init__(self):
        pass
    
    @abstractmethod
    def finalfix(self):
        pass

    @abstractmethod
    def fix(self):
        pass

    @abstractmethod
    def check(self):
        pass

    @abstractmethod
    def rollback(self):
        pass
    
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def get_des(self):
        pass

    