# OCR Text Recognition Application

A clean, modern OCR (Optical Character Recognition) application built with PySide6 and EasyOCR, following a proper MVC (Model-View-Controller) architecture.

## Features

- **Modern GUI**: Built with PySide6 for a responsive and intuitive user interface
- **Advanced OCR**: Uses EasyOCR for accurate text extraction from images
- **Multi-language Support**: Supports English and Vietnamese text recognition
- **Drag & Drop**: Easy image loading via drag and drop functionality
- **Image Preprocessing**: Automatic image enhancement for better OCR results
- **Export Functionality**: Save extracted text to files
- **Clean Architecture**: Proper MVC separation for maintainable code

## Architecture

The application follows a clean MVC (Model-View-Controller) architecture:

```
src/
├── model/
│   ├── __init__.py
│   └── ocr_model.py          # OCRModel - handles image processing and text extraction
├── view/
│   ├── __init__.py
│   └── main_window.py        # MainWindow - PySide6 GUI interface
├── controller/
│   ├── __init__.py
│   └── ocr_controller.py     # OCRController - connects GUI signals to model
└── __init__.py
```

### Components

- **OCRModel**: Handles loading image files, preprocessing, and running OCR using EasyOCR
- **MainWindow**: Builds the GUI using PySide6 components, emits signals for user interactions
- **OCRController**: Connects the GUI signals to the model, controls application flow

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/khanhnguyentuann/ocr-text-recognition.git
   cd ocr-text-recognition
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

## Requirements

- Python 3.7+
- PySide6 >= 6.0.0
- EasyOCR >= 1.6.0
- Pillow >= 9.0.0
- OpenCV-Python >= 4.5.0
- pytest >= 7.0.0 (for testing)

## Usage

1. **Launch the application**:
   ```bash
   python app.py
   ```

2. **Load an image**:
   - Click "File" → "Open" to select an image file
   - Or drag and drop an image directly onto the application window

3. **Extract text**:
   - Click the "Extract Text" button or press Ctrl+E
   - Wait for the OCR processing to complete

4. **Save results**:
   - Click "File" → "Save" or press Ctrl+S to save the extracted text

## Testing

Run the unit tests to verify OCR functionality:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_ocr_model.py

# Run with verbose output
pytest tests/ -v

# Run manual test
python tests/test_ocr_model.py
```

## Supported Image Formats

- PNG (.png)
- JPEG (.jpg, .jpeg)
- BMP (.bmp)
- TIFF (.tiff)

## Project Structure

```
ocr-text-recognition/
├── src/                      # Source code
│   ├── model/               # Model layer
│   ├── view/                # View layer
│   ├── controller/          # Controller layer
│   └── __init__.py
├── tests/                   # Unit tests
│   ├── __init__.py
│   └── test_ocr_model.py
├── resources/               # Application resources
│   ├── icons/              # UI icons
│   ├── favicon/            # Application icon
│   └── input_mages/        # Sample images
├── app.py                  # Main application entry point
├── requirements.txt        # Python dependencies
├── style.qss              # Application stylesheet
└── README_NEW.md          # This file
```

## Development

### Adding New Features

1. **Model changes**: Modify `src/model/ocr_model.py` for OCR-related functionality
2. **View changes**: Modify `src/view/main_window.py` for UI components
3. **Controller changes**: Modify `src/controller/ocr_controller.py` for business logic

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all classes and methods
- Write unit tests for new functionality

### Signal-Slot Architecture

The application uses Qt's signal-slot mechanism for communication:

```python
# View emits signals
self.extract_text_requested.emit()

# Controller connects to signals
self.view.extract_text_requested.connect(self.on_extract_text_requested)
```

## Troubleshooting

### Common Issues

1. **EasyOCR installation fails**:
   - Ensure you have sufficient disk space
   - Try installing with `--no-cache-dir` flag

2. **OCR model not loading**:
   - Check internet connection (EasyOCR downloads models on first use)
   - Verify sufficient memory is available

3. **GUI not displaying correctly**:
   - Ensure PySide6 is properly installed
   - Check if Qt libraries are available

### Performance Tips

- Use image preprocessing for better OCR accuracy
- Ensure images are high resolution and well-lit
- Consider image orientation (the app auto-rotates landscape images)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Changelog

### Version 2.0 (Current)
- Complete refactor to MVC architecture
- Migrated from PyQt5 to PySide6
- Replaced Tesseract with EasyOCR
- Added comprehensive unit tests
- Improved error handling and user feedback
- Enhanced image preprocessing
- Added multi-threading for OCR processing

### Version 1.0 (Legacy)
- Basic OCR functionality with PyQt5
- Tesseract-based text extraction
- Simple GUI interface

## Authors

- Original development team: B, N, K, T, T
- Refactored architecture: Clean MVC implementation

## Acknowledgments

- EasyOCR team for the excellent OCR library
- Qt/PySide6 team for the GUI framework
- OpenCV team for image processing capabilities
