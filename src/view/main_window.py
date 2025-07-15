# Main Window View - PySide6 GUI for the OCR application.
import os
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QMessageBox,
    QProgressBar, QMenuBar, QApplication, QSplitter, QSizePolicy,
    QTableWidget, QTableWidgetItem, QTabWidget, QHeaderView,
    QAbstractItemView, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QPixmap, QIcon, QAction, QDragEnterEvent, QDropEvent, QResizeEvent

# Attempt to import resource configuration, with a fallback for compatibility
try:
    from resources.resource_config import get_icon, VALID_IMAGE_EXTENSIONS
except (ImportError, ModuleNotFoundError):
    get_icon = None
    VALID_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')


class MainWindow(QMainWindow):
    # Main window of the OCR application, responsible for the UI.
    open_file_requested = Signal()
    save_text_requested = Signal()
    image_selected = Signal(str)
    extract_text_requested = Signal()
    extract_table_requested = Signal()
    clear_text_requested = Signal()
    copy_text_requested = Signal()
    copy_table_requested = Signal()
    export_csv_requested = Signal()
    export_json_requested = Signal()
    export_excel_requested = Signal()
    capture_webcam_requested = Signal()

    def __init__(self) -> None:
        # Initializes the main window, UI components, and theme settings.
        super().__init__()
        self.image_path: Optional[str] = None
        self.original_pixmap: Optional[QPixmap] = None
        self.is_dark_mode: bool = False
        
        self.setup_ui()
        self.setup_menu()
        self.setup_connections()
        self.load_theme()

    def setup_ui(self) -> None:
        # Sets up the main user interface, including layouts and widgets.
        self.setWindowTitle("OCR Table Recognition")
        self.setMinimumSize(1000, 700)
        self.resize(1400, 800)
        self.set_window_icon()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Left Panel (Image Display) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        self.image_label = QLabel("Drag & Drop Image Here\nor\nClick to Upload")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setAcceptDrops(True)
        self.image_label.setStyleSheet("border: 2px dashed #aaa; font-size: 14px;")
        self.image_label.setMinimumHeight(300)

        # Image control buttons
        image_controls = QHBoxLayout()
        self.btn_upload_image = QPushButton("Upload Image")
        self.btn_capture_webcam = QPushButton("Capture Webcam")
        image_controls.addWidget(self.btn_upload_image)
        image_controls.addWidget(self.btn_capture_webcam)

        # OCR control buttons
        ocr_controls = QHBoxLayout()
        self.btn_extract_text = QPushButton("Extract Text")
        self.btn_extract_table = QPushButton("Extract Table")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        ocr_controls.addWidget(self.btn_extract_text)
        ocr_controls.addWidget(self.btn_extract_table)
        ocr_controls.addWidget(self.progress_bar)

        left_layout.addWidget(self.image_label, 1)
        left_layout.addLayout(image_controls)
        left_layout.addLayout(ocr_controls)

        # --- Right Panel (Results Display) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Tab widget for different result views
        self.tab_widget = QTabWidget()
        
        # Text tab
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        self.text_edit = QTextEdit()
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        text_controls = QHBoxLayout()
        self.btn_clear_text = QPushButton("Clear")
        self.btn_copy_text = QPushButton("Copy Text")
        text_controls.addStretch()
        text_controls.addWidget(self.btn_clear_text)
        text_controls.addWidget(self.btn_copy_text)
        
        text_layout.addWidget(self.text_edit, 1)
        text_layout.addLayout(text_controls)
        self.tab_widget.addTab(text_tab, "Text Results")

        # Table tab
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)
        
        self.table_widget = QTableWidget()
        self.table_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        table_controls = QHBoxLayout()
        self.btn_copy_table = QPushButton("Copy Table")
        self.btn_export_csv = QPushButton("Export CSV")
        self.btn_export_json = QPushButton("Export JSON")
        self.btn_export_excel = QPushButton("Export Excel")
        self.btn_clear_table = QPushButton("Clear")
        
        table_controls.addWidget(self.btn_copy_table)
        table_controls.addWidget(self.btn_export_csv)
        table_controls.addWidget(self.btn_export_json)
        table_controls.addWidget(self.btn_export_excel)
        table_controls.addStretch()
        table_controls.addWidget(self.btn_clear_table)
        
        table_layout.addWidget(self.table_widget, 1)
        table_layout.addLayout(table_controls)
        self.tab_widget.addTab(table_tab, "Table Results")

        # Metadata tab
        metadata_tab = QWidget()
        metadata_layout = QVBoxLayout(metadata_tab)
        
        metadata_group = QGroupBox("Detected Metadata")
        self.metadata_form = QFormLayout(metadata_group)
        
        self.metadata_labels = {}
        metadata_fields = ['Student Name', 'Class', 'School', 'Subject', 'Semester', 'Year']
        for field in metadata_fields:
            label = QLabel("Not detected")
            label.setStyleSheet("color: #666; font-style: italic;")
            self.metadata_labels[field.lower().replace(' ', '_')] = label
            self.metadata_form.addRow(f"{field}:", label)
        
        metadata_layout.addWidget(metadata_group)
        metadata_layout.addStretch()
        self.tab_widget.addTab(metadata_tab, "Metadata")

        right_layout.addWidget(self.tab_widget, 1)

        # --- Splitter ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)  # Give more space to results
        main_layout.addWidget(splitter)

        self.setAcceptDrops(True)

    def setup_menu(self) -> None:
        # Sets up the main menu bar with file, view, and help menus.
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")
        
        open_icon = get_icon("open") if get_icon else None
        open_action = QAction(icon=open_icon, text="Open", parent=self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file_requested.emit)
        file_menu.addAction(open_action)

        save_icon = get_icon("save") if get_icon else None
        save_action = QAction(icon=save_icon, text="Save", parent=self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_text_requested.emit)
        file_menu.addAction(save_action)

        # Extract Action (direct on menubar)
        extract_icon = get_icon("extract") if get_icon else None
        extract_action = QAction(icon=extract_icon, text="Extract", parent=self)
        extract_action.setShortcut("Ctrl+E")
        extract_action.triggered.connect(self.request_text_extraction)
        menubar.addAction(extract_action)

        # View Menu
        view_menu = menubar.addMenu("View")
        self.theme_action = QAction("Toggle Dark Mode", self, checkable=True)
        self.theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(self.theme_action)

        # Help Menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_connections(self) -> None:
        # Connects widget signals to their respective handler methods or signals.
        self.btn_upload_image.clicked.connect(self.open_file_requested.emit)
        self.btn_capture_webcam.clicked.connect(self.capture_webcam_requested.emit)
        self.btn_extract_text.clicked.connect(self.request_text_extraction)
        self.btn_extract_table.clicked.connect(self.request_table_extraction)
        self.btn_clear_text.clicked.connect(self.clear_text_requested.emit)
        self.btn_copy_text.clicked.connect(self.copy_text_requested.emit)
        self.btn_clear_table.clicked.connect(self.clear_table)
        self.btn_copy_table.clicked.connect(self.copy_table_requested.emit)
        self.btn_export_csv.clicked.connect(self.export_csv_requested.emit)
        self.btn_export_json.clicked.connect(self.export_json_requested.emit)
        self.btn_export_excel.clicked.connect(self.export_excel_requested.emit)

    def set_window_icon(self) -> None:
        # Sets the main window icon, with a fallback for compatibility.
        if get_icon:
            self.setWindowIcon(get_icon("favicon.ico"))
        else:
            icon_path = os.path.join("resources", "assets", "ui", "favicon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))

    def set_image(self, file_path: str) -> None:
        # Displays the specified image in the image label.
        self.image_path = file_path
        self.original_pixmap = QPixmap(file_path)
        if self.original_pixmap.isNull():
            self.show_error("Failed to load the image file.")
            self.original_pixmap = None
            self.image_label.setText('Failed to load image')
        else:
            self.update_image_display()

    def update_image_display(self) -> None:
        # Scales the currently loaded pixmap to fit the image label.
        if self.original_pixmap:
            scaled_pixmap = self.original_pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def request_text_extraction(self) -> None:
        # Emits a signal to request text extraction if an image is loaded.
        if not self.image_path:
            self.show_warning("Please select an image first.")
            return
        self.extract_text_requested.emit()

    def show_progress(self, show: bool = True) -> None:
        # Shows or hides the progress bar.
        self.progress_bar.setVisible(show)
        if show:
            self.progress_bar.setRange(0, 0)  # Indeterminate mode

    def set_extracted_text(self, text: str) -> None:
        # Populates the text edit area with the extracted text.
        self.text_edit.setText(text)
        self.btn_copy_text.setText("Copy")

    def clear_text(self) -> None:
        # Clears the content of the text edit area.
        self.text_edit.clear()

    def set_copy_button_text(self, text: str) -> None:
        # Updates the text of the copy button.
        self.btn_copy_text.setText(text)

    def get_text_content(self) -> str:
        # Retrieves the current text from the text edit area.
        return self.text_edit.toPlainText()

    def show_success(self, message: str) -> None:
        """Displays a success message box."""
        QMessageBox.information(self, "Success", message)

    def show_error(self, message: str) -> None:
        """Displays an error message box."""
        QMessageBox.critical(self, "Error", message)

    def show_warning(self, message: str) -> None:
        """Displays a warning message box."""
        QMessageBox.warning(self, "Warning", message)

    def show_about(self) -> None:
        # Displays the 'About' dialog with application information.
        about_text = """
        <p><b>OCR Text Recognition</b></p>
        <p>Version: 2.0</p>
        <p>This application uses EasyOCR to extract text from images.</p>
        <p>Built with PySide6 and EasyOCR.</p>
        """
        QMessageBox.about(self, "About OCR Text Recognition", about_text)

    def resizeEvent(self, event: QResizeEvent) -> None:
        # Handles the window resize event to scale the displayed image.
        super().resizeEvent(event)
        self.update_image_display()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        # Handles the drag enter event to accept image files.
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        # Handles the drop event to process the dropped image file.
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            if file_path.lower().endswith(VALID_IMAGE_EXTENSIONS):
                self.set_image(file_path)
                self.image_selected.emit(file_path)
            else:
                self.show_warning("Please drop a valid image file.")

    def toggle_theme(self) -> None:
        # Toggles the application's theme between light and dark mode.
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        self.save_theme()

    def apply_theme(self) -> None:
        # Applies the currently selected theme (light or dark) to the application.
        light_stylesheet = """
            QLabel#ImageLabel { border: 2px dashed #aaa; }
            QPushButton { padding: 8px; }
        """
        dark_stylesheet = """
            QWidget {
                background-color: #2b2b2b;
                color: #f0f0f0;
            }
            QMenuBar, QMenu {
                background-color: #3c3c3c;
                color: #f0f0f0;
            }
            QMenuBar::item:selected, QMenu::item:selected {
                background-color: #555;
            }
            QTextEdit, QLabel {
                background-color: #3c3c3c;
                color: #f0f0f0;
                border: 1px solid #555;
            }
            QLabel#ImageLabel {
                border: 2px dashed #555;
            }
            QPushButton {
                background-color: #555;
                color: #f0f0f0;
                border: 1px solid #777;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #777;
            }
            QSplitter::handle {
                background-color: #3c3c3c;
            }
        """
        if self.is_dark_mode:
            self.setStyleSheet(dark_stylesheet)
        else:
            self.setStyleSheet(light_stylesheet)
        
        self.image_label.setObjectName("ImageLabel")
        self.theme_action.setChecked(self.is_dark_mode)

    def save_theme(self) -> None:
        # Saves the current theme preference to the application settings.
        settings = QSettings("MyCompany", "OCRApp")
        settings.setValue("is_dark_mode", self.is_dark_mode)

    def load_theme(self) -> None:
        # Loads the theme preference from application settings and applies it.
        settings = QSettings("MyCompany", "OCRApp")
        self.is_dark_mode = settings.value("is_dark_mode", False, type=bool)
        self.apply_theme()

    def request_table_extraction(self) -> None:
        """Emits a signal to request table extraction if an image is loaded."""
        if not self.image_path:
            self.show_warning("Please select an image first.")
            return
        self.extract_table_requested.emit()

    def set_table_data(self, df) -> None:
        """Populates the table widget with DataFrame data."""
        if df.empty:
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            return

        # Set table dimensions
        self.table_widget.setRowCount(len(df))
        self.table_widget.setColumnCount(len(df.columns))
        
        # Set column headers
        self.table_widget.setHorizontalHeaderLabels(df.columns.tolist())
        
        # Populate table with data
        for row in range(len(df)):
            for col in range(len(df.columns)):
                item = QTableWidgetItem(str(df.iloc[row, col]))
                self.table_widget.setItem(row, col, item)
        
        # Auto-resize columns to content
        self.table_widget.resizeColumnsToContents()
        
        # Switch to table tab
        self.tab_widget.setCurrentIndex(1)

    def clear_table(self) -> None:
        """Clears the table widget."""
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)

    def get_table_data(self):
        """Retrieves data from the table widget as a list of lists."""
        if self.table_widget.rowCount() == 0:
            return []
        
        data = []
        # Get headers
        headers = []
        for col in range(self.table_widget.columnCount()):
            header_item = self.table_widget.horizontalHeaderItem(col)
            headers.append(header_item.text() if header_item else f"Column_{col+1}")
        data.append(headers)
        
        # Get data rows
        for row in range(self.table_widget.rowCount()):
            row_data = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        
        return data

    def set_metadata(self, metadata: dict) -> None:
        """Updates the metadata display with detected information."""
        for key, value in metadata.items():
            if key in self.metadata_labels:
                if value:
                    self.metadata_labels[key].setText(str(value))
                    self.metadata_labels[key].setStyleSheet("color: #000; font-style: normal;")
                else:
                    self.metadata_labels[key].setText("Not detected")
                    self.metadata_labels[key].setStyleSheet("color: #666; font-style: italic;")

    def clear_metadata(self) -> None:
        """Clears all metadata fields."""
        for label in self.metadata_labels.values():
            label.setText("Not detected")
            label.setStyleSheet("color: #666; font-style: italic;")

    def clear_all_results(self) -> None:
        """Clears all results (text, table, and metadata)."""
        self.clear_text()
        self.clear_table()
        self.clear_metadata()
