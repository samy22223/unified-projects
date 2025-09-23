# Adding OpenCV to the Pinnacle AI Platform

## Overview

OpenCV was excluded from the initial installation due to compilation issues on macOS. This document explains how to add OpenCV later when needed.

## Why OpenCV was excluded

- **Compilation Issues**: OpenCV requires extensive C++ compilation with CMake, which can fail on macOS due to system dependencies
- **Large Size**: OpenCV adds significant bloat to the installation
- **Alternative Solutions**: Many OpenCV use cases can be handled by existing packages like Pillow, imageio, and scikit-image

## Current Computer Vision Setup

The platform currently includes these computer vision packages:
- **Pillow** (PIL): Image processing and manipulation
- **imageio**: Reading and writing image/video files
- **albumentations**: Image augmentation
- **scikit-image**: Advanced image processing algorithms

## Adding OpenCV

### Option 1: Using Pre-compiled Binaries (Recommended)

```bash
# Activate the virtual environment
source venv/bin/activate

# Install OpenCV with pre-compiled binaries
pip install opencv-python

# Or for additional contrib modules
pip install opencv-contrib-python
```

### Option 2: Using Conda (Alternative)

If you have conda installed:

```bash
# Create a new conda environment with OpenCV
conda create -n pinnacle-opencv python=3.11
conda activate pinnacle-opencv
conda install opencv

# Then install the rest of the requirements
pip install -r requirements-pyarrow-free.txt
```

### Option 3: Building from Source (Advanced)

If you need specific OpenCV features:

```bash
# Install system dependencies first
brew install cmake pkg-config

# Install OpenCV from source
pip install opencv-python --no-binary opencv-python
```

## Testing OpenCV Installation

After installation, test OpenCV functionality:

```python
import cv2
import numpy as np

# Test basic functionality
img = np.zeros((100, 100, 3), dtype=np.uint8)
cv2.putText(img, 'OpenCV Test', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
print("OpenCV version:", cv2.__version__)
print("OpenCV test passed!")
```

## Common Use Cases and Alternatives

### 1. Image Loading and Display
```python
# Instead of cv2.imread()
from PIL import Image
img = Image.open('image.jpg')

# Instead of cv2.imshow()
import matplotlib.pyplot as plt
plt.imshow(img)
plt.show()
```

### 2. Image Processing
```python
# Instead of cv2.resize()
from PIL import Image
img = Image.open('image.jpg')
resized = img.resize((new_width, new_height))

# Instead of cv2.cvtColor()
from skimage import color
gray = color.rgb2gray(np.array(img))
```

### 3. Video Processing
```python
# Instead of cv2.VideoCapture()
import imageio
reader = imageio.get_reader('video.mp4')
```

## Performance Considerations

- **OpenCV** is generally faster for computer vision tasks
- **PIL + NumPy** is sufficient for most image processing tasks
- **scikit-image** provides more advanced algorithms with cleaner API

## Troubleshooting

### Common Issues:

1. **Import Error**: Make sure you're in the correct virtual environment
2. **Qt/GUI Issues**: Use `opencv-python-headless` for server environments
3. **Memory Issues**: OpenCV can be memory-intensive with large images

### Getting Help:

If you encounter issues:
1. Check the [OpenCV documentation](https://docs.opencv.org/)
2. Search for solutions on [Stack Overflow](https://stackoverflow.com/questions/tagged/opencv)
3. Check the [OpenCV Python tutorials](https://opencv-python-tutroals.readthedocs.io/)

## Integration with Existing Code

When adding OpenCV to existing code:

1. **Import at the top**: `import cv2`
2. **Check for availability**: Use try/except blocks
3. **Provide fallbacks**: Use PIL/scikit-image as alternatives
4. **Update requirements**: Add OpenCV to your requirements files

Example:
```python
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

def process_image(image_path):
    if OPENCV_AVAILABLE:
        # Use OpenCV
        img = cv2.imread(image_path)
        # ... processing
    else:
        # Use PIL fallback
        from PIL import Image
        img = Image.open(image_path)
        # ... processing
```

## Conclusion

OpenCV can be added to the Pinnacle AI Platform when specific computer vision features are needed. The current setup provides a solid foundation with alternative packages that handle most common use cases efficiently.