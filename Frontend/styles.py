def get_styles():
    return """
    html {
        height: 100%;
    }

    body {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        margin: 0;
        font-family: 'Roboto', sans-serif;
        overflow: hidden;
        transition: background-color 0.3s ease;
    }

    .search-container {
        text-align: center;
        position: relative;
        margin-top: -100px;
    }

    .search-bar {
        width: 600px;
        height: 50px;
        padding: 10px 20px 10px 50px;
        font-size: 24px;
        border: 2px solid #ddd;
        border-radius: 30px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }

    .search-bar:focus {
        border-color: #4285F4;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        outline: none;
    }

    .search-bar::placeholder {
        font-size: 24px;
        color: #999;
        opacity: 1;
    }

    .search-icon {
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        width: 24px;
        height: 24px;
        -webkit-mask-image: url(//resources/cr_components/searchbox/icons/search_cr23.svg);
        background-color: #999;
    }

    .image {
        display: block;
        width: 300px;
        height: 300px;
        object-fit: cover;
        margin: 0 auto 20px;
    }

    .customize-button {
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
    }

    .customize-button:hover {
        background-color: #357ae8;
    }

    .customize-panel {
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
    }

    .customize-panel.open {
        right: 0;
    }

    .customize-header {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
        position: relative;
    }

    .customize-header h2 {
        font-size: 28px;
        font-weight: 300;
        letter-spacing: 1px;
        margin: 0;
        text-align: center;
        width: 100%;
        color: #f1f1f1;
    }

    .close {
        color: #aaa;
        font-size: 28px;
        font-weight: bold;
        position: absolute;
        right: 0;
        cursor: pointer;
    }

    .close:hover,
    .close:focus {
        color: white;
        text-decoration: none;
    }

    .settings-container {
        padding: 20px;
        border-radius: 20px;
        background-color: #3b3b3b;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }

    .customize-mode {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
        padding: 10px;
        border: 1px solid #4285F4;
        border-radius: 30px;
    }

    .customize-mode button {
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
    }

    .customize-mode button:focus {
        outline: none;
        box-shadow: 0 0 0 3px #4285F4, 0 0 0 5px #000;
        border-radius: 20px;
    }

    .customize-mode button.active {
        background-color: #adc8ff;
        color: #000;
        border-radius: 20px;
        outline: none;
        box-shadow: none;
    }

    .theme-container {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
        padding: 10px;
        border: 1px solid #4285F4;
        border-radius: 30px;
        flex-wrap: wrap;
        width: 100%;
    }

    .theme-option {
        display: inline-block;
        width: 80px;
        height: 80px;
        background-color: #555;
        border-radius: 50%;
        margin: 10px;
        cursor: pointer;
        border: 3px solid white;
        transition: transform 0.3s ease;
    }

    .theme-option.selected {
        border-color: #4285F4;
    }

    .custom-color {
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
    }

    .shortcuts-container {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        margin-top: 20px;
    }

    .shortcut {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 80px;
        height: 80px;
        background-color: white !important;
        border-radius: 50%;
        margin: 10px;
        cursor: pointer;
        transition: transform 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .shortcut svg {
        width: 50%;
        height: 50%;
        fill: black !important;
    }

    .shortcut:hover {
        transform: scale(1.1);
    }

    .divider {
        width: 100%;
        height: 1px;
        background-color: #555;
        margin: 20px 0;
    }

    .customize-theme-button {
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
    }

    .customize-theme-button:hover {
        background-color: #357ae8;
    }

    .shortcuts-toggle-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        padding: 10px;
        border-radius: 30px;
        background-color: #3b3b3b;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    .shortcuts-toggle-container h3 {
        margin: 0;
        margin-left: 20px;
        font-size: 18px;
        color: #f1f1f1;
    }

    .switch {
        position: relative;
        display: inline-block;
        width: 34px;
        height: 20px;
        margin-right: 20px;
        margin-top: 10px;
    }

    .switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: .2s;
        border-radius: 34px;
    }

    .slider:before {
        position: absolute;
        content: "";
        height: 12px;
        width: 12px;
        left: 4px;
        bottom: 4px;
        background-color: white;
        transition: .2s;
        border-radius: 50%;
    }

    input:checked + .slider {
        background-color: #4285F4;
    }

    input:checked + .slider:before {
        transform: translateX(14px);
    }

    .reset-button {
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
    }

    .reset-button:hover {
        background-color: #aaaaaa;
    }

    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: #4285F4;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #357ae8;
    }
    """

def get_qt_styles():
    return """
    QTabWidget::pane {
        border: none;
        background: #2e2e2e;
    }
    
    QTabBar::tab {
        background: #383838;
        color: #ffffff;
        padding: 8px 15px;
        border: none;
        margin-right: 2px;
        min-width: 100px;
    }
    
    QTabBar::tab:selected {
        background: #4285F4;
        color: white;
    }
    
    QTabBar::tab:!selected:hover {
        background: #4f4f4f;
    }
    
    QTabBar::scroller {
        width: 0px;
    }
    
    QTabBar QToolButton {
        background-color: #383838;
        color: white;
        border: none;
        padding: 5px;
    }
    
    QTabBar QToolButton:hover {
        background-color: #4285F4;
    }
    
    QToolButton#newTabButton {
        background-color: #383838;
        color: white;
        border: none;
        padding: 8px 15px;
        margin: 0;
        font-size: 15px;
        font-weight: bold;
        height: 100%;
        min-width: 40px;
    }
    
    QToolButton#newTabButton:hover {
        background-color: #4285F4;
    }

    QTabBar::close-button {
        image: url(../Firecat/Images/close.png);
        background: #ffffff;
        border-radius: 2px;
        margin: 2px;
        padding: 2px;
        width: 16px;
        height: 16px;
        subcontrol-position: right;
    }

    QTabBar::close-button:hover {
        background: #666666;
    }
    """