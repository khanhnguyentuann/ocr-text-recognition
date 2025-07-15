"""
Unit tests for the refactored OCR Controller and its interaction with services.
"""
import sys
import pytest
from unittest.mock import MagicMock, patch, call
from PySide6.QtWidgets import QApplication

# Ensure the application instance is available for QObject-based classes
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# Since the controller now uses services, we can import it directly
from src.controller.ocr_controller import OCRController


@pytest.fixture
def mock_view():
    """Fixture for a mocked MainWindow."""
    return MagicMock()

@pytest.fixture
def mock_file_service():
    """Fixture for a mocked FileService."""
    return MagicMock()

@pytest.fixture
def mock_ocr_service():
    """Fixture for a mocked OCRService."""
    return MagicMock()

@pytest.fixture
def controller(mock_view, mock_file_service, mock_ocr_service):
    """
    Fixture for OCRController with mocked view and services.
    This patches the dependencies of the controller, allowing it to be
    tested in isolation.
    """
    with patch('src.controller.ocr_controller.MainWindow', return_value=mock_view):
        with patch('src.controller.ocr_controller.FileService', return_value=mock_file_service):
            with patch('src.controller.ocr_controller.OCRService', return_value=mock_ocr_service):
                instance = OCRController()
                # The controller now creates its own instances, so we assert they are created
                assert instance.view is mock_view
                assert instance.file_service is mock_file_service
                assert instance.ocr_service is mock_ocr_service
                return instance

class TestOCRControllerRefactored:
    """Test cases for the refactored OCRController."""

    def test_initialization(self, controller):
        """Test that the controller initializes and connects signals correctly."""
        controller.view.open_file_requested.connect.assert_called_with(controller.select_image_file)
        controller.view.save_text_requested.connect.assert_called_with(controller.save_text_to_file)
        controller.view.extract_text_requested.connect.assert_called_with(controller.on_extract_text_requested)
        controller.view.clear_text_requested.connect.assert_called_with(controller.on_clear_text_requested)
        controller.view.copy_text_requested.connect.assert_called_with(controller.on_copy_text_requested)

    def test_select_image_file_success(self, controller):
        """Test selecting a valid image file."""
        file_path = "/fake/valid_image.png"
        controller.file_service.select_image_file.return_value = file_path
        controller.file_service.is_valid_image.return_value = True

        controller.select_image_file()

        controller.file_service.select_image_file.assert_called_once_with(controller.view)
        controller.file_service.is_valid_image.assert_called_once_with(file_path)
        controller.view.set_image.assert_called_once_with(file_path)
        assert controller.current_image_path == file_path

    def test_select_image_file_invalid_type(self, controller):
        """Test selecting a file that is not a valid image."""
        file_path = "/fake/document.txt"
        controller.file_service.select_image_file.return_value = file_path
        controller.file_service.is_valid_image.return_value = False

        controller.select_image_file()

        controller.file_service.is_valid_image.assert_called_once_with(file_path)
        controller.view.show_warning.assert_called_once_with("The selected file is not a valid image format.")
        controller.view.set_image.assert_not_called()

    def test_select_image_file_cancelled(self, controller):
        """Test cancelling the file selection dialog."""
        controller.file_service.select_image_file.return_value = None
        controller.select_image_file()
        controller.file_service.is_valid_image.assert_not_called()
        controller.view.set_image.assert_not_called()

    def test_on_extract_text_no_image(self, controller):
        """Test extract text request when no image is selected."""
        controller.current_image_path = None
        controller.on_extract_text_requested()
        controller.view.show_warning.assert_called_with("Please select an image before extracting text.")
        controller.ocr_service.extract_text.assert_not_called()

    def test_on_extract_text_file_not_exists(self, controller):
        """Test extract text when the file path is invalid."""
        image_path = "/fake/non_existent_image.png"
        controller.current_image_path = image_path
        controller.file_service.is_valid_image.return_value = False

        controller.on_extract_text_requested()

        controller.file_service.is_valid_image.assert_called_with(image_path)
        controller.view.show_error.assert_called_with("The selected file is not a valid or existing image.")
        controller.ocr_service.extract_text.assert_not_called()

    def test_on_extract_text_success(self, controller):
        """Test a successful text extraction flow."""
        image_path = "/fake/image.png"
        controller.current_image_path = image_path
        controller.file_service.is_valid_image.return_value = True

        controller.on_extract_text_requested()

        controller.view.show_progress.assert_called_once_with(True)
        controller.ocr_service.extract_text.assert_called_once()
        
        # Simulate the success callback from the service
        args, kwargs = controller.ocr_service.extract_text.call_args
        success_callback = kwargs['success_callback']
        success_callback("extracted text")

        controller.view.set_extracted_text.assert_called_with("extracted text")
        controller.view.show_success.assert_called_with("Text extraction completed successfully.")

    def test_on_extraction_error(self, controller):
        """Test the error handling during text extraction."""
        error_msg = "OCR engine failed"
        controller.on_extraction_error(error_msg)
        controller.view.show_error.assert_called_with(f"An error occurred during text extraction: {error_msg}")

    def test_on_extraction_finished(self, controller):
        """Test that progress is hidden when extraction finishes."""
        controller.on_extraction_finished()
        controller.view.show_progress.assert_called_with(False)

    def test_save_text_to_file_no_text(self, controller):
        """Test saving when there is no text content."""
        controller.view.get_text_content.return_value = ""
        controller.save_text_to_file()
        controller.view.show_warning.assert_called_with("There is no text content to save.")
        controller.file_service.save_text_to_file.assert_not_called()

    def test_save_text_to_file_success(self, controller):
        """Test successful text saving via the file service."""
        text_content = "some important text"
        saved_path = "/fake/saved.txt"
        controller.view.get_text_content.return_value = text_content
        controller.file_service.save_text_to_file.return_value = saved_path

        controller.save_text_to_file()

        controller.file_service.save_text_to_file.assert_called_once_with(text_content, controller.view)
        controller.view.show_success.assert_called_once_with(f"Text was successfully saved to {saved_path}")

    def test_save_text_to_file_failure(self, controller):
        """Test failed text saving."""
        text_content = "some important text"
        controller.view.get_text_content.return_value = text_content
        controller.file_service.save_text_to_file.return_value = None

        controller.save_text_to_file()

        controller.view.show_error.assert_called_once_with("The file could not be saved.")

    def test_on_copy_text_no_text(self, controller):
        """Test copying when there is no text."""
        controller.view.get_text_content.return_value = ""
        controller.on_copy_text_requested()
        controller.view.show_warning.assert_called_with("There is no text to copy.")

    @patch('src.controller.ocr_controller.QApplication.clipboard')
    def test_on_copy_text_success(self, mock_clipboard, controller):
        """Test successful copying of text."""
        clipboard_instance = mock_clipboard.return_value
        text_to_copy = "text to be copied"
        controller.view.get_text_content.return_value = text_to_copy

        controller.on_copy_text_requested()

        clipboard_instance.setText.assert_called_with(text_to_copy)
        controller.view.set_copy_button_text.assert_called_with("Copied ✓")

    def test_cleanup(self, controller):
        """Test that the cleanup method on the ocr_service is called."""
        controller.cleanup()
        controller.ocr_service.cleanup.assert_called_once()
