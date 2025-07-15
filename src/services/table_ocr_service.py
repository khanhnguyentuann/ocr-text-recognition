"""
Table OCR Service - Handles table detection, OCR processing, and data structuring
"""
import cv2
import numpy as np
import pandas as pd
import pytesseract
import easyocr
from typing import List, Dict, Tuple, Optional, Any
from PIL import Image
import re
from src.services.log_service import get_logger

logger = get_logger(__name__)


class TableOCRService:
    """Service for detecting and processing tables in images"""
    
    def __init__(self):
        """Initialize the table OCR service"""
        self.confidence_threshold = 0.5
        self.min_table_area = 1000
        self.easyocr_reader = None
        self._initialize_easyocr()
    
    def _initialize_easyocr(self):
        """Initialize EasyOCR reader as fallback"""
        try:
            self.easyocr_reader = easyocr.Reader(['en', 'vi'])
            logger.info("EasyOCR reader initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize EasyOCR reader: {e}")
            self.easyocr_reader = None
        
    def preprocess_image_for_table(self, image: np.ndarray) -> np.ndarray:
        """
        Enhanced preprocessing specifically for table detection
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image optimized for table detection
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding for better binarization
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up the image
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # Deskew the image
        deskewed = self._deskew_image(cleaned)
        
        # Sharpen the image
        sharpened = self._sharpen_image(deskewed)
        
        return sharpened
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """
        Correct skew in the image
        
        Args:
            image: Binary image
            
        Returns:
            Deskewed image
        """
        # Find contours
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return image
            
        # Find the largest contour (likely the table)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Get minimum area rectangle
        rect = cv2.minAreaRect(largest_contour)
        angle = rect[2]
        
        # Correct the angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        # Only apply rotation if angle is significant
        if abs(angle) > 0.5:
            h, w = image.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return rotated
            
        return image
    
    def _sharpen_image(self, image: np.ndarray) -> np.ndarray:
        """
        Apply sharpening filter to enhance text clarity
        
        Args:
            image: Input image
            
        Returns:
            Sharpened image
        """
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(image, -1, kernel)
        return sharpened
    
    def detect_table_structure(self, image: np.ndarray) -> Tuple[List[int], List[int]]:
        """
        Detect table structure by finding horizontal and vertical lines
        
        Args:
            image: Preprocessed binary image
            
        Returns:
            Tuple of (horizontal_lines, vertical_lines) positions
        """
        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Detect vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, vertical_kernel)
        
        # Find line positions
        h_lines = self._find_line_positions(horizontal_lines, axis=0)  # horizontal
        v_lines = self._find_line_positions(vertical_lines, axis=1)    # vertical
        
        return h_lines, v_lines
    
    def _find_line_positions(self, line_image: np.ndarray, axis: int) -> List[int]:
        """
        Find positions of lines in the image
        
        Args:
            line_image: Binary image with detected lines
            axis: 0 for horizontal lines, 1 for vertical lines
            
        Returns:
            List of line positions
        """
        if axis == 0:  # horizontal lines
            projection = np.sum(line_image, axis=1)
        else:  # vertical lines
            projection = np.sum(line_image, axis=0)
            
        # Find peaks in projection
        lines = []
        threshold = np.max(projection) * 0.3
        
        for i, value in enumerate(projection):
            if value > threshold:
                lines.append(i)
                
        # Merge nearby lines
        merged_lines = []
        if lines:
            current_line = lines[0]
            for line in lines[1:]:
                if line - current_line > 10:  # minimum distance between lines
                    merged_lines.append(current_line)
                    current_line = line
                else:
                    current_line = (current_line + line) // 2
            merged_lines.append(current_line)
            
        return sorted(merged_lines)
    
    def extract_table_data(self, image: np.ndarray) -> pd.DataFrame:
        """
        Extract table data from image using OCR
        
        Args:
            image: Input image
            
        Returns:
            DataFrame containing the extracted table data
        """
        try:
            # Preprocess image
            processed_image = self.preprocess_image_for_table(image)
            
            # Try to use pytesseract first, fallback to EasyOCR if not available
            try:
                # Use pytesseract to get detailed OCR data
                ocr_data = pytesseract.image_to_data(
                    processed_image, 
                    output_type=pytesseract.Output.DICT,
                    config='--psm 6'  # Assume uniform block of text
                )
                
                # Group text by lines and positions
                table_data = self._group_text_into_table(ocr_data)
                
            except Exception as tesseract_error:
                logger.warning(f"Tesseract not available, falling back to EasyOCR: {tesseract_error}")
                # Fallback to EasyOCR-based table extraction
                table_data = self._extract_table_with_easyocr(processed_image)
            
            # Convert to DataFrame
            df = self._create_dataframe_from_table_data(table_data)
            
            logger.info(f"Successfully extracted table with {len(df)} rows and {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            # Return empty DataFrame on error
            return pd.DataFrame()
    
    def _group_text_into_table(self, ocr_data: Dict) -> List[List[str]]:
        """
        Group OCR text data into table structure
        
        Args:
            ocr_data: OCR data from pytesseract
            
        Returns:
            2D list representing table structure
        """
        # Filter out low confidence text
        filtered_data = []
        for i in range(len(ocr_data['text'])):
            if int(ocr_data['conf'][i]) > 30 and ocr_data['text'][i].strip():
                filtered_data.append({
                    'text': ocr_data['text'][i].strip(),
                    'left': ocr_data['left'][i],
                    'top': ocr_data['top'][i],
                    'width': ocr_data['width'][i],
                    'height': ocr_data['height'][i]
                })
        
        if not filtered_data:
            return []
        
        # Sort by vertical position (top) first, then horizontal (left)
        filtered_data.sort(key=lambda x: (x['top'], x['left']))
        
        # Group into rows based on vertical position
        rows = []
        current_row = []
        current_top = filtered_data[0]['top']
        row_height_threshold = 20  # pixels
        
        for item in filtered_data:
            if abs(item['top'] - current_top) <= row_height_threshold:
                current_row.append(item)
            else:
                if current_row:
                    # Sort current row by horizontal position
                    current_row.sort(key=lambda x: x['left'])
                    rows.append([item['text'] for item in current_row])
                current_row = [item]
                current_top = item['top']
        
        # Add the last row
        if current_row:
            current_row.sort(key=lambda x: x['left'])
            rows.append([item['text'] for item in current_row])
        
        return rows
    
    def _create_dataframe_from_table_data(self, table_data: List[List[str]]) -> pd.DataFrame:
        """
        Create DataFrame from table data
        
        Args:
            table_data: 2D list of table data
            
        Returns:
            DataFrame with proper structure
        """
        if not table_data:
            return pd.DataFrame()
        
        # Find the maximum number of columns
        max_cols = max(len(row) for row in table_data) if table_data else 0
        
        # Pad rows to have the same number of columns
        padded_data = []
        for row in table_data:
            padded_row = row + [''] * (max_cols - len(row))
            padded_data.append(padded_row)
        
        # Create DataFrame
        if padded_data:
            # Use first row as headers if it looks like headers
            if len(padded_data) > 1 and self._is_header_row(padded_data[0]):
                df = pd.DataFrame(padded_data[1:], columns=padded_data[0])
            else:
                # Generate column names
                columns = [f'Column_{i+1}' for i in range(max_cols)]
                df = pd.DataFrame(padded_data, columns=columns)
        else:
            df = pd.DataFrame()
        
        return df
    
    def _is_header_row(self, row: List[str]) -> bool:
        """
        Determine if a row is likely a header row
        
        Args:
            row: List of strings representing a row
            
        Returns:
            True if row is likely a header
        """
        # Simple heuristic: if most cells contain text (not numbers)
        text_count = 0
        for cell in row:
            if cell and not self._is_numeric(cell):
                text_count += 1
        
        return text_count > len(row) / 2
    
    def _is_numeric(self, text: str) -> bool:
        """
        Check if text represents a number
        
        Args:
            text: Text to check
            
        Returns:
            True if text is numeric
        """
        try:
            float(text.replace(',', '').replace('%', ''))
            return True
        except ValueError:
            return False
    
    def _extract_table_with_easyocr(self, image: np.ndarray) -> List[List[str]]:
        """
        Extract table data using EasyOCR as fallback
        
        Args:
            image: Preprocessed image
            
        Returns:
            2D list representing table structure
        """
        if not self.easyocr_reader:
            logger.warning("EasyOCR reader not available")
            return []
        
        try:
            # Use EasyOCR to get text with bounding boxes
            results = self.easyocr_reader.readtext(image)
            
            # Convert EasyOCR results to similar format as Tesseract
            filtered_data = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5 and text.strip():
                    # Extract bounding box coordinates
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    left = int(min(x_coords))
                    top = int(min(y_coords))
                    width = int(max(x_coords) - min(x_coords))
                    height = int(max(y_coords) - min(y_coords))
                    
                    filtered_data.append({
                        'text': text.strip(),
                        'left': left,
                        'top': top,
                        'width': width,
                        'height': height
                    })
            
            if not filtered_data:
                return []
            
            # Sort by vertical position (top) first, then horizontal (left)
            filtered_data.sort(key=lambda x: (x['top'], x['left']))
            
            # Group into rows based on vertical position
            rows = []
            current_row = []
            current_top = filtered_data[0]['top']
            row_height_threshold = 30  # pixels - slightly larger for EasyOCR
            
            for item in filtered_data:
                if abs(item['top'] - current_top) <= row_height_threshold:
                    current_row.append(item)
                else:
                    if current_row:
                        # Sort current row by horizontal position
                        current_row.sort(key=lambda x: x['left'])
                        rows.append([item['text'] for item in current_row])
                    current_row = [item]
                    current_top = item['top']
            
            # Add the last row
            if current_row:
                current_row.sort(key=lambda x: x['left'])
                rows.append([item['text'] for item in current_row])
            
            return rows
            
        except Exception as e:
            logger.error(f"Error in EasyOCR table extraction: {e}")
            return []

    def detect_metadata(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect metadata from the image (student names, class, etc.)
        
        Args:
            image: Input image
            
        Returns:
            Dictionary containing detected metadata
        """
        metadata = {}
        
        try:
            # Try Tesseract first, fallback to EasyOCR
            try:
                text = pytesseract.image_to_string(image, lang='vie+eng')
            except Exception as tesseract_error:
                logger.warning(f"Tesseract not available for metadata, using EasyOCR: {tesseract_error}")
                if self.easyocr_reader:
                    results = self.easyocr_reader.readtext(image)
                    text = ' '.join([result[1] for result in results if result[2] > 0.5])
                else:
                    logger.error("No OCR engine available for metadata detection")
                    return metadata
            
            # Look for common patterns
            patterns = {
                'student_name': [
                    r'(?:Tên|Họ tên|Name)[\s:]*([^\n\r]+)',
                    r'(?:Học sinh|Student)[\s:]*([^\n\r]+)'
                ],
                'class': [
                    r'(?:Lớp|Class)[\s:]*([^\n\r]+)',
                    r'(?:Khối|Grade)[\s:]*([^\n\r]+)'
                ],
                'school': [
                    r'(?:Trường|School)[\s:]*([^\n\r]+)'
                ],
                'subject': [
                    r'(?:Môn|Subject)[\s:]*([^\n\r]+)'
                ],
                'semester': [
                    r'(?:Học kỳ|Semester)[\s:]*([^\n\r]+)'
                ],
                'year': [
                    r'(?:Năm học|Academic year)[\s:]*([^\n\r]+)'
                ]
            }
            
            for key, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        metadata[key] = match.group(1).strip()
                        break
            
            logger.info(f"Detected metadata: {metadata}")
            
        except Exception as e:
            logger.error(f"Error detecting metadata: {e}")
        
        return metadata
    
    def export_to_csv(self, df: pd.DataFrame, file_path: str) -> bool:
        """
        Export DataFrame to CSV file
        
        Args:
            df: DataFrame to export
            file_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            logger.info(f"Successfully exported to CSV: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def export_to_json(self, df: pd.DataFrame, file_path: str) -> bool:
        """
        Export DataFrame to JSON file
        
        Args:
            df: DataFrame to export
            file_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            df.to_json(file_path, orient='records', indent=2, force_ascii=False)
            logger.info(f"Successfully exported to JSON: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False
    
    def export_to_excel(self, df: pd.DataFrame, file_path: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Export DataFrame to Excel file with optional metadata
        
        Args:
            df: DataFrame to export
            file_path: Output file path
            metadata: Optional metadata to include
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Write main data
                df.to_excel(writer, sheet_name='Table Data', index=False)
                
                # Write metadata if available
                if metadata:
                    metadata_df = pd.DataFrame(list(metadata.items()), columns=['Field', 'Value'])
                    metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            logger.info(f"Successfully exported to Excel: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False
    
    def dataframe_to_clipboard_format(self, df: pd.DataFrame) -> str:
        """
        Convert DataFrame to tab-separated format for clipboard
        
        Args:
            df: DataFrame to convert
            
        Returns:
            Tab-separated string
        """
        return df.to_csv(sep='\t', index=False)
