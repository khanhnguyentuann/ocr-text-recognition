# OCR Service - Manages OCR model initialization and text extraction processes.
from typing import Callable, Optional, List
from PySide6.QtCore import QObject, QThread, Signal
from src.model.ocr_model import OCRModel
from src.services.log_service import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class OCRWorker(QThread):
    # A dedicated worker thread for running the OCR process.
    text_extracted = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model: OCRModel, image_path: str) -> None:
        # Initializes the OCR worker.
        super().__init__()
        self.model = model
        self.image_path = image_path

    def run(self) -> None:
        # The main execution method of the worker thread.
        try:
            logger.info(f"Worker starting OCR extraction for: {self.image_path}")
            text = self.model.extract_text(self.image_path)
            self.text_extracted.emit(text)
        except Exception as e:
            logger.error(f"An error occurred in OCR worker: {e}", exc_info=True)
            self.error_occurred.emit(f"Failed to process image: {e}")


class OCRService(QObject):
    # A service class for managing the OCR model and extraction process.
    def __init__(self, languages: Optional[List[str]] = None) -> None:
        # Initializes the OCR service and the underlying model.
        super().__init__()
        if languages is None:
            languages = ['en', 'vi']
        self.model = self._initialize_model(languages)
        self.worker: Optional[OCRWorker] = None

    def _initialize_model(self, languages: List[str]) -> Optional[OCRModel]:
        # Initializes the OCR model with the specified languages.
        try:
            logger.info(f"Initializing OCR model with languages: {languages}")
            model = OCRModel(languages=languages)
            logger.info("OCR model initialized successfully.")
            return model
        except Exception as e:
            logger.error(f"Failed to initialize OCR model: {e}", exc_info=True)
            return None

    def extract_text(
        self,
        image_path: str,
        success_callback: Callable[[str], None],
        error_callback: Callable[[str], None],
        finished_callback: Callable[[], None]
    ) -> None:
        # Starts the text extraction process in a non-blocking worker thread.
        if not self.model:
            error_message = "OCR model is not initialized. Cannot extract text."
            logger.error(error_message)
            error_callback(error_message)
            return

        self.worker = OCRWorker(self.model, image_path)
        self.worker.text_extracted.connect(success_callback)
        self.worker.error_occurred.connect(error_callback)
        self.worker.finished.connect(finished_callback)
        self.worker.start()

    def cleanup(self) -> None:
        # Performs cleanup by ensuring the worker thread is properly terminated.
        if self.worker and self.worker.isRunning():
            logger.info("Attempting to terminate the OCR worker thread.")
            self.worker.quit()
            self.worker.wait()  # Wait for the thread to finish gracefully
            logger.info("OCR worker thread terminated.")
