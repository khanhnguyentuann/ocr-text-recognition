# File Service - Handles file opening, saving, and validation for the OCR application.
import os
from typing import Optional
from PySide6.QtWidgets import QFileDialog, QWidget
from src.services.log_service import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Define valid image extensions as a constant
VALID_IMAGE_EXTENSIONS: tuple[str, ...] = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')


class FileService:
    # A service class dedicated to handling all file-related operations.

    @staticmethod
    def select_image_file(parent_widget: Optional[QWidget] = None) -> Optional[str]:
        # Opens a file dialog for the user to select an image file.
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
        # Saves the given text content to a file chosen by the user.
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
        # Validates if a given file path points to a valid and existing image file.
        if not os.path.exists(file_path):
            logger.warning(f"Validation failed: File does not exist at path: {file_path}")
            return False
        
        _, ext = os.path.splitext(file_path)
        is_valid = ext.lower() in VALID_IMAGE_EXTENSIONS
        if not is_valid:
            logger.warning(f"Validation failed: File with extension '{ext}' is not a supported image type.")
        return is_valid
