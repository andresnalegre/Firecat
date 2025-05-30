import os
import json
import re
import shutil
from typing import Dict, Any, Optional

# Constantes
CONFIG_FILE = "user_preferences.json"
IMAGE_FOLDER = "background_images"

# Cores padrão
LIGHT_MODE_COLOR = "#ffffff"
DARK_MODE_COLOR = "#2e2e2e"

# Modos disponíveis
MODES = {
    "light": LIGHT_MODE_COLOR,
    "dark": DARK_MODE_COLOR
}

def rgb_to_hex(rgb: str) -> str:
    """Converte strings RGB para formato hex padronizado.
    
    Args:
        rgb: String no formato "#xxxxxx" ou "rgb(r, g, b)"
        
    Returns:
        String no formato hexadecimal "#xxxxxx" em minúsculas
    """
    # Já é hex? Padroniza para minúsculas
    if isinstance(rgb, str) and rgb.startswith('#') and len(rgb) == 7:
        return rgb.lower()
    
    # É formato RGB?
    match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', str(rgb))
    if match:
        r, g, b = [int(match.group(i)) for i in range(1, 4)]
        return f"#{r:02x}{g:02x}{b:02x}"
        
    # Fallback, retorna o valor original
    return rgb


class PreferencesManager:
    """Gerencia as preferências do usuário para o Firecat Browser."""
    
    def __init__(self, config_file: str = CONFIG_FILE, image_folder: str = IMAGE_FOLDER):
        """Inicializa o gerenciador de preferências.
        
        Args:
            config_file: Caminho para o arquivo de configuração JSON
            image_folder: Pasta para armazenar imagens de fundo
        """
        self.config_file = config_file
        self.image_folder = image_folder
        self._ensure_directories()
        self._settings_cache = None
    
    def _ensure_directories(self) -> None:
        """Garante que os diretórios necessários existam."""
        # Cria pasta de imagens
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder, exist_ok=True)
        
        # Cria diretório do arquivo de configuração
        config_dir = os.path.dirname(os.path.abspath(self.config_file))
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Retorna as configurações padrão.
        
        Returns:
            Dicionário com as configurações padrão
        """
        return {
            "theme": "light",
            "backgroundColor": LIGHT_MODE_COLOR,
            "backgroundImage": None,
            "shortcuts": True,
            "mode": "light"
        }
    
    def _determine_mode(self, color: str) -> str:
        """Determina o modo baseado na cor de fundo.
        
        Args:
            color: Cor de fundo em formato hexadecimal
        
        Returns:
            Modo correspondente ("light", "dark" ou "custom")
        """
        color = color.lower()
        for mode, mode_color in MODES.items():
            if color == mode_color:
                return mode
        return "custom"
    
    def load_preferences(self) -> Dict[str, Any]:
        """Carrega as preferências do arquivo de configuração.
        
        Returns:
            Dicionário com as preferências do usuário
        """
        # Usa cache se disponível
        if self._settings_cache is not None:
            return self._settings_cache.copy()
        
        # Tenta carregar do arquivo
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                    
                    # Adiciona valores padrão para chaves ausentes
                    defaults = self._get_default_settings()
                    for key, value in defaults.items():
                        if key not in settings:
                            settings[key] = value
                    
                    # Normaliza valores
                    self._normalize_settings(settings)
                    
                    # Atualiza o cache
                    self._settings_cache = settings.copy()
                    return settings
            except Exception as e:
                print(f"Erro ao carregar configurações: {e}")
                # Retorna padrões em caso de erro
                self._settings_cache = self._get_default_settings()
                return self._settings_cache.copy()
        
        # Arquivo não existe, retorna padrões
        self._settings_cache = self._get_default_settings()
        return self._settings_cache.copy()
    
    def _normalize_settings(self, settings: Dict[str, Any]) -> None:
        """Normaliza as configurações para garantir consistência.
        
        Args:
            settings: Dicionário de configurações a ser normalizado
        """
        # Garante que backgroundColor seja hex e minúsculo
        if "backgroundColor" in settings:
            settings["backgroundColor"] = rgb_to_hex(settings["backgroundColor"])
        
        # Atualiza o modo baseado na cor
        if "backgroundColor" in settings:
            settings["mode"] = self._determine_mode(settings["backgroundColor"])
    
    def save_settings(self, settings: Dict[str, Any]) -> None:
        """Salva as configurações no arquivo.
        
        Args:
            settings: Dicionário com as configurações a serem salvas
        """
        try:
            # Começar com configurações padrão
            merged_settings = self._get_default_settings()
            
            # Mesclar com as configurações fornecidas
            merged_settings.update(settings)
            
            # Normalizar valores
            self._normalize_settings(merged_settings)
            
            # Salvar no arquivo
            with open(self.config_file, 'w') as f:
                json.dump(merged_settings, f, indent=4)
            
            # Atualizar cache
            self._settings_cache = merged_settings.copy()
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Obtém um valor específico das configurações.
        
        Args:
            key: A chave da configuração desejada
            default: Valor padrão se a chave não existir
            
        Returns:
            O valor da configuração ou o valor padrão
        """
        settings = self.load_preferences()
        return settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Define um único valor de configuração.
        
        Args:
            key: A chave da configuração
            value: O valor a ser definido
        """
        settings = self.load_preferences()
        settings[key] = value
        self.save_settings(settings)
    
    def get_theme(self) -> str:
        """Retorna o tema atual.
        
        Returns:
            Nome do tema atual
        """
        return self.get_setting("theme", "light")
    
    def get_background_color(self) -> str:
        """Retorna a cor de fundo atual.
        
        Returns:
            Cor de fundo em formato hexadecimal
        """
        return self.get_setting("backgroundColor", LIGHT_MODE_COLOR)
    
    def get_mode(self) -> str:
        """Retorna o modo atual.
        
        Returns:
            Modo atual ("light", "dark" ou "custom")
        """
        return self.get_setting("mode", "light")
    
    def get_shortcuts(self) -> bool:
        """Verifica se os atalhos estão habilitados.
        
        Returns:
            True se os atalhos estiverem habilitados, False caso contrário
        """
        return self.get_setting("shortcuts", True)
    
    def get_background_image(self) -> Optional[str]:
        """Retorna o caminho para a imagem de fundo, se definida.
        
        Returns:
            Caminho para a imagem de fundo ou None
        """
        return self.get_setting("backgroundImage")
    
    def set_background_image(self, image_path: str) -> None:
        """Define uma imagem de fundo.
        
        Args:
            image_path: Caminho para o arquivo de imagem
            
        Raises:
            FileNotFoundError: Se o arquivo de imagem não existir
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Arquivo de imagem '{image_path}' não existe.")
        
        # Garante que o diretório de imagens existe
        os.makedirs(self.image_folder, exist_ok=True)
        
        # Copia a imagem para o diretório de imagens
        image_name = os.path.basename(image_path)
        target_path = os.path.join(self.image_folder, image_name)
        
        # Usar shutil é mais seguro e eficiente para copiar arquivos
        shutil.copy2(image_path, target_path)
        
        # Atualiza a configuração
        self.set_setting("backgroundImage", target_path)
    
    def clear_background_image(self) -> None:
        """Remove a imagem de fundo atual."""
        self.set_setting("backgroundImage", None)
    
    def reset_settings(self) -> None:
        """Redefine todas as configurações para os valores padrão."""
        self.save_settings(self._get_default_settings())
        # Limpa também o cache
        self._settings_cache = None