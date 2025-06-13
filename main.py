#!/usr/bin/env python3
"""
STARK AI Desktop Application
Main entry point for the smart assistant GUI application.
"""

import logging
import os
import sys

from PySide6.QtCore import Qt, QTranslator
from PySide6.QtGui import QFont, QFontDatabase, QPixmap, QIcon
from PySide6.QtWidgets import QApplication, QMessageBox
from config_manager import config_manager
from main_window import MainWindow


def setup_logging():
    """Set up logging based on config settings"""
    if config_manager.is_logging_enabled():
        log_level = getattr(logging, config_manager.get_log_level().upper(), logging.INFO)
        logs_path = config_manager.get_logs_path()

        # Ensure logs directory exists
        os.makedirs(logs_path, exist_ok=True)

        log_file = os.path.join(logs_path, 'stark_ai.log')

        # Configure logging with both file and console handlers
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        logger = logging.getLogger(__name__)
        logger.info(f"STARK AI Application Starting... (Version {config_manager.get_app_version()})")
        logger.info(f"Log level set to: {config_manager.get_log_level()}")
        return logger
    return None


def load_custom_fonts():
    """Load custom fonts from assets directory"""
    logger = logging.getLogger(__name__) if config_manager.is_logging_enabled() else None

    try:
        fonts_path = config_manager.get_fonts_path()

        # Create fonts directory if it doesn't exist
        os.makedirs(fonts_path, exist_ok=True)

        # List of potential font files to try
        font_files = [
            'custom_font.ttf',
            'arial.ttf',
            'roboto.ttf',
            'inter.ttf',
            'opensans.ttf'
        ]

        loaded_fonts = []

        for font_file in font_files:
            font_path = os.path.join(fonts_path, font_file)
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    loaded_fonts.extend(font_families)
                    if logger:
                        logger.info(f"Loaded font: {font_file} -> {font_families}")

        return loaded_fonts[0] if loaded_fonts else None

    except Exception as e:
        if logger:
            logger.warning(f"Failed to load custom fonts: {e}")
        return None


def setup_application_properties(app):
    """Set up application properties from config"""
    logger = logging.getLogger(__name__) if config_manager.is_logging_enabled() else None

    try:
        app_name = config_manager.get_app_name()
        app_version = config_manager.get_app_version()

        app.setApplicationName(app_name)
        app.setApplicationVersion(app_version)
        app.setOrganizationName("STARK AI")
        app.setOrganizationDomain("stark-ai.local")

        # Enable high DPI scaling for better display on high-resolution screens
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        app.setAttribute(Qt.AA_SynthesizeMouseForUnhandledTouchEvents, False)

        # Set application icon if available
        icons_path = config_manager.get_icons_path()
        app_icon_path = os.path.join(icons_path, "app_icon.png")

        if os.path.exists(app_icon_path):
            icon = QIcon(app_icon_path)
            app.setWindowIcon(icon)
            if logger:
                logger.info(f"Application icon loaded from: {app_icon_path}")
        else:
            # Create a simple default icon
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.blue)
            app.setWindowIcon(QIcon(pixmap))
            if logger:
                logger.info("Using default application icon")

    except Exception as e:
        if logger:
            logger.error(f"Error setting up application properties: {e}")


def setup_application_font(app):
    """Set up application font from config"""
    logger = logging.getLogger(__name__) if config_manager.is_logging_enabled() else None

    try:
        # Try to load custom fonts first
        custom_font_family = load_custom_fonts()

        font_family = custom_font_family or config_manager.get_font_family()
        font_size = config_manager.get_font_size()

        # Create and configure font
        font = QFont(font_family, font_size)
        font.setHintingPreference(QFont.PreferFullHinting)
        font.setStyleStrategy(QFont.PreferAntialias)

        app.setFont(font)

        if logger:
            logger.info(f"Application font set to: {font_family}, {font_size}px")

    except Exception as e:
        if logger:
            logger.error(f"Error setting up application font: {e}")


def setup_translations(app):
    """Set up application translations if available"""
    logger = logging.getLogger(__name__) if config_manager.is_logging_enabled() else None

    try:
        language = config_manager.get('User', 'preferred_language', 'en')

        if language != 'en':
            translator = QTranslator()
            translations_path = os.path.join(config_manager.get_assets_path(), 'translations')

            if translator.load(f"stark_ai_{language}", translations_path):
                app.installTranslator(translator)
                if logger:
                    logger.info(f"Translations loaded for language: {language}")
            else:
                if logger:
                    logger.warning(f"No translations found for language: {language}")

    except Exception as e:
        if logger:
            logger.error(f"Error setting up translations: {e}")


def ensure_required_directories():
    """Ensure all required directories exist"""
    logger = logging.getLogger(__name__) if config_manager.is_logging_enabled() else None

    try:
        directories = [
            config_manager.get_assets_path(),
            config_manager.get_icons_path(),
            config_manager.get_fonts_path(),
            config_manager.get_data_path(),
            config_manager.get_ui_path(),
            config_manager.get_logs_path()
        ]

        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                if logger:
                    logger.info(f"Created directory: {directory}")

    except Exception as e:
        if logger:
            logger.error(f"Error creating required directories: {e}")


def check_system_requirements():
    """Check if system meets minimum requirements"""
    logger = logging.getLogger(__name__) if config_manager.is_logging_enabled() else None

    try:
        import platform

        system_info = {
            'platform': platform.system(),
            'version': platform.version(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0]
        }

        if logger:
            logger.info(f"System info: {system_info}")

        # Check minimum Python version
        if sys.version_info < (3, 8):
            if logger:
                logger.error("Python 3.8+ is required")
            return False

        return True

    except Exception as e:
        if logger:
            logger.error(f"Error checking system requirements: {e}")
        return True  # Continue anyway


def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    if config_manager.is_logging_enabled():
        logger = logging.getLogger(__name__)
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def main():
    """Main application entry point"""
    # Set up logging first
    logger = setup_logging()

    # Install global exception handler
    if logger:
        sys.excepthook = handle_exception

    try:
        # Check system requirements
        if not check_system_requirements():
            return 1

        # Create QApplication instance
        app = QApplication(sys.argv)

        # Ensure required directories exist
        ensure_required_directories()

        # Set up application properties from config
        setup_application_properties(app)

        # Set up application font from config
        setup_application_font(app)

        # Set up translations
        setup_translations(app)

        # Create and show main window
        try:
            window = MainWindow()
            window.show()

            # Center window and bring to front
            window.raise_()
            window.activateWindow()

        except Exception as e:
            error_msg = f"Failed to create main window: {e}"
            if logger:
                logger.critical(error_msg)
            else:
                print(error_msg)

            # Show error dialog
            QMessageBox.critical(None, "Startup Error",
                                 f"Failed to start STARK AI:\n{error_msg}")
            return 1

        # Mark first time launch as complete if it was the first time
        if config_manager.is_first_time_launch():
            config_manager.set_first_time_launch(False)
            if logger:
                logger.info("First time launch completed")

        if logger:
            logger.info("Application started successfully")

        # Start event loop
        exit_code = app.exec()

        if logger:
            logger.info(f"Application exited with code: {exit_code}")

        return exit_code

    except Exception as e:
        error_msg = f"Critical error starting application: {e}"
        if logger:
            logger.critical(error_msg)
        else:
            print(error_msg)

        try:
            QMessageBox.critical(None, "Critical Error",
                                 f"A critical error occurred:\n{error_msg}")
        except:
            pass  # GUI might not be available

        return 1

    finally:
        # Cleanup
        if logger:
            logger.info("Application cleanup completed")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)





