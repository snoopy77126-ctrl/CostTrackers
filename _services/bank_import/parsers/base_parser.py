from abc import ABC, abstractmethod
from pathlib import Path

class BaseParser(ABC):
    @abstractmethod
    def parse(self, path: Path) -> list[dict]:
        """Prend un chemin de fichier et retourne une liste de dictionnaires (lignes brutes)."""
        pass
