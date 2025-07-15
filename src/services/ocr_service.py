"""
OCR Service - Manages OCR model initialization and text extraction processes.

This module provides the `OCRService` class, which is responsible for handling
the OCR (Optical Character Recognition) functionalities of the application.
It initializes the OCR model and uses a worker thread (`OCRWorker`) to perform
text extraction from images, ensuring the GUI remains responsive.
"""
from typing import Callable, Optional, List
from PySide6.QtCore import QObject, QThread, Signal
from src.model.ocr_model import OCRModel
from src.services.log_service import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class OCRWorker(QThread):
    """
    A dedicated worker thread for running the OCR process.

    This `QThread` subclass offloads the time-consuming OCR task from the main
    GUI thread, preventing the application from freezing. It emits signals to
    communicate the results or any errors back to the main thread.

    Signals:
        text_extracted (str): Emitted when text is successfully extracted.
        error_occurred (str): Emitted when an error occurs during extraction.
    """
    text_extracted = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model: OCRModel, image_path: str) -> None:
        """
        Initializes the OCR worker.

        Args:
            model (OCRModel): The OCR model instance to use for extraction.
            image_path (str): The path to the image file to process.
        """
        super().__init__()
        self.model = model
        self.image_path = image_path

    def run(self) -> None:
        """
        The main execution method of the worker thread.

        This method calls the OCR model to extract text from the image. It
        handles exceptions and emits the appropriate signal upon completion.
        """
        try:
            logger.info(f"Worker starting OCR extraction for: {self.image_path}")
            text = self.model.extract_text(self.image_path)
            self.text_extracted.emit(text)
        except Exception as e:
            logger.error(f"An error occurred in OCR worker: {e}", exc_info=True)
            self.error_occurred.emit(f"Failed to process image: {e}")


class OCRService(QObject):
    """
    A service class for managing the OCR model and extraction process.

    This class acts as an interface to the OCR functionalities. It handles the
    initialization of the OCR model and manages the lifecycle of the `OCRWorker`
    thread for each extraction request.
    """
    def __init__(self, languages: Optional[List[str]] = None) -> None:
        """
        Initializes the OCR service and the underlying model.

        Args:
            languages (Optional[List[str]]): A list of language codes (e.g.,
                                             ['en', 'vi']) to be used by the
                                             OCR model. Defaults to English and
                                             Vietnamese.
        """
        super().__init__()
        if languages is None:
            languages = ['en', 'vi']
        self.model = self._initialize_model(languages)
        self.worker: Optional[OCRWorker] = None

    def _initialize_model(self, languages: List[str]) -> Optional[OCRModel]:
        """
        Initializes the OCR model with the specified languages.

        Args:
            languages (List[str]): The languages for the OCR model.

        Returns:
            Optional[OCRModel]: An instance of `OCRModel` if successful,
                                otherwise None.
        """
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
        """
        Starts the text extraction process in a non-blocking worker thread.

        This method creates and starts an `OCRWorker` to handle the extraction.
        Callbacks are connected to the worker's signals to handle the results
        asynchronously.

        Args:
            image_path (str): The path to the image file.
            success_callback (Callable[[str], None]): Callback for successful extraction.
            error_callback (Callable[[str], None]): Callback for handling errors.
            finished_callback (Callable[[], None]): Callback for when the process is finished.
        """
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
        """
        Performs cleanup by ensuring the worker thread is properly terminated.

        This should be called when the application is closing to prevent any
        lingering threads.
        """
        if self.worker and self.worker.isRunning():
            logger.info("Attempting to terminate the OCR worker thread.")
            self.worker.quit()
            self.worker.wait()  # Wait for the thread to finish gracefully
            logger.info("OCR worker thread terminated.")
