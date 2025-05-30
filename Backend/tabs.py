from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
from PyQt5.QtCore import pyqtSignal, QUrl

class BrowserTab(QWebEngineView):
    navigation_changed = pyqtSignal()
    
    def __init__(self, url=None):
        super().__init__()
        self._page = QWebEnginePage(self)
        self.setPage(self._page)
        self._page.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
        self._page.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        self._page.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        self._page.loadStarted.connect(self.on_navigation_changed)
        self._page.loadFinished.connect(self.on_navigation_changed)
        self._page.urlChanged.connect(self.on_navigation_changed)
        self._page.loadProgress.connect(lambda _: self.navigation_changed.emit())
        if url:
            self.setUrl(QUrl(url))
    
    def on_navigation_changed(self):
        self.navigation_changed.emit()
            
    def back(self):
        self.page().triggerAction(QWebEnginePage.Back)
        self.navigation_changed.emit()
        
    def forward(self):
        self.page().triggerAction(QWebEnginePage.Forward)
        self.navigation_changed.emit()
        
    def reload(self):
        self.page().triggerAction(QWebEnginePage.Reload)
        self.navigation_changed.emit()