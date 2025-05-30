from PyQt5.QtWidgets import QToolBar, QToolButton, QLineEdit, QCompleter, QAction, QSizePolicy
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QStandardItemModel, QStandardItem
from PyQt5.QtSvg import QSvgRenderer
from Backend.utils import get_back_svg, get_forward_svg, get_refresh_svg, get_home_svg, get_close_svg
from Backend.tabs import BrowserTab
import os
import json

CONFIG_FILE = "user_preferences.json"
HISTORY_FILE = "browser_history.json"
MAX_HISTORY_ITEMS = 1000

class NavigationBar(QToolBar):
    def __init__(self, tab_widget, browser_manager):
        super().__init__()
        self.tab_widget = tab_widget
        self.browser_manager = browser_manager
        self._icon_cache = {}
        self._completer_model = QStandardItemModel()
        self.setup_ui()
        
    def setup_ui(self):
        self.setMovable(False)
        self.setIconSize(QSize(16, 16))
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.setStyleSheet("""
            QToolBar { background-color: #383838; border: none; spacing: 5px; padding: 5px; min-height: 30px; max-height: 30px; }
            QToolButton { background-color: #383838; color: white; border: none; border-radius: 3px; padding: 5px; }
            QToolButton:hover { background-color: #4f4f4f; }
            QToolButton:disabled { background-color: #2a2a2a; color: #666666; }
            QLineEdit { background-color: #383838; color: white; border: 1px solid #4f4f4f; border-radius: 3px; padding: 5px; selection-background-color: #4285F4; min-height: 20px; max-height: 20px; }
            QLineEdit:focus { border: 1px solid #4285F4; }
            QMenu { background-color: #383838; color: white; border: 1px solid #4f4f4f; }
            QMenu::item { padding: 5px 20px 5px 20px; }
            QMenu::item:selected { background-color: #4f4f4f; }
        """)
        self._create_navigation_buttons()
        self._create_url_bar()
        self._create_additional_buttons()
        self.setFixedHeight(35)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    
    def _create_navigation_buttons(self):
        self.back_button = QToolButton()
        back_icon = self._get_icon_from_svg(get_back_svg())
        self.back_button.setIcon(back_icon)
        self.back_button.setToolTip("Back (Alt+Left)")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setDisabled(True)
        
        self.forward_button = QToolButton()
        forward_icon = self._get_icon_from_svg(get_forward_svg())
        self.forward_button.setIcon(forward_icon)
        self.forward_button.setToolTip("Forward (Alt+Right)")
        self.forward_button.clicked.connect(self.go_forward)
        self.forward_button.setDisabled(True)
        
        self.refresh_button = QToolButton()
        refresh_icon = self._get_icon_from_svg(get_refresh_svg())
        self.refresh_button.setIcon(refresh_icon)
        self.refresh_button.setToolTip("Refresh (F5)")
        self.refresh_button.clicked.connect(self.refresh_page)
        
        self.home_button = QToolButton()
        home_icon = self._get_icon_from_svg(get_home_svg())
        self.home_button.setIcon(home_icon)
        self.home_button.setToolTip("Home")
        self.home_button.clicked.connect(self.go_home)
        
        self.addWidget(self.back_button)
        self.addWidget(self.forward_button)
        self.addWidget(self.refresh_button)
        self.addWidget(self.home_button)
    
    def _create_url_bar(self):
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter a web address")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setFixedHeight(25)
        
        completer = QCompleter(self._completer_model, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.url_bar.setCompleter(completer)
        
        self.url_bar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.url_bar.customContextMenuRequested.connect(self._show_url_context_menu)
        
        self.addWidget(self.url_bar)
    
    def _create_additional_buttons(self):
        pass
    
    def _show_url_context_menu(self, pos):
        menu = self.url_bar.createStandardContextMenu()
        clear_history_action = QAction("Clear Browsing History", self)
        clear_history_action.triggered.connect(self._clear_history)
        menu.addSeparator()
        menu.addAction(clear_history_action)
        menu.exec_(self.url_bar.mapToGlobal(pos))
    
    def _clear_history(self):
        self._completer_model.clear()
        if hasattr(self.browser_manager, 'clear_history'):
            self.browser_manager.clear_history()
    
    def _get_icon_from_svg(self, svg_content, size=16):
        cache_key = f"{svg_content}_{size}"
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        
        renderer = QSvgRenderer()
        renderer.load(bytearray(svg_content.encode('utf-8')))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        icon = QIcon(pixmap)
        self._icon_cache[cache_key] = icon
        return icon
    
    def update_navigation_controls(self):
        if self.tab_widget is None:
            return
        
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.currentWidget()
        self.setVisible(True)
        
        if current_index == 0:
            self.url_bar.clear()
            self.back_button.setEnabled(False)
            self.forward_button.setEnabled(False)
            return
        
        if current_tab:
            self.back_button.setEnabled(current_tab.page().history().canGoBack())
            self.forward_button.setEnabled(current_tab.page().history().canGoForward())
            url = current_tab.url().toString()
            if url != "about:blank":
                self.url_bar.setText(url)
                self._add_to_history(url)
            else:
                self.url_bar.clear()
    
    def _add_to_history(self, url):
        if url and url != "about:blank":
            for i in range(self._completer_model.rowCount()):
                if self._completer_model.item(i).text() == url:
                    return
            
            self._completer_model.insertRow(0, QStandardItem(url))
            if self._completer_model.rowCount() > MAX_HISTORY_ITEMS:
                self._completer_model.removeRow(self._completer_model.rowCount() - 1)
            
            if hasattr(self.browser_manager, 'add_to_history'):
                self.browser_manager.add_to_history(url)
    
    def go_back(self):
        if self.tab_widget is None:
            return
        
        current_tab = self.tab_widget.currentWidget()
        if current_tab and isinstance(current_tab, BrowserTab):
            if current_tab.page().history().canGoBack():
                current_tab.back()
                self.update_navigation_controls()
            
    def go_forward(self):
        if self.tab_widget is None:
            return
        
        current_tab = self.tab_widget.currentWidget()
        if current_tab and isinstance(current_tab, BrowserTab):
            if current_tab.page().history().canGoForward():
                current_tab.forward()
                self.update_navigation_controls()
    
    def go_home(self):
        if self.tab_widget is None:
            return
        
        self.tab_widget.setCurrentIndex(0)
        self.url_bar.clear()
        self.update_navigation_controls()
        
        if hasattr(self.browser_manager, 'go_to_home_tab'):
            self.browser_manager.go_to_home_tab()
            
    def refresh_page(self):
        if self.tab_widget is None:
            return
        
        current_tab = self.tab_widget.currentWidget()
        if current_tab and isinstance(current_tab, BrowserTab):
            current_tab.reload()
            self.update_navigation_controls()
            
    def navigate_to_url(self):
        if self.tab_widget is None or self.browser_manager is None:
            return
        
        url = self.url_bar.text().strip()
        if not url:
            return
        
        current_index = self.tab_widget.currentIndex()
        if current_index == 0:
            self.browser_manager.navigate_to_url(url, new_tab=True)
        else:
            self.browser_manager.navigate_to_url(url)
    
    def load_history(self, urls):
        self._completer_model.clear()
        for url in urls:
            self._completer_model.appendRow(QStandardItem(url))


class BrowserManager:
    def __init__(self, tab_widget):
        from Backend.preferences import PreferencesManager
        self.tab_widget = tab_widget
        self.tabs = []
        self.first_tab_created = False
        self.parent = tab_widget.parent() if tab_widget else None
        self.current_background_color = "#FFFFFF"
        self.navigation_bar = None
        self.history = []
        self._load_history()
        
    def _load_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as f:
                    self.history = json.load(f)
                    if len(self.history) > MAX_HISTORY_ITEMS:
                        self.history = self.history[:MAX_HISTORY_ITEMS]
        except Exception as e:
            print(f"Error loading history: {e}")
            self.history = []
    
    def _save_history(self):
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.history, f)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_to_history(self, url):
        if url in self.history:
            self.history.remove(url)
        self.history.insert(0, url)
        if len(self.history) > MAX_HISTORY_ITEMS:
            self.history = self.history[:MAX_HISTORY_ITEMS]
        QTimer.singleShot(1000, self._save_history)
    
    def clear_history(self):
        self.history = []
        self._save_history()
    
    def go_to_home_tab(self):
        if self.tab_widget and self.tab_widget.count() > 0:
            self.tab_widget.setCurrentIndex(0)
            
            if hasattr(self.parent, 'handler'):
                self.parent.handler.apply_current_background()
            
            self.update_navigation_controls()
        
    def setup_navigation_bar(self, parent_layout):
        self.navigation_bar = NavigationBar(self.tab_widget, self)
        parent_layout.addWidget(self.navigation_bar)
        self.navigation_bar.setVisible(True)
        if self.tab_widget:
            self.tab_widget.currentChanged.connect(self.update_navigation_controls)
        self.navigation_bar.load_history(self.history)

    def update_navigation_controls(self):
        if not self.navigation_bar or not self.tab_widget:
            return
        self.navigation_bar.update_navigation_controls()

    def create_new_tab(self, url=None):
        from PyQt5.QtWidgets import QTabBar, QToolButton
        from PyQt5.QtCore import QSize, Qt
        from PyQt5.QtGui import QIcon, QPixmap, QPainter
        from PyQt5.QtSvg import QSvgRenderer

        if url is None:
            url = "about:blank"
        
        new_tab = BrowserTab(url)
        index = self.tab_widget.addTab(new_tab, "New Tab")
        self.tabs.append(new_tab)
        
        new_tab.navigation_changed.connect(self.update_navigation_controls)
        
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
        
        self.update_navigation_controls()
        return new_tab

    def setup_close_button(self, index):
        from PyQt5.QtWidgets import QTabBar, QToolButton
        from PyQt5.QtCore import QSize, Qt
        from PyQt5.QtGui import QIcon, QPixmap, QPainter
        from PyQt5.QtSvg import QSvgRenderer

        close_button = self.tab_widget.tabBar().tabButton(index, QTabBar.RightSide)
        if isinstance(close_button, QToolButton):
            close_button.setFixedSize(16, 16)
            svg_content = get_close_svg()
            renderer = QSvgRenderer()
            renderer.load(bytearray(svg_content.encode('utf-8')))
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            close_icon = QIcon(pixmap)
            close_button.setIcon(close_icon)
            close_button.setIconSize(QSize(10, 10))
            close_button.setVisible(True)
            self.apply_inactive_tab_style(close_button)

    def apply_active_tab_style(self, button):
        button.setStyleSheet("""
            QToolButton { border: 1px solid rgba(255, 255, 255, 0.3); background: rgba(80, 80, 80, 0.95); border-radius: 8px; margin: 2px 4px 0 0; padding: 2px; }
            QToolButton:hover { background: rgba(200, 60, 60, 0.95); border: 1px solid rgba(255, 255, 255, 0.5); }
        """)

    def apply_inactive_tab_style(self, button):
        button.setStyleSheet("""
            QToolButton { border: 1px solid rgba(255, 255, 255, 0.2); background: rgba(60, 60, 60, 0.95); border-radius: 8px; margin: 2px 4px 0 0; padding: 2px; }
            QToolButton:hover { background: rgba(180, 50, 50, 0.95); border: 1px solid rgba(255, 255, 255, 0.4); }
        """)

    def on_load_finished(self, ok, tab):
        if ok and hasattr(self.parent, 'handler'):
            if self.tab_widget.indexOf(tab) == 0:
                self.parent.handler.apply_current_background()
        self.update_navigation_controls()

    def ensure_first_tab_not_closable(self):
        from PyQt5.QtWidgets import QTabBar
        if self.tab_widget.count() > 0:
            self.tab_widget.tabBar().setTabButton(0, QTabBar.RightSide, None)
            self.tab_widget.tabBar().setTabButton(0, QTabBar.LeftSide, None)

    def update_tab_title(self, title, index):
        if index < 0 or index >= self.tab_widget.count():
            return
        
        if title:
            display_title = title[:15] + "..." if len(title) > 15 else title
            self.tab_widget.setTabText(index, display_title)
            self.tab_widget.setTabToolTip(index, title)
        else:
            self.tab_widget.setTabText(index, "New Tab")
            self.tab_widget.setTabToolTip(index, "")
        
        self.ensure_first_tab_not_closable()

    def close_tab(self, index):
        from PyQt5.QtWidgets import QTabBar
        if index != 0 and self.tab_widget.count() > 1:
            tab_to_close = self.tab_widget.widget(index)
            if self.tabs and index < len(self.tabs):
                self.tabs.pop(index)
            
            self.tab_widget.removeTab(index)
            
            if tab_to_close and isinstance(tab_to_close, BrowserTab):
                tab_to_close.setUrl(QUrl("about:blank"))
                try:
                    tab_to_close.navigation_changed.disconnect()
                    tab_to_close.titleChanged.disconnect()
                    tab_to_close.loadFinished.disconnect()
                except:
                    pass
                tab_to_close.deleteLater()
        
        self.ensure_first_tab_not_closable()
        self.update_navigation_controls()

    def navigate_to_url(self, url, new_tab=False):
        from PyQt5.QtCore import QUrl
        from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
        
        if not url:
            return
        
        if not url.startswith(('http://', 'https://')):
            if '.' in url and not url.startswith('.') and ' ' not in url:
                url = 'https://' + url
            else:
                url = 'https://www.google.com/search?q=' + url.replace(' ', '+')
        
        if new_tab:
            tab = self.create_new_tab()
            self.tab_widget.setTabsClosable(True)
            self.ensure_first_tab_not_closable()
        else:
            tab = self.tab_widget.currentWidget()
        
        if tab and isinstance(tab, BrowserTab):
            if self.navigation_bar:
                self.navigation_bar._add_to_history(url)
            tab.setUrl(QUrl(url))
            if self.navigation_bar:
                self.navigation_bar.url_bar.setText(url)
            self.update_navigation_controls()