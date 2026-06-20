import configparser
from pathlib import Path

class ConfigManagerDynamic:
    def __init__(self, ini_path=None):

        self.config_path = Path(ini_path) if ini_path else Path(__file__).parent / 'config.ini'
        self.config = configparser.ConfigParser()
        self._write_locked = True
        self.settings = {}
        self.load()  # charge la config

    def load(self):
        if not self.config_path.exists():
            print(f"⚠️ {self.config_path} introuvable, création avec valeurs par défaut")
            self.config['GENERAL'] = {}
            self._write_locked = False
            self.save()
            self._write_locked = True

        self.config.read(self.config_path)

        # Lecture dynamique de toutes les sections et clés
        for section in self.config.sections():
            for key, value in self.config.items(section):
                attr_name = key.upper()
                setattr(self, attr_name, value)
                self.settings[attr_name] = value

    def save(self):
        if self._write_locked:
            return
        for attr, value in self.settings.items():
            # Trouve la section correspondante si possible
            found = False
            for section in self.config.sections():
                if attr.lower() in self.config[section]:
                    self.config[section][attr.lower()] = str(value)
                    found = True
                    break
            if not found:
                # Ajoute dans GENERAL si section inconnue
                if 'GENERAL' not in self.config:
                    self.config['GENERAL'] = {}
                self.config['GENERAL'][attr.lower()] = str(value)

        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def get(self, key, default=None):
        return self.settings.get(key.upper(), default)

    def set(self, key, value):
        self.settings[key.upper()] = value
        setattr(self, key.upper(), value)

    def enable_writes(self):
        self._write_locked = False

    def disable_writes(self):
        self._write_locked = True


cfg = ConfigManagerDynamic()

