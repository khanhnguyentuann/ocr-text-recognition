"""
File Service - Handles file opening, saving, and validation for the OCR application.

This module provides a `FileService` class that encapsulates all file-related
operations, such as opening image files, saving text files, and validating
file types. This helps to keep the controller logic clean and focused.
"""
import os
from typing import Optional
from PySide6.QtWidgets import QFileDialog, QWidget
from src.services.log_service import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Define valid image extensions as a constant
VALID_IMAGE_EXTENSIONS: tuple[str, ...] = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')


class FileService:
    """
    A service class dedicated to handling all file-related operations.

    This class uses static methods to provide utility functions for file
    selection, saving, and validation, abstracting the underlying details
    of file dialogs and file system checks.
    """

    @staticmethod
    def select_image_file(parent_widget: Optional[QWidget] = None) -> Optional[str]:
        """
        Opens a file dialog for the user to select an image file.

        This method displays a standard file dialog, filtered to show valid
        image file types. It logs the selected file path for debugging purposes.

        Args:
            parent_widget (Optional[QWidget]): The parent widget for the dialog.
                                               This helps in proper window layering.

        Returns:
            Optional[str]: The absolute path to the selected image file, or None
                           if the user cancels the dialog.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            parent_widget,
            "Select Image",
            "",
            f"Images (*{' *'.join(VALID_IMAGE_EXTENSIONS)});;All Files (*)"
        )
        if file_path:
            logger.info(f"User selected image file: {file_path}")
            return file_path
        logger.info("File selection was cancelled by the user.")
        return None

    @staticmethod
    def save_text_to_file(text_content: str, parent_widget: Optional[QWidget] = None) -> Optional[str]:
        """
        Saves the given text content to a file chosen by the user.

        This method opens a save file dialog, allowing the user to specify a
        location and filename. It handles potential `IOError` exceptions during
        the file writing process.

        Args:
            text_content (str): The string content to be saved to the file.
            parent_widget (Optional[QWidget]): The parent widget for the dialog.

        Returns:
            Optional[str]: The path where the file was saved, or None if the
                           operation was cancelled or an error occurred.
        """
        if not text_content:
            logger.warning("Attempted to save empty text content.")
            return None

        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            "Save Text",
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                logger.info(f"Text content successfully saved to: {file_path}")
                return file_path
            except IOError as e:
                logger.error(f"An IOError occurred while saving file to {file_path}: {e}", exc_info=True)
                return None
        logger.info("File save operation was cancelled by the user.")
        return None

    @staticmethod
    def is_valid_image(file_path: str) -> bool:
        """
        Validates if a given file path points to a valid and existing image file.

        This method checks for the file's existence and whether its extension
        is in the list of supported image formats.

        Args:
            file_path (str): The path to the file to be validated.

        Returns:
            bool: True if the file is a valid and existing image, False otherwise.
        """
        if not os.path.exists(file_path):
            logger.warning(f"Validation failed: File does not exist at path: {file_path}")
            return False
        
        _, ext = os.path.splitext(file_path)
        is_valid = ext.lower() in VALID_IMAGE_EXTENSIONS
        if not is_valid:
            logger.warning(f"Validation failed: File with extension '{ext}' is not a supported image type.")
        return is_valid
