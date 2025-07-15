"""
Demo script for Enhanced Table OCR Service
Demonstrates advanced table detection with clustering and cell segmentation
"""
import cv2
import numpy as np
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.services.enhanced_table_ocr_service import EnhancedTableOCRService
from src.services.log_service import get_logger

logger = get_logger(__name__)


def demo_enhanced_table_ocr():
    """Demonstrate enhanced table OCR capabilities"""
    
    print("🚀 Enhanced Table OCR Demo")
    print("=" * 50)
    
    # Initialize the enhanced service
    service = EnhancedTableOCRService()
    
    # Test images directory
    test_images_dir = Path("resources/test_data/samples")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    if not test_images_dir.exists():
        print(f"❌ Test images directory not found: {test_images_dir}")
        return
    
    # Get all image files
    image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
    image_files = []
    for ext in image_extensions:
        image_files.extend(test_images_dir.glob(f"*{ext}"))
    
    if not image_files:
        print(f"❌ No image files found in {test_images_dir}")
        return
    
    print(f"📁 Found {len(image_files)} test images")
    print()
    
    for i, image_path in enumerate(image_files[:3], 1):  # Process first 3 images
        print(f"🖼️  Processing image {i}: {image_path.name}")
        print("-" * 40)
        
        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                print(f"❌ Could not load image: {image_path}")
                continue
            
            print(f"📏 Image size: {image.shape[1]}x{image.shape[0]}")
            
            # Step 1: Enhanced preprocessing
            print("🔧 Step 1: Enhanced preprocessing...")
            processed_image = service.enhanced_preprocess_image(image)
            
            # Save preprocessed image
            preprocessed_path = output_dir / f"{image_path.stem}_preprocessed.png"
            cv2.imwrite(str(preprocessed_path), processed_image)
            print(f"💾 Saved preprocessed image: {preprocessed_path}")
            
            # Step 2: Line detection
            print("📏 Step 2: Detecting lines with HoughLines...")
            h_lines, v_lines = service.detect_lines_with_hough(processed_image)
            print(f"   Found {len(h_lines)} horizontal lines")
            print(f"   Found {len(v_lines)} vertical lines")
            
            # Visualize detected lines
            lines_image = image.copy()
            for line in h_lines:
                x1, y1, x2, y2 = line
                cv2.line(lines_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            for line in v_lines:
                x1, y1, x2, y2 = line
                cv2.line(lines_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            lines_path = output_dir / f"{image_path.stem}_lines.png"
            cv2.imwrite(str(lines_path), lines_image)
            print(f"💾 Saved lines visualization: {lines_path}")
            
            # Step 3: Cell segmentation
            print("🔲 Step 3: Segmenting cells...")
            cells = service.segment_cells(image, h_lines, v_lines)
            print(f"   Segmented {len(cells)} cells")
            
            if cells:
                # Visualize cells
                cells_image = image.copy()
                for cell in cells:
                    left, top, width, height = cell['bbox']
                    cv2.rectangle(cells_image, (left, top), (left + width, top + height), (0, 0, 255), 2)
                    # Add cell coordinates as text
                    cv2.putText(cells_image, f"({cell['row']},{cell['col']})", 
                              (left + 5, top + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                cells_path = output_dir / f"{image_path.stem}_cells.png"
                cv2.imwrite(str(cells_path), cells_image)
                print(f"💾 Saved cells visualization: {cells_path}")
                
                # Step 4: Extract text from cells
                print("📝 Step 4: Extracting text from cells...")
                cells_with_text = service.extract_text_from_cells(image, cells)
                
                # Count non-empty cells
                non_empty_cells = [cell for cell in cells_with_text if cell['text'].strip()]
                print(f"   Extracted text from {len(non_empty_cells)} cells")
                
                # Step 5: Clustering
                print("🎯 Step 5: Clustering cells by position...")
                clustered_rows = service.cluster_cells_by_position(cells_with_text)
                print(f"   Clustered into {len(clustered_rows)} rows")
                
                # Step 6: Create DataFrame
                print("📊 Step 6: Creating DataFrame...")
                df = service.create_dataframe_from_clustered_cells(clustered_rows)
                print(f"   Created DataFrame: {len(df)} rows × {len(df.columns)} columns")
                
                if not df.empty:
                    print("\n📋 Table Preview:")
                    print(df.head().to_string(index=False))
                    
                    # Export to different formats
                    base_name = output_dir / image_path.stem
                    
                    # CSV export
                    csv_path = f"{base_name}_table.csv"
                    if service.export_to_csv(df, csv_path):
                        print(f"💾 Exported to CSV: {csv_path}")
                    
                    # Excel export
                    excel_path = f"{base_name}_table.xlsx"
                    metadata = {
                        'source_image': str(image_path),
                        'processing_method': 'Enhanced Table OCR with Clustering',
                        'cells_detected': len(cells),
                        'rows_clustered': len(clustered_rows)
                    }
                    if service.export_to_excel(df, excel_path, metadata):
                        print(f"💾 Exported to Excel: {excel_path}")
                    
                    # JSON format (student grades style)
                    json_path = f"{base_name}_grades.json"
                    sample_metadata = {
                        'student_name': 'Nguyễn Minh Thái',
                        'class': '10A11'
                    }
                    if service.export_to_json_format(df, json_path, sample_metadata):
                        print(f"💾 Exported to JSON (grades format): {json_path}")
                
            else:
                print("⚠️  No cells detected, trying fallback OCR extraction...")
                df = service._fallback_ocr_extraction(processed_image)
                if not df.empty:
                    print(f"   Fallback extraction: {len(df)} rows × {len(df.columns)} columns")
                    print("\n📋 Fallback Table Preview:")
                    print(df.head().to_string(index=False))
            
        except Exception as e:
            print(f"❌ Error processing {image_path.name}: {e}")
            logger.error(f"Error processing {image_path}: {e}", exc_info=True)
        
        print()
    
    print("✅ Demo completed!")
    print(f"📁 Output files saved to: {output_dir.absolute()}")


def demo_clustering_visualization():
    """Demonstrate clustering visualization"""
    
    print("\n🎯 Clustering Visualization Demo")
    print("=" * 50)
    
    # Create sample cell data for demonstration
    sample_cells = [
        {'top': 100, 'left': 50, 'text': 'Subject'},
        {'top': 102, 'left': 200, 'text': 'HK1'},
        {'top': 98, 'left': 350, 'text': 'HK2'},
        {'top': 150, 'left': 52, 'text': 'Math'},
        {'top': 148, 'left': 202, 'text': '8.5'},
        {'top': 152, 'left': 348, 'text': '9.0'},
        {'top': 200, 'left': 48, 'text': 'Physics'},
        {'top': 198, 'left': 198, 'text': '7.5'},
        {'top': 202, 'left': 352, 'text': '8.0'},
    ]
    
    service = EnhancedTableOCRService()
    
    print("📊 Sample cell data:")
    for i, cell in enumerate(sample_cells):
        print(f"   Cell {i}: top={cell['top']}, left={cell['left']}, text='{cell['text']}'")
    
    print("\n🎯 Clustering cells by position...")
    clustered_rows = service.cluster_cells_by_position(sample_cells)
    
    print(f"   Clustered into {len(clustered_rows)} rows:")
    for i, row in enumerate(clustered_rows):
        texts = [cell['text'] for cell in row]
        print(f"   Row {i}: {texts}")
    
    # Create DataFrame
    df = service.create_dataframe_from_clustered_cells(clustered_rows)
    print(f"\n📊 Resulting DataFrame:")
    print(df.to_string(index=False))
    
    # Format as student grades
    grades_data = service.format_as_student_grades(df)
    print(f"\n🎓 Student grades format:")
    import json
    print(json.dumps(grades_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        demo_enhanced_table_ocr()
        demo_clustering_visualization()
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}", exc_info=True)
