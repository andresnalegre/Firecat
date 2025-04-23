import sys
import os
from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QVBoxLayout, 
    QWidget, 
    QTabWidget,
    QTabBar,
    QToolButton,
    QStyle
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl, QObject, pyqtSlot, Qt, QTimer, QSize
from PyQt5.QtGui import QIcon
from Frontend.styles import get_qt_styles
from Backend.logics import BrowserManager, PreferencesManager
from Backend.content import get_html_content
import json

class Handler(QObject):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_background_color = "#FFFFFF"

    @pyqtSlot(str)
    def openLink(self, url):
        if self.parent.tab_widget.count() < 10:
            self.parent.browser_manager.navigate_to_url(url, new_tab=True)
            if self.parent.tab_widget.count() >= 10:
                self.parent.new_tab_button.setVisible(False)

    @pyqtSlot(str)
    def search(self, query):
        if self.parent.tab_widget.count() < 10:
            url = f"https://www.google.com/search?q={query}"
            self.parent.browser_manager.navigate_to_url(url, new_tab=True)
            if self.parent.tab_widget.count() >= 10:
                self.parent.new_tab_button.setVisible(False)

    @pyqtSlot(str)
    def saveSettings(self, settings):
        try:
            settings_dict = json.loads(settings)
            if 'backgroundColor' in settings_dict:
                self.current_background_color = settings_dict['backgroundColor']
            self.parent.preferences.save_settings(settings_dict)
        except Exception as e:
            print(f"Error saving settings: {e}")

    @pyqtSlot()
    def resetSettings(self):
        try:
            self.parent.preferences.reset_settings()
            self.current_background_color = "#FFFFFF"

            if self.parent.tab_widget.count() > 0:
                main_tab = self.parent.tab_widget.widget(0)
                if main_tab:
                    main_tab.page().runJavaScript(
                        f"document.body.style.backgroundColor = '{self.current_background_color}';"
                        f"document.body.style.color = '#000000';"
                    )
        except Exception as e:
            print(f"Error resetting settings: {e}")

    @pyqtSlot(result=str)
    def getSettings(self):
        try:
            settings = self.parent.preferences.load_preferences()
            if 'backgroundColor' in settings:
                self.current_background_color = settings['backgroundColor']
            return json.dumps(settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return json.dumps({})

    @pyqtSlot(str)
    def changeBackground(self, color):
        self.current_background_color = color
        
        current_tab = self.parent.tab_widget.currentWidget()
        if current_tab:
            current_tab.page().runJavaScript(
                f"document.body.style.backgroundColor = '{color}';"
            )
        
        settings = self.parent.preferences.load_preferences()
        settings['backgroundColor'] = color
        self.parent.preferences.save_settings(settings)

    def apply_current_background(self):
        current_tab = self.parent.tab_widget.currentWidget()
        if current_tab:
            current_tab.page().runJavaScript(
                f"document.body.style.backgroundColor = '{self.current_background_color}';"
            )

    @pyqtSlot(str)
    def setMode(self, mode):
        color = '#FFFFFF' if mode == 'light' else '#2e2e2e'
        text_color = '#000000' if mode == 'light' else '#FFFFFF'
        
        self.current_background_color = color
        
        current_tab = self.parent.tab_widget.currentWidget()
        if current_tab:
            js_code = f"""
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
            current_tab.page().runJavaScript(js_code)
        
        settings = self.parent.preferences.load_preferences()
        settings['mode'] = mode
        settings['backgroundColor'] = color
        self.parent.preferences.save_settings(settings)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_browser()
        self.load_preferences()
        
    def init_ui(self):
        self.setWindowTitle("Firecat Browser")
        self.setGeometry(50, 50, 1366, 768)
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
        self.browser_manager.setup_navigation_bar(self.layout)
        
        self.tab_widget.setStyleSheet(get_qt_styles())

        self.tab_bar = self.tab_widget.tabBar()
        
        self.new_tab_button = QToolButton(self.tab_bar)
        self.new_tab_button.setText("+")
        self.new_tab_button.setObjectName("newTabButton")
        self.new_tab_button.clicked.connect(self.add_new_tab)
        
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setExpanding(False)
        
        self.layout.addWidget(self.tab_widget)
        
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_new_tab_button_position)
        self.update_timer.start(100)
    
    def add_new_tab(self):
        if self.tab_widget.count() < 10:
            self.browser_manager.create_new_tab("https://www.google.com")
            self.update_new_tab_button_position()
            if self.tab_widget.count() >= 10:
                self.new_tab_button.hide()

    def update_new_tab_button_position(self):
        if self.tab_widget.count() > 0 and self.tab_widget.count() < 10:
            tab_count = self.tab_widget.count()
            last_tab_rect = self.tab_bar.tabRect(tab_count - 1)
            button_x = last_tab_rect.right() + 2
            button_y = 0
            button_height = self.tab_bar.height()
            self.new_tab_button.setGeometry(button_x, button_y, 40, button_height)
            self.new_tab_button.setVisible(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_new_tab_button_position()

    def init_browser(self):
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

    def tabChanged(self, index):
        self.browser_manager.update_navigation_controls()
        
        for i in range(self.tab_widget.count()):
            close_button = self.tab_widget.tabBar().tabButton(i, QTabBar.RightSide)
            if isinstance(close_button, QToolButton) and i > 0:
                close_button.setVisible(True)
                if i == index:
                    close_button.setStyleSheet("""
                        QToolButton {
                            border: none;
                            background: rgba(255, 255, 255, 0.8);
                            border-radius: 2px;
                            margin: 2px 4px 0 0;
                        }
                        QToolButton:hover {
                            background: rgba(255, 255, 255, 1.0);
                        }
                    """)
                else:
                    close_button.setStyleSheet("""
                        QToolButton {
                            border: none;
                            background: rgba(96, 96, 96, 0.8);
                            border-radius: 2px;
                            margin: 2px 4px 0 0;
                        }
                        QToolButton:hover {
                            background: rgba(255, 255, 255, 0.3);
                        }
                    """)

    def load_preferences(self):
        self.preferences = PreferencesManager()
        
    def close_tab(self, index):
        self.browser_manager.close_tab(index)
        if self.tab_widget.count() < 10:
            self.new_tab_button.show()
        self.update_new_tab_button_position()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())