"""
Main Window View - PySide6 GUI for the OCR application.

This module defines the `MainWindow` class, which constitutes the main graphical
user interface of the application. It is built using PySide6 and handles the
presentation logic, such as displaying images, text, and handling user interactions.
"""
import os
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QMessageBox,
    QProgressBar, QMenuBar, QApplication, QSplitter, QSizePolicy
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
    """
    The main window of the OCR application, responsible for the UI.

    This class sets up all the widgets, layouts, and menus. It emits signals
    to the controller when the user performs actions, such as opening a file
    or requesting text extraction.

    Signals:
        open_file_requested: Emitted when the user wants to open a file.
        save_text_requested: Emitted when the user wants to save the text.
        image_selected (str): Emitted with the file path when an image is selected.
        extract_text_requested: Emitted when text extraction is requested.
        clear_text_requested: Emitted when the user requests to clear the text.
        copy_text_requested: Emitted when the user requests to copy the text.
    """
    open_file_requested = Signal()
    save_text_requested = Signal()
    image_selected = Signal(str)
    extract_text_requested = Signal()
    clear_text_requested = Signal()
    copy_text_requested = Signal()

    def __init__(self) -> None:
        """
        Initializes the main window, UI components, and theme settings.
        """
        super().__init__()
        self.image_path: Optional[str] = None
        self.original_pixmap: Optional[QPixmap] = None
        self.is_dark_mode: bool = False
        
        self.setup_ui()
        self.setup_menu()
        self.setup_connections()
        self.load_theme()

    def setup_ui(self) -> None:
        """
        Sets up the main user interface, including layouts and widgets.
        """
        self.setWindowTitle("OCR Text Recognition")
        self.resize(1550, 830)
        self.set_window_icon()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Left Panel (Image Display) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel("Drag & Drop\nImage Here")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(300, 300)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setAcceptDrops(True)

        left_bottom_bar = QHBoxLayout()
        self.btn_extract_text = QPushButton("Extract Text")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_bottom_bar.addWidget(self.btn_extract_text)
        left_bottom_bar.addWidget(self.progress_bar)

        left_layout.addWidget(self.image_label)
        left_layout.addLayout(left_bottom_bar)

        # --- Right Panel (Text Display) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = QTextEdit()
        self.text_edit.setMinimumSize(300, 300)
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_bottom_bar = QHBoxLayout()
        self.btn_clear_text = QPushButton("Clear")
        self.btn_copy_text = QPushButton("Copy")
        right_bottom_bar.addStretch()
        right_bottom_bar.addWidget(self.btn_clear_text)
        right_bottom_bar.addWidget(self.btn_copy_text)

        right_layout.addWidget(self.text_edit)
        right_layout.addLayout(right_bottom_bar)

        # --- Splitter ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([750, 750])
        main_layout.addWidget(splitter)

        self.setAcceptDrops(True)

    def setup_menu(self) -> None:
        """
        Sets up the main menu bar with file, view, and help menus.
        """
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
        """
        Connects widget signals to their respective handler methods or signals.
        """
        self.btn_extract_text.clicked.connect(self.request_text_extraction)
        self.btn_clear_text.clicked.connect(self.clear_text_requested.emit)
        self.btn_copy_text.clicked.connect(self.copy_text_requested.emit)

    def set_window_icon(self) -> None:
        """
        Sets the main window icon, with a fallback for compatibility.
        """
        if get_icon:
            self.setWindowIcon(get_icon("favicon.ico"))
        else:
            icon_path = os.path.join("resources", "assets", "ui", "favicon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))

    def set_image(self, file_path: str) -> None:
        """
        Displays the specified image in the image label.

        Args:
            file_path (str): The path to the image file to display.
        """
        self.image_path = file_path
        self.original_pixmap = QPixmap(file_path)
        if self.original_pixmap.isNull():
            self.show_error("Failed to load the image file.")
            self.original_pixmap = None
            self.image_label.setText('Failed to load image')
        else:
            self.update_image_display()

    def update_image_display(self) -> None:
        """
        Scales the currently loaded pixmap to fit the image label.
        """
        if self.original_pixmap:
            scaled_pixmap = self.original_pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def request_text_extraction(self) -> None:
        """
        Emits a signal to request text extraction if an image is loaded.
        """
        if not self.image_path:
            self.show_warning("Please select an image first.")
            return
        self.extract_text_requested.emit()

    def show_progress(self, show: bool = True) -> None:
        """
        Shows or hides the progress bar.

        Args:
            show (bool): True to show the progress bar, False to hide it.
        """
        self.progress_bar.setVisible(show)
        if show:
            self.progress_bar.setRange(0, 0)  # Indeterminate mode

    def set_extracted_text(self, text: str) -> None:
        """
        Populates the text edit area with the extracted text.

        Args:
            text (str): The text extracted from the image.
        """
        self.text_edit.setText(text)
        self.btn_copy_text.setText("Copy")

    def clear_text(self) -> None:
        """
        Clears the content of the text edit area.
        """
        self.text_edit.clear()

    def set_copy_button_text(self, text: str) -> None:
        """
        Updates the text of the copy button.

        Args:
            text (str): The new text for the button.
        """
        self.btn_copy_text.setText(text)

    def get_text_content(self) -> str:
        """
        Retrieves the current text from the text edit area.

        Returns:
            str: The plain text content.
        """
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
        """
        Displays the 'About' dialog with application information.
        """
        about_text = """
        <p><b>OCR Text Recognition</b></p>
        <p>Version: 2.0</p>
        <p>This application uses EasyOCR to extract text from images.</p>
        <p>Built with PySide6 and EasyOCR.</p>
        """
        QMessageBox.about(self, "About OCR Text Recognition", about_text)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handles the window resize event to scale the displayed image.

        Args:
            event (QResizeEvent): The resize event object.
        """
        super().resizeEvent(event)
        self.update_image_display()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        Handles the drag enter event to accept image files.

        Args:
            event (QDragEnterEvent): The drag enter event object.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Handles the drop event to process the dropped image file.

        Args:
            event (QDropEvent): The drop event object.
        """
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            if file_path.lower().endswith(VALID_IMAGE_EXTENSIONS):
                self.set_image(file_path)
                self.image_selected.emit(file_path)
            else:
                self.show_warning("Please drop a valid image file.")

    def toggle_theme(self) -> None:
        """
        Toggles the application's theme between light and dark mode.
        """
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        self.save_theme()

    def apply_theme(self) -> None:
        """
        Applies the currently selected theme (light or dark) to the application.
        """
        dark_stylesheet = """
            QMainWindow, QMenuBar, QMenu {
                background-color: #2b2b2b;
                color: #f0f0f0;
            }
            QTextEdit, QLabel {
                background-color: #3c3c3c;
                color: #f0f0f0;
                border: 1px solid #555;
            }
            QPushButton {
                background-color: #555;
                color: #f0f0f0;
                border: 1px solid #777;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #777;
            }
            QMenuBar::item:selected, QMenu::item:selected {
                background-color: #555;
            }
        """
        self.setStyleSheet(dark_stylesheet if self.is_dark_mode else "")
        self.theme_action.setChecked(self.is_dark_mode)

    def save_theme(self) -> None:
        """
        Saves the current theme preference to the application settings.
        """
        settings = QSettings("MyCompany", "OCRApp")
        settings.setValue("is_dark_mode", self.is_dark_mode)

    def load_theme(self) -> None:
        """
        Loads the theme preference from application settings and applies it.
        """
        settings = QSettings("MyCompany", "OCRApp")
        self.is_dark_mode = settings.value("is_dark_mode", False, type=bool)
        self.apply_theme()
