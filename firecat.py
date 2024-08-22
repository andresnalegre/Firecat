import sys
import base64
import webbrowser
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl, QObject, pyqtSlot

class Handler(QObject):
    @pyqtSlot(str)
    def openLink(self, url):
        # Opens the provided URL in the system's default web browser
        webbrowser.open(url)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set the main window title and size
        self.setWindowTitle("Firecat")
        self.setGeometry(100, 100, 1200, 800)

        # Create and set up the central widget and its layout
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        # Initialize the web engine view and add it to the layout
        self.browser = QWebEngineView()
        self.layout.addWidget(self.browser)

        # Set up a communication channel between Python and the HTML/JavaScript frontend
        self.channel = QWebChannel()
        self.handler = Handler()
        self.channel.registerObject('handler', self.handler)
        self.browser.page().setWebChannel(self.channel)

        # Load the HTML content into the web view
        self.browser.setHtml(self.get_html_content())

    def get_html_content(self):
        # Path to the image file that will be embedded in the HTML
        image_path = "/Users/andresnicolasalegre/Desktop/Firecat/Firecat.png"
        # Encode the image as a Base64 string to embed directly in HTML
        with open(image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

        # HTML content with embedded CSS, JavaScript, and the image
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
                body {{
                    background-color: #2e2e2e;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    font-family: 'Roboto', sans-serif;
                    overflow: hidden;
                }}
                .search-container {{
                    text-align: center;
                    position: relative;
                    margin-top: -100px;
                }}
                .search-bar {{
                    width: 600px;
                    height: 50px;
                    padding: 10px 20px 10px 50px;
                    font-size: 24px;
                    border: 2px solid #ddd;
                    border-radius: 30px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    transition: all 0.3s ease;
                }}
                .search-bar:focus {{
                    border-color: #4285F4;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
                    outline: none;
                }}
                .search-bar::placeholder {{
                    font-size: 24px;
                    color: #999;
                    opacity: 1;
                }}
                .search-icon {{
                    position: absolute;
                    left: 20px;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 24px;
                    height: 24px;
                    -webkit-mask-image: url(//resources/cr_components/searchbox/icons/search_cr23.svg);
                    background-color: #999;
                }}
                .image {{
                    display: block;
                    width: 300px;
                    height: 300px;
                    object-fit: cover;
                    margin: 0 auto 20px;
                }}
                .customize-button {{
                    position: absolute;
                    bottom: 20px;
                    right: 20px;
                    width: 170px;
                    height: 30px;
                    background-color: #4285F4;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                }}
                .customize-button:hover {{
                    background-color: #357ae8;
                }}
                .customize-panel {{
                    position: fixed;
                    top: 0;
                    right: -500px;
                    width: 450px;
                    height: 100%;
                    background-color: #333;
                    color: white;
                    box-shadow: -2px 0 5px rgba(0,0,0,0.5);
                    padding: 20px;
                    transition: right 0.3s ease;
                    z-index: 1000;
                    overflow-y: auto;
                    scrollbar-width: thin;
                    scrollbar-color: #4285F4 transparent;
                }}
                .customize-panel.open {{
                    right: 0;
                }}
                .customize-header {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin-bottom: 20px;
                    position: relative;
                }}
                .customize-header h2 {{
                    font-size: 28px;
                    font-weight: 300;
                    letter-spacing: 1px;
                    margin: 0;
                    text-align: center;
                    width: 100%;
                    color: #f1f1f1;
                }}
                .close {{
                    color: #aaa;
                    font-size: 28px;
                    font-weight: bold;
                    position: absolute;
                    right: 0;
                    cursor: pointer;
                }}
                .close:hover,
                .close:focus {{
                    color: white;
                    text-decoration: none;
                }}
                .settings-container {{
                    padding: 20px;
                    border-radius: 20px;
                    background-color: #3b3b3b;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    margin-bottom: 20px;
                }}
                .customize-mode {{
                    display: flex;
                    justify-content: center;
                    margin-bottom: 20px;
                    padding: 10px;
                    border: 1px solid #4285F4;
                    border-radius: 30px;
                }}
                .customize-mode button {{
                    flex: 1;
                    padding: 10px;
                    margin: 0 5px;
                    background-color: #444;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                    box-shadow: none;
                    outline: none;
                }}

                .customize-mode button:focus {{
                    outline: none; 
                    box-shadow: 0 0 0 3px #4285F4, 0 0 0 5px #000; 
                    border-radius: 20px; 
                }}

                .customize-mode button.active {{
                    background-color: #adc8ff;
                    color: #000;
                    border-radius: 20px;
                    outline: none;
                    box-shadow: none;
                }}
                .theme-container {{
                    display: flex;
                    justify-content: center;
                    margin-bottom: 20px;
                    padding: 10px;
                    border: 1px solid #4285F4;
                    border-radius: 30px;
                    flex-wrap: wrap;
                    width: 100%;
                }}
                .theme-option {{
                    display: inline-block;
                    width: 80px;
                    height: 80px;
                    background-color: #555;
                    border-radius: 50%;
                    margin: 10px;
                    cursor: pointer;
                    border: 3px solid white;
                    transition: transform 0.3s ease;
                }}
                .theme-option.selected {{
                    border-color: #4285F4;
                }}
                .custom-color {{
                    display: inline-block;
                    width: 80px;
                    height: 80px;
                    background-color: #444;
                    border-radius: 50%;
                    margin: 10px;
                    cursor: pointer;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-size: 24px;
                    color: #fff;
                }}
                .shortcuts-container {{
                    display: flex;
                    justify-content: center;
                    flex-wrap: wrap;
                    margin-top: 20px;
                }}
                .shortcut {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    width: 80px;
                    height: 80px;
                    background-color: white;
                    border-radius: 50%;
                    margin: 10px;
                    cursor: pointer;
                    transition: transform 0.3s ease;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .shortcut svg {{
                    width: 50%;
                    height: 50%;
                    fill: black;
                }}
                .shortcut:hover {{
                    transform: scale(1.1);
                }}
                .divider {{
                    width: 100%;
                    height: 1px;
                    background-color: #555;
                    margin: 20px 0;
                }}
                .customize-theme-button {{
                    width: 100%;
                    padding: 10px;
                    background-color: #4285F4;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    text-align: center;
                    transition: background-color 0.3s ease;
                }}
                .customize-theme-button:hover {{
                    background-color: #357ae8;
                }}
                .shortcuts-toggle-container {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                    padding: 10px;
                    border-radius: 30px;
                    background-color: #3b3b3b;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                }}
                .shortcuts-toggle-container h3 {{
                    margin: 0;
                    margin-left: 20px;
                    font-size: 18px;
                    color: #f1f1f1;
                }}
                .switch {{
                    position: relative;
                    display: inline-block;
                    width: 34px;
                    height: 20px;
                    margin-right: 20px;
                    margin-top: 10px;
                }}
                .switch input {{
                    opacity: 0;
                    width: 0;
                    height: 0;
                }}
                .slider {{
                    position: absolute;
                    cursor: pointer;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: #ccc;
                    transition: .2s;
                    border-radius: 34px;
                }}
                .slider:before {{
                    position: absolute;
                    content: "";
                    height: 12px;
                    width: 12px;
                    left: 4px;
                    bottom: 4px;
                    background-color: white;
                    transition: .2s;
                    border-radius: 50%;
                }}
                input:checked + .slider {{
                    background-color: #4285F4;
                }}
                input:checked + .slider:before {{
                    transform: translateX(14px);
                }}
                .reset-button {{
                    display: block;
                    margin: 20px auto;
                    padding: 10px 20px;
                    background-color: #cccccc;
                    color: #333333;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    text-align: center;
                    transition: background-color 0.3s ease;
                }}
                .reset-button:hover {{
                    background-color: #aaaaaa;
                }}
            </style>
            <script>
                function openCustomizePanel() {{
                    // Opens the customisation panel by sliding it in from the right
                    document.getElementById("customizePanel").style.right = '0';
                    setTimeout(function() {{
                        document.body.style.overflow = 'hidden';
                        document.getElementById("customizePanel").classList.add("open");
                    }}, 10);
                }}

                function closeCustomizePanel() {{
                    // Closes the customisation panel by sliding it out to the right
                    document.getElementById("customizePanel").classList.remove("open");
                    document.body.style.overflow = '';
                    setTimeout(function() {{
                        document.getElementById("customizePanel").style.right = '-500px';
                    }}, 300);
                }}

                function selectTheme(element) {{
                    // Selects a theme by changing the background colour of the body
                    var themes = document.getElementsByClassName("theme-option");
                    for (var i = 0; i < themes.length; i++) {{
                        themes[i].classList.remove("selected");
                    }}
                    element.classList.add("selected");

                    var color = element.style.backgroundColor;
                    document.body.style.backgroundColor = color;
                }}

                function setMode(mode) {{
                    // Switches between light and dark modes
                    var buttons = document.querySelectorAll('.customize-mode button');
                    buttons.forEach(button => {{
                        button.classList.remove('active');
                    }});
                    document.getElementById(mode).classList.add('active');

                    if (mode === 'light') {{
                        document.body.style.backgroundColor = '#FFFFFF';
                        document.body.style.color = '#000000';
                    }} else {{
                        document.body.style.backgroundColor = '#2e2e2e';
                        document.body.style.color = '#FFFFFF';
                    }}
                }}

                function openBackgroundUpload() {{
                    // Opens the file input dialog to upload a background image
                    document.getElementById('background-upload').click();
                }}

                function uploadBackgroundImage() {{
                    // Handles the background image upload and applies it to the body
                    var file = document.getElementById('background-upload').files[0];
                    if (file) {{
                        var reader = new FileReader();
                        reader.onload = function(e) {{
                            document.body.style.backgroundImage = 'url(' + e.target.result + ')';
                            document.body.style.backgroundSize = 'cover';
                        }}
                        reader.readAsDataURL(file);
                    }}
                }}

                function openColorPicker() {{
                    // Opens the colour picker dialog
                    document.getElementById('color-picker').click();
                }}

                function applyCustomColor(event) {{
                    // Applies the selected custom colour as the background colour
                    var color = event.target.value;
                    document.body.style.backgroundColor = color;
                }}

                function toggleShortcuts() {{
                    // Toggles the visibility of the shortcuts container
                    var shortcutsContainer = document.getElementById('shortcuts-container');
                    var toggleSwitch = document.getElementById('shortcuts-toggle');

                    if (shortcutsContainer && toggleSwitch) {{
                        if (toggleSwitch.checked) {{
                            shortcutsContainer.style.display = "flex";
                        }} else {{
                            shortcutsContainer.style.display = "none";
                        }}
                    }} else {{
                        console.error("Elements not found: shortcuts-container or shortcuts-toggle");
                    }}
                }}

                function handleSearch(event) {{
                    // Handles the search input and redirects to Google search on Enter key press
                    if (event.key === "Enter") {{
                        const query = document.getElementById("search-input").value;
                        const url = `https://www.google.com/search?q=${{encodeURIComponent(query)}}`;
                        window.location.href = url;
                    }}
                }}

                function resetDefaults() {{
                    // Resets the theme and settings to their default values
                    setMode('dark');
                    document.body.style.backgroundColor = '#2e2e2e';
                    document.body.style.color = '#FFFFFF';
                    document.getElementById('shortcuts-toggle').checked = true;
                    toggleShortcuts();
                    document.body.style.backgroundImage = '';
                    document.body.style.backgroundSize = '';
                }}

                function handleSearch(event) {{
                    // Custom search handler that integrates with the QWebChannel
                    if (event.key === 'Enter') {{
                        const query = document.getElementById('search-input').value;
                        const url = `https://www.google.com/search?q=${{encodeURIComponent(query)}}`;
                        new QWebChannel(qt.webChannelTransport, function(channel) {{
                            channel.objects.handler.openLink(url);
                        }});
                    }}
                }}

                window.onload = function() {{
                    // Initial setup for handling clicks on shortcut icons
                    function openLink(url) {{
                        new QWebChannel(qt.webChannelTransport, function(channel) {{
                            channel.objects.handler.openLink(url);
                        }});
                    }}

                    document.getElementById("youtube-shortcut").onclick = function() {{ openLink('https://www.youtube.com'); }};
                    document.getElementById("instagram-shortcut").onclick = function() {{ openLink('https://www.instagram.com'); }};
                    document.getElementById("reddit-shortcut").onclick = function() {{ openLink('https://www.reddit.com'); }};
                    document.getElementById("linkedin-shortcut").onclick = function() {{ openLink('https://www.linkedin.com'); }};
                    document.getElementById("twitter-shortcut").onclick = function() {{ openLink('https://www.twitter.com'); }};
                    document.getElementById("google-shortcut").onclick = function() {{ openLink('https://www.google.com'); }};
                }};
            </script>
        </head>
        <body>
            <div class="search-container">
                <img src="data:image/png;base64,{image_base64}" alt="Firecat Image" class="image">
                <div class="search-icon"></div>
                <input type="text" id="search-input" class="search-bar" placeholder="What do you want to search today?" onkeypress="handleSearch(event)">
                
                <div id="shortcuts-container" class="shortcuts-container">
                    <div class="shortcut" id="youtube-shortcut">{self.get_youtube_svg()}</div>
                    <div class="shortcut" id="instagram-shortcut">{self.get_instagram_svg()}</div>
                    <div class="shortcut" id="reddit-shortcut">{self.get_reddit_svg()}</div>
                    <div class="shortcut" id="linkedin-shortcut">{self.get_linkedin_svg()}</div>
                    <div class="shortcut" id="twitter-shortcut">{self.get_twitter_svg()}</div>
                    <div class="shortcut" id="google-shortcut">{self.get_google_svg()}</div>
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
                        <div class="theme-option" style="background-color: #3A3A3A;" onclick="selectTheme(this)"></div>
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

    def get_youtube_svg(self):
        # Returns the SVG code for the YouTube icon
        return '''<svg height="200px" width="200px" version="1.1" id="Layer_1" xmlns="http://www.w3.org/1999/xlink" viewBox="0 0 461.001 461.001"><g><path style="fill:#F61C0D;" d="M365.257,67.393H95.744C42.866,67.393,0,110.259,0,163.137v134.728c0,52.878,42.866,95.744,95.744,95.744h269.513c52.878,0,95.744-42.866,95.744-95.744V163.137C461.001,110.259,418.135,67.393,365.257,67.393z M300.506,237.056l-126.06,60.123c-3.359,1.602-7.239-0.847-7.239-4.568V168.607c0-3.774,3.982-6.22,7.348-4.514l126.06,63.881C304.363,229.873,304.298,235.248,300.506,237.056z"></path></g></svg>'''

    def get_instagram_svg(self):
        # Returns the SVG code for the Instagram icon
        return '''<svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><g><rect x="2" y="2" width="28" height="28" rx="6" fill="url(#paint0_radial_87_7153)"></rect> <rect x="2" y="2" width="28" height="28" rx="6" fill="url(#paint1_radial_87_7153)"></rect> <rect x="2" y="2" width="28" height="28" rx="6" fill="url(#paint2_radial_87_7153)"></rect> <path d="M23 10.5C23 11.3284 22.3284 12 21.5 12C20.6716 12 20 11.3284 20 10.5C20 9.67157 20.6716 9 21.5 9C22.3284 9 23 9.67157 23 10.5Z" fill="white"></path> <path fill-rule="evenodd" clip-rule="evenodd" d="M16 21C18.7614 21 21 18.7614 21 16C21 13.2386 18.7614 11 16 11C13.2386 11 11 13.2386 11 16C11 18.7614 13.2386 21 16 21ZM16 19C17.6569 19 19 17.6569 19 16C19 14.3431 17.6569 13 16 13C14.3431 13 13 14.3431 13 16C13 17.6569 14.3431 19 16 19Z" fill="white"></path> <path fill-rule="evenodd" clip-rule="evenodd" d="M6 15.6C6 12.2397 6 10.5595 6.65396 9.27606C7.2292 8.14708 8.14708 7.2292 9.27606 6.65396C10.5595 6 12.2397 6 15.6 6H16.4C19.7603 6 21.4405 6 22.7239 6.65396C23.8529 7.2292 24.7708 8.14708 25.346 9.27606C26 10.5595 26 12.2397 26 15.6V16.4C26 19.7603 26 21.4405 25.346 22.7239C24.7708 23.8529 23.8529 24.7708 22.7239 25.346C21.4405 26 19.7603 26 16.4 26H15.6C12.2397 26 10.5595 26 9.27606 25.346C8.14708 24.7708 7.2292 23.8529 6.65396 22.7239C6 21.4405 6 19.7603 6 16.4V15.6ZM15.6 8H16.4C18.1132 8 19.2777 8.00156 20.1779 8.0751C21.0548 8.14674 21.5032 8.27659 21.816 8.43597C22.5686 8.81947 23.1805 9.43139 23.564 10.184C23.7234 10.4968 23.8533 10.9452 23.9249 11.8221C23.9984 12.7223 24 13.8868 24 15.6V16.4C24 18.1132 23.9984 19.2777 23.9249 20.1779C23.8533 21.0548 23.7234 21.5032 23.564 21.816C23.1805 22.5686 22.5686 23.1805 21.816 23.564C21.5032 23.7234 21.0548 23.8533 20.1779 23.9249C19.2777 23.9984 18.1132 24 16.4 24H15.6C13.8868 24 12.7223 23.9984 11.8221 23.9249C10.9452 23.8533 10.4968 23.7234 10.184 23.564C9.43139 23.1805 8.81947 22.5686 8.43597 21.816C8.27659 21.5032 8.14674 21.0548 8.0751 20.1779C8.00156 19.2777 8 18.1132 8 16.4V15.6C8 13.8868 8.00156 12.7223 8.0751 11.8221C8.14674 10.9452 8.27659 10.4968 8.43597 10.184C8.81947 9.43139 9.43139 8.81947 10.184 8.43597C10.4968 8.27659 10.9452 8.14674 11.8221 8.0751C12.7223 8.00156 13.8868 8 15.6 8Z" fill="white"></path> <defs> <radialGradient id="paint0_radial_87_7153" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(12 23) rotate(-55.3758) scale(25.5196)"> <stop stop-color="#B13589"></stop> <stop offset="0.79309" stop-color="#C62F94"></stop> <stop offset="1" stop-color="#8A3AC8"></stop> </radialGradient> <radialGradient id="paint1_radial_87_7153" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(11 31) rotate(-65.1363) scale(22.5942)"> <stop stop-color="#E0E8B7"></stop> <stop offset="0.444662" stop-color="#FB8A2E"></stop> <stop offset="0.71474" stop-color="#E2425C"></stop> <stop offset="1" stop-color="#E2425C" stop-opacity="0"></stop> </radialGradient> <radialGradient id="paint2_radial_87_7153" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(0.500002 3) rotate(-8.1301) scale(38.8909 8.31836)"> <stop offset="0.156701" stop-color="#406ADC"></stop> <stop offset="0.467799" stop-color="#6A45BE"></stop> <stop offset="1" stop-color="#6A45BE" stop-opacity="0"></stop> </radialGradient> </defs> </g></svg>'''

    def get_reddit_svg(self):
        # Returns the SVG code for the Reddit icon
        return '''<svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><g><path d="M16 2C8.27812 2 2 8.27812 2 16C2 23.7219 8.27812 30 16 30C23.7219 30 30 23.7219 30 16C30 8.27812 23.7219 2 16 2Z" fill="#FC471E"></path> <path fill-rule="evenodd" clip-rule="evenodd" d="M20.0193 8.90951C20.0066 8.98984 20 9.07226 20 9.15626C20 10.0043 20.6716 10.6918 21.5 10.6918C22.3284 10.6918 23 10.0043 23 9.15626C23 8.30819 22.3284 7.6207 21.5 7.6207C21.1309 7.6207 20.7929 7.7572 20.5315 7.98359L16.6362 7L15.2283 12.7651C13.3554 12.8913 11.671 13.4719 10.4003 14.3485C10.0395 13.9863 9.54524 13.7629 9 13.7629C7.89543 13.7629 7 14.6796 7 15.8103C7 16.5973 7.43366 17.2805 8.06967 17.6232C8.02372 17.8674 8 18.1166 8 18.3696C8 21.4792 11.5817 24 16 24C20.4183 24 24 21.4792 24 18.3696C24 18.1166 23.9763 17.8674 23.9303 17.6232C24.5663 17.2805 25 16.5973 25 15.8103C25 14.6796 24.1046 13.7629 23 13.7629C22.4548 13.7629 21.9605 13.9863 21.5997 14.3485C20.2153 13.3935 18.3399 12.7897 16.2647 12.7423L17.3638 8.24143L20.0193 8.90951ZM12.5 18.8815C13.3284 18.8815 14 18.194 14 17.3459C14 16.4978 13.3284 15.8103 12.5 15.8103C11.6716 15.8103 11 16.4978 11 17.3459C11 18.194 11.6716 18.8815 12.5 18.8815ZM19.5 18.8815C20.3284 18.8815 21 18.194 21 17.3459C21 16.4978 20.3284 15.8103 19.5 15.8103C18.6716 15.8103 18 16.4978 18 17.3459C18 18.194 18.6716 18.8815 19.5 18.8815ZM12.7773 20.503C12.5476 20.3462 12.2372 20.4097 12.084 20.6449C11.9308 20.8802 11.9929 21.198 12.2226 21.3548C13.3107 22.0973 14.6554 22.4686 16 22.4686C17.3446 22.4686 18.6893 22.0973 19.7773 21.3548C20.0071 21.198 20.0692 20.8802 19.916 20.6449C19.7628 20.4097 19.4524 20.3462 19.2226 20.503C18.3025 21.1309 17.1513 21.4449 16 21.4449C15.3173 21.4449 14.6345 21.3345 14 21.1137C13.5646 20.9621 13.1518 20.7585 12.7773 20.503Z" fill="white"></path></g></svg>'''

    def get_linkedin_svg(self):
        # Returns the SVG code for the LinkedIn icon
        return '''<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" fill="none"><g><path fill="#0A66C2" d="M12.225 12.225h-1.778V9.44c0-.664-.012-1.519-.925-1.519-.926 0-1.068.724-1.068 1.47v2.834H6.676V6.498h1.707v.783h.024c.348-.594.996-.95 1.684-.925 1.802 0 2.135 1.185 2.135 2.728l-.001 3.14zM4.67 5.715a1.037 1.037 0 01-1.032-1.031c0-.566.466-1.032 1.032-1.032.566 0 1.031.466 1.032 1.032 0 .566-.466 1.032-1.032 1.032zm.889 6.51h-1.78V6.498h1.78v5.727zM13.11 2H2.885A.88.88 0 002 2.866v10.268a.88.88 0 00.885.866h10.226a.882.882 0 00.889-.866V2.865a.88.88 0 00-.889-.864z"></path></g></svg>'''

    def get_twitter_svg(self):
        # Returns the SVG code for the Twitter icon
        return '''<svg viewBox="0 0 24 24" aria-hidden="true" class="r-4qtqp9 r-yyyyoo r-dnmrzs r-bnwqim r-lrvibr r-m6rgpd r-k200y r-1nao33i r-5sfk15 r-kzbkwu"><g><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"></path></g></svg>'''

    def get_google_svg(self):
        # Returns the SVG code for the Google icon
        return '''<svg viewBox="-0.5 0 48 48" version="1.1" xmlns="http://www.w3.org/1999/xlink" fill="#000000"><g><g><g><path d="M9.82727273,24 C9.82727273,22.4757333 10.0804318,21.0144 10.5322727,19.6437333 L2.62345455,13.6042667 C1.08206818,16.7338667 0.213636364,20.2602667 0.213636364,24 C0.213636364,27.7365333 1.081,31.2608 2.62025,34.3882667 L10.5247955,28.3370667 C10.0772273,26.9728 9.82727273,25.5168 9.82727273,24" fill="#FBBC05"> </path> <path d="M23.7136364,10.1333333 C27.025,10.1333333 30.0159091,11.3066667 32.3659091,13.2266667 L39.2022727,6.4 C35.0363636,2.77333333 29.6954545,0.533333333 23.7136364,0.533333333 C14.4268636,0.533333333 6.44540909,5.84426667 2.62345455,13.6042667 L10.5322727,19.6437333 C12.3545909,14.112 17.5491591,10.1333333 23.7136364,10.1333333" fill="#EB4335"> </path> <path d="M23.7136364,37.8666667 C17.5491591,37.8666667 12.3545909,33.888 10.5322727,28.3562667 L2.62345455,34.3946667 C6.44540909,42.1557333 14.4268636,47.4666667 23.7136364,47.4666667 C29.4455,47.4666667 34.9177955,45.4314667 39.0249545,41.6181333 L31.5177727,35.8144 C29.3995682,37.1488 26.7323182,37.8666667 23.7136364,37.8666667" fill="#34A853"> </path> <path d="M46.1454545,24 C46.1454545,22.6133333 45.9318182,21.12 45.6113636,19.7333333 L23.7136364,19.7333333 L23.7136364,28.8 L36.3181818,28.8 C35.6879545,31.8912 33.9724545,34.2677333 31.5177727,35.8144 L39.0249545,41.6181333 C43.3393409,37.6138667 46.1454545,31.6490667 46.1454545,24" fill="#4285F4"> </path></g></g></g></svg>'''

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
