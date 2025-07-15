"""
Test cases for Enhanced Table OCR Service
"""
import unittest
import numpy as np
import cv2
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from src.services.enhanced_table_ocr_service import EnhancedTableOCRService


class TestEnhancedTableOCRService(unittest.TestCase):
    """Test cases for Enhanced Table OCR Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = EnhancedTableOCRService()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_image(self, width=400, height=300):
        """Create a simple test image with table-like structure"""
        # Create white background
        image = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Draw horizontal lines
        cv2.line(image, (50, 100), (350, 100), (0, 0, 0), 2)  # Header line
        cv2.line(image, (50, 150), (350, 150), (0, 0, 0), 2)  # Row 1
        cv2.line(image, (50, 200), (350, 200), (0, 0, 0), 2)  # Row 2
        cv2.line(image, (50, 250), (350, 250), (0, 0, 0), 2)  # Bottom line
        
        # Draw vertical lines
        cv2.line(image, (50, 100), (50, 250), (0, 0, 0), 2)   # Left border
        cv2.line(image, (150, 100), (150, 250), (0, 0, 0), 2) # Column 1
        cv2.line(image, (250, 100), (250, 250), (0, 0, 0), 2) # Column 2
        cv2.line(image, (350, 100), (350, 250), (0, 0, 0), 2) # Right border
        
        # Add some text (simplified - in real scenario OCR would detect this)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(image, 'Subject', (60, 125), font, 0.5, (0, 0, 0), 1)
        cv2.putText(image, 'HK1', (160, 125), font, 0.5, (0, 0, 0), 1)
        cv2.putText(image, 'HK2', (260, 125), font, 0.5, (0, 0, 0), 1)
        
        cv2.putText(image, 'Math', (60, 175), font, 0.5, (0, 0, 0), 1)
        cv2.putText(image, '8.5', (160, 175), font, 0.5, (0, 0, 0), 1)
        cv2.putText(image, '9.0', (260, 175), font, 0.5, (0, 0, 0), 1)
        
        cv2.putText(image, 'Physics', (60, 225), font, 0.5, (0, 0, 0), 1)
        cv2.putText(image, '7.5', (160, 225), font, 0.5, (0, 0, 0), 1)
        cv2.putText(image, '8.0', (260, 225), font, 0.5, (0, 0, 0), 1)
        
        return image
    
    def test_enhanced_preprocess_image(self):
        """Test enhanced image preprocessing"""
        # Create test image
        test_image = self.create_test_image()
        
        # Test preprocessing
        processed = self.service.enhanced_preprocess_image(test_image)
        
        # Verify output
        self.assertIsInstance(processed, np.ndarray)
        self.assertEqual(len(processed.shape), 2)  # Should be grayscale
        self.assertEqual(processed.dtype, np.uint8)
        
        # Check that image was processed (not identical to input)
        gray_input = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        self.assertFalse(np.array_equal(processed, gray_input))
    
    def test_detect_lines_with_hough(self):
        """Test line detection using HoughLines"""
        # Create test image
        test_image = self.create_test_image()
        processed = self.service.enhanced_preprocess_image(test_image)
        
        # Test line detection
        h_lines, v_lines = self.service.detect_lines_with_hough(processed)
        
        # Verify output
        self.assertIsInstance(h_lines, list)
        self.assertIsInstance(v_lines, list)
        
        # Should detect some lines in our test image
        self.assertGreater(len(h_lines) + len(v_lines), 0)
        
        # Check line format
        if h_lines:
            line = h_lines[0]
            self.assertEqual(len(line), 4)  # x1, y1, x2, y2
            self.assertIsInstance(line[0], (int, np.integer))
    
    def test_segment_cells(self):
        """Test cell segmentation"""
        # Create test image
        test_image = self.create_test_image()
        processed = self.service.enhanced_preprocess_image(test_image)
        h_lines, v_lines = self.service.detect_lines_with_hough(processed)
        
        # Test cell segmentation
        cells = self.service.segment_cells(test_image, h_lines, v_lines)
        
        # Verify output
        self.assertIsInstance(cells, list)
        
        if cells:
            cell = cells[0]
            self.assertIn('row', cell)
            self.assertIn('col', cell)
            self.assertIn('bbox', cell)
            self.assertIn('top', cell)
            self.assertIn('bottom', cell)
            self.assertIn('left', cell)
            self.assertIn('right', cell)
            
            # Check bbox format
            bbox = cell['bbox']
            self.assertEqual(len(bbox), 4)  # left, top, width, height
    
    def test_cluster_cells_by_position(self):
        """Test cell clustering by position"""
        # Create sample cells
        sample_cells = [
            {'top': 100, 'left': 50, 'text': 'Subject'},
            {'top': 102, 'left': 200, 'text': 'HK1'},
            {'top': 98, 'left': 350, 'text': 'HK2'},
            {'top': 150, 'left': 52, 'text': 'Math'},
            {'top': 148, 'left': 202, 'text': '8.5'},
            {'top': 152, 'left': 348, 'text': '9.0'},
        ]
        
        # Test clustering
        clustered_rows = self.service.cluster_cells_by_position(sample_cells)
        
        # Verify output
        self.assertIsInstance(clustered_rows, list)
        self.assertEqual(len(clustered_rows), 2)  # Should have 2 rows
        
        # Check first row
        first_row = clustered_rows[0]
        self.assertEqual(len(first_row), 3)  # Should have 3 cells
        
        # Check that cells are sorted by x-coordinate
        x_coords = [cell['left'] for cell in first_row]
        self.assertEqual(x_coords, sorted(x_coords))
    
    def test_create_dataframe_from_clustered_cells(self):
        """Test DataFrame creation from clustered cells"""
        # Create sample clustered rows
        clustered_rows = [
            [
                {'text': 'Subject', 'top': 100, 'left': 50},
                {'text': 'HK1', 'top': 100, 'left': 200},
                {'text': 'HK2', 'top': 100, 'left': 350}
            ],
            [
                {'text': 'Math', 'top': 150, 'left': 50},
                {'text': '8.5', 'top': 150, 'left': 200},
                {'text': '9.0', 'top': 150, 'left': 350}
            ]
        ]
        
        # Test DataFrame creation
        df = self.service.create_dataframe_from_clustered_cells(clustered_rows)
        
        # Verify output
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)  # Should have 1 data row (header excluded)
        self.assertEqual(len(df.columns), 3)  # Should have 3 columns
        
        # Check column names (should use first row as headers)
        expected_columns = ['Subject', 'HK1', 'HK2']
        self.assertEqual(list(df.columns), expected_columns)
        
        # Check data
        self.assertEqual(df.iloc[0]['Subject'], 'Math')
        self.assertEqual(df.iloc[0]['HK1'], '8.5')
        self.assertEqual(df.iloc[0]['HK2'], '9.0')
    
    def test_format_as_student_grades(self):
        """Test formatting DataFrame as student grades JSON"""
        # Create sample DataFrame
        data = {
            'Subject': ['Math', 'Physics'],
            'HK1': ['8.5', '7.5'],
            'HK2': ['9.0', '8.0']
        }
        df = pd.DataFrame(data)
        
        # Test formatting
        metadata = {'student_name': 'Nguyễn Minh Thái', 'class': '10A11'}
        grades_data = self.service.format_as_student_grades(df, metadata)
        
        # Verify output
        self.assertIsInstance(grades_data, dict)
        self.assertEqual(grades_data['student'], 'Nguyễn Minh Thái')
        self.assertEqual(grades_data['class'], '10A11')
        self.assertIn('grades', grades_data)
        
        grades = grades_data['grades']
        self.assertEqual(len(grades), 2)
        
        # Check first grade entry
        first_grade = grades[0]
        self.assertEqual(first_grade['subject'], 'Math')
        self.assertEqual(first_grade['HK1'], 8.5)  # Should be converted to float
        self.assertEqual(first_grade['HK2'], 9.0)
    
    def test_is_numeric(self):
        """Test numeric detection"""
        # Test various numeric formats
        self.assertTrue(self.service._is_numeric('8.5'))
        self.assertTrue(self.service._is_numeric('8,5'))  # Vietnamese format
        self.assertTrue(self.service._is_numeric('85%'))
        self.assertTrue(self.service._is_numeric('10'))
        
        # Test non-numeric
        self.assertFalse(self.service._is_numeric('Math'))
        self.assertFalse(self.service._is_numeric('Subject'))
        self.assertFalse(self.service._is_numeric(''))
    
    def test_export_to_csv(self):
        """Test CSV export"""
        # Create sample DataFrame
        data = {'Subject': ['Math', 'Physics'], 'Grade': [8.5, 7.5]}
        df = pd.DataFrame(data)
        
        # Test export
        csv_path = os.path.join(self.temp_dir, 'test.csv')
        result = self.service.export_to_csv(df, csv_path)
        
        # Verify export
        self.assertTrue(result)
        self.assertTrue(os.path.exists(csv_path))
        
        # Verify content
        imported_df = pd.read_csv(csv_path)
        self.assertEqual(len(imported_df), 2)
        self.assertEqual(list(imported_df.columns), ['Subject', 'Grade'])
    
    def test_export_to_json_format(self):
        """Test JSON format export"""
        # Create sample DataFrame
        data = {
            'Subject': ['Math', 'Physics'],
            'HK1': ['8.5', '7.5'],
            'HK2': ['9.0', '8.0']
        }
        df = pd.DataFrame(data)
        
        # Test export
        json_path = os.path.join(self.temp_dir, 'test.json')
        metadata = {'student_name': 'Test Student', 'class': '10A'}
        result = self.service.export_to_json_format(df, json_path, metadata)
        
        # Verify export
        self.assertTrue(result)
        self.assertTrue(os.path.exists(json_path))
        
        # Verify content
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data['student'], 'Test Student')
        self.assertEqual(data['class'], '10A')
        self.assertEqual(len(data['grades']), 2)
    
    def test_export_to_excel(self):
        """Test Excel export"""
        # Create sample DataFrame
        data = {'Subject': ['Math', 'Physics'], 'Grade': [8.5, 7.5]}
        df = pd.DataFrame(data)
        
        # Test export
        excel_path = os.path.join(self.temp_dir, 'test.xlsx')
        metadata = {'source': 'test'}
        result = self.service.export_to_excel(df, excel_path, metadata)
        
        # Verify export
        self.assertTrue(result)
        self.assertTrue(os.path.exists(excel_path))
        
        # Verify content
        imported_df = pd.read_excel(excel_path, sheet_name='Table Data')
        self.assertEqual(len(imported_df), 2)
        self.assertEqual(list(imported_df.columns), ['Subject', 'Grade'])
    
    def test_empty_input_handling(self):
        """Test handling of empty inputs"""
        # Test empty cell list
        clustered_rows = self.service.cluster_cells_by_position([])
        self.assertEqual(clustered_rows, [])
        
        # Test empty DataFrame creation
        df = self.service.create_dataframe_from_clustered_cells([])
        self.assertTrue(df.empty)
        
        # Test empty DataFrame formatting
        grades_data = self.service.format_as_student_grades(pd.DataFrame())
        self.assertEqual(grades_data['grades'], [])


if __name__ == '__main__':
    unittest.main()
