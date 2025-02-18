from abc import ABC, abstractmethod
from values_definition import Position

class Strategy(ABC):

    @abstractmethod 
    def checkIfCanEnterPosition(self, i: int) -> Position:
        pass

    # @abstractmethod
    # def computeIndicator(self, i: int):
    #     pass

    # @abstractmethod 
    # def setParams(self, **kwargs):
    #     pass

    # @abstractmethod 
    # def updateSl(self, currentPrice: float, entryPrice:float, tpInPips:float) -> float:
    #     pass
