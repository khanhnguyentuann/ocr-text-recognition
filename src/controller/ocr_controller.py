# OCR Controller - Orchestrates the application flow by connecting services to the view.
from typing import Optional
import pandas as pd
import cv2
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from src.view.main_window import MainWindow
from src.services.file_service import FileService
from src.services.ocr_service import OCRService
from src.services.table_ocr_service import TableOCRService
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
        self.table_ocr_service: TableOCRService = TableOCRService()
        self.current_image_path: Optional[str] = None
        self.current_table_data: Optional[pd.DataFrame] = None
        self.current_metadata: dict = {}
        self.connect_signals()

    def connect_signals(self) -> None:
        # Connects signals from the view to the controller's handler methods.
        self.view.open_file_requested.connect(self.select_image_file)
        self.view.save_text_requested.connect(self.save_text_to_file)
        self.view.image_selected.connect(self.on_image_selected)
        self.view.extract_text_requested.connect(self.on_extract_text_requested)
        self.view.extract_table_requested.connect(self.on_extract_table_requested)
        self.view.clear_text_requested.connect(self.on_clear_text_requested)
        self.view.copy_text_requested.connect(self.on_copy_text_requested)
        self.view.copy_table_requested.connect(self.on_copy_table_requested)
        self.view.export_csv_requested.connect(self.on_export_csv_requested)
        self.view.export_json_requested.connect(self.on_export_json_requested)
        self.view.export_excel_requested.connect(self.on_export_excel_requested)
        self.view.capture_webcam_requested.connect(self.on_capture_webcam_requested)

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

    def on_extract_table_requested(self) -> None:
        """Initiates the table extraction process for the currently selected image."""
        if not self.current_image_path:
            self.view.show_warning("Please select an image before extracting table.")
            return

        if not self.file_service.is_valid_image(self.current_image_path):
            self.view.show_error("The selected file is not a valid or existing image.")
            return

        try:
            self.view.show_progress(True)
            
            # Load image
            image = cv2.imread(self.current_image_path)
            if image is None:
                self.view.show_error("Failed to load the image.")
                return
            
            # Extract table data
            self.current_table_data = self.table_ocr_service.extract_table_data(image)
            
            # Extract metadata
            self.current_metadata = self.table_ocr_service.detect_metadata(image)
            
            # Update UI
            self.view.set_table_data(self.current_table_data)
            self.view.set_metadata(self.current_metadata)
            
            if not self.current_table_data.empty:
                self.view.show_success(f"Table extraction completed successfully. Found {len(self.current_table_data)} rows and {len(self.current_table_data.columns)} columns.")
            else:
                self.view.show_warning("No table data was detected in the image.")
            
            logger.info("Successfully extracted table from the image.")
            
        except Exception as e:
            self.view.show_error(f"An error occurred during table extraction: {str(e)}")
            logger.error(f"Table extraction process failed with error: {e}")
        finally:
            self.view.show_progress(False)

    def on_copy_table_requested(self) -> None:
        """Handles the user's request to copy the table to clipboard."""
        if self.current_table_data is None or self.current_table_data.empty:
            self.view.show_warning("There is no table data to copy.")
            return

        try:
            # Convert to tab-separated format
            clipboard_text = self.table_ocr_service.dataframe_to_clipboard_format(self.current_table_data)
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(clipboard_text)
            
            self.view.show_success("Table data copied to clipboard in tab-separated format.")
            logger.info("Table data has been copied to the clipboard.")
            
        except Exception as e:
            self.view.show_error(f"Failed to copy table data: {str(e)}")
            logger.error(f"Error copying table data: {e}")

    def on_export_csv_requested(self) -> None:
        """Handles the user's request to export table data to CSV."""
        if self.current_table_data is None or self.current_table_data.empty:
            self.view.show_warning("There is no table data to export.")
            return

        file_path = self.file_service.save_csv_file(self.view)
        if file_path:
            if self.table_ocr_service.export_to_csv(self.current_table_data, file_path):
                self.view.show_success(f"Table data successfully exported to {file_path}")
            else:
                self.view.show_error("Failed to export CSV file.")

    def on_export_json_requested(self) -> None:
        """Handles the user's request to export table data to JSON."""
        if self.current_table_data is None or self.current_table_data.empty:
            self.view.show_warning("There is no table data to export.")
            return

        file_path = self.file_service.save_json_file(self.view)
        if file_path:
            if self.table_ocr_service.export_to_json(self.current_table_data, file_path):
                self.view.show_success(f"Table data successfully exported to {file_path}")
            else:
                self.view.show_error("Failed to export JSON file.")

    def on_export_excel_requested(self) -> None:
        """Handles the user's request to export table data to Excel."""
        if self.current_table_data is None or self.current_table_data.empty:
            self.view.show_warning("There is no table data to export.")
            return

        file_path = self.file_service.save_excel_file(self.view)
        if file_path:
            if self.table_ocr_service.export_to_excel(self.current_table_data, file_path, self.current_metadata):
                self.view.show_success(f"Table data successfully exported to {file_path}")
            else:
                self.view.show_error("Failed to export Excel file.")

    def on_capture_webcam_requested(self) -> None:
        """Handles the user's request to capture from webcam."""
        try:
            # Initialize webcam
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.view.show_error("Could not access webcam.")
                return

            # Capture frame
            ret, frame = cap.read()
            cap.release()

            if not ret:
                self.view.show_error("Failed to capture image from webcam.")
                return

            # Save temporary image
            import tempfile
            import os
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, "webcam_capture.jpg")
            cv2.imwrite(temp_path, frame)

            # Set as current image
            self.view.set_image(temp_path)
            self.on_image_selected(temp_path)
            
            self.view.show_success("Webcam image captured successfully.")
            logger.info("Successfully captured image from webcam.")

        except Exception as e:
            self.view.show_error(f"Error capturing from webcam: {str(e)}")
            logger.error(f"Webcam capture failed: {e}")

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
