import json
import os
import webbrowser

# The configuration file that stores user preferences
CONFIG_FILE = "user_preferences.json"

def load_user_preferences():
    """Load user preferences from the JSON configuration file.
    If the file doesn't exist, return default preferences."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # Return default preferences if the config file is missing
        return {
            "theme": "dark",
            "selected_color": "#4285F4"
        }

def save_user_preferences(preferences):
    """Save the user preferences to the JSON configuration file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(preferences, f, indent=4)

def set_theme(theme):
    """Update the theme preference and save it to the configuration file."""
    preferences = load_user_preferences()
    preferences['theme'] = theme
    save_user_preferences(preferences)

def set_background_image(image_path):
    """Set and save the background image specified by the user.
    
    Copies the image to a designated folder and updates the config file.
    Raises FileNotFoundError if the specified image does not exist.
    """
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)

    if os.path.exists(image_path):
        image_name = os.path.basename(image_path)
        target_path = os.path.join(IMAGE_FOLDER, image_name)

        # Copy the image file to the target path
        with open(image_path, 'rb') as fsrc:
            with open(target_path, 'wb') as fdst:
                fdst.write(fsrc.read())

        # Update preferences with the new background image path
        preferences = load_user_preferences()
        preferences['background_image'] = target_path
        save_user_preferences(preferences)
    else:
        # Raise an error if the image file is not found
        raise FileNotFoundError(f"The image file '{image_path}' does not exist.")

def get_background_image():
    """Retrieve the path to the user's background image from preferences.
    
    Returns None if no background image is set.
    """
    preferences = load_user_preferences()
    return preferences.get('background_image', None)

def open_url_in_browser(shortcut_name):
    """Open a predefined URL in the web browser based on the shortcut name.
    
    Recognizes specific shortcuts like 'youtube', 'instagram', etc.
    """
    urls = {
        "youtube": "https://www.youtube.com",
        "instagram": "https://www.instagram.com",
        "reddit": "https://www.reddit.com",
        "linkedin": "https://www.linkedin.com",
        "twitter": "https://www.twitter.com",
        "google": "https://www.google.com"
    }
    
    if shortcut_name in urls:
        webbrowser.open(urls[shortcut_name])
    else:
        # Log an error message if the shortcut is not recognized
        print(f"Shortcut '{shortcut_name}' not recognized.")
