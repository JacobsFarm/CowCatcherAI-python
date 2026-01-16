import customtkinter as ctk
import webbrowser

class HelpPopup(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("CowCatcher AI – User Manual")
        self.geometry("750x650")
        
        # Keep the popup on top of the main window
        self.transient(parent)
        self.grab_set()

        # Title
        self.lbl_title = ctk.CTkLabel(self, text="CowCatcher AI Manual", 
                                      font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_title.pack(pady=(20, 10))

        # Scrollable content area
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=25, pady=10)

        self.add_section("1. Overview & Project", 
            "CowCatcher AI is an open-source computer vision system designed to monitor your herd 24/7. "
            "This version is a Python-based fork of the original repository, making it easier to modify and ideal for "
            "developers who prefer a standalone interface. It uses YOLO AI to detect behaviors via live RTSP camera streams.")

        self.add_section("2. Detection Modes", 
            "• CowCatcher: Specifically monitors for 'mounting' behavior, the primary sign of estrus (heat).\n"
            "• CalvingCatcher: Monitors for signs of calving and automatically saves high-resolution photos when detection confidence is high.")

        self.add_section("3. Hardware Requirements", 
            "• Camera: Any IP camera that supports RTSP.\n"
            "• Computer: For best performance, a PC with an NVIDIA graphics card (e.g., GTX 16-series or RTX series) is recommended.\n"
            "• Connectivity: A stable internet connection for notifications and a PoE switch for wired camera setups.")

        self.add_section("4. Telegram Integration", 
            "The system sends instant photo notifications to your smartphone via Telegram.\n\n"
            "Remote Commands (CalvingCatcher):\n"
            "• 'start' or 'check': Manually triggers monitoring for 15 minutes.\n"
            "• 'stop': Immediately terminates manual monitoring.")

        self.add_section("5. Settings & Thresholds", 
            "• Notify Threshold: The confidence level (0.0 - 1.0) the AI must reach before sending an alert.\n"
            "• Save Threshold: Saves an image to your local drive without triggering a notification alarm.\n"
            "• Min. Detections: The number of consecutive frames required to validate an event.")

        self.add_section("6. Support & Resources", 
            "For updates and source code, visit our GitHub:\n"
            "https://github.com/JacobsFarm/CowCatcherAI-python/tree/main\n\n"
            "Need help? Contact us via:\n"
            "• Telegram public group: CowCatcher AI | opensource project\n"
            "• Email: cowcatcherai@gmail.com\n"
            "• Community: Facebook Group 'CowCatcher AI | opensource project'")

        self.add_section("7. Troubleshooting", 
            "• No video feed? Verify the RTSP link is accessible in a player like VLC.\n"
            "• No notifications? Check your Telegram Bot Token and Chat ID in the Configuration tab.\n"
            "• Model issues? Ensure you have an active internet connection during the first launch to download AI models.")

        # GitHub Button
        self.btn_github = ctk.CTkButton(self, text="Open GitHub Repository", 
                                         command=lambda: webbrowser.open("https://github.com/JacobsFarm/CowCatcherAI-python/tree/main"),
                                         fg_color="#1f538d", hover_color="#14375e")
        self.btn_github.pack(pady=(10, 0))

        # Close button
        self.btn_close = ctk.CTkButton(self, text="Close", command=self.destroy, 
                                       fg_color="#2D572C", hover_color="#3A6B39")
        self.btn_close.pack(pady=20)

    def add_section(self, title, content):
        """Helper method to add formatted sections to the scroll frame"""
        title_lbl = ctk.CTkLabel(self.scroll_frame, text=title, 
                                 font=ctk.CTkFont(size=16, weight="bold"), 
                                 text_color="#2D572C", justify="left", anchor="w")
        title_lbl.pack(fill="x", pady=(15, 5))
        
        content_lbl = ctk.CTkLabel(self.scroll_frame, text=content, 
                                   justify="left", anchor="w", wraplength=650)
        content_lbl.pack(fill="x", padx=10, pady=(0, 5))