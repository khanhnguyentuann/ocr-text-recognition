# OCR Table Recognition Application

A comprehensive OCR (Optical Character Recognition) application built with PySide6, EasyOCR, and Tesseract. This application specializes in table detection and extraction from images, following a `Model-View-Controller-Service` architecture to ensure clean separation of concerns and maintainable code.

## Features

### Core OCR Capabilities
- **Modern GUI**: A responsive and intuitive user interface built with PySide6 with tabbed results display.
- **Dual OCR Engines**: Leverages both `EasyOCR` for general text extraction and `Tesseract` for detailed table processing.
- **Multi-language Support**: Natively supports both English and Vietnamese text recognition.
- **Image Preprocessing**: Advanced image processing including binarization, sharpening, and deskewing for optimal OCR results.

### Table Processing Features
- **Table Detection**: Automatically detects and extracts table structures from images.
- **Smart Table Reconstruction**: Groups OCR text into proper rows and columns based on coordinates.
- **Interactive Table Display**: Shows extracted tables in a proper QTableWidget with sorting, selection, and scrolling.
- **Multiple Export Formats**: Export table data to CSV, JSON, and Excel formats.
- **Clipboard Integration**: Copy tables in tab-separated format for easy pasting into Excel or other applications.

### Input Methods
- **File Upload**: Support for PNG, JPG, JPEG, BMP, and TIFF image formats.
- **Drag & Drop**: Intuitive drag-and-drop interface for image loading.
- **Webcam Capture**: Real-time image capture from webcam for instant processing.

### Metadata Detection
- **Academic Document Recognition**: Automatically detects student names, classes, schools, subjects, semesters, and academic years.
- **Smart Field Mapping**: Uses regex patterns to identify and extract structured information from Vietnamese and English documents.

### User Experience
- **Asynchronous Processing**: Performs OCR in background threads to keep the UI responsive.
- **Progress Indicators**: Visual feedback during processing operations.
- **Dark/Light Theme**: Toggle between light and dark modes for comfortable viewing.
- **Comprehensive Error Handling**: Robust error handling with user-friendly messages.

## Architecture

The application is structured around a `Model-View-Controller-Service` pattern, which separates the application into four interconnected components:

```
ocr-text-recognition/
├── src/
│   ├── model/
│   │   └── ocr_model.py        # Handles the core OCR logic via EasyOCR
│   ├── view/
│   │   └── main_window.py      # The GUI layer (PySide6)
│   ├── controller/
│   │   └── ocr_controller.py   # Connects the view to the services
│   └── services/
│       ├── ocr_service.py      # Manages OCR operations and background threading
│       ├── file_service.py     # Handles file I/O (open/save)
│       └── log_service.py      # Configures and provides logging
├── tests/
│   ├── test_ocr_model.py
│   └── test_ocr_controller.py
└── app.py
```

### Component Roles

-   **Model (`OCRModel`)**: The core of the application, responsible for processing images and extracting text using the `EasyOCR` library. It has no knowledge of the view or controller.
-   **View (`MainWindow`)**: The user interface. It displays data to the user and emits signals in response to user actions (e.g., button clicks, file drops). It does not contain any business logic.
-   **Controller (`OCRController`)**: Acts as the central hub, connecting the `View`'s signals to the appropriate `Service` methods. It orchestrates the flow of data between the UI and the application's business logic.
-   **Services**: A layer of specialized modules that handle distinct business logic:
    -   `OCRService`: Manages the `OCRModel` and runs text extraction in a background thread (`QThread`) to prevent the UI from freezing.
    -   `FileService`: Handles all file-related operations, such as opening, validating, and saving files.
    -   `LogService`: Provides a centralized logging setup for the entire application.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/khanhnguyentuann/ocr-text-recognition.git
    cd ocr-text-recognition
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**:
    ```bash
    python app.py
    ```

## Usage

### Getting Started
1.  **Launch the application** by running `python app.py`.
2.  **Load an image** using one of these methods:
    - Click "Upload Image" button to select a file
    - Drag and drop an image file onto the application window
    - Click "Capture Webcam" to take a photo using your camera

### Text Extraction
3.  **Extract text** by clicking the "Extract Text" button. The results will appear in the "Text Results" tab.
4.  **Copy or save** the extracted text using the "Copy Text" button or the File menu.

### Table Extraction
3.  **Extract table data** by clicking the "Extract Table" button. The application will:
    - Preprocess the image for optimal table detection
    - Detect table structure and extract data
    - Display results in the "Table Results" tab as an interactive table
    - Show detected metadata in the "Metadata" tab

### Working with Table Results
4.  **Interact with the table**:
    - Scroll through large tables
    - Select individual cells or ranges
    - Resize columns by dragging column borders
    - Sort data by clicking column headers

5.  **Export table data**:
    - **CSV**: Click "Export CSV" for spreadsheet compatibility
    - **JSON**: Click "Export JSON" for structured data format
    - **Excel**: Click "Export Excel" for full Excel workbook with metadata
    - **Clipboard**: Click "Copy Table" to paste into other applications

### Metadata Information
6.  **View detected metadata** in the "Metadata" tab, which automatically identifies:
    - Student names
    - Class information
    - School names
    - Subject details
    - Semester and academic year information

### Additional Features
- **Theme Toggle**: Switch between light and dark modes in the View menu
- **Clear Results**: Use "Clear" buttons to reset individual result areas
- **Progress Tracking**: Monitor processing progress with the built-in progress bar

## Testing

The project includes a suite of unit tests to ensure the reliability of the model and controller.

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v
