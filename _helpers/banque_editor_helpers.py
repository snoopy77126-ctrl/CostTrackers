from _helpers._generique_helpers import BaseHelper

class BanqueEditorHelpers(BaseHelper):
    def __init__(self, services):
        super().__init__(services)
        self.tracker = services.get('banques')
        self.current_id = None  # Requis par _on_add_new()

    def initialise(self):
        self.tracker.clear_cache()

    def fetch_row_organisation(self):
        # TODO: Appeler un tiers_trackers d'entreprises/organisations si tu en as un
        # Pour l'instant, on retourne une liste vide pour éviter le crash de la combobox
        return []

    def fetch_data_banque(self, banque_id):
        self.current_id = banque_id
        # Récupère l'objet métier complet via le tiers_trackers
        return self.tracker.get_by_id(banque_id)

    def save_banque(self, data):
        """Sauvegarde via le tiers_trackers."""
        print(f'[DEBUG]banque_editor_helpers.save_banque()')
        print(f'data: {data}')
        # Création
        nouveau=self.tracker.create(data)
        return self.tracker.add(nouveau) is not None

    def delete_banque(self, data):
        # TODO: Implémenter la logique de suppression
        print(f"Suppression demandée pour : {data}")
        return True # Simule un succès