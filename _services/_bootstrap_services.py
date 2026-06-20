from databases.database import db
from _manager.operation_manager import OperationManager
from _manager.operation_import_manager import OperationImportManager
from _manager.operation_import_manager import FileImportManager
from _services.bank_import_services import BankImportService
from _trackers.banque_trackers import BanqueTracker
from _trackers.categorie_tracker import CategoryTracker
from _trackers.compte_tracker import CompteTracker
from _trackers.operation_tracker import OperationTracker
from _trackers.operation_tracker import OperationImportTracker
from _trackers.operation_tracker import FileImportTracker
from _trackers.tiers_tracker import TiersTracker
from _trackers.type_compte_tracker import TypeCompteTracker
from config.config import cfg


def build_app_services(database=db, config=cfg):
    # 1. Instanciation des trackers de base
    bank_tracker = BanqueTracker()
    cat_tracker = CategoryTracker()
    compte_tracker = CompteTracker()

    tiers_tracker = TiersTracker()
    type_compte_tracker = TypeCompteTracker()

    # 2. Instanciation des Managers et Services
    bank_import_service = BankImportService(db_service=database, cfg=config)

    operation_manager = OperationManager(cat_tracker, tiers_tracker, compte_tracker)

    # --- LA CORRECTION EST ICI ---
    import_manager = OperationImportManager()  # Pour les lignes d'opérations
    file_manager = FileImportManager()  # Pour le fichier parent (à vérifier selon votre nommage)

    operation_tracker = OperationTracker(operation_manager)
    operation_import_tracker = OperationImportTracker(import_manager)

    # On donne le BON manager au tiers_trackers de fichier
    file_tracker = FileImportTracker(file_manager)

    # 3. Retour du conteneur de services
    return {
        "categorie": cat_tracker,
        "banque": bank_tracker,
        "compte": compte_tracker,
        "operation": operation_tracker,
        "operation_import": operation_import_tracker,
        "file_tracker": file_tracker,
        "tiers": tiers_tracker,
        "type_compte": type_compte_tracker,
        "bank_import": bank_import_service,
        "db": database,
    }
