# OCR Text Recognition Application

A clean, modern OCR (Optical Character Recognition) application built with PySide6 and EasyOCR, following a proper MVC (Model-View-Controller) architecture.

## Features

- **Modern GUI**: Built with PySide6 for a responsive and intuitive user interface
- **Advanced OCR**: Uses EasyOCR for accurate text extraction from images
- **Multi-language Support**: Supports English and Vietnamese text recognition
- **Drag & Drop**: Easy image loading via drag and drop functionality
- **File Handling**: Open, save, and copy functionality is handled by the controller.
- **Configuration**: Centralized configuration for resources and constants.
- **Logging**: Added logging for file errors and OCR failures.
- **Testing**: Unit tests for both model and controller, with mocks for external dependencies.
- **Code Quality**: Formatted and linted with PEP8 standards.

## Architecture

The application follows a clean MVC (Model-View-Controller) architecture, with a dedicated module for resource management.

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
│   └── ocr_controller.py     # OCRController - connects GUI signals to model, handles file I/O and business logic
└── __init__.py

resources/
├── __init__.py
└── resource_config.py      # Manages all resource paths and application constants

tests/
├── __init__.py
├── test_ocr_model.py       # Unit tests for the OCR model
└── test_ocr_controller.py  # Unit tests for the controller, with mocked dependencies
```

### Components

-   **`OCRModel`**: Responsible for the core OCR logic. It uses `EasyOCR` to extract text from images. It does not interact with the view directly.
-   **`MainWindow`**: The main GUI window. It is responsible for displaying the UI and emitting signals based on user interaction (e.g., button clicks, drag-and-drop). It contains no business logic.
-   **`OCRController`**: Acts as the intermediary between the model and the view. It handles user actions (like opening files, saving text, and requesting OCR), calls the appropriate model methods, and updates the view with the results. It also manages the application's state, such as the current image path.
-   **`resource_config.py`**: A centralized module for managing all application resources, such as icon paths, valid file extensions, and other constants. This makes the application easier to configure and maintain.
-   **`OCRWorker`**: A `QThread` worker that runs the OCR process in the background to prevent the GUI from freezing during long operations.

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

## Requirements

-   Python 3.7+
-   PySide6 >= 6.0.0
-   EasyOCR >= 1.6.0
-   Pillow >= 9.0.0
-   OpenCV-Python >= 4.5.0
-   pytest >= 7.0.0 (for testing)
-   autopep8 (for code formatting)

## Usage

1.  **Launch the application**:
    ```bash
    python app.py
    ```

2.  **Load an image**:
    -   Click "File" → "Open" to select an image file.
    -   Or drag and drop an image directly onto the application window.

3.  **Extract text**:
    -   Click the "Extract Text" button or press `Ctrl+E`.
    -   A progress bar will indicate that OCR is in progress.

4.  **Save results**:
    -   Click "File" → "Save" or press `Ctrl+S` to save the extracted text to a `.txt` file.

## Testing

The project includes a suite of unit tests to ensure the reliability of the model and controller.

```bash
# Run all tests
pytest

# Run tests for a specific file
pytest tests/test_ocr_controller.py

# Run with verbose output
pytest -v
```

## Project Structure

```
ocr-text-recognition/
├── src/                      # Source code
│   ├── controller/          # Controller layer
│   ├── model/               # Model layer
│   └── view/                # View layer
├── tests/                    # Unit tests
│   ├── __init__.py
│   ├── test_ocr_controller.py
│   └── test_ocr_model.py
├── resources/                # Application resources
│   ├── assets/
│   │   ├── icons/
│   │   └── ui/
│   └── resource_config.py
├── .gitignore
├── app.py                    # Main application entry point
├── README.md                 # This file
└── requirements.txt          # Python dependencies
```

## Development

### Code Style

-   The codebase is formatted using `autopep8` to adhere to PEP 8 standards.
-   Type hints are used for clarity and static analysis.
-   Docstrings are provided for all modules, classes, and functions.

### Signal-Slot Architecture

The application relies heavily on Qt's signal-slot mechanism for communication between the view and the controller, ensuring a clean separation of concerns.

-   The **View** (`MainWindow`) emits signals when the user performs an action (e.g., `open_file_requested`).
-   The **Controller** (`OCRController`) has slots that are connected to these signals. When a signal is emitted, the corresponding slot in the controller is executed to handle the business logic.

This decoupled architecture makes it easy to modify the UI without affecting the underlying application logic, and vice-versa.
