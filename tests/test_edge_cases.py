"""
Unit tests for edge cases in the OCR application.
"""
import sys
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

# Ensure the application instance is available
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

from src.controller.ocr_controller import OCRController

@pytest.fixture
def mock_view():
    """Fixture for a mocked MainWindow."""
    return MagicMock()

@pytest.fixture
def mock_file_service():
    """Fixture for a mocked FileService."""
    service = MagicMock()
    # Default to valid image for most tests
    service.is_valid_image.return_value = True
    return service

@pytest.fixture
def mock_ocr_service():
    """Fixture for a mocked OCRService."""
    return MagicMock()

@pytest.fixture
def controller(mock_view, mock_file_service, mock_ocr_service):
    """Fixture for OCRController with mocked dependencies."""
    with patch('src.controller.ocr_controller.MainWindow', return_value=mock_view):
        with patch('src.controller.ocr_controller.FileService', return_value=mock_file_service):
            with patch('src.controller.ocr_controller.OCRService', return_value=mock_ocr_service):
                instance = OCRController()
                return instance

class TestEdgeCases:
    """Test cases for handling edge cases and invalid inputs."""

    def test_extract_text_from_non_existent_file(self, controller):
        """
        Test case: User tries to extract text from a file that does not exist.
        The application should show an error message.
        """
        image_path = "/fake/non_existent_file.png"
        controller.current_image_path = image_path
        # Simulate that the file service reports the file as invalid (e.g., not existing)
        controller.file_service.is_valid_image.return_value = False

        controller.on_extract_text_requested()

        controller.view.show_error.assert_called_once_with("The selected file is not a valid or existing image.")
        controller.ocr_service.extract_text.assert_not_called()

    def test_extract_text_from_non_image_file(self, controller):
        """
        Test case: User tries to extract text from a file that is not an image.
        The application should show a warning or error.
        """
        image_path = "/fake/my_document.txt"
        controller.current_image_path = image_path
        controller.file_service.is_valid_image.return_value = False

        controller.on_extract_text_requested()

        controller.view.show_error.assert_called_once_with("The selected file is not a valid or existing image.")
        controller.ocr_service.extract_text.assert_not_called()

    def test_extract_text_from_empty_image(self, controller):
        """
        Test case: The OCR model returns an empty string for an image.
        The application should display the empty result without errors.
        """
        image_path = "/fake/empty_image.png"
        controller.current_image_path = image_path
        controller.file_service.is_valid_image.return_value = True

        controller.on_extract_text_requested()

        # Simulate the OCR service successfully extracting an empty string
        args, kwargs = controller.ocr_service.extract_text.call_args
        success_callback = kwargs['success_callback']
        success_callback("")  # Simulate empty result

        controller.view.set_extracted_text.assert_called_once_with("")
        controller.view.show_success.assert_called_once_with("Text extraction completed successfully.")

    def test_ocr_service_returns_error(self, controller):
        """
        Test case: The OCR service encounters an internal error.
        The application should display the error message to the user.
        """
        image_path = "/fake/corrupted_image.png"
        error_message = "Internal OCR engine error"
        controller.current_image_path = image_path
        controller.file_service.is_valid_image.return_value = True

        controller.on_extract_text_requested()

        # Simulate the OCR service calling the error callback
        args, kwargs = controller.ocr_service.extract_text.call_args
        error_callback = kwargs['error_callback']
        error_callback(error_message)

        controller.view.show_error.assert_called_once_with(f"An error occurred during text extraction: {error_message}")
        controller.view.set_extracted_text.assert_not_called()
