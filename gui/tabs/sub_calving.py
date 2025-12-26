from .forms import DynamicSettingsFrame

class CalvingSettings(DynamicSettingsFrame):
    def __init__(self, parent, config_manager):
        """
        GUI Frame voor CalvingCatcher instellingen.
        De DynamicSettingsFrame bouwt automatisch de invoervelden op basis 
        van de 'calvingcatcher_settings' in de config.
        """
        super().__init__(
            parent, 
            config_manager, 
            "calvingcatcher", 
            "CalvingCatcher Instellingen"
        )
        