import base64
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

def get_html_content(image_path="../Firecat/Images/Firecat.png"):
    try:
        with open(image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        image_base64 = ""
        print(f"Warning: Image file not found at {image_path}")

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
                    backgroundColor: document.body.style.backgroundColor || '#FFFFFF',
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
                    shortcut.style.backgroundColor = mode === 'light' ? '#f0f0f0' : '#2e2e2e';
                    const svg = shortcut.querySelector('svg');
                    if (svg) {{
                        svg.style.fill = mode === 'light' ? '#000000' : '#FFFFFF';
                    }}
                }});

                document.body.classList.remove('light-mode', 'dark-mode');
                document.body.classList.add(mode + '-mode');

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
                try {{
                    const h = await ensureHandler();
                    await h.resetSettings();
                    
                    document.body.style.backgroundImage = 'none';
                    document.body.style.backgroundColor = '#FFFFFF';
                    document.body.style.color = '#000000';
                    
                    const shortcutsToggle = document.getElementById('shortcuts-toggle');
                    if (shortcutsToggle) {{
                        shortcutsToggle.checked = true;
                        toggleShortcuts();
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
                        colorPicker.value = '#FFFFFF';
                    }}
                    
                    document.body.classList.remove('dark-mode');
                    document.body.classList.add('light-mode');
                    
                    const searchBar = document.querySelector('.search-bar');
                    if (searchBar) {{
                        searchBar.style.backgroundColor = '#FFFFFF';
                        searchBar.style.color = '#000000';
                    }}
                    
                    document.querySelectorAll('.shortcut').forEach(shortcut => {{
                        shortcut.style.backgroundColor = '#f0f0f0';
                    }});
                    
                    document.querySelectorAll('.customize-mode button').forEach(button => {{
                        button.classList.remove('active');
                    }});
                    document.getElementById('light').classList.add('active');
                    
                    console.log("Reset to defaults (light mode) completed successfully");
                }} catch (error) {{
                    console.error("Error resetting to defaults:", error);
                }}
            }}

            async function handleSearch(event) {{
                if (event.key === 'Enter') {{
                    const h = await ensureHandler();
                    const query = document.getElementById('search-input')?.value || '';
                    await h.search(query);
                }}
            }}

            async function applyLightMode() {{
                document.body.style.backgroundColor = '#FFFFFF';
                document.body.style.color = '#000000';
                document.body.classList.remove('dark-mode');
                document.body.classList.add('light-mode');
                
                const searchBar = document.querySelector('.search-bar');
                if (searchBar) {{
                    searchBar.style.backgroundColor = '#FFFFFF';
                    searchBar.style.color = '#000000';
                }}
                
                document.querySelectorAll('.shortcut').forEach(shortcut => {{
                    shortcut.style.backgroundColor = '#f0f0f0';
                    const svg = shortcut.querySelector('svg');
                    if (svg) {{
                        svg.style.fill = '#000000';
                    }}
                }});
                
                document.querySelectorAll('.customize-mode button').forEach(button => {{
                    button.classList.remove('active');
                }});
                document.getElementById('light').classList.add('active');
            }}

            window.addEventListener('load', async function() {{
                try {{
                    await applyLightMode();
                    
                    const h = await ensureHandler();
                    let settings = await h.getSettings();
                    let savedSettings = JSON.parse(settings);
                    
                    if (savedSettings.mode === 'dark') {{
                        savedSettings.mode = 'light';
                        savedSettings.backgroundColor = '#FFFFFF';
                        await h.saveSettings(JSON.stringify(savedSettings));
                    }}
                    
                    if (savedSettings.backgroundColor && savedSettings.backgroundColor !== '#2e2e2e') {{
                        await h.changeBackground(savedSettings.backgroundColor);
                    }} else {{
                        await h.changeBackground('#FFFFFF');
                    }}
                    
                    if (savedSettings.backgroundImage) {{
                        document.body.style.backgroundImage = savedSettings.backgroundImage;
                        document.body.style.backgroundSize = 'cover';
                        document.body.style.backgroundPosition = 'center';
                        document.body.style.backgroundRepeat = 'no-repeat';
                    }}
                    
                    await setMode('light');
                    
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
                    applyLightMode();
                }}
            }});
            
            document.addEventListener('DOMContentLoaded', function() {{
                document.body.style.backgroundColor = '#FFFFFF';
                document.body.style.color = '#000000';
                document.body.classList.add('light-mode');
            }});
        </script>
    </head>
    <body class="light-mode" style="background-color: #FFFFFF; color: #000000;">
        <div class="search-container">
            <img src="data:image/png;base64,{image_base64}" alt="Firecat Image" class="image">
            <div class="search-icon"></div>
            <input type="text" id="search-input" class="search-bar" placeholder="What do you want to search today?" onkeypress="handleSearch(event)" style="background-color: #FFFFFF; color: #000000;">
            
            <div id="shortcuts-container" class="shortcuts-container">
                <div class="shortcut" id="youtube-shortcut" style="background-color: #f0f0f0;">{str(get_youtube_svg())}</div>
                <div class="shortcut" id="instagram-shortcut" style="background-color: #f0f0f0;">{str(get_instagram_svg())}</div>
                <div class="shortcut" id="reddit-shortcut" style="background-color: #f0f0f0;">{str(get_reddit_svg())}</div>
                <div class="shortcut" id="linkedin-shortcut" style="background-color: #f0f0f0;">{str(get_linkedin_svg())}</div>
                <div class="shortcut" id="twitter-shortcut" style="background-color: #f0f0f0;">{str(get_twitter_svg())}</div>
                <div class="shortcut" id="google-shortcut" style="background-color: #f0f0f0;">{str(get_google_svg())}</div>
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
    </body>
    </html>
    """
    return html_content