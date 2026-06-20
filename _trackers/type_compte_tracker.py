from _manager.type_manager import TypeCompteManager
from _trackers._generic_tracker import GenericTracker


class TypeCompteTracker(GenericTracker):
    def __init__(self):
        super().__init__(TypeCompteManager(), "id_type_de_compte")

