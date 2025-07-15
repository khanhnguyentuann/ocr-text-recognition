# OCR Text Recognition Application

A clean, modern OCR (Optical Character Recognition) application built with PySide6 and EasyOCR. This project follows a `Model-View-Controller-Service` architecture to ensure a clear separation of concerns and maintainable code.

## Features

- **Modern GUI**: A responsive and intuitive user interface built with PySide6.
- **Accurate OCR**: Leverages `EasyOCR` for high-quality text extraction.
- **Multi-language Support**: Natively supports both English and Vietnamese.
- **User-Friendly**: Includes drag-and-drop for images, progress indicators, and clipboard integration.
- **Asynchronous Processing**: Performs OCR in a background thread to keep the UI responsive.
- **Robust Services**: Dedicated services for file operations, OCR processing, and logging.
- **Comprehensive Testing**: Includes unit tests with mocked dependencies to ensure reliability.

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

1.  **Launch the application**.
2.  **Load an image** by clicking "Open Image" or by dragging and dropping an image file onto the window.
3.  **Extract text** by clicking the "Extract Text" button. A progress bar will appear while the OCR is running.
4.  **Copy or save** the extracted text using the "Copy Text" and "Save Text" buttons.

## Testing

The project includes a suite of unit tests to ensure the reliability of the model and controller.

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v
