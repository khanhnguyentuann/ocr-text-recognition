"""
OCR Controller - Connects GUI signals to model, controls application flow
"""
import os
import logging
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QApplication, QFileDialog
from src.model.ocr_model import OCRModel
from src.view.main_window import MainWindow

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class OCRWorker(QThread):
    """Worker thread for OCR processing to avoid blocking UI"""

    text_extracted = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model: OCRModel, image_path: str):
        super().__init__()
        self.model = model
        self.image_path = image_path

    def run(self):
        """Run OCR extraction in separate thread"""
        try:
            text = self.model.extract_text(self.image_path)
            self.text_extracted.emit(text)
        except Exception as e:
            self.error_occurred.emit(str(e))


class OCRController(QObject):
    """Controller class that manages the interaction between Model and View"""

    def __init__(self):
        super().__init__()
        self.model = None
        self.view = None
        self.worker = None
        self.current_image_path = None

        # Initialize model
        self.initialize_model()

        # Initialize view
        self.initialize_view()

        # Connect signals
        self.connect_signals()

    def select_image_file(self):
        """Open file dialog to select image."""
        file_dialog = QFileDialog(self.view)
        file_path, _ = file_dialog.getOpenFileName(
            self.view,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )

        if file_path:
            self.view.set_image(file_path)
            self.on_image_selected(file_path)

    def initialize_model(self):
        """Initialize the OCR model"""
        try:
            self.model = OCRModel(languages=['en', 'vi'])
        except Exception as e:
            # If model initialization fails, we'll handle it gracefully
            print(f"Warning: Failed to initialize OCR model: {e}")
            self.model = None

    def initialize_view(self):
        """Initialize the main window view"""
        self.view = MainWindow()

    def connect_signals(self):
        """Connect view signals to controller methods"""
        if self.view:
            # File operations
            self.view.open_file_requested.connect(self.select_image_file)
            self.view.save_text_requested.connect(self.save_text_to_file)

            # OCR operations
            self.view.image_selected.connect(self.on_image_selected)
            self.view.extract_text_requested.connect(
                self.on_extract_text_requested)

            # Text management
            self.view.clear_text_requested.connect(
                self.on_clear_text_requested)
            self.view.copy_text_requested.connect(self.on_copy_text_requested)

    def show_view(self):
        """Show the main window"""
        if self.view:
            self.view.show()

    def on_image_selected(self, image_path: str):
        """Handle image selection"""
        self.current_image_path = image_path
        logging.info(f"Image selected: {image_path}")

    def on_extract_text_requested(self):
        """Handle text extraction request"""
        if not self.model:
            logging.error("OCR model not initialized.")
            self.view.show_error(
                "OCR model not initialized. Please check your installation.")
            return

        if not self.current_image_path:
            self.view.show_warning("Please select an image first!")
            return

        if not os.path.exists(self.current_image_path):
            logging.error(f"Image file not found at {self.current_image_path}")
            self.view.show_error("Selected image file does not exist!")
            return

        # Show progress
        self.view.show_progress(True)

        # Start OCR processing in worker thread
        self.worker = OCRWorker(self.model, self.current_image_path)
        self.worker.text_extracted.connect(self.on_text_extracted)
        self.worker.error_occurred.connect(self.on_extraction_error)
        self.worker.finished.connect(self.on_extraction_finished)
        self.worker.start()

    def on_text_extracted(self, text: str):
        """Handle successful text extraction"""
        self.view.set_extracted_text(text)
        logging.info("Text extracted successfully.")
        self.view.show_success("Text extracted successfully!")

    def on_extraction_error(self, error_message: str):
        """Handle extraction error"""
        logging.error(f"OCR extraction failed: {error_message}")
        self.view.show_error(f"Error during text extraction: {error_message}")

    def on_extraction_finished(self):
        """Handle extraction completion (success or failure)"""
        self.view.show_progress(False)
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def save_text_to_file(self):
        """Handle save text request"""
        text_content = self.view.get_text_content()
        if not text_content:
            self.view.show_warning("Nothing to save!")
            return

        file_dialog = QFileDialog(self.view)
        file_path, _ = file_dialog.getSaveFileName(
            self.view,
            "Save Text",
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(text_content)
                logging.info(f"Text saved to {file_path}")
                self.view.show_success(
                    f"Text saved successfully to {file_path}")
            except IOError as e:
                logging.error(f"File save error: {e}")
                self.view.show_error(f"Error saving file: {str(e)}")

    def on_clear_text_requested(self):
        """Handle clear text request"""
        self.view.clear_text()

    def on_copy_text_requested(self):
        """Handle copy text request"""
        text = self.view.get_text_content()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.view.set_copy_button_text("Copied ✓")
            logging.info("Text copied to clipboard.")
        else:
            self.view.show_warning("Nothing to copy!")

    def cleanup(self):
        """Cleanup resources"""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()


def run_application():
    """Main function to run the OCR application"""
    app = QApplication([])

    # Apply stylesheet if available
    try:
        if os.path.exists("style.qss"):
            with open("style.qss", "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Warning: Could not load stylesheet: {e}")

    # Create and run controller
    controller = OCRController()
    controller.show_view()

    # Run application
    try:
        exit_code = app.exec()
    finally:
        controller.cleanup()

    return exit_code
