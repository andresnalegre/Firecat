import sys
import os
import base64
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
from Frontend.styles import get_styles, get_qt_styles
from Backend.utils import (
    get_youtube_svg, 
    get_instagram_svg, 
    get_reddit_svg, 
    get_linkedin_svg,
    get_twitter_svg,
    get_google_svg
)
from Backend.logics import BrowserManager, PreferencesManager
import json

class Handler(QObject):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_background_color = "#2e2e2e"

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
            self.apply_current_background()
        except Exception as e:
            print(f"Error saving settings: {e}")

    @pyqtSlot()
    def resetSettings(self):
        try:
            self.parent.preferences.reset_settings()
            self.current_background_color = "#2e2e2e"
            self.apply_current_background()
        except Exception as e:
            print(f"Error resetting settings: {e}")

    @pyqtSlot(result=str) #type: ignore
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
        self.apply_current_background()
        settings = self.parent.preferences.load_preferences()
        settings['backgroundColor'] = color
        self.parent.preferences.save_settings(settings)

    def apply_current_background(self):
        for i in range(self.parent.tab_widget.count()):
            web_view = self.parent.tab_widget.widget(i)
            if web_view:
                web_view.page().runJavaScript(
                    f"document.body.style.backgroundColor = '{self.current_background_color}';"
                )

    @pyqtSlot(str)
    def setMode(self, mode):
        color = '#FFFFFF' if mode == 'light' else '#2e2e2e'
        text_color = '#000000' if mode == 'light' else '#FFFFFF'
        
        self.changeBackground(color)
        
        for i in range(self.parent.tab_widget.count()):
            web_view = self.parent.tab_widget.widget(i)
            if web_view:
                js_code = f"""
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
                web_view.page().runJavaScript(js_code)
        
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
        self.setWindowTitle("Firecat")
        self.setGeometry(50, 50, 1366, 768)
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setElideMode(Qt.ElideRight)
        self.tab_widget.setMovable(True)
        self.tab_widget.currentChanged.connect(self.tabChanged)
        
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
        self.browser_manager = BrowserManager(self.tab_widget)
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
        self.current_tab.setHtml(self.get_html_content())
        
        self.update_new_tab_button_position()

    def tabChanged(self, index):
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

    def get_html_content(self):
        image_path = "../Firecat/Images/Firecat.png"
        with open(image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Firecat</title>
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <style>
            {get_styles()}
            </style>
            <script>
                let channel = null;
                let handler = null;

                function initializeQWebChannel() {{
                    return new Promise((resolve) => {{
                        new QWebChannel(qt.webChannelTransport, function(ch) {{
                            channel = ch;
                            handler = channel.objects.handler;
                            resolve();
                        }});
                    }});
                }}

                async function ensureHandler() {{
                    if (!handler) {{
                        await initializeQWebChannel();
                    }}
                    return handler;
                }}

                async function saveCurrentSettings() {{
                    const h = await ensureHandler();
                    const settings = {{
                        backgroundColor: document.body.style.backgroundColor || '#2e2e2e',
                        backgroundImage: document.body.style.backgroundImage,
                        mode: document.body.style.color === '#000000' ? 'light' : 'dark',
                        shortcuts: document.getElementById('shortcuts-toggle')?.checked ?? true
                    }};
                    
                    h.saveSettings(JSON.stringify(settings));
                }}

                function getCookie(name) {{
                    const value = '; ' + document.cookie;
                    const parts = value.split('; ' + name + '=');
                    if (parts.length === 2) return parts.pop().split(';').shift();
                    return null;
                }}

                function openCustomizePanel() {{
                    const panel = document.getElementById("customizePanel");
                    if (panel) {{
                        panel.style.right = '0';
                        setTimeout(function() {{
                            document.body.style.overflow = 'hidden';
                            panel.classList.add("open");
                        }}, 10);
                    }}
                }}

                function closeCustomizePanel() {{
                    const panel = document.getElementById("customizePanel");
                    if (panel) {{
                        panel.classList.remove("open");
                        document.body.style.overflow = '';
                        setTimeout(function() {{
                            panel.style.right = '-500px';
                        }}, 300);
                    }}
                }}

                async function selectTheme(element) {{
                    if (!element) return;
                    
                    const h = await ensureHandler();
                    
                    document.querySelectorAll('.theme-option').forEach(el => {{
                        el.classList.remove("selected");
                        el.style.border = "2px solid transparent";
                    }});
                    
                    element.classList.add("selected");
                    element.style.border = "2px solid white";
                    
                    const color = window.getComputedStyle(element).backgroundColor;
                    console.log('Applying color:', color);
                    
                    await h.changeBackground(color);
                    
                    document.body.style.backgroundColor = color;
                    document.documentElement.style.backgroundColor = color;
                    
                    document.body.style.color = '#FFFFFF';
                    
                    await saveCurrentSettings();
                }}

                async function setMode(mode) {{
                    const h = await ensureHandler();
                    
                    document.querySelectorAll('.customize-mode button').forEach(button => {{
                        button.classList.remove('active');
                    }});
                    document.getElementById(mode).classList.add('active');

                    const color = mode === 'light' ? '#FFFFFF' : '#2e2e2e';
                    const textColor = mode === 'light' ? '#000000' : '#FFFFFF';
                    
                    h.changeBackground(color);
                    document.body.style.color = textColor;
                    
                    if (mode === 'light') {{
                        document.querySelector('.search-bar').style.backgroundColor = '#FFFFFF';
                        document.querySelector('.search-bar').style.color = '#000000';
                    }} else {{
                        document.querySelector('.search-bar').style.backgroundColor = '#3b3b3b';
                        document.querySelector('.search-bar').style.color = '#FFFFFF';
                    }}

                    document.querySelectorAll('.shortcut').forEach(shortcut => {{
                        shortcut.style.backgroundColor = '#FFFFFF';
                        const svg = shortcut.querySelector('svg');
                        if (svg) {{
                            svg.style.fill = '#000000';
                        }}
                    }});

                    const settings = {{
                        backgroundColor: color,
                        backgroundImage: document.body.style.backgroundImage,
                        mode: mode,
                        shortcuts: document.getElementById('shortcuts-toggle')?.checked ?? true
                    }};
                    
                    await h.saveSettings(JSON.stringify(settings));
                }}

                function openBackgroundUpload() {{
                    document.getElementById('background-upload').click();
                }}

                async function uploadBackgroundImage() {{
                    const file = document.getElementById('background-upload').files[0];
                    if (file) {{
                        const reader = new FileReader();
                        reader.onload = async function(e) {{
                            document.body.style.backgroundImage = 'url(' + e.target.result + ')';
                            document.body.style.backgroundSize = 'cover';
                            document.body.style.backgroundPosition = 'center';
                            document.body.style.backgroundRepeat = 'no-repeat';
                            await saveCurrentSettings();
                        }}
                        reader.readAsDataURL(file);
                    }}
                }}

                function openColorPicker() {{
                    document.getElementById('color-picker').click();
                }}

                async function applyCustomColor(event) {{
                    const h = await ensureHandler();
                    const color = event.target.value;
                    await h.changeBackground(color);
                    await saveCurrentSettings();
                }}

                async function toggleShortcuts() {{
                    const shortcutsContainer = document.getElementById('shortcuts-container');
                    const toggleSwitch = document.getElementById('shortcuts-toggle');

                    if (shortcutsContainer && toggleSwitch) {{
                        shortcutsContainer.style.display = toggleSwitch.checked ? "flex" : "none";
                        await saveCurrentSettings();
                    }}
                }}

                async function resetDefaults() {{
                    const h = await ensureHandler();
                    
                    await h.resetSettings();
                    
                    document.body.style.backgroundImage = 'none';
                    
                    const shortcutsToggle = document.getElementById('shortcuts-toggle');
                    if (shortcutsToggle) {{
                        shortcutsToggle.checked = true;
                        await toggleShortcuts();
                    }}
                    
                    document.querySelectorAll('.theme-option').forEach(el => {{
                        el.classList.remove("selected");
                    }});
                    
                    const fileInput = document.getElementById('background-upload');
                    if (fileInput) {{
                        fileInput.value = '';
                    }}
                    
                    const colorPicker = document.getElementById('color-picker');
                    if (colorPicker) {{
                        colorPicker.value = '#2e2e2e';
                    }}
                    
                    await setMode('dark');
                }}

                async function handleSearch(event) {{
                    if (event.key === 'Enter') {{
                        const h = await ensureHandler();
                        const query = document.getElementById('search-input')?.value || '';
                        await h.search(query);
                    }}
                }}

                window.addEventListener('load', async function() {{
                    try {{
                        const h = await ensureHandler();
                        
                        const settings = await h.getSettings();
                        const savedSettings = JSON.parse(settings);
                        
                        if (savedSettings.backgroundColor) {{
                            await h.changeBackground(savedSettings.backgroundColor);
                        }}
                        
                        if (savedSettings.backgroundImage) {{
                            document.body.style.backgroundImage = savedSettings.backgroundImage;
                            document.body.style.backgroundSize = 'cover';
                            document.body.style.backgroundPosition = 'center';
                            document.body.style.backgroundRepeat = 'no-repeat';
                        }}
                        
                        if (savedSettings.mode) {{
                            await setMode(savedSettings.mode);
                        }}
                        
                        const shortcutsToggle = document.getElementById('shortcuts-toggle');
                        if (shortcutsToggle && savedSettings.shortcuts !== undefined) {{
                            shortcutsToggle.checked = savedSettings.shortcuts;
                            await toggleShortcuts();
                        }}

                        const shortcuts = {{
                            "youtube-shortcut": 'https://www.youtube.com',
                            "instagram-shortcut": 'https://www.instagram.com',
                            "reddit-shortcut": 'https://www.reddit.com',
                            "linkedin-shortcut": 'https://www.linkedin.com',
                            "twitter-shortcut": 'https://www.twitter.com',
                            "google-shortcut": 'https://www.google.com'
                        }};

                        Object.entries(shortcuts).forEach(([id, url]) => {{
                            const element = document.getElementById(id);
                            if (element) {{
                                element.onclick = async () => {{
                                    const h = await ensureHandler();
                                    h.openLink(url);
                                }};
                            }}
                        }});
                    }} catch (e) {{
                        console.error('Error in initialization:', e);
                    }}
                }});
            </script>
        </head>
        <body>
            <div class="search-container">
                <img src="data:image/png;base64,{image_base64}" alt="Firecat Image" class="image">
                <div class="search-icon"></div>
                <input type="text" id="search-input" class="search-bar" placeholder="What do you want to search today?" onkeypress="handleSearch(event)">
                
                <div id="shortcuts-container" class="shortcuts-container">
                    <div class="shortcut" id="youtube-shortcut">{str(get_youtube_svg())}</div>
                    <div class="shortcut" id="instagram-shortcut">{str(get_instagram_svg())}</div>
                    <div class="shortcut" id="reddit-shortcut">{str(get_reddit_svg())}</div>
                    <div class="shortcut" id="linkedin-shortcut">{str(get_linkedin_svg())}</div>
                    <div class="shortcut" id="twitter-shortcut">{str(get_twitter_svg())}</div>
                    <div class="shortcut" id="google-shortcut">{str(get_google_svg())}</div>
                </div>
            </div>

            <button class="customize-button" onclick="openCustomizePanel()">Customize Firecat</button>

            <input type="file" id="background-upload" accept="image/png, image/jpeg" style="display:none;" onchange="uploadBackgroundImage()">
            <input type="color" id="color-picker" style="display:none;" onchange="applyCustomColor(event)">

            <div id="customizePanel" class="customize-panel">
                <div class="customize-header">
                    <h2>Settings</h2>
                    <span class="close" onclick="closeCustomizePanel()">&times;</span>
                </div>

                <div class="settings-container">
                    <div class="customize-mode">
                        <button id="light" onclick="setMode('light')">Light</button>
                        <button id="dark" class="active" onclick="setMode('dark')">Dark</button>
                    </div>
                    <div class="theme-container">
                        <div class="theme-option" style="background-color: #4285F4;" onclick="selectTheme(this)"></div>
                        <div class="theme-option" style="background-color: #34A853;" onclick="selectTheme(this)"></div>
                        <div class="theme-option" style="background-color: #FBBC05;" onclick="selectTheme(this)"></div>
                        <div class="theme-option" style="background-color: #EA4335;" onclick="selectTheme(this)"></div>
                        <div class="theme-option" style="background-color: #00ffff;" onclick="selectTheme(this)"></div>
                        <div class="theme-option" style="background-color: #6a1b9a;" onclick="selectTheme(this)"></div>
                        <div class="theme-option" style="background-color: #8e24aa;" onclick="selectTheme(this)"></div>
                        <div class="theme-option" style="background-color: #ff7043;" onclick="selectTheme(this)"></div>
                        <div class="custom-color" onclick="openColorPicker()">
                            <svg height="50px" width="50px" viewBox="0 0 489.6 489.6">
                                <g>
                                    <path style="fill:#F4AD31;" d="M244.8,207.2c25.6-20.8,58.4-32.8,94.4-32.8c19.2,0,37.6,4,55.2,10.4c0.8-6.4,1.6-13.6,1.6-20
                                        c0-83.2-67.2-150.4-150.4-150.4S95.2,81.6,95.2,164.8c0,7.2,0.8,13.6,1.6,20c16.8-6.4,35.2-10.4,55.2-10.4
                                        C186.4,174.4,219.2,187.2,244.8,207.2z"></path>
                                    <path style="fill:#E2821A;" d="M150.4,174.4c36,0,68,12.8,94.4,32.8c25.6-20.8,58.4-32.8,94.4-32.8c19.2,0,37.6,4,55.2,10.4
                                        c0.8-6.4,1.6-13.6,1.6-20c0-83.2-67.2-150.4-150.4-150.4"></path>
                                    <path style="fill:#D32A0F;" d="M188,324.8c0-7.2,0.8-13.6,1.6-20c-49.6-19.2-86.4-64.8-94.4-120C40,207.2,0,260.8,0,324.8
                                        C0,408,67.2,475.2,150.4,475.2c36,0,68-12.8,94.4-32.8C210.4,414.4,188,372,188,324.8z"></path>
                                    <path style="fill:#B71100;" d="M150.4,475.2c36,0,68-12.8,94.4-32.8c-34.4-27.2-56.8-69.6-56.8-117.6c0-7.2,0.8-13.6,1.6-20"></path>
                                    <path style="fill:#0878A0;" d="M393.6,184.8c-7.2,55.2-44,100-94.4,120c0.8,6.4,1.6,13.6,1.6,20c0,47.2-22.4,89.6-56.8,117.6
                                        c25.6,20.8,58.4,32.8,94.4,32.8c83.2,0,150.4-67.2,150.4-150.4C489.6,260.8,449.6,207.2,393.6,184.8z"></path>
                                    <path style="fill:#0C6C8E;" d="M244.8,442.4c25.6,20.8,58.4,32.8,94.4,32.8c83.2,0,150.4-67.2,150.4-150.4"></path>
                                    <path style="fill:#3D3736;" d="M244.8,207.2c-29.6,23.2-49.6,57.6-55.2,96.8c16.8,6.4,35.2,10.4,55.2,10.4c19.2,0,37.6-4,55.2-10.4
                                        C294.4,265.6,274.4,231.2,244.8,207.2z"></path>
                                    <path d="M244.8,315.2c19.2,0,37.6-4,55.2-10.4c-5.6-39.2-25.6-73.6-55.2-96.8"></path>
                                    <path style="fill:#0CAA7D;" d="M300,304.8c49.6-19.2,86.4-64.8,94.4-120c-16.8-6.4-35.2-10.4-55.2-10.4c-35.2,0-68,12.8-94.4,32.8
                                        C274.4,231.2,294.4,265.6,300,304.8z"></path>
                                    <path style="fill:#720D20;" d="M244.8,207.2c-25.6-20.8-58.4-32.8-94.4-32.8c-19.2,0-37.6,4-55.2,10.4c7.2,55.2,44,100,94.4,120
                                        C195.2,265.6,215.2,231.2,244.8,207.2z"></path>
                                    <path style="fill:#783089;" d="M301.6,324.8c0-7.2-0.8-13.6-1.6-20c-16.8,6.4-35.2,10.4-55.2,10.4c-19.2,0-37.6-4-55.2-10.4
                                        c-0.8,6.4-1.6,13.6-1.6,20c0,47.2,22.4,89.6,56.8,117.6C279.2,414.4,301.6,372,301.6,324.8z"></path>
                                </g>
                            </svg>
                        </div>
                    </div>
                    <div class="divider"></div>
                    <button class="customize-theme-button" onclick="openBackgroundUpload()">Customize Theme</button>
                </div>

                <div class="shortcuts-toggle-container">
                    <h3>Shortcuts</h3>
                    <label class="switch">
                        <input type="checkbox" id="shortcuts-toggle" checked onchange="toggleShortcuts()">
                        <span class="slider"></span>
                    </label>
                </div>

                <button class="reset-button" onclick="resetDefaults()">Reset as Default</button>
            </div>
        </body>
        </html>
        """
        return html_content

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