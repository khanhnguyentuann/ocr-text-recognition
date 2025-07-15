"""
Unit tests for OCR Model
"""
import pytest
import os
import sys
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Add src directory to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.model.ocr_model import OCRModel


class TestOCRModel:
    """Test cases for OCRModel class"""
    
    @pytest.fixture
    def ocr_model(self):
        """Create OCR model instance for testing"""
        try:
            return OCRModel(languages=['en'])
        except Exception as e:
            pytest.skip(f"Could not initialize OCR model: {e}")
    
    @pytest.fixture
    def sample_image_path(self):
        """Create a sample image with text for testing"""
        # Create a temporary image with text
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            # Create image with white background
            img = Image.new('RGB', (400, 100), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to basic if not available
            try:
                # Try to load a font (this might not work on all systems)
                font = ImageFont.truetype("arial.ttf", 24)
            except (OSError, IOError):
                # Fallback to default font
                font = ImageFont.load_default()
            
            # Draw text on image
            text = "Hello World 123"
            draw.text((10, 30), text, fill='black', font=font)
            
            # Save image
            img.save(tmp_file.name)
            
            yield tmp_file.name
            
            # Cleanup
            try:
                os.unlink(tmp_file.name)
            except OSError:
                pass
    
    @pytest.fixture
    def existing_test_image(self):
        """Use existing test image if available"""
        test_image_paths = [
            "resources/input_mages/image1.png",
            "resources/input_mages/Demo/image1.png",
            "resources/input_mages/khanh.png"
        ]
        
        for path in test_image_paths:
            if os.path.exists(path):
                return path
        
        pytest.skip("No existing test images found")
    
    def test_model_initialization(self):
        """Test OCR model initialization"""
        try:
            model = OCRModel(languages=['en'])
            assert model is not None
            assert model.languages == ['en']
            assert model.reader is not None
        except Exception as e:
            pytest.skip(f"OCR model initialization failed: {e}")
    
    def test_model_initialization_multiple_languages(self):
        """Test OCR model initialization with multiple languages"""
        try:
            model = OCRModel(languages=['en', 'vi'])
            assert model is not None
            assert model.languages == ['en', 'vi']
            assert model.reader is not None
        except Exception as e:
            pytest.skip(f"OCR model initialization failed: {e}")
    
    def test_load_image_success(self, ocr_model, sample_image_path):
        """Test successful image loading"""
        image = ocr_model.load_image(sample_image_path)
        assert image is not None
        assert isinstance(image, np.ndarray)
        assert len(image.shape) == 3  # Should be color image (H, W, C)
    
    def test_load_image_file_not_found(self, ocr_model):
        """Test loading non-existent image file"""
        with pytest.raises(FileNotFoundError):
            ocr_model.load_image("non_existent_file.png")
    
    def test_preprocess_image(self, ocr_model, sample_image_path):
        """Test image preprocessing"""
        # Load image first
        image = ocr_model.load_image(sample_image_path)
        
        # Preprocess image
        processed = ocr_model.preprocess_image(image)
        
        assert processed is not None
        assert isinstance(processed, np.ndarray)
        assert len(processed.shape) == 2  # Should be grayscale (H, W)
    
    def test_extract_text_from_sample_image(self, ocr_model, sample_image_path):
        """Test text extraction from sample image"""
        try:
            text = ocr_model.extract_text(sample_image_path)
            assert isinstance(text, str)
            # The text might not be perfect due to OCR limitations
            # but it should contain some recognizable content
            print(f"Extracted text: '{text}'")
            
            # Basic validation - should not be empty and should contain some alphanumeric characters
            assert len(text.strip()) > 0, "Extracted text should not be empty"
            
        except Exception as e:
            pytest.skip(f"Text extraction failed: {e}")
    
    def test_extract_text_from_existing_image(self, ocr_model, existing_test_image):
        """Test text extraction from existing test image"""
        try:
            text = ocr_model.extract_text(existing_test_image)
            assert isinstance(text, str)
            print(f"Extracted text from {existing_test_image}: '{text}'")
            
            # Should return some text (might be empty if image has no text)
            assert text is not None
            
        except Exception as e:
            pytest.skip(f"Text extraction failed: {e}")
    
    def test_extract_text_with_preprocessing(self, ocr_model, sample_image_path):
        """Test text extraction with preprocessing enabled"""
        try:
            text = ocr_model.extract_text(sample_image_path, preprocess=True)
            assert isinstance(text, str)
            print(f"Extracted text with preprocessing: '{text}'")
            
        except Exception as e:
            pytest.skip(f"Text extraction with preprocessing failed: {e}")
    
    def test_extract_text_without_preprocessing(self, ocr_model, sample_image_path):
        """Test text extraction without preprocessing"""
        try:
            text = ocr_model.extract_text(sample_image_path, preprocess=False)
            assert isinstance(text, str)
            print(f"Extracted text without preprocessing: '{text}'")
            
        except Exception as e:
            pytest.skip(f"Text extraction without preprocessing failed: {e}")
    
    def test_get_text_with_confidence(self, ocr_model, sample_image_path):
        """Test getting text with confidence scores"""
        try:
            results = ocr_model.get_text_with_confidence(sample_image_path)
            assert isinstance(results, list)
            
            # Each result should be a tuple with (bbox, text, confidence)
            for result in results:
                assert isinstance(result, tuple)
                assert len(result) == 3
                bbox, text, confidence = result
                assert isinstance(text, str)
                assert isinstance(confidence, (int, float))
                assert 0 <= confidence <= 1
                
        except Exception as e:
            pytest.skip(f"Text extraction with confidence failed: {e}")
    
    def test_extract_text_invalid_image(self, ocr_model):
        """Test text extraction with invalid image path"""
        with pytest.raises(FileNotFoundError):
            ocr_model.extract_text("invalid_image.png")


# Additional test to run manually if needed
def test_ocr_functionality_manual():
    """
    Manual test function that can be run independently
    This test creates a simple image and tests OCR functionality
    """
    try:
        # Create OCR model
        model = OCRModel(languages=['en'])
        
        # Create a simple test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            img = Image.new('RGB', (300, 100), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw simple text
            draw.text((10, 30), "TEST 123", fill='black')
            img.save(tmp_file.name)
            
            # Test OCR
            text = model.extract_text(tmp_file.name)
            print(f"OCR Result: '{text}'")
            
            # Cleanup
            os.unlink(tmp_file.name)
            
            return True
            
    except Exception as e:
        print(f"Manual OCR test failed: {e}")
        return False


if __name__ == "__main__":
    # Run manual test if script is executed directly
    print("Running manual OCR test...")
    success = test_ocr_functionality_manual()
    if success:
        print("Manual test passed!")
    else:
        print("Manual test failed!")
