
# Firecat

Firecat is a simple desktop application built using PyQt5 that provides a customisable web interface with shortcuts to popular websites and the ability to personalise the theme and background. This project is ideal for users who want a visually appealing and functional dashboard on their desktop.

## Features

- **Customisable Theme**: Easily switch between light and dark themes.
- **Background Image**: Set your own background image to personalise the look.
- **Quick Shortcuts**: Quickly access popular websites like YouTube, Instagram, Reddit, and more.
- **Settings Panel**: Modify settings like theme and background from within the application.

## Installation

### Prerequisites

Before you begin, let's make sure you have everything you need:

- **Python 3.x**: Firecat requires Python 3.x to run.
- **Visual Studio Code**: I’m using VS Code as the development environment.

### Setting Up the Environment in VS Code (macOS)

1. **Create and Activate the Virtual Environment**:
   - In the terminal, navigate to the project directory and create a virtual environment:

     ```bash
     python3 -m venv firecat-env
     ```

   - Activate the environment:

     ```bash
     source firecat-env/bin/activate
     ```

2. **Install Dependencies**:
   - With the virtual environment active, install the required libraries:

     ```bash
     python3 -m pip install PyQt5 
     python3 -m pip install PyQt5-sip 
     python3 -m pip install PyQtWebEngine
     ```

3. **Configure VS Code**:
   - Open the Command Palette (`Cmd+Shift+P`) in VS Code.
   - Select "Python: Select Interpreter" and choose the Python interpreter from the virtual environment (`firecat-env/bin/python`).

### Troubleshooting PyQt5 Installation

If you encounter issues while installing PyQt5, here are some tips:

1. **Update pip**: Sometimes, outdated versions of pip can cause issues. Update pip with:

   ```bash
   python3 -m pip install --upgrade pip
   ```

2. **Install Xcode Command Line Tools**: On macOS, certain issues can arise if you don't have Xcode installed:

   ```bash
   xcode-select --install
   ```

3. **Check Python Compatibility**: The version of PyQt5 I'm using to run Firecat is 5.15.4. Install it with:

   ```bash
   pip install PyQt5==5.15.4
   ```

4. **Reinstall PyQt5**: Reinstalling can often resolve some bugs:

   ```bash
   python3.8 -m pip uninstall PyQt5 
   python3.8 -m pip uninstall PyQt5-sip 
   python3.8 -m pip uninstall PyQtWebEngine
   python3.8 -m pip install PyQt5 
   python3.8 -m pip install PyQt5-sip 
   python3.8 -m pip install PyQtWebEngine
   ```

### Running Firecat

After everything is set up, let's run Firecat as follows:

1. **Open the Project in VS Code**:
   - Navigate to the project directory using the terminal in VS Code.

2. **Run the Application**:
   - In the terminal, with the virtual environment still active, run:

     ```bash
     python3 firecat.py
     ```

This should open the main window of Firecat, where you can start interacting with the prototype browser or application.

## Contributing

Contributions are welcome! If you have any improvements or new features you’d like to add, feel free to fork the repository and submit a pull request. Please ensure that your code follows the existing style and structure.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Thanks to the developers of PyQt5 for providing a robust framework for building desktop applications.
- Icons and themes used in the project are sourced from various open libraries.

---

If you have any feedback, questions, or suggestions, please feel free to open an issue or contact me directly through GitHub.

[![GitHub](https://img.shields.io/badge/Made%20by-Andres%20Nicolas%20Alegre-brightgreen)](https://github.com/andresnalegre)
