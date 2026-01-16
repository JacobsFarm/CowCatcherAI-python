from .forms import DynamicSettingsFrame

class CalvingSettings(DynamicSettingsFrame):
    def __init__(self, parent, config_manager):
        super().__init__(
            parent, 
            config_manager, 
            "calvingcatcher", 
            "CalvingCatcher Settings"
        )