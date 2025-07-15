"""
Resource Configuration Module
Centralized configuration for all application resources
"""
import os
from pathlib import Path
from PySide6.QtGui import QIcon

# Base resource directory
RESOURCES_BASE = Path(__file__).parent

# Application constants
VALID_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')

class ResourcePaths:
    """Centralized resource path management"""
    
    # Base directories
    ASSETS = RESOURCES_BASE / "assets"
    TEST_DATA = RESOURCES_BASE / "test_data"
    
    # Asset subdirectories
    ICONS = ASSETS / "icons"
    IMAGES = ASSETS / "images"
    UI = ASSETS / "ui"
    
    # Test data subdirectories
    SAMPLES = TEST_DATA / "samples"
    DEMO = TEST_DATA / "demo"
    VALIDATION = TEST_DATA / "validation"
    
    # Specific files
    FAVICON = UI / "favicon.ico"
    BACKGROUND = IMAGES / "background.jpg"
    
    # Icon files
    CAPTURE_ICON = ICONS / "capture.png"
    EXTRACT_ICON = ICONS / "extract.png"
    INFO_ICON = ICONS / "info.png"
    OPEN_ICON = ICONS / "open.png"
    SAVE_ICON = ICONS / "save.png"
    
    @classmethod
    def get_sample_images(cls):
        """Get list of all sample image files"""
        if cls.SAMPLES.exists():
            return list(cls.SAMPLES.glob("*.png")) + list(cls.SAMPLES.glob("*.jpg"))
        return []
    
    @classmethod
    def get_demo_images(cls):
        """Get list of all demo image files"""
        if cls.DEMO.exists():
            return list(cls.DEMO.glob("*.png")) + list(cls.DEMO.glob("*.jpg"))
        return []
    
    @classmethod
    def get_validation_images(cls):
        """Get list of all validation image files"""
        if cls.VALIDATION.exists():
            return list(cls.VALIDATION.glob("*.png")) + list(cls.VALIDATION.glob("*.jpg"))
        return []
    
    @classmethod
    def get_all_test_images(cls):
        """Get all test images from all categories"""
        return cls.get_sample_images() + cls.get_demo_images() + cls.get_validation_images()
    
    @classmethod
    def ensure_directories_exist(cls):
        """Ensure all resource directories exist"""
        directories = [
            cls.ASSETS, cls.TEST_DATA, cls.ICONS, cls.IMAGES, cls.UI,
            cls.SAMPLES, cls.DEMO, cls.VALIDATION
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_resources(cls):
        """Validate that all expected resources exist"""
        missing_resources = []
        
        # Check critical files
        critical_files = [cls.FAVICON]
        
        for file_path in critical_files:
            if not file_path.exists():
                missing_resources.append(str(file_path))
        
        # Check directories
        critical_dirs = [cls.ICONS, cls.IMAGES, cls.UI, cls.SAMPLES]
        
        for dir_path in critical_dirs:
            if not dir_path.exists():
                missing_resources.append(str(dir_path))
        
        return missing_resources


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path for a resource given its relative path
    
    Args:
        relative_path: Path relative to resources directory
        
    Returns:
        Absolute Path object
    """
    return RESOURCES_BASE / relative_path


def get_icon_path(icon_name: str) -> Path:
    """
    Get path for an icon file
    
    Args:
        icon_name: Name of the icon (with or without .png extension)
        
    Returns:
        Path to the icon file
    """
    if not icon_name.endswith('.png'):
        icon_name += '.png'
    
    return ResourcePaths.ICONS / icon_name


def get_icon(icon_name: str) -> QIcon:
    """
    Get a QIcon object for a given icon name, with fallback.

    Args:
        icon_name: The name of the icon.

    Returns:
        A QIcon object. Returns an empty QIcon if not found.
    """
    path = get_icon_path(icon_name)
    if path.exists():
        return QIcon(str(path))
    return QIcon()  # Return empty icon as a fallback


def get_test_image_path(category: str, filename: str) -> Path:
    """
    Get path for a test image
    
    Args:
        category: Category of test image ('samples', 'demo', 'validation')
        filename: Name of the image file
        
    Returns:
        Path to the test image
    """
    category_map = {
        'samples': ResourcePaths.SAMPLES,
        'demo': ResourcePaths.DEMO,
        'validation': ResourcePaths.VALIDATION
    }
    
    if category not in category_map:
        raise ValueError(f"Invalid category: {category}. Must be one of {list(category_map.keys())}")
    
    return category_map[category] / filename


# Initialize and validate resources on import
if __name__ == "__main__":
    # This can be run as a script to validate resources
    ResourcePaths.ensure_directories_exist()
    missing = ResourcePaths.validate_resources()
    
    if missing:
        print("Missing resources:")
        for resource in missing:
            print(f"  - {resource}")
    else:
        print("All resources validated successfully!")
        
    print(f"\nResource structure:")
    print(f"Base: {RESOURCES_BASE}")
    print(f"Assets: {ResourcePaths.ASSETS}")
    print(f"Test Data: {ResourcePaths.TEST_DATA}")
    print(f"Sample images: {len(ResourcePaths.get_sample_images())}")
    print(f"Demo images: {len(ResourcePaths.get_demo_images())}")
    print(f"Validation images: {len(ResourcePaths.get_validation_images())}")
