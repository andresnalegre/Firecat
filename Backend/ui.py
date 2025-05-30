import sys
import os
import gc
import json
import weakref

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget, QTabBar,
    QToolButton, QShortcut, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineProfile
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl, QObject, pyqtSlot, Qt, QTimer, QSize, QEvent, QCoreApplication
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap

from Frontend.styles import get_qt_styles
from Backend.browser import BrowserManager
from Backend.preferences import PreferencesManager
from Backend.content import get_html_content

# Configuração global da aplicação para alta resolução
QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

class Handler(QObject):
    """Manipulador para interação entre JavaScript e Python"""
    
    def __init__(self, parent):
        super().__init__()
        self.parent = weakref.ref(parent)
        self.current_background_color = "#FFFFFF"
        self._js_cache = {}
        self._current_mode = "light"
    
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
    
    def _get_home_tab(self):
        """Retorna a tab inicial se existir"""
        parent = self._get_parent()
        if parent.tab_widget.count() > 0:
            tab = parent.tab_widget.widget(0)
            if self._is_home_tab(tab):
                return tab
        return None
    
    def _update_preferences(self, **kwargs):
        """Atualiza as preferências com os valores fornecidos"""
        parent = self._get_parent()
        settings = parent.preferences.load_preferences()
        for key, value in kwargs.items():
            settings[key] = value
        parent.preferences.save_settings(settings)
        return settings
    
    def _get_js_code(self, key, generator):
        """Recupera ou cria código JS em cache"""
        if key not in self._js_cache:
            self._js_cache[key] = generator()
        return self._js_cache[key]

    def _apply_js_to_home_tab(self, js_code):
        """Aplica código JavaScript à tab inicial"""
        tab = self._get_home_tab()
        if tab:
            tab.page().runJavaScript(js_code)

    @pyqtSlot(str)
    def openLink(self, url):
        parent = self._get_parent()
        if parent.tab_widget.count() < parent.MAX_TABS:
            parent.browser_manager.navigate_to_url(url, new_tab=True)
            parent.update_tab_ui()

    @pyqtSlot(str)
    def search(self, query):
        parent = self._get_parent()
        if parent.tab_widget.count() < parent.MAX_TABS:
            url = f"https://www.google.com/search?q={query}"
            parent.browser_manager.navigate_to_url(url, new_tab=True)
            parent.update_tab_ui()

    @pyqtSlot(str)
    def saveSettings(self, settings):
        try:
            settings_dict = json.loads(settings)
            if 'backgroundColor' in settings_dict:
                self.current_background_color = settings_dict['backgroundColor']
            if 'mode' in settings_dict:
                self._current_mode = settings_dict['mode']
            self._update_preferences(**settings_dict)
        except Exception as e:
            print(f"Error saving settings: {e}")

    @pyqtSlot()
    def resetSettings(self):
        try:
            parent = self._get_parent()
            parent.preferences.reset_settings()
            self.current_background_color = "#FFFFFF"
            self._current_mode = "light"
            self._apply_js_to_home_tab(
                "document.body.style.backgroundColor = '#FFFFFF';"
                "document.body.style.color = '#000000';"
                "document.body.classList.remove('light-mode', 'dark-mode');"
                "document.body.classList.add('light-mode');"
            )
        except Exception as e:
            print(f"Error resetting settings: {e}")

    @pyqtSlot(result=str)
    def getSettings(self):
        try:
            settings = self._get_parent().preferences.load_preferences()
            # Sincroniza o estado interno com as configurações carregadas
            if 'backgroundColor' in settings:
                self.current_background_color = settings['backgroundColor']
            if 'mode' in settings:
                self._current_mode = settings['mode']
            return json.dumps(settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return json.dumps({})

    @pyqtSlot(str)
    def changeBackground(self, color):
        self.current_background_color = color
        
        # Determinar o modo com base na cor
        if color.lower() == '#ffffff':
            mode = 'light'
        elif color.lower() == '#2e2e2e':
            mode = 'dark'
        else:
            mode = 'custom'
        
        # Atualizar o modo atual
        self._current_mode = mode
        
        # Aplicar a cor de fundo
        js_code = self._get_js_code(f"bg_{color}", 
                                lambda: f"document.body.style.backgroundColor = '{color}';")
        self._apply_js_to_home_tab(js_code)
        
        # Salvar preferências com a cor e o modo correto
        self._update_preferences(backgroundColor=color, mode=mode)

    def apply_current_background(self):
        """Aplica a cor de fundo atual à tab inicial"""
        js_code = self._get_js_code(f"bg_{self.current_background_color}", 
                                lambda: f"document.body.style.backgroundColor = '{self.current_background_color}';")
        self._apply_js_to_home_tab(js_code)

    @pyqtSlot(str)
    def setMode(self, mode):
        self._current_mode = mode
        
        # Para modo personalizado, não alteramos a cor atual
        if mode == 'custom':
            # Apenas atualiza as classes e elementos sem mudar a cor
            js_code = self._get_js_code(f"mode_{mode}", lambda: f"""
                document.body.classList.remove('light-mode', 'dark-mode', 'custom-mode');
                document.body.classList.add('custom-mode');
                
                // Desselecionar botões light/dark
                document.querySelectorAll('.customize-mode button').forEach(button => {{
                    button.classList.remove('active');
                }});
                
                // Manter a cor atual, apenas garantir que todo resto está atualizado
                const textColor = getContrastYIQ(document.body.style.backgroundColor);
                
                // Atualizar cor do texto
                document.body.style.color = textColor;
                
                // Atualizar barra de pesquisa
                const searchBar = document.querySelector('.search-bar');
                if (searchBar) {{
                    searchBar.style.backgroundColor = textColor === '#000000' ? '#FFFFFF' : '#3b3b3b';
                    searchBar.style.color = textColor;
                }}
                
                // Atualizar atalhos
                document.querySelectorAll('.shortcut').forEach(shortcut => {{
                    shortcut.style.backgroundColor = textColor === '#000000' ? '#f0f0f0' : '#2e2e2e';
                    const svg = shortcut.querySelector('svg');
                    if (svg) {{
                        svg.style.fill = textColor;
                    }}
                }});
            """)
            
            self._apply_js_to_home_tab(js_code)
            # Manter a cor atual, apenas atualizar o modo
            self._update_preferences(mode=mode)
            return
        
        # Para modos light/dark, usar valores padrão
        color = '#FFFFFF' if mode == 'light' else '#2e2e2e'
        text_color = '#000000' if mode == 'light' else '#FFFFFF'
        search_bg = '#FFFFFF' if mode == 'light' else '#3b3b3b'
        shortcut_bg = '#f0f0f0' if mode == 'light' else '#2e2e2e'
        
        self.current_background_color = color
        
        js_code = self._get_js_code(f"mode_{mode}", lambda: f"""
            document.body.style.backgroundColor = '{color}';
            document.body.style.color = '{text_color}';
            document.body.classList.remove('light-mode', 'dark-mode', 'custom-mode');
            document.body.classList.add('{mode}-mode');
            
            // Atualizar seleção dos botões
            document.querySelectorAll('.customize-mode button').forEach(button => {{
                button.classList.remove('active');
            }});
            if (document.getElementById('{mode}')) {{
                document.getElementById('{mode}').classList.add('active');
            }}
            
            const searchBar = document.querySelector('.search-bar');
            if (searchBar) {{
                searchBar.style.backgroundColor = '{search_bg}';
                searchBar.style.color = '{text_color}';
            }}
            document.querySelectorAll('.shortcut').forEach(shortcut => {{
                shortcut.style.backgroundColor = '{shortcut_bg}';
                const svg = shortcut.querySelector('svg');
                if (svg) {{
                    svg.style.fill = '{text_color}';
                }}
            }});
        """)
        
        self._apply_js_to_home_tab(js_code)
        self._update_preferences(backgroundColor=color, mode=mode)


class MainWindow(QMainWindow):
    MAX_TABS = 10
    UPDATE_INTERVAL = 250
    DEFAULT_WIDTH = 1366
    DEFAULT_HEIGHT = 768
    
    def __init__(self):
        super().__init__()
        # Inicialização das preferências antes de tudo
        self.preferences = PreferencesManager()
        
        self._setup_window_properties()
        self.init_ui()
        self.init_browser()
        self.setup_shortcuts()
        
        # Configurar garbage collector timer
        self.gc_timer = QTimer(self)
        self.gc_timer.timeout.connect(lambda: gc.collect())
        self.gc_timer.start(30000)  # 30 segundos
    
    def _setup_window_properties(self):
        """Configura as propriedades básicas da janela"""
        self.setWindowTitle("Firecat Browser")
        self.setGeometry(50, 50, self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "firecat.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def init_ui(self):
        """Inicializa a interface do usuário"""
        # Widget central e layout
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)
        
        # Gerenciador de navegador
        self.browser_manager = BrowserManager(None)
        
        # Widget de abas
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setElideMode(Qt.ElideRight)
        self.tab_widget.setMovable(True)
        self.tab_widget.currentChanged.connect(self.tab_changed)
        self.tab_widget.setStyleSheet(get_qt_styles())
        
        # Configurar o gerenciador de navegador
        self.browser_manager.tab_widget = self.tab_widget
        self.browser_manager.parent = self
        self.browser_manager.setup_navigation_bar(self.layout)
        
        # Configurar barra de abas e botão de nova aba
        self.tab_bar = self.tab_widget.tabBar()
        self.new_tab_button = QToolButton(self.tab_bar)
        self.new_tab_button.setText("+")
        self.new_tab_button.setObjectName("newTabButton")
        self.new_tab_button.setToolTip("New Tab (Ctrl+T)")
        self.new_tab_button.clicked.connect(self.add_new_tab)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setExpanding(False)
        
        # Adicionar widget de abas ao layout
        self.layout.addWidget(self.tab_widget)
        
        # Timer para atualizar posição do botão de nova aba
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_tab_ui)
        self.update_timer.start(self.UPDATE_INTERVAL)
        
        # Filtro de eventos para a barra de abas
        self.tab_widget.tabBar().installEventFilter(self)
    
    def setup_shortcuts(self):
        """Configura os atalhos de teclado"""
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
        ]
        
        # Adicionar atalhos para alternar entre abas (Ctrl+1 até Ctrl+9)
        for i in range(9):
            shortcuts.append((QKeySequence(f"Ctrl+{i+1}"), lambda idx=i: self.go_to_tab(idx)))
        
        # Criar os objetos de atalho
        self.shortcut_objects = []
        for key, callback in shortcuts:
            shortcut = QShortcut(key, self)
            shortcut.activated.connect(callback)
            self.shortcut_objects.append(shortcut)
    
    def go_to_tab(self, index):
        """Muda para a aba com o índice especificado"""
        if 0 <= index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(index)
    
    def next_tab(self):
        """Muda para a próxima aba"""
        current = self.tab_widget.currentIndex()
        count = self.tab_widget.count()
        if count > 1:
            self.tab_widget.setCurrentIndex((current + 1) % count)
    
    def previous_tab(self):
        """Muda para a aba anterior"""
        current = self.tab_widget.currentIndex()
        count = self.tab_widget.count()
        if count > 1:
            self.tab_widget.setCurrentIndex((current - 1) % count)
    
    def navigate_back(self):
        """Navega para trás na página atual"""
        if self.browser_manager.navigation_bar:
            self.browser_manager.navigation_bar.go_back()
    
    def navigate_forward(self):
        """Navega para frente na página atual"""
        if self.browser_manager.navigation_bar:
            self.browser_manager.navigation_bar.go_forward()
    
    def reload_current_tab(self):
        """Recarrega a página atual"""
        if self.browser_manager.navigation_bar:
            self.browser_manager.navigation_bar.refresh_page()
    
    def focus_url_bar(self):
        """Coloca o foco na barra de URL"""
        if self.browser_manager.navigation_bar:
            self.browser_manager.navigation_bar.url_bar.setFocus()
            self.browser_manager.navigation_bar.url_bar.selectAll()
    
    def eventFilter(self, obj, event):
        """Filtro de eventos personalizado"""
        if obj == self.tab_widget.tabBar() and event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MiddleButton:
                tab_index = self.tab_widget.tabBar().tabAt(event.pos())
                if tab_index > 0:  # Não fechar a tab inicial
                    self.close_tab(tab_index)
                    return True
        return super().eventFilter(obj, event)
    
    def add_new_tab(self):
        """Adiciona uma nova aba de navegação"""
        if self.tab_widget.count() < self.MAX_TABS:
            self.browser_manager.create_new_tab("https://www.google.com")
            self.update_tab_ui()
        else:
            QMessageBox.information(self, "Tab Limit", f"Maximum of {self.MAX_TABS} tabs allowed.")

    def update_tab_ui(self):
        """Atualiza a UI das abas, incluindo posição e visibilidade do botão '+'"""
        if not self.tab_widget or not self.tab_bar:
            return
            
        # Atualizar visibilidade do botão de nova aba
        should_show = self.tab_widget.count() > 0 and self.tab_widget.count() < self.MAX_TABS
        self.new_tab_button.setVisible(should_show)
        
        if should_show:
            # Posicionar o botão após a última aba
            tab_count = self.tab_widget.count()
            last_tab_rect = self.tab_bar.tabRect(tab_count - 1)
            button_x = last_tab_rect.right() + 2
            button_y = 0
            button_height = self.tab_bar.height()
            self.new_tab_button.setGeometry(button_x, button_y, 40, button_height)

    def resizeEvent(self, event):
        """Evento de redimensionamento"""
        super().resizeEvent(event)
        QTimer.singleShot(0, self.update_tab_ui)

    def init_browser(self):
        """Inicializa o navegador e suas configurações"""
        # Configurar o perfil do WebEngine
        self._setup_web_profile()
        
        # Criar primeira aba
        self.current_tab = self.browser_manager.create_new_tab()
        
        # Configurar tabs fecháveis
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabBar().setTabButton(0, QTabBar.RightSide, None)  # Exceto a primeira
        
        # Configurar comunicação JS-Python
        self.channel = QWebChannel()
        self.handler = Handler(self)
        self.channel.registerObject('handler', self.handler)
        self.current_tab.page().setWebChannel(self.channel)
        
        # Carregar página inicial
        self.current_tab.setHtml(get_html_content())
        
        # Atualizar UI
        self.update_tab_ui()
        
        # Aplicar configurações salvas
        self._apply_saved_preferences()

    def _setup_web_profile(self):
        """Configura o perfil do WebEngine"""
        profile = QWebEngineProfile.defaultProfile()
        
        # Configurações de cookies e cache
        profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)
        
        # Diretórios para cache e armazenamento
        base_dir = os.path.join(os.path.expanduser("~"), ".firecat")
        cache_dir = os.path.join(base_dir, "cache")
        storage_dir = os.path.join(base_dir, "storage")
        
        profile.setCachePath(cache_dir)
        profile.setPersistentStoragePath(storage_dir)
        
        # Criar diretórios se não existirem
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(storage_dir, exist_ok=True)
        
        # Configurações globais do WebEngine
        settings = QWebEngineSettings.globalSettings()
        
        # Habilitar recursos necessários
        for attribute in [
            QWebEngineSettings.PluginsEnabled,
            QWebEngineSettings.JavascriptEnabled,
            QWebEngineSettings.FullScreenSupportEnabled,
            QWebEngineSettings.LocalStorageEnabled,
            QWebEngineSettings.WebGLEnabled,
            QWebEngineSettings.Accelerated2dCanvasEnabled,
            QWebEngineSettings.AutoLoadIconsForPage,
            QWebEngineSettings.JavascriptCanAccessClipboard
        ]:
            settings.setAttribute(attribute, True)

    def _apply_saved_preferences(self):
        """Aplica as preferências salvas"""
        if not hasattr(self, 'handler'):
            return
            
        settings = self.preferences.load_preferences()
        
        # Aplicar cor de fundo
        if 'backgroundColor' in settings:
            QTimer.singleShot(500, lambda: self.handler.changeBackground(settings['backgroundColor']))
        
        # Aplicar modo (claro/escuro)
        if 'mode' in settings:
            QTimer.singleShot(600, lambda: self.handler.setMode(settings['mode']))

    def tab_changed(self, index):
        """Manipula mudanças de aba"""
        # Atualizar controles de navegação
        self.browser_manager.update_navigation_controls()
        
        # Estilos para botões de fechar
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
        
        # Atualizar estilo dos botões de fechar de todas as abas
        for i in range(self.tab_widget.count()):
            close_button = self.tab_widget.tabBar().tabButton(i, QTabBar.RightSide)
            if isinstance(close_button, QToolButton) and i > 0:
                close_button.setVisible(True)
                current_style = active_style if i == index else inactive_style
                if close_button.property("current_style") != current_style:
                    close_button.setStyleSheet(current_style)
                    close_button.setProperty("current_style", current_style)
    
    def close_tab(self, index):
        """Fecha uma aba"""
        if index <= 0:  # Não fechar a aba inicial
            return
            
        self.browser_manager.close_tab(index)
        self.update_tab_ui()
    
    def closeEvent(self, event):
        """Manipula o fechamento da janela"""
        # Parar timers
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
        if hasattr(self, 'gc_timer') and self.gc_timer.isActive():
            self.gc_timer.stop()
        
        # Salvar preferências
        self._save_preferences_before_exit()
        
        # Limpar recursos das abas
        self._clean_tabs()
        
        # Forçar coleta de lixo
        gc.collect()
        
        # Aceitar o evento de fechamento
        event.accept()
    
    def _save_preferences_before_exit(self):
        """Salva as preferências antes de sair"""
        if hasattr(self, 'handler'):
            settings = self.preferences.load_preferences()
            settings['backgroundColor'] = self.handler.current_background_color
            settings['mode'] = self.handler.get_current_mode()
            self.preferences.save_settings(settings)
    
    def _clean_tabs(self):
        """Limpa recursos associados às abas"""
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab:
                tab.setUrl(QUrl("about:blank"))
                tab.page().deleteLater()

# Função de entrada
def run_firecat():
    app = QApplication(sys.argv)
    app.setApplicationName("Firecat Browser")
    app.setOrganizationName("Firecat")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

# Se este arquivo for executado diretamente
if __name__ == "__main__":
    run_firecat()