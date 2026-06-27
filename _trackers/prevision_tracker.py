import inspect
from typing import Optional
from typing import List

from _trackers._generic_tracker import GenericTracker
from _manager.prevision_manager import PrevisionManager

class PrevisionTracker(GenericTracker):
    def __init__(self):
        # On définit bien l'id_field pour que le parent travaille correctement
        super().__init__(PrevisionManager(), "id_prevision")
        self._prevision = {}