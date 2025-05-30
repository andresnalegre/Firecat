import os
import json
import re
import shutil
from typing import Dict, Any, Optional

CONFIG_FILE = "user_preferences.json"
IMAGE_FOLDER = "background_images"

LIGHT_MODE_COLOR = "#ffffff"
DARK_MODE_COLOR = "#2e2e2e"

MODES = {
    "light": LIGHT_MODE_COLOR,
    "dark": DARK_MODE_COLOR
}

def rgb_to_hex(rgb: str) -> str:
    if isinstance(rgb, str) and rgb.startswith('#') and len(rgb) == 7:
        return rgb.lower()
    
    match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', str(rgb))
    if match:
        r, g, b = [int(match.group(i)) for i in range(1, 4)]
        return f"#{r:02x}{g:02x}{b:02x}"
        
    return rgb


class PreferencesManager:
    
    def __init__(self, config_file: str = CONFIG_FILE, image_folder: str = IMAGE_FOLDER):
        self.config_file = config_file
        self.image_folder = image_folder
        self._ensure_directories()
        self._settings_cache = None
    
    def _ensure_directories(self) -> None:
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder, exist_ok=True)
        
        config_dir = os.path.dirname(os.path.abspath(self.config_file))
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
    
    def _get_default_settings(self) -> Dict[str, Any]:
        return {
            "theme": "light",
            "backgroundColor": LIGHT_MODE_COLOR,
            "backgroundImage": None,
            "shortcuts": True,
            "mode": "light"
        }
    
    def _determine_mode(self, color: str) -> str:
        color = color.lower()
        for mode, mode_color in MODES.items():
            if color == mode_color:
                return mode
        return "custom"
    
    def load_preferences(self) -> Dict[str, Any]:
        if self._settings_cache is not None:
            return self._settings_cache.copy()
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                    
                    defaults = self._get_default_settings()
                    for key, value in defaults.items():
                        if key not in settings:
                            settings[key] = value
                    
                    self._normalize_settings(settings)
                    
                    self._settings_cache = settings.copy()
                    return settings
            except Exception as e:
                print(f"Erro ao carregar configurações: {e}")
                self._settings_cache = self._get_default_settings()
                return self._settings_cache.copy()
        
        self._settings_cache = self._get_default_settings()
        return self._settings_cache.copy()
    
    def _normalize_settings(self, settings: Dict[str, Any]) -> None:
        if "backgroundColor" in settings:
            settings["backgroundColor"] = rgb_to_hex(settings["backgroundColor"])
        
        if "backgroundColor" in settings:
            settings["mode"] = self._determine_mode(settings["backgroundColor"])
    
    def save_settings(self, settings: Dict[str, Any]) -> None:
        try:
            merged_settings = self._get_default_settings()
            
            merged_settings.update(settings)
            
            self._normalize_settings(merged_settings)
            
            with open(self.config_file, 'w') as f:
                json.dump(merged_settings, f, indent=4)
            
            self._settings_cache = merged_settings.copy()
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        settings = self.load_preferences()
        return settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        settings = self.load_preferences()
        settings[key] = value
        self.save_settings(settings)
    
    def get_theme(self) -> str:
        return self.get_setting("theme", "light")
    
    def get_background_color(self) -> str:
        return self.get_setting("backgroundColor", LIGHT_MODE_COLOR)
    
    def get_mode(self) -> str:
        return self.get_setting("mode", "light")
    
    def get_shortcuts(self) -> bool:
        return self.get_setting("shortcuts", True)
    
    def get_background_image(self) -> Optional[str]:
        return self.get_setting("backgroundImage")
    
    def set_background_image(self, image_path: str) -> None:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Arquivo de imagem '{image_path}' não existe.")
        
        os.makedirs(self.image_folder, exist_ok=True)
        
        image_name = os.path.basename(image_path)
        target_path = os.path.join(self.image_folder, image_name)
        
        shutil.copy2(image_path, target_path)
        
        self.set_setting("backgroundImage", target_path)
    
    def clear_background_image(self) -> None:
        self.set_setting("backgroundImage", None)
    
    def reset_settings(self) -> None:
        self.save_settings(self._get_default_settings())
        self._settings_cache = None