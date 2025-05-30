import sys
import os
import gc
from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QVBoxLayout, 
    QWidget, 
    QTabWidget,
    QTabBar,
    QToolButton,
    QStyle,
    QShortcut,
    QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineProfile
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl, QObject, pyqtSlot, Qt, QTimer, QSize, QEvent, QCoreApplication
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap
from Frontend.styles import get_qt_styles
from Backend.logics import BrowserManager, PreferencesManager
from Backend.content import get_html_content
import json
import weakref

QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

class Handler(QObject):
    def __init__(self, parent):
        super().__init__()
        self.parent = weakref.ref(parent)
        self.current_background_color = "#FFFFFF"
        self._js_cache = {}

    def _get_parent(self):
        parent = self.parent()
        if parent is None:
            raise RuntimeError("Parent window has been destroyed")
        return parent

    def _is_home_tab(self, tab):
        if not tab:
            return False
        parent = self._get_parent()
        return parent.tab_widget.indexOf(tab) == 0

    @pyqtSlot(str)
    def openLink(self, url):
        parent = self._get_parent()
        if parent.tab_widget.count() < parent.MAX_TABS:
            parent.browser_manager.navigate_to_url(url, new_tab=True)
            if parent.tab_widget.count() >= parent.MAX_TABS:
                parent.new_tab_button.setVisible(False)

    @pyqtSlot(str)
    def search(self, query):
        parent = self._get_parent()
        if parent.tab_widget.count() < parent.MAX_TABS:
            url = f"https://www.google.com/search?q={query}"
            parent.browser_manager.navigate_to_url(url, new_tab=True)
            if parent.tab_widget.count() >= parent.MAX_TABS:
                parent.new_tab_button.setVisible(False)

    @pyqtSlot(str)
    def saveSettings(self, settings):
        try:
            settings_dict = json.loads(settings)
            if 'backgroundColor' in settings_dict:
                self.current_background_color = settings_dict['backgroundColor']
            self._get_parent().preferences.save_settings(settings_dict)
        except Exception as e:
            print(f"Error saving settings: {e}")

    @pyqtSlot()
    def resetSettings(self):
        try:
            parent = self._get_parent()
            parent.preferences.reset_settings()
            self.current_background_color = "#FFFFFF"
            main_tab = parent.tab_widget.widget(0)
            if main_tab and self._is_home_tab(main_tab):
                js_code = (
                    f"document.body.style.backgroundColor = '{self.current_background_color}';"
                    f"document.body.style.color = '#000000';"
                )
                main_tab.page().runJavaScript(js_code)
        except Exception as e:
            print(f"Error resetting settings: {e}")

    @pyqtSlot(result=str)
    def getSettings(self):
        try:
            settings = self._get_parent().preferences.load_preferences()
            if 'backgroundColor' in settings:
                self.current_background_color = settings['backgroundColor']
            return json.dumps(settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return json.dumps({})

    def _save_theme_preference(self, color=None, mode=None):
        settings = self._get_parent().preferences.load_preferences()
        if color is not None:
            settings['backgroundColor'] = color
        if mode is not None:
            settings['mode'] = mode
        self._get_parent().preferences.save_settings(settings)

    @pyqtSlot(str)
    def changeBackground(self, color):
        self.current_background_color = color
        parent = self._get_parent()
        main_tab = parent.tab_widget.widget(0)
        if main_tab and self._is_home_tab(main_tab):
            js_key = f"bg_{color}"
            if js_key not in self._js_cache:
                self._js_cache[js_key] = f"document.body.style.backgroundColor = '{color}';"
            main_tab.page().runJavaScript(self._js_cache[js_key])
        self._save_theme_preference(color=color)

    def apply_current_background(self):
        parent = self._get_parent()
        main_tab = parent.tab_widget.widget(0)
        if main_tab and self._is_home_tab(main_tab):
            js_key = f"bg_{self.current_background_color}"
            if js_key not in self._js_cache:
                self._js_cache[js_key] = f"document.body.style.backgroundColor = '{self.current_background_color}';"
            main_tab.page().runJavaScript(self._js_cache[js_key])

    @pyqtSlot(str)
    def setMode(self, mode):
        color = '#FFFFFF' if mode == 'light' else '#2e2e2e'
        text_color = '#000000' if mode == 'light' else '#FFFFFF'
        self.current_background_color = color
        parent = self._get_parent()
        main_tab = parent.tab_widget.widget(0)
        if main_tab and self._is_home_tab(main_tab):
            js_key = f"mode_{mode}"
            if js_key not in self._js_cache:
                self._js_cache[js_key] = f"""
                    document.body.style.backgroundColor = '{color}';
                    document.body.style.color = '{text_color}';
                    document.body.classList.remove('light-mode', 'dark-mode');
                    document.body.classList.add('{mode}-mode');
                    const searchBar = document.querySelector('.search-bar');
                    if (searchBar) {{
                        searchBar.style.backgroundColor = '{('#FFFFFF' if mode == 'light' else '#3b3b3b')}';
                        searchBar.style.color = '{text_color}';
                    }}
                    document.querySelectorAll('.shortcut').forEach(shortcut => {{
                        shortcut.style.backgroundColor = '{('#f0f0f0' if mode == 'light' else '#2e2e2e')}';
                    }});
                """
            main_tab.page().runJavaScript(self._js_cache[js_key])
        self._save_theme_preference(color=color, mode=mode)

class MainWindow(QMainWindow):
    MAX_TABS = 10
    UPDATE_INTERVAL = 250
    DEFAULT_WIDTH = 1366
    DEFAULT_HEIGHT = 768
    
    def __init__(self):
        super().__init__()
        self._setup_window_properties()
        self.init_ui()
        self.init_browser()
        self.load_preferences()
        self.setup_shortcuts()
        self.gc_timer = QTimer(self)
        self.gc_timer.timeout.connect(self._collect_garbage)
        self.gc_timer.start(30000)
    
    def _setup_window_properties(self):
        self.setWindowTitle("Firecat Browser")
        self.setGeometry(50, 50, self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "firecat.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def _collect_garbage(self):
        gc.collect()
        
    def init_ui(self):
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)
        self.browser_manager = BrowserManager(None)
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setElideMode(Qt.ElideRight)
        self.tab_widget.setMovable(True)
        self.tab_widget.currentChanged.connect(self.tabChanged)
        self.browser_manager.tab_widget = self.tab_widget
        self.browser_manager.parent = self
        self.browser_manager.setup_navigation_bar(self.layout)
        self.tab_widget.setStyleSheet(get_qt_styles())
        self.tab_bar = self.tab_widget.tabBar()
        self.new_tab_button = QToolButton(self.tab_bar)
        self.new_tab_button.setText("+")
        self.new_tab_button.setObjectName("newTabButton")
        self.new_tab_button.setToolTip("New Tab (Ctrl+T)")
        self.new_tab_button.clicked.connect(self.add_new_tab)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setExpanding(False)
        self.layout.addWidget(self.tab_widget)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_new_tab_button_position)
        self.update_timer.start(self.UPDATE_INTERVAL)
        self.tab_widget.tabBar().installEventFilter(self)
    
    def setup_shortcuts(self):
        shortcuts = [
            (QKeySequence("Ctrl+T"), self.add_new_tab),
            (QKeySequence("Ctrl+W"), lambda: self.close_tab(self.tab_widget.currentIndex())),
            (QKeySequence("F5"), self.reload_current_tab),
            (QKeySequence("Ctrl+R"), self.reload_current_tab),
            (QKeySequence("Ctrl+L"), self.focus_url_bar),
            (QKeySequence("Alt+Left"), self.navigate_back),
            (QKeySequence("Alt+Right"), self.navigate_forward),
            (QKeySequence("Ctrl+Tab"), self.next_tab),
            (QKeySequence("Ctrl+Shift+Tab"), self.previous_tab),
            (QKeySequence("Ctrl+1"), lambda: self.go_to_tab(0)),
            (QKeySequence("Ctrl+2"), lambda: self.go_to_tab(1)),
            (QKeySequence("Ctrl+3"), lambda: self.go_to_tab(2)),
            (QKeySequence("Ctrl+4"), lambda: self.go_to_tab(3)),
            (QKeySequence("Ctrl+5"), lambda: self.go_to_tab(4)),
            (QKeySequence("Ctrl+6"), lambda: self.go_to_tab(5)),
            (QKeySequence("Ctrl+7"), lambda: self.go_to_tab(6)),
            (QKeySequence("Ctrl+8"), lambda: self.go_to_tab(7)),
            (QKeySequence("Ctrl+9"), lambda: self.go_to_tab(8)),
        ]
        self.shortcut_objects = []
        for key, callback in shortcuts:
            shortcut = QShortcut(key, self)
            shortcut.activated.connect(callback)
            self.shortcut_objects.append(shortcut)
    
    def go_to_tab(self, index):
        if 0 <= index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(index)
    
    def next_tab(self):
        current = self.tab_widget.currentIndex()
        count = self.tab_widget.count()
        if count > 1:
            self.tab_widget.setCurrentIndex((current + 1) % count)
    
    def previous_tab(self):
        current = self.tab_widget.currentIndex()
        count = self.tab_widget.count()
        if count > 1:
            self.tab_widget.setCurrentIndex((current - 1) % count)
    
    def navigate_back(self):
        if self.browser_manager.navigation_bar:
            self.browser_manager.navigation_bar.go_back()
    
    def navigate_forward(self):
        if self.browser_manager.navigation_bar:
            self.browser_manager.navigation_bar.go_forward()
    
    def reload_current_tab(self):
        if self.browser_manager.navigation_bar:
            self.browser_manager.navigation_bar.refresh_page()
    
    def focus_url_bar(self):
        if self.browser_manager.navigation_bar:
            self.browser_manager.navigation_bar.url_bar.setFocus()
            self.browser_manager.navigation_bar.url_bar.selectAll()
    
    def eventFilter(self, obj, event):
        if obj == self.tab_widget.tabBar() and event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MiddleButton:
                tab_index = self.tab_widget.tabBar().tabAt(event.pos())
                if tab_index > 0:
                    self.close_tab(tab_index)
                    return True
        return super().eventFilter(obj, event)
    
    def add_new_tab(self):
        if self.tab_widget.count() < self.MAX_TABS:
            self.browser_manager.create_new_tab("https://www.google.com")
            self.update_new_tab_button_position()
            if self.tab_widget.count() >= self.MAX_TABS:
                self.new_tab_button.hide()
        else:
            QMessageBox.information(self, "Tab Limit", f"Maximum of {self.MAX_TABS} tabs allowed.")

    def update_new_tab_button_position(self):
        if not self.tab_widget or not self.tab_bar:
            return
        if self.tab_widget.count() > 0 and self.tab_widget.count() < self.MAX_TABS:
            tab_count = self.tab_widget.count()
            last_tab_rect = self.tab_bar.tabRect(tab_count - 1)
            button_x = last_tab_rect.right() + 2
            button_y = 0
            button_height = self.tab_bar.height()
            self.new_tab_button.setGeometry(button_x, button_y, 40, button_height)
            self.new_tab_button.setVisible(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.update_new_tab_button_position)

    def init_browser(self):
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)
        profile.setCachePath(os.path.join(os.path.expanduser("~"), ".firecat", "cache"))
        profile.setPersistentStoragePath(os.path.join(os.path.expanduser("~"), ".firecat", "storage"))
        os.makedirs(profile.cachePath(), exist_ok=True)
        os.makedirs(profile.persistentStoragePath(), exist_ok=True)
        settings = QWebEngineSettings.globalSettings()
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadIconsForPage, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        self.current_tab = self.browser_manager.create_new_tab()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabBar().setTabButton(0, QTabBar.RightSide, None)
        for i in range(1, self.tab_widget.count()):
            close_button = self.tab_widget.tabBar().tabButton(i, QTabBar.RightSide)
            if isinstance(close_button, QToolButton):
                close_button.setVisible(True)
        self.channel = QWebChannel()
        self.handler = Handler(self)
        self.channel.registerObject('handler', self.handler)
        self.current_tab.page().setWebChannel(self.channel)
        self.current_tab.setHtml(get_html_content())
        self.update_new_tab_button_position()
        # Aplique a cor salva ao criar a home tab
        if hasattr(self, 'preferences'):
            color = self.preferences.get_background_color()
            QTimer.singleShot(500, lambda: self.handler.changeBackground(color))

    def tabChanged(self, index):
        self.browser_manager.update_navigation_controls()
        active_style = """
            QToolButton {
                border: none;
                background: rgba(255, 255, 255, 0.8);
                border-radius: 2px;
                margin: 2px 4px 0 0;
            }
            QToolButton:hover {
                background: rgba(255, 255, 255, 1.0);
            }
        """
        inactive_style = """
            QToolButton {
                border: none;
                background: rgba(96, 96, 96, 0.8);
                border-radius: 2px;
                margin: 2px 4px 0 0;
            }
            QToolButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """
        for i in range(self.tab_widget.count()):
            close_button = self.tab_widget.tabBar().tabButton(i, QTabBar.RightSide)
            if isinstance(close_button, QToolButton) and i > 0:
                close_button.setVisible(True)
                current_style = active_style if i == index else inactive_style
                if close_button.property("current_style") != current_style:
                    close_button.setStyleSheet(current_style)
                    close_button.setProperty("current_style", current_style)

    def load_preferences(self):
        self.preferences = PreferencesManager()
        settings = self.preferences.load_preferences()
        if hasattr(self, 'handler'):
            if 'backgroundColor' in settings:
                QTimer.singleShot(500, lambda: self.handler.changeBackground(settings['backgroundColor']))
            if 'mode' in settings:
                QTimer.singleShot(600, lambda: self.handler.setMode(settings['mode']))
        else:
            self._pending_preferences = settings
        
    def close_tab(self, index):
        if index <= 0:
            return
        self.browser_manager.close_tab(index)
        if self.tab_widget.count() < self.MAX_TABS:
            self.new_tab_button.show()
        self.update_new_tab_button_position()
    
    def _save_mode_before_exit(self, mode):
        if hasattr(self, 'preferences'):
            settings = self.preferences.load_preferences()
            settings['mode'] = mode
            self.preferences.save_settings(settings)
    
    def closeEvent(self, event):
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
        if hasattr(self, 'gc_timer') and self.gc_timer.isActive():
            self.gc_timer.stop()
        if hasattr(self, 'handler') and hasattr(self, 'preferences'):
            settings = self.preferences.load_preferences()
            settings['backgroundColor'] = self.handler.current_background_color
            self.preferences.save_settings(settings)
            home_tab = self.tab_widget.widget(0)
            if home_tab:
                home_tab.page().runJavaScript(
                    "document.body.classList.contains('dark-mode') ? 'dark' : 'light'",
                    lambda result: self._save_mode_before_exit(result)
                )
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab:
                tab.setUrl(QUrl("about:blank"))
                tab.page().deleteLater()
        gc.collect()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Firecat Browser")
    app.setOrganizationName("Firecat")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())