# Resources Directory

This directory contains all application resources organized in a clean, maintainable structure.

## Directory Structure

```
resources/
├── assets/                 # Application assets
│   ├── icons/             # UI icons (PNG format)
│   │   ├── capture.png    # Screen capture icon
│   │   ├── extract.png    # Text extraction icon
│   │   ├── info.png       # Information icon
│   │   ├── open.png       # Open file icon
│   │   └── save.png       # Save file icon
│   ├── images/            # Application images
│   │   └── background.jpg # Background image
│   └── ui/                # UI-specific resources
│       └── favicon.ico    # Application favicon
├── test_data/             # Test and sample data
│   ├── samples/           # Sample images for testing
│   ├── demo/              # Demo images and data
│   └── validation/        # Validation test images
└── resource_config.py     # Resource path configuration
```

## Usage

### Using Resource Configuration

The `resource_config.py` module provides centralized path management:

```python
from resources.resource_config import ResourcePaths, get_icon_path, get_test_image_path

# Access specific resources
favicon_path = ResourcePaths.FAVICON
background_path = ResourcePaths.BACKGROUND

# Get icon paths
capture_icon = get_icon_path('capture')
save_icon = get_icon_path('save.png')

# Get test image paths
sample_image = get_test_image_path('samples', 'image1.png')
demo_image = get_test_image_path('demo', 'image1.png')

# Get all test images
all_samples = ResourcePaths.get_sample_images()
all_demo = ResourcePaths.get_demo_images()
all_validation = ResourcePaths.get_validation_images()
```

### Resource Categories

#### Assets
- **icons/**: UI icons in PNG format for buttons and interface elements
- **images/**: General application images (backgrounds, logos, etc.)
- **ui/**: UI-specific resources like favicons and themes

#### Test Data
- **samples/**: General sample images for testing OCR functionality
- **demo/**: Demo images and associated data files for demonstrations
- **validation/**: Images specifically for validation and quality testing

## Migration from Old Structure

The old `resources/` directory had the following issues that have been fixed:

1. **Typo**: `input_mages/` → `test_data/samples/`
2. **Better organization**: Separated assets from test data
3. **Consistent naming**: All directories use clear, descriptive names
4. **Centralized configuration**: All paths managed through `resource_config.py`

### Old vs New Mapping

| Old Path | New Path |
|----------|----------|
| `resources/icons/` | `resources/assets/icons/` |
| `resources/favicon/` | `resources/assets/ui/` |
| `resources/background/` | `resources/assets/images/` |
| `resources/input_mages/` | `resources/test_data/samples/` |
| `resources/input_mages/Demo/` | `resources/test_data/demo/` |
| `resources/input_mages/fix/` | `resources/test_data/validation/` |

## Validation

Run the resource configuration script to validate the structure:

```bash
python resources/resource_config.py
```

This will:
- Ensure all directories exist
- Validate critical files are present
- Display resource statistics

## Adding New Resources

### Adding Icons
1. Place PNG files in `assets/icons/`
2. Update `ResourcePaths` class if needed for direct access
3. Use `get_icon_path()` function for dynamic access

### Adding Test Images
1. Choose appropriate category: `samples`, `demo`, or `validation`
2. Place images in the corresponding `test_data/` subdirectory
3. Use `get_test_image_path()` or class methods to access

### Adding Other Assets
1. Place in appropriate `assets/` subdirectory
2. Update `ResourcePaths` class for commonly used files
3. Use `get_resource_path()` for dynamic access

## Best Practices

1. **Use the configuration module**: Always access resources through `resource_config.py`
2. **Consistent naming**: Use lowercase with underscores for file names
3. **Appropriate formats**: PNG for icons, JPG for photos, ICO for favicons
4. **Documentation**: Update this README when adding new resource categories
5. **Validation**: Run validation script after making changes

## Maintenance

- Regularly validate resources using the configuration script
- Keep test data organized by purpose (samples, demo, validation)
- Remove unused resources to keep the directory clean
- Update path references in code when restructuring
