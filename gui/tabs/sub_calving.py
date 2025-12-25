from .forms import DynamicSettingsFrame

class CalvingSettings(DynamicSettingsFrame):
    def __init__(self, parent, config_manager):
        # We roepen de basisklasse aan met de key "calvingcatcher" (zonder _settings, dat doet de logic wel, of check forms logic)
        # In forms.py gebruiken we if key == "cowcatcher" else... dus we geven hier een identificatie mee.
        # De forms.py logica verwacht "cowcatcher" of "calvingcatcher"
        super().__init__(parent, config_manager, "calvingcatcher", "CalvingCatcher Instellingen")