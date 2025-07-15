# OCR Controller - Orchestrates the application flow by connecting services to the view.
from typing import Optional
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from src.view.main_window import MainWindow
from src.services.file_service import FileService
from src.services.ocr_service import OCRService
from src.services.log_service import get_logger, setup_logging

# Initialize the logging system for the entire application
setup_logging()
logger = get_logger(__name__)


class OCRController(QObject):
    # The main controller that manages the interaction between the UI and services.

    def __init__(self) -> None:
        # Initializes the controller, view, and services.
        super().__init__()
        self.view: MainWindow = MainWindow()
        self.file_service: FileService = FileService()
        self.ocr_service: OCRService = OCRService(languages=['en', 'vi'])
        self.current_image_path: Optional[str] = None
        self.connect_signals()

    def connect_signals(self) -> None:
        # Connects signals from the view to the controller's handler methods.
        self.view.open_file_requested.connect(self.select_image_file)
        self.view.save_text_requested.connect(self.save_text_to_file)
        self.view.image_selected.connect(self.on_image_selected)
        self.view.extract_text_requested.connect(self.on_extract_text_requested)
        self.view.clear_text_requested.connect(self.on_clear_text_requested)
        self.view.copy_text_requested.connect(self.on_copy_text_requested)

    def show_view(self) -> None:
        # Displays the main application window.
        self.view.show()

    def select_image_file(self) -> None:
        # Handles the user's request to select an image file from the disk.
        file_path = self.file_service.select_image_file(self.view)
        if file_path:
            if self.file_service.is_valid_image(file_path):
                self.view.set_image(file_path)
                self.on_image_selected(file_path)
            else:
                self.view.show_warning("The selected file is not a valid image format.")

    def on_image_selected(self, image_path: str) -> None:
        # Callback for when an image is selected, either by file dialog or drag-and-drop.
        self.current_image_path = image_path
        logger.info(f"Image has been selected for processing: {image_path}")

    def on_extract_text_requested(self) -> None:
        # Initiates the text extraction process for the currently selected image.
        if not self.current_image_path:
            self.view.show_warning("Please select an image before extracting text.")
            return

        if not self.file_service.is_valid_image(self.current_image_path):
            self.view.show_error("The selected file is not a valid or existing image.")
            return

        self.view.show_progress(True)
        self.ocr_service.extract_text(
            self.current_image_path,
            success_callback=self.on_text_extracted,
            error_callback=self.on_extraction_error,
            finished_callback=self.on_extraction_finished
        )

    def on_text_extracted(self, text: str) -> None:
        # Callback for when text has been successfully extracted from an image.
        self.view.set_extracted_text(text)
        self.view.show_success("Text extraction completed successfully.")
        logger.info("Successfully extracted text from the image.")

    def on_extraction_error(self, error_message: str) -> None:
        # Callback for handling errors that occur during text extraction.
        self.view.show_error(f"An error occurred during text extraction: {error_message}")
        logger.error(f"OCR extraction process failed with error: {error_message}")

    def on_extraction_finished(self) -> None:
        # Callback for when the extraction process is finished, regardless of outcome.
        self.view.show_progress(False)
        logger.info("The OCR extraction process has finished.")

    def save_text_to_file(self) -> None:
        # Handles the user's request to save the extracted text to a file.
        text_content = self.view.get_text_content()
        if not text_content:
            self.view.show_warning("There is no text content to save.")
            return

        saved_path = self.file_service.save_text_to_file(text_content, self.view)
        if saved_path:
            self.view.show_success(f"Text was successfully saved to {saved_path}")
        else:
            self.view.show_error("The file could not be saved.")

    def on_clear_text_requested(self) -> None:
        # Handles the user's request to clear the text display area.
        self.view.clear_text()
        logger.info("The text area has been cleared.")

    def on_copy_text_requested(self) -> None:
        # Handles the user's request to copy the extracted text to the clipboard.
        text = self.view.get_text_content()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.view.set_copy_button_text("Copied ✓")
            logger.info("Extracted text has been copied to the clipboard.")
        else:
            self.view.show_warning("There is no text to copy.")

    def cleanup(self) -> None:
        # Performs necessary cleanup operations before the application exits.
        self.ocr_service.cleanup()
        logger.info("Application cleanup has been completed.")


def run_application() -> int:
    # The main entry point for running the OCR application.
    app = QApplication([])
    controller = OCRController()
    controller.show_view()

    try:
        exit_code = app.exec()
    finally:
        controller.cleanup()

    return exit_code
