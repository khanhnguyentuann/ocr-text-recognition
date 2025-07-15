"""
Unit tests for OCR Controller
"""
from src.controller.ocr_controller import OCRController
import pytest
import os
import sys
from unittest.mock import MagicMock, patch

# Add src and resources directories to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'resources'))


@pytest.fixture
def mock_view():
    """Fixture for a mocked MainWindow."""
    return MagicMock()


@pytest.fixture
def mock_model():
    """Fixture for a mocked OCRModel."""
    model = MagicMock()
    model.extract_text.return_value = "mocked text"
    return model


@pytest.fixture
def controller(mock_view, mock_model):
    """Fixture for OCRController with mocked view and model."""
    with patch('src.controller.ocr_controller.MainWindow', return_value=mock_view):
        with patch('src.controller.ocr_controller.OCRModel', return_value=mock_model):
            # The QObject.__init__ needs to be called within a QApplication instance
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            instance = OCRController()
            instance.view = mock_view
            instance.model = mock_model
            return instance


class TestOCRController:
    """Test cases for OCRController class"""

    def test_initialization(self, controller, mock_view, mock_model):
        """Test controller initialization."""
        assert controller.view is not None
        assert controller.model is not None
        # Check that signals were connected
        mock_view.open_file_requested.connect.assert_called_with(
            controller.select_image_file)
        mock_view.save_text_requested.connect.assert_called_with(
            controller.save_text_to_file)
        mock_view.extract_text_requested.connect.assert_called_with(
            controller.on_extract_text_requested)

    def test_on_image_selected(self, controller):
        """Test the on_image_selected method."""
        image_path = "/fake/path/to/image.png"
        controller.on_image_selected(image_path)
        assert controller.current_image_path == image_path

    def test_on_extract_text_requested_no_image(self, controller):
        """Test extract text request when no image is selected."""
        controller.current_image_path = None
        controller.on_extract_text_requested()
        controller.view.show_warning.assert_called_with(
            "Please select an image first!")

    @patch('src.controller.ocr_controller.os.path.exists', return_value=True)
    @patch('src.controller.ocr_controller.OCRWorker')
    def test_on_extract_text_requested_success(self, mock_worker, mock_exists, controller):
        """Test a successful text extraction request."""
        controller.current_image_path = "/fake/path/to/image.png"
        controller.on_extract_text_requested()

        # Check that the worker was created and started
        mock_worker.assert_called_with(
            controller.model, controller.current_image_path)
        worker_instance = mock_worker.return_value
        worker_instance.start.assert_called_once()

        # Manually call the slots to simulate the worker's signals
        controller.on_text_extracted("mocked text")
        controller.on_extraction_finished()

        # Assertions
        controller.view.show_progress.assert_any_call(True)
        controller.view.set_extracted_text.assert_called_with("mocked text")
        controller.view.show_success.assert_called_with(
            "Text extracted successfully!")
        controller.view.show_progress.assert_called_with(False)

    @patch('src.controller.ocr_controller.os.path.exists', return_value=True)
    @patch('src.controller.ocr_controller.OCRWorker')
    def test_on_extract_text_requested_error(self, mock_worker, mock_exists, controller):
        """Test a failed text extraction request."""
        controller.current_image_path = "/fake/path/to/image.png"
        error_message = "OCR failed"

        controller.on_extract_text_requested()

        # Check that the worker was created and started
        mock_worker.assert_called_with(
            controller.model, controller.current_image_path)
        worker_instance = mock_worker.return_value
        worker_instance.start.assert_called_once()

        # Manually call the slots to simulate the worker's signals
        controller.on_extraction_error(error_message)
        controller.on_extraction_finished()

        # Assertions
        controller.view.show_progress.assert_any_call(True)
        controller.view.show_error.assert_called_with(
            f"Error during text extraction: {error_message}")
        controller.view.show_progress.assert_called_with(False)

    def test_save_text_to_file_no_text(self, controller):
        """Test saving when there is no text."""
        controller.view.get_text_content.return_value = ""
        controller.save_text_to_file()
        controller.view.show_warning.assert_called_with("Nothing to save!")

    @patch('src.controller.ocr_controller.QFileDialog')
    @patch('builtins.open')
    def test_save_text_to_file_success(self, mock_open, mock_file_dialog, controller):
        """Test successful text saving."""
        controller.view.get_text_content.return_value = "some text"
        mock_file_dialog.return_value.getSaveFileName.return_value = (
            "/fake/path/save.txt", "Text Files (*.txt)")

        controller.save_text_to_file()

        mock_open.assert_called_with(
            "/fake/path/save.txt", 'w', encoding='utf-8')
        controller.view.show_success.assert_called_with(
            "Text saved successfully to /fake/path/save.txt")

    def test_on_copy_text_requested_success(self, controller):
        """Test copying text to clipboard."""
        with patch('src.controller.ocr_controller.QApplication.clipboard') as mock_clipboard:
            clipboard_instance = mock_clipboard.return_value
            controller.view.get_text_content.return_value = "text to copy"

            controller.on_copy_text_requested()

            clipboard_instance.setText.assert_called_with("text to copy")
            controller.view.set_copy_button_text.assert_called_with("Copied ✓")

    def test_on_copy_text_requested_no_text(self, controller):
        """Test copying when there is no text."""
        controller.view.get_text_content.return_value = ""
        controller.on_copy_text_requested()
        controller.view.show_warning.assert_called_with("Nothing to copy!")
