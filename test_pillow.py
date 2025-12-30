from PIL import Image
import sys

try:
    print(f"Pillow Version: {Image.__version__}")
    # Create valid dummy image
    img = Image.new('RGB', (2000, 2000), color='red')
    
    # Try BOX filter
    if hasattr(Image, 'Resampling'):
        print("Image.Resampling exists")
        if hasattr(Image.Resampling, 'BOX'):
            print("Image.Resampling.BOX exists")
            img.thumbnail((1500, 1500), Image.Resampling.BOX)
            print("Thumbnail with BOX successful")
        else:
            print("Image.Resampling.BOX MISSING")
    else:
        print("Image.Resampling MISSING")
        
except Exception as e:
    print(f"Error: {e}")
