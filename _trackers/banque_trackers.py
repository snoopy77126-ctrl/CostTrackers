from _manager.banque_manager import BanqueManager
from _trackers._generic_tracker import GenericTracker


class BanqueTracker(GenericTracker):
    def __init__(self):
        super().__init__(BanqueManager(), "id_banque")

    def create(self, data):
        print(f'[DEBUG]BanqueTracker.create()')
        print(f'kwargs: {data}')
        return self.from_dict(data)

    def from_dict(self, data):
        """ Transforme les données UI en Objet Métier. """
        return self.manager._from_row(data)
