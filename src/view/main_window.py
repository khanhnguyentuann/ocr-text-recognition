"""
Main Window View - PySide6 GUI for OCR application
"""
import os
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox,
    QProgressBar, QMenuBar, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QIcon, QAction

# Add resources to path for resource configuration
try:
    from resources.resource_config import ResourcePaths, get_icon_path
except (ImportError, ModuleNotFoundError):
    # Fallback to old structure if new resources not available
    ResourcePaths = None
    get_icon_path = None


class MainWindow(QMainWindow):
    """Main window for OCR application"""
    
    # Signals
    image_selected = Signal(str)  # Emitted when user selects an image
    extract_text_requested = Signal()  # Emitted when user requests text extraction
    save_text_requested = Signal(str)  # Emitted when user wants to save text
    clear_text_requested = Signal()  # Emitted when user wants to clear text
    copy_text_requested = Signal()  # Emitted when user wants to copy text
    
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.setup_ui()
        self.setup_menu()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("OCR Text Recognition")
        self.setFixedSize(1550, 830)
        
        # Set window icon
        self.set_window_icon()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Body layout
        body_layout = QGridLayout()
        
        # Image display area
        self.image_label = QLabel()
        self.image_label.setFixedSize(700, 700)
        self.image_label.setStyleSheet('border: 2px solid black')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText('Drag & Drop\nImage Here')
        self.image_label.setAcceptDrops(True)
        
        # Extract button
        self.btn_extract_text = QPushButton('Extract Text')
        self.btn_extract_text.setFixedSize(100, 30)
        
        # Text display area
        self.text_edit = QTextEdit()
        self.text_edit.setFixedSize(700, 700)
        self.text_edit.setStyleSheet('border: 2px solid black')
        
        # Control buttons
        self.btn_clear_text = QPushButton("Clear")
        self.btn_clear_text.setFixedSize(100, 30)
        
        self.btn_copy_text = QPushButton("Copy")
        self.btn_copy_text.setFixedSize(100, 30)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Add widgets to layout
        body_layout.addWidget(self.image_label, 0, 0)
        body_layout.addWidget(self.btn_extract_text, 0, 1)
        body_layout.addWidget(self.text_edit, 0, 2)
        body_layout.addWidget(self.btn_clear_text, 1, 2, Qt.AlignBottom)
        body_layout.addWidget(self.btn_copy_text, 1, 2, Qt.AlignBottom | Qt.AlignRight)
        body_layout.addWidget(self.progress_bar, 1, 0)
        
        main_layout.addLayout(body_layout)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
    
    def setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        # Open action
        if get_icon_path and get_icon_path("open").exists():
            open_action = QAction(QIcon(str(get_icon_path("open"))), "Open", self)
        else:
            open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.select_image)
        file_menu.addAction(open_action)

        # Save action
        if get_icon_path and get_icon_path("save").exists():
            save_action = QAction(QIcon(str(get_icon_path("save"))), "Save", self)
        else:
            save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_text)
        file_menu.addAction(save_action)

        # Extract action
        if get_icon_path and get_icon_path("extract").exists():
            extract_action = QAction(QIcon(str(get_icon_path("extract"))), "Extract", self)
        else:
            extract_action = QAction("Extract", self)
        extract_action.setShortcut("Ctrl+E")
        extract_action.triggered.connect(self.request_text_extraction)
        menubar.addAction(extract_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.btn_extract_text.clicked.connect(self.request_text_extraction)
        self.btn_clear_text.clicked.connect(self.clear_text_requested.emit)
        self.btn_copy_text.clicked.connect(self.copy_text_requested.emit)
    
    def set_window_icon(self):
        """Set window icon"""
        try:
            if ResourcePaths and ResourcePaths.FAVICON.exists():
                self.setWindowIcon(QIcon(str(ResourcePaths.FAVICON)))
            else:
                # Fallback to old path for compatibility
                icon_path = os.path.join("resources", "favicon", "favicon.ico")
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass  # Ignore if icon not found
    
    def select_image(self):
        """Open file dialog to select image"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )
        
        if file_path:
            self.set_image(file_path)
            self.image_selected.emit(file_path)
    
    def set_image(self, file_path: str):
        """Display image in the label"""
        self.image_path = file_path
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Scale pixmap to fit label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setScaledContents(False)
            else:
                self.show_error("Failed to load image")
        except Exception as e:
            self.show_error(f"Error loading image: {str(e)}")
    
    def request_text_extraction(self):
        """Request text extraction from current image"""
        if not self.image_path:
            self.show_warning("Please select an image first!")
            return
        
        self.extract_text_requested.emit()
    
    def show_progress(self, show: bool = True):
        """Show or hide progress bar"""
        self.progress_bar.setVisible(show)
        if show:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
    
    def set_extracted_text(self, text: str):
        """Set extracted text in text edit"""
        self.text_edit.setText(text)
        self.btn_copy_text.setText("Copy Text")
    
    def clear_text(self):
        """Clear text edit"""
        self.text_edit.clear()
    
    def copy_text(self):
        """Copy text to clipboard"""
        text = self.text_edit.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.btn_copy_text.setText("Copied ✓")
        else:
            self.show_warning("Nothing to copy!")
    
    def save_text(self):
        """Save text to file"""
        text = self.text_edit.toPlainText()
        if not text:
            self.show_warning("Nothing to save!")
            return
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self,
            "Save Text",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            self.save_text_requested.emit(file_path)
    
    def get_text_content(self) -> str:
        """Get current text content"""
        return self.text_edit.toPlainText()
    
    def show_success(self, message: str):
        """Show success message"""
        QMessageBox.information(self, "Success", message)
    
    def show_error(self, message: str):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)
    
    def show_warning(self, message: str):
        """Show warning message"""
        QMessageBox.warning(self, "Warning", message)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        OCR Text Recognition Application
        
        This application uses EasyOCR technology to extract text from images.
        Simply select an image and click 'Extract Text' to get started.
        
        Features:
        - Support for multiple image formats
        - Drag and drop functionality
        - Text extraction with high accuracy
        - Save extracted text to file
        
        Version: 2.0
        Built with PySide6 and EasyOCR
        """
        QMessageBox.about(self, "About OCR Text Recognition", about_text)
    
    # Drag and drop events
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            # Check if it's an image file
            valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
            if file_path.lower().endswith(valid_extensions):
                self.set_image(file_path)
                self.image_selected.emit(file_path)
            else:
                self.show_warning("Please drop a valid image file!")
