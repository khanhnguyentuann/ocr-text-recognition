"""
Enhanced Table OCR Service - Advanced table detection with clustering and cell segmentation
"""
import cv2
import numpy as np
import pandas as pd
import pytesseract
import easyocr
import json
from typing import List, Dict, Tuple, Optional, Any
from PIL import Image
import re
from sklearn.cluster import DBSCAN
from src.services.log_service import get_logger

logger = get_logger(__name__)


class EnhancedTableOCRService:
    """Enhanced service for detecting and processing tables with advanced preprocessing and clustering"""
    
    def __init__(self):
        """Initialize the enhanced table OCR service"""
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
    
    def enhanced_preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Enhanced preprocessing with grayscale conversion and adaptive threshold
        
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
        
        # Enhanced adaptive thresholding
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 2
        )
        
        # Morphological operations to clean up the image
        kernel_close = np.ones((3, 3), np.uint8)
        kernel_open = np.ones((2, 2), np.uint8)
        
        # Close small gaps
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close)
        # Remove small noise
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel_open)
        
        # Deskew the image
        deskewed = self._deskew_image(cleaned)
        
        # Apply sharpening
        sharpened = self._sharpen_image(deskewed)
        
        return sharpened
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """
        Correct skew in the image using contour analysis
        
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
    
    def detect_lines_with_hough(self, image: np.ndarray) -> Tuple[List[Tuple], List[Tuple]]:
        """
        Detect lines using HoughLines and findContours
        
        Args:
            image: Preprocessed binary image
            
        Returns:
            Tuple of (horizontal_lines, vertical_lines)
        """
        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
        horizontal_lines_img = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Detect vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
        vertical_lines_img = cv2.morphologyEx(image, cv2.MORPH_OPEN, vertical_kernel)
        
        # Use HoughLines to detect line segments
        horizontal_lines = cv2.HoughLinesP(
            horizontal_lines_img, 1, np.pi/180, threshold=50, minLineLength=100, maxLineGap=10
        )
        
        vertical_lines = cv2.HoughLinesP(
            vertical_lines_img, 1, np.pi/180, threshold=50, minLineLength=100, maxLineGap=10
        )
        
        # Convert to list of tuples
        h_lines = []
        if horizontal_lines is not None:
            for line in horizontal_lines:
                x1, y1, x2, y2 = line[0]
                h_lines.append((x1, y1, x2, y2))
        
        v_lines = []
        if vertical_lines is not None:
            for line in vertical_lines:
                x1, y1, x2, y2 = line[0]
                v_lines.append((x1, y1, x2, y2))
        
        return h_lines, v_lines
    
    def segment_cells(self, image: np.ndarray, h_lines: List[Tuple], v_lines: List[Tuple]) -> List[Dict]:
        """
        Segment table cells based on detected lines
        
        Args:
            image: Original image
            h_lines: Horizontal lines
            v_lines: Vertical lines
            
        Returns:
            List of cell dictionaries with coordinates and content
        """
        cells = []
        
        if not h_lines or not v_lines:
            logger.warning("No lines detected for cell segmentation")
            return cells
        
        # Extract y-coordinates from horizontal lines and sort
        h_coords = sorted(set([line[1] for line in h_lines] + [line[3] for line in h_lines]))
        # Extract x-coordinates from vertical lines and sort
        v_coords = sorted(set([line[0] for line in v_lines] + [line[2] for line in v_lines]))
        
        # Create cells from grid intersections
        for i in range(len(h_coords) - 1):
            for j in range(len(v_coords) - 1):
                top = h_coords[i]
                bottom = h_coords[i + 1]
                left = v_coords[j]
                right = v_coords[j + 1]
                
                # Ensure valid cell dimensions
                if bottom - top > 10 and right - left > 10:
                    cell = {
                        'row': i,
                        'col': j,
                        'top': top,
                        'bottom': bottom,
                        'left': left,
                        'right': right,
                        'bbox': (left, top, right - left, bottom - top)
                    }
                    cells.append(cell)
        
        return cells
    
    def extract_text_from_cells(self, image: np.ndarray, cells: List[Dict]) -> List[Dict]:
        """
        Extract text from individual cells using OCR
        
        Args:
            image: Original image
            cells: List of cell dictionaries
            
        Returns:
            List of cells with extracted text
        """
        for cell in cells:
            try:
                # Extract cell region
                left, top, width, height = cell['bbox']
                cell_img = image[top:top+height, left:left+width]
                
                # Skip if cell is too small
                if cell_img.shape[0] < 10 or cell_img.shape[1] < 10:
                    cell['text'] = ''
                    continue
                
                # Preprocess cell image
                cell_processed = self.enhanced_preprocess_image(cell_img)
                
                # Extract text using Tesseract first, fallback to EasyOCR
                try:
                    text = pytesseract.image_to_string(
                        cell_processed, 
                        config='--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂưăạảấầẩẫậắằẳẵặẹẻẽềềểỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪễệỉịọỏốồổỗộớờởỡợụủứừỬỮỰỲỴÝỶỸửữựỳỵýỷỹ .,()-'
                    ).strip()
                except Exception:
                    # Fallback to EasyOCR
                    if self.easyocr_reader:
                        results = self.easyocr_reader.readtext(cell_processed)
                        text = ' '.join([result[1] for result in results if result[2] > 0.3])
                    else:
                        text = ''
                
                cell['text'] = text.strip()
                
            except Exception as e:
                logger.warning(f"Error extracting text from cell {cell.get('row', 0)},{cell.get('col', 0)}: {e}")
                cell['text'] = ''
        
        return cells
    
    def cluster_cells_by_position(self, cells: List[Dict]) -> List[List[Dict]]:
        """
        Cluster cells by y-coordinate (rows) using DBSCAN, then sort by x-coordinate (columns)
        
        Args:
            cells: List of cell dictionaries
            
        Returns:
            List of rows, each containing sorted cells
        """
        if not cells:
            return []
        
        # Extract top positions for clustering
        positions = np.array([[cell['top']] for cell in cells])
        
        # Use DBSCAN to cluster by y-coordinate (top position)
        clustering = DBSCAN(eps=20, min_samples=1).fit(positions)
        labels = clustering.labels_
        
        # Group cells by cluster labels (rows)
        rows = {}
        for i, label in enumerate(labels):
            if label not in rows:
                rows[label] = []
            rows[label].append(cells[i])
        
        # Sort rows by average y-coordinate and cells within rows by x-coordinate
        sorted_rows = []
        for label in sorted(rows.keys(), key=lambda l: np.mean([cell['top'] for cell in rows[l]])):
            row_cells = sorted(rows[label], key=lambda cell: cell['left'])
            sorted_rows.append(row_cells)
        
        return sorted_rows
    
    def create_dataframe_from_clustered_cells(self, clustered_rows: List[List[Dict]]) -> pd.DataFrame:
        """
        Create DataFrame from clustered cell rows
        
        Args:
            clustered_rows: List of rows with sorted cells
            
        Returns:
            DataFrame with table data
        """
        if not clustered_rows:
            return pd.DataFrame()
        
        # Find maximum number of columns
        max_cols = max(len(row) for row in clustered_rows) if clustered_rows else 0
        
        # Create table data
        table_data = []
        for row in clustered_rows:
            row_data = [cell['text'] for cell in row]
            # Pad row to max columns
            row_data.extend([''] * (max_cols - len(row_data)))
            table_data.append(row_data)
        
        # Create DataFrame
        if table_data:
            # Check if first row looks like headers
            if len(table_data) > 1 and self._is_header_row(table_data[0]):
                df = pd.DataFrame(table_data[1:], columns=table_data[0])
            else:
                columns = [f'Column_{i+1}' for i in range(max_cols)]
                df = pd.DataFrame(table_data, columns=columns)
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
            # Handle Vietnamese decimal separator
            text_clean = text.replace(',', '.').replace('%', '').strip()
            float(text_clean)
            return True
        except ValueError:
            return False
    
    def extract_enhanced_table_data(self, image: np.ndarray) -> pd.DataFrame:
        """
        Extract table data using enhanced preprocessing and clustering
        
        Args:
            image: Input image
            
        Returns:
            DataFrame containing the extracted table data
        """
        try:
            logger.info("Starting enhanced table extraction")
            
            # Step 1: Enhanced preprocessing
            processed_image = self.enhanced_preprocess_image(image)
            
            # Step 2: Detect lines using HoughLines
            h_lines, v_lines = self.detect_lines_with_hough(processed_image)
            logger.info(f"Detected {len(h_lines)} horizontal and {len(v_lines)} vertical lines")
            
            # Step 3: Segment cells
            cells = self.segment_cells(image, h_lines, v_lines)
            logger.info(f"Segmented {len(cells)} cells")
            
            if not cells:
                logger.warning("No cells detected, falling back to OCR-based extraction")
                return self._fallback_ocr_extraction(processed_image)
            
            # Step 4: Extract text from cells
            cells_with_text = self.extract_text_from_cells(image, cells)
            
            # Step 5: Cluster cells by position
            clustered_rows = self.cluster_cells_by_position(cells_with_text)
            logger.info(f"Clustered into {len(clustered_rows)} rows")
            
            # Step 6: Create DataFrame
            df = self.create_dataframe_from_clustered_cells(clustered_rows)
            
            logger.info(f"Successfully extracted table with {len(df)} rows and {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error in enhanced table extraction: {e}")
            # Fallback to basic OCR extraction
            return self._fallback_ocr_extraction(image)
    
    def _fallback_ocr_extraction(self, image: np.ndarray) -> pd.DataFrame:
        """
        Fallback OCR extraction when line detection fails
        
        Args:
            image: Preprocessed image
            
        Returns:
            DataFrame from OCR text extraction
        """
        try:
            # Use pytesseract to get detailed OCR data
            ocr_data = pytesseract.image_to_data(
                image, 
                output_type=pytesseract.Output.DICT,
                config='--psm 6'
            )
            
            # Group text by lines and positions
            table_data = self._group_text_into_table(ocr_data)
            
            # Convert to DataFrame
            df = self._create_dataframe_from_table_data(table_data)
            
            return df
            
        except Exception as e:
            logger.error(f"Error in fallback OCR extraction: {e}")
            return pd.DataFrame()
    
    def _group_text_into_table(self, ocr_data: Dict) -> List[List[str]]:
        """
        Group OCR text data into table structure using clustering
        
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
        
        # Use clustering for row detection
        positions = np.array([[item['top']] for item in filtered_data])
        clustering = DBSCAN(eps=15, min_samples=1).fit(positions)
        labels = clustering.labels_
        
        # Group by cluster labels (rows)
        rows = {}
        for i, label in enumerate(labels):
            if label not in rows:
                rows[label] = []
            rows[label].append(filtered_data[i])
        
        # Sort rows and cells within rows
        sorted_rows = []
        for label in sorted(rows.keys(), key=lambda l: np.mean([item['top'] for item in rows[l]])):
            row_items = sorted(rows[label], key=lambda x: x['left'])
            sorted_rows.append([item['text'] for item in row_items])
        
        return sorted_rows
    
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
    
    def format_as_student_grades(self, df: pd.DataFrame, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Format DataFrame as student grades JSON structure
        
        Args:
            df: DataFrame with table data
            metadata: Optional metadata (student name, class, etc.)
            
        Returns:
            Dictionary in student grades format
        """
        result = {
            "student": metadata.get('student_name', '') if metadata else '',
            "class": metadata.get('class', '') if metadata else '',
            "grades": []
        }
        
        if df.empty:
            return result
        
        # Try to identify subject and grade columns
        columns = df.columns.tolist()
        
        # Look for common patterns in Vietnamese grade tables
        subject_col = None
        grade_cols = []
        
        for col in columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in ['môn', 'subject', 'tên môn']):
                subject_col = col
            elif any(keyword in col_lower for keyword in ['hk1', 'hk2', 'học kỳ', 'semester', 'điểm', 'grade', 'final', 'cuối kỳ']):
                grade_cols.append(col)
        
        # If no specific columns found, use first column as subject and rest as grades
        if subject_col is None and len(columns) > 0:
            subject_col = columns[0]
            grade_cols = columns[1:]
        
        # Process each row
        for _, row in df.iterrows():
            if subject_col and str(row[subject_col]).strip():
                grade_entry = {
                    "subject": str(row[subject_col]).strip()
                }
                
                # Add grades
                for grade_col in grade_cols:
                    grade_value = str(row[grade_col]).strip()
                    if grade_value and self._is_numeric(grade_value):
                        try:
                            grade_entry[grade_col] = float(grade_value.replace(',', '.'))
                        except ValueError:
                            grade_entry[grade_col] = grade_value
                    else:
                        grade_entry[grade_col] = grade_value
                
                result["grades"].append(grade_entry)
        
        return result
    
    def export_to_json_format(self, df: pd.DataFrame, file_path: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Export DataFrame to JSON in student grades format
        
        Args:
            df: DataFrame to export
            file_path: Output file path
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            grades_data = self.format_as_student_grades(df, metadata)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(grades_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully exported to JSON format: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to JSON format: {e}")
            return False
    
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
