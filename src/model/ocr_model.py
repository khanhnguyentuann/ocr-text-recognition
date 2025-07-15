"""
OCR Model - Handles image processing and text extraction
"""
import os
import easyocr
from PIL import Image
import cv2
import numpy as np
from typing import Optional, List


class OCRModel:
    """Model class for OCR text recognition using EasyOCR"""
    
    def __init__(self, languages: List[str] = ['en', 'vi']):
        """
        Initialize OCR model with specified languages
        
        Args:
            languages: List of language codes for OCR recognition
        """
        self.languages = languages
        self.reader = None
        self._initialize_reader()
    
    def _initialize_reader(self) -> None:
        """Initialize EasyOCR reader"""
        try:
            self.reader = easyocr.Reader(self.languages)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OCR reader: {str(e)}")
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load image from file path
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Loaded image as numpy array or None if failed
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # Load image using OpenCV
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            return image
        except Exception as e:
            raise RuntimeError(f"Error loading image: {str(e)}")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Check and correct image orientation
        height, width = image.shape[:2]
        if height > width:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply adaptive thresholding
        processed = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Noise reduction
        processed = cv2.medianBlur(processed, 3)
        
        return processed
    
    def extract_text(self, image_path: str, preprocess: bool = True) -> str:
        """
        Extract text from image using OCR
        
        Args:
            image_path: Path to the image file
            preprocess: Whether to preprocess the image
            
        Returns:
            Extracted text as string
        """
        if not self.reader:
            raise RuntimeError("OCR reader not initialized")
        
        # Load image
        image = self.load_image(image_path)
        
        # Preprocess if requested
        if preprocess:
            image = self.preprocess_image(image)
        
        try:
            # Extract text using EasyOCR
            results = self.reader.readtext(image)
            
            # Combine all detected text
            extracted_text = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Filter out low confidence results
                    extracted_text.append(text)
            
            return '\n'.join(extracted_text)
            
        except Exception as e:
            raise RuntimeError(f"Error during text extraction: {str(e)}")
    
    def get_text_with_confidence(self, image_path: str, preprocess: bool = True) -> List[tuple]:
        """
        Extract text with confidence scores and bounding boxes
        
        Args:
            image_path: Path to the image file
            preprocess: Whether to preprocess the image
            
        Returns:
            List of tuples (bbox, text, confidence)
        """
        if not self.reader:
            raise RuntimeError("OCR reader not initialized")
        
        # Load image
        image = self.load_image(image_path)
        
        # Preprocess if requested
        if preprocess:
            image = self.preprocess_image(image)
        
        try:
            # Extract text with details using EasyOCR
            results = self.reader.readtext(image)
            return results
            
        except Exception as e:
            raise RuntimeError(f"Error during text extraction: {str(e)}")
