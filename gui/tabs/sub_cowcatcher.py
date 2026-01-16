from .forms import DynamicSettingsFrame

class CowCatcherSettings(DynamicSettingsFrame):
    def __init__(self, parent, config_manager):
        super().__init__(parent, config_manager, "cowcatcher", "CowCatcher Instellingen")