import json
import os
from urllib.parse import urlparse
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, QSize
from PyQt5.QtWidgets import QTabBar, QToolButton
from PyQt5.QtGui import QIcon
from Frontend.styles import get_qt_styles

CONFIG_FILE = "user_preferences.json"
IMAGE_FOLDER = "background_images"

class BrowserTab(QWebEngineView):
    def __init__(self, url=None):
        super().__init__()
        if url:
            self.setUrl(QUrl(url))

class BrowserManager:
    def __init__(self, tab_widget):
        self.tab_widget = tab_widget
        self.tabs = []
        self.first_tab_created = False
        self.parent = tab_widget.parent()
        self.current_background_color = "#2e2e2e"

    def create_new_tab(self, url=None):
        if url is None:
            url = "about:blank"
            
        new_tab = BrowserTab(url)
        index = self.tab_widget.addTab(new_tab, "New Tab")
        self.tabs.append(new_tab)
        
        if hasattr(self.parent, 'channel'):
            new_tab.page().setWebChannel(self.parent.channel)
            if hasattr(self.parent, 'handler'):
                self.parent.handler.apply_current_background()
        
        if not self.first_tab_created:
            self.first_tab_created = True
            self.tab_widget.setTabsClosable(False)
        else:
            self.tab_widget.setTabsClosable(True)
            self.setup_close_button(index)
        
        self.ensure_first_tab_not_closable()
        self.tab_widget.setCurrentIndex(index)
        
        new_tab.titleChanged.connect(
            lambda title, tab=new_tab: self.update_tab_title(title, self.tab_widget.indexOf(tab))
        )
        
        new_tab.loadFinished.connect(
            lambda ok, tab=new_tab: self.on_load_finished(ok, tab)
        )
        
        if hasattr(self.parent, 'update_new_tab_button_position'):
            self.parent.update_new_tab_button_position()
        
        return new_tab

    def setup_close_button(self, index):
        close_button = self.tab_widget.tabBar().tabButton(index, QTabBar.RightSide)
        if isinstance(close_button, QToolButton):
            close_button.setFixedSize(16, 16)
            close_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "../Firecat/Images/close.png")))
            close_button.setIconSize(QSize(10, 10))
            close_button.setVisible(True)
            self.apply_inactive_tab_style(close_button)

    def apply_active_tab_style(self, button):
        button.setStyleSheet("""
            QToolButton {
                border: 1px solid rgba(255, 255, 255, 0.3);
                background: rgba(80, 80, 80, 0.95);
                border-radius: 8px;
                margin: 2px 4px 0 0;
                padding: 2px;
            }
            QToolButton:hover {
                background: rgba(200, 60, 60, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
        """)

    def apply_inactive_tab_style(self, button):
        button.setStyleSheet("""
            QToolButton {
                border: 1px solid rgba(255, 255, 255, 0.2);
                background: rgba(60, 60, 60, 0.95);
                border-radius: 8px;
                margin: 2px 4px 0 0;
                padding: 2px;
            }
            QToolButton:hover {
                background: rgba(180, 50, 50, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }
        """)

    def on_load_finished(self, ok, tab):
        if ok and hasattr(self.parent, 'handler'):
            self.parent.handler.apply_current_background()

    def ensure_first_tab_not_closable(self):
        self.tab_widget.tabBar().setTabButton(0, QTabBar.RightSide, None)
        self.tab_widget.tabBar().setTabButton(0, QTabBar.LeftSide, None)

    def update_tab_title(self, title, index):
        if title:
            self.tab_widget.setTabText(
                index, 
                title[:15] + "..." if len(title) > 15 else title
            )
        else:
            self.tab_widget.setTabText(index, "New Tab")
        self.ensure_first_tab_not_closable()

    def close_tab(self, index):
        if index != 0 and self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
            if self.tabs:
                self.tabs.pop(index)
        self.ensure_first_tab_not_closable()

    def navigate_to_url(self, url, new_tab=False):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        if new_tab:
            tab = self.create_new_tab()
            self.tab_widget.setTabsClosable(True)
            self.ensure_first_tab_not_closable()
        else:
            tab = self.tab_widget.currentWidget()
            
        tab.setUrl(QUrl(url))

class PreferencesManager:
    def __init__(self):
        self.config_file = CONFIG_FILE
        self.image_folder = IMAGE_FOLDER
        self._ensure_directories()

    def _ensure_directories(self):
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)

    def load_preferences(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                    default_settings = self._get_default_settings()
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
            except json.JSONDecodeError:
                return self._get_default_settings()
        return self._get_default_settings()

    def _get_default_settings(self):
        return {
            "theme": "dark",
            "backgroundColor": "#2e2e2e",
            "backgroundImage": None,
            "shortcuts": True
        }

    def save_settings(self, settings):
        try:
            default_settings = self._get_default_settings()
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
                    
            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def reset_settings(self):
        self.save_settings(self._get_default_settings())

    def set_background_image(self, image_path):
        if os.path.exists(image_path):
            image_name = os.path.basename(image_path)
            target_path = os.path.join(self.image_folder, image_name)

            with open(image_path, 'rb') as fsrc:
                with open(target_path, 'wb') as fdst:
                    fdst.write(fsrc.read())

            preferences = self.load_preferences()
            preferences['backgroundImage'] = target_path
            self.save_settings(preferences)
        else:
            raise FileNotFoundError(f"Image file '{image_path}' does not exist.")

    def get_background_image(self):
        preferences = self.load_preferences()
        return preferences.get('backgroundImage', None)

    def clear_background_image(self):
        preferences = self.load_preferences()
        preferences['backgroundImage'] = None
        self.save_settings(preferences)

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) or "." in url
    except ValueError:
        return False