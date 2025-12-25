from .forms import DynamicSettingsFrame

class CowCatcherSettings(DynamicSettingsFrame):
    def __init__(self, parent, config_manager):
        # We roepen de basisklasse aan met de key "cowcatcher"
        super().__init__(parent, config_manager, "cowcatcher", "CowCatcher Instellingen")