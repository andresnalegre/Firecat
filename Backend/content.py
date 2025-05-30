import base64
import os
from Backend.utils import (
    get_youtube_svg,
    get_instagram_svg,
    get_reddit_svg,
    get_linkedin_svg,
    get_twitter_svg,
    get_google_svg,
    get_color_wheel_svg
)
from Frontend.styles import get_styles

# Constantes para cores e imagens
DEFAULT_IMAGE_PATH = "../Firecat/Images/Firecat.png"
LIGHT_BG_COLOR = "#FFFFFF"
DARK_BG_COLOR = "#2e2e2e"
LIGHT_TEXT_COLOR = "#000000"
DARK_TEXT_COLOR = "#FFFFFF"

def get_html_content(image_path=DEFAULT_IMAGE_PATH):
    """Gera o conteúdo HTML para a página inicial do navegador.
    
    Args:
        image_path: Caminho para o arquivo de imagem do logotipo
        
    Returns:
        String contendo o HTML completo da página inicial
    """
    # Carregar e codificar a imagem
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        else:
            image_base64 = ""
            print(f"Warning: Image file not found at {image_path}")
    except Exception as e:
        image_base64 = ""
        print(f"Error loading image {image_path}: {e}")

    # JavaScript com funções refatoradas mas mantendo a mesma funcionalidade
    javascript = """
        // Retorna preto ou branco para melhor contraste dado um fundo (funciona para rgb ou hex)
        function getContrastYIQ(color) {
            let r,g,b;
            if (color.startsWith('rgb')) {
                let vals = color.match(/\\d+/g);
                [r,g,b] = vals.map(Number);
            } else {
                color = color.replace('#','');
                if (color.length === 3) {
                  r = parseInt(color[0]+color[0],16);
                  g = parseInt(color[1]+color[1],16);
                  b = parseInt(color[2]+color[2],16);
                } else {
                  r = parseInt(color.substr(0,2),16);
                  g = parseInt(color.substr(2,2),16);
                  b = parseInt(color.substr(4,2),16);
                }
            }
            let yiq = ((r*299)+(g*587)+(b*114))/1000;
            return (yiq >= 128) ? '#000000' : '#FFFFFF';
        }

        let channel = null;
        let handler = null;

        function initializeQWebChannel() {
            return new Promise((resolve) => {
                new QWebChannel(qt.webChannelTransport, function(ch) {
                    channel = ch;
                    handler = channel.objects.handler;
                    resolve();
                });
            });
        }

        async function ensureHandler() {
            if (!handler) {
                await initializeQWebChannel();
            }
            return handler;
        }

        async function saveCurrentSettings(mode=null, colorOverride=null) {
            const h = await ensureHandler();
            // Permite sobrescrever e salvar um modo/caracter cor custom explicitamente
            let modeValue = mode !== null ? mode : (
                document.body.classList.contains('dark-mode') ? 'dark' :
                (document.body.classList.contains('light-mode') ? 'light' :
                (document.body.classList.contains('custom-mode') ? 'custom' : 'light'))
            );
            const settings = {
                backgroundColor: colorOverride || document.body.style.backgroundColor || '#FFFFFF',
                backgroundImage: document.body.style.backgroundImage,
                mode: modeValue,
                shortcuts: document.getElementById('shortcuts-toggle')?.checked ?? true
            };
            h.saveSettings(JSON.stringify(settings));
        }

        async function selectTheme(element) {
            if (!element) return;
            const h = await ensureHandler();
            document.querySelectorAll('.theme-option').forEach(el => {
                el.classList.remove("selected");
                el.style.border = "2px solid transparent";
            });
            element.classList.add("selected");
            element.style.border = "2px solid white";
            const color = window.getComputedStyle(element).backgroundColor;

            // Detecta light (branco), dark (cinza escuro), ou custom
            let mode, textColor;
            if (color === 'rgb(255, 255, 255)' || color === '#FFFFFF') {
                mode = 'light';
                textColor = '#000000';
            } else if (color === 'rgb(46, 46, 46)' || color === '#2e2e2e') {
                mode = 'dark';
                textColor = '#FFFFFF';
            } else {
                mode = 'custom';
                textColor = getContrastYIQ(color);
            }

            document.body.classList.remove('light-mode', 'dark-mode', 'custom-mode');
            document.body.classList.add(mode + '-mode');

            await h.changeBackground(color);

            document.body.style.backgroundColor = color;
            document.body.style.color = textColor;

            let searchBar = document.querySelector('.search-bar');
            if (searchBar) {
                searchBar.style.backgroundColor = (mode === 'dark') ? '#3b3b3b' : '#FFFFFF';
                searchBar.style.color = textColor;
            }

            document.querySelectorAll('.shortcut').forEach(shortcut => {
                shortcut.style.backgroundColor = (mode === 'dark') ? '#2e2e2e' : '#f0f0f0';
                let svg = shortcut.querySelector('svg');
                if (svg)
                    svg.style.fill = textColor;
            });

            await saveCurrentSettings(mode, color);
        }

        async function setMode(mode) {
            const h = await ensureHandler();
            
            // Desselecionar todos os botões primeiro
            document.querySelectorAll('.customize-mode button').forEach(button => {
                button.classList.remove('active');
            });
            
            // Se for um modo personalizado, não alteramos as cores
            if (mode === 'custom') {
                // Se tiver seleção personalizada, mantém essa seleção
                document.body.classList.remove('light-mode', 'dark-mode');
                document.body.classList.add('custom-mode');
                
                // Manter a cor atual, apenas salvar o modo
                await saveCurrentSettings('custom');
                return;
            }
            
            // Somente para light e dark selecionamos o botão correspondente
            if (document.getElementById(mode)) {
                document.getElementById(mode).classList.add('active');
            }
            
            // Define as cores para modos light e dark
            const color = mode === 'light' ? '#FFFFFF' : '#2e2e2e';
            const textColor = mode === 'light' ? '#000000' : '#FFFFFF';
            
            // Atualiza as configurações no servidor
            await h.changeBackground(color);
            
            // Atualiza a aparência
            document.body.style.backgroundColor = color;
            document.body.style.color = textColor;
            
            // Atualiza a barra de pesquisa
            let searchBar = document.querySelector('.search-bar');
            if (searchBar) {
                searchBar.style.backgroundColor = (mode === 'light') ? '#FFFFFF' : '#3b3b3b';
                searchBar.style.color = textColor;
            }
            
            // Atualiza os atalhos
            document.querySelectorAll('.shortcut').forEach(shortcut => {
                shortcut.style.backgroundColor = (mode === 'light') ? '#f0f0f0' : '#2e2e2e';
                const svg = shortcut.querySelector('svg');
                if (svg) {
                    svg.style.fill = textColor;
                }
            });
            
            // Atualiza as classes do corpo
            document.body.classList.remove('light-mode', 'dark-mode', 'custom-mode');
            document.body.classList.add(mode + '-mode');
            
            // Salva as configurações
            await saveCurrentSettings(mode, color);
        }

        function openCustomizePanel() {
            const panel = document.getElementById("customizePanel");
            if (panel) {
                panel.style.right = '0';
                setTimeout(function() {
                    document.body.style.overflow = 'hidden';
                    panel.classList.add("open");
                }, 10);
            }
        }

        function closeCustomizePanel() {
            const panel = document.getElementById("customizePanel");
            if (panel) {
                panel.classList.remove("open");
                document.body.style.overflow = '';
                setTimeout(function() {
                    panel.style.right = '-500px';
                }, 300);
            }
        }

        function openBackgroundUpload() {
            document.getElementById('background-upload').click();
        }

        async function uploadBackgroundImage() {
            const file = document.getElementById('background-upload').files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = async function(e) {
                    document.body.style.backgroundImage = 'url(' + e.target.result + ')';
                    document.body.style.backgroundSize = 'cover';
                    document.body.style.backgroundPosition = 'center';
                    document.body.style.backgroundRepeat = 'no-repeat';
                    await saveCurrentSettings();
                }
                reader.readAsDataURL(file);
            }
        }

        function openColorPicker() {
            document.getElementById('color-picker').click();
        }

        async function applyCustomColor(event) {
            const h = await ensureHandler();
            const color = event.target.value;
            document.body.classList.remove('light-mode','dark-mode');
            document.body.classList.add('custom-mode');
            document.body.style.backgroundColor = color;
            let textColor = getContrastYIQ(color);
            document.body.style.color = textColor;

            await h.changeBackground(color);
            await saveCurrentSettings('custom', color);
        }

        async function toggleShortcuts() {
            const shortcutsContainer = document.getElementById('shortcuts-container');
            const toggleSwitch = document.getElementById('shortcuts-toggle');
            if (shortcutsContainer && toggleSwitch) {
                shortcutsContainer.style.display = toggleSwitch.checked ? "flex" : "none";
                await saveCurrentSettings();
            }
        }

        async function resetDefaults() {
            try {
                const h = await ensureHandler();
                await h.resetSettings();
                document.body.style.backgroundImage = 'none';
                document.body.style.backgroundColor = '#FFFFFF';
                document.body.style.color = '#000000';

                const shortcutsToggle = document.getElementById('shortcuts-toggle');
                if (shortcutsToggle) {
                    shortcutsToggle.checked = true;
                    toggleShortcuts();
                }

                document.querySelectorAll('.theme-option').forEach(el => {
                    el.classList.remove("selected");
                });
                const fileInput = document.getElementById('background-upload');
                if (fileInput) fileInput.value = '';
                const colorPicker = document.getElementById('color-picker');
                if (colorPicker) colorPicker.value = '#FFFFFF';
                document.body.classList.remove('dark-mode','custom-mode');
                document.body.classList.add('light-mode');
                let searchBar = document.querySelector('.search-bar');
                if (searchBar) {
                    searchBar.style.backgroundColor = '#FFFFFF';
                    searchBar.style.color = '#000000';
                }
                document.querySelectorAll('.shortcut').forEach(shortcut => {
                    shortcut.style.backgroundColor = '#f0f0f0';
                });
                document.querySelectorAll('.customize-mode button').forEach(button => {
                    button.classList.remove('active');
                });
                if(document.getElementById('light')) {
                    document.getElementById('light').classList.add('active');
                }
            } catch (error) {
                console.error("Error resetting to defaults:", error);
            }
        }

        async function handleSearch(event) {
            if (event.key === 'Enter') {
                const h = await ensureHandler();
                const query = document.getElementById('search-input')?.value || '';
                await h.search(query);
            }
        }

        window.addEventListener('load', async function() {
            try {
                const h = await ensureHandler();
                let settings_json = await h.getSettings();
                let saved = {};
                try { saved = JSON.parse(settings_json); } catch (e) {}
                
                // FIX: Usar o modo salvo diretamente, em vez de determiná-lo apenas pela cor
                let mode = saved.mode || 'light';
                let bgColor = saved.backgroundColor ? saved.backgroundColor.toLowerCase() : "#ffffff";
                let textColor;
                
                // Verificações de consistência
                if (mode === 'light' && bgColor !== "#ffffff") {
                    if (bgColor === "#2e2e2e") {
                        mode = 'dark';
                    } else {
                        mode = 'custom';
                    }
                } else if (mode === 'dark' && bgColor !== "#2e2e2e") {
                    if (bgColor === "#ffffff") {
                        mode = 'light';
                    } else {
                        mode = 'custom';
                    }
                }
                
                // Atualizar classes do corpo
                document.body.classList.remove('light-mode','dark-mode','custom-mode');
                document.body.classList.add(mode + '-mode');
                
                // Determinar cor do texto baseado no modo
                if (mode === 'light') {
                    textColor = '#000000';
                } else if (mode === 'dark') {
                    textColor = '#ffffff';
                } else { // custom
                    textColor = getContrastYIQ(bgColor);
                }
                
                // Aplicar cores
                document.body.style.backgroundColor = bgColor;
                document.body.style.color = textColor;

                // Atualizar barra de pesquisa
                let searchBar = document.querySelector('.search-bar');
                if (searchBar) {
                    // Para modo personalizado, usar cor mais adequada para a barra de pesquisa
                    let searchBarBg;
                    if (mode === 'custom') {
                        // Mais claro para texto escuro, mais escuro para texto claro
                        searchBarBg = textColor === '#000000' ? '#ffffff' : '#3b3b3b';
                    } else {
                        searchBarBg = (mode === 'dark') ? '#3b3b3b' : '#ffffff';
                    }
                    searchBar.style.backgroundColor = searchBarBg;
                    searchBar.style.color = textColor;
                }

                // Atualizar atalhos
                document.querySelectorAll('.shortcut').forEach(shortcut => {
                    let shortcutBg;
                    if (mode === 'custom') {
                        // Escolher cor de fundo adequada para atalhos em modo personalizado
                        shortcutBg = textColor === '#000000' ? '#f0f0f0' : '#2e2e2e';
                    } else {
                        shortcutBg = (mode === 'dark') ? '#2e2e2e' : '#f0f0f0';
                    }
                    shortcut.style.backgroundColor = shortcutBg;
                    let svg = shortcut.querySelector('svg');
                    if (svg)
                        svg.style.fill = textColor;
                });

                // Atualizar botões de modo
                document.querySelectorAll('.customize-mode button').forEach(button => {
                    button.classList.remove('active');
                });
                
                // Ativar o botão apenas se for light ou dark (não para custom)
                if (mode === 'light' && document.getElementById('light')) {
                    document.getElementById('light').classList.add('active');
                } else if (mode === 'dark' && document.getElementById('dark')) {
                    document.getElementById('dark').classList.add('active');
                }

                // Configurar atalhos
                const shortcutsToggle = document.getElementById('shortcuts-toggle');
                if (shortcutsToggle && saved.shortcuts !== undefined) {
                    shortcutsToggle.checked = saved.shortcuts;
                    await toggleShortcuts();
                }

                // Aplicar imagem de fundo se existir
                if (saved.backgroundImage) {
                    document.body.style.backgroundImage = saved.backgroundImage;
                    document.body.style.backgroundSize = "cover";
                    document.body.style.backgroundPosition = "center";
                    document.body.style.backgroundRepeat = "no-repeat";
                }

                // Configurar atalhos
                const shortcuts = {
                    "youtube-shortcut": 'https://www.youtube.com',
                    "instagram-shortcut": 'https://www.instagram.com',
                    "reddit-shortcut": 'https://www.reddit.com',
                    "linkedin-shortcut": 'https://www.linkedin.com',
                    "twitter-shortcut": 'https://www.twitter.com',
                    "google-shortcut": 'https://www.google.com'
                };
                Object.entries(shortcuts).forEach(([id, url]) => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.onclick = async () => {
                            const h = await ensureHandler();
                            h.openLink(url);
                        };
                    }
                });
            } catch (e) {
                console.error('Error in initialization:', e);
            }
        });
    """

    # Corpo HTML
    html_body = f"""
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
                    <button id="light" class="active" onclick="setMode('light')">Light</button>
                    <button id="dark" onclick="setMode('dark')">Dark</button>
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
                        {str(get_color_wheel_svg())}
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
    """

    # Montar HTML completo
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Firecat</title>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <style>
        {get_styles()}
        </style>
        <script>
        {javascript}
        </script>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    
    return html_content