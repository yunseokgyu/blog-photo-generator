from PIL import Image, ImageDraw
import os

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

create_directory('./raw_images')
img = Image.new('RGB', (1200, 800), color = 'red')
d = ImageDraw.Draw(img)
d.text((10,10), "Hello World", fill=(255,255,0))
img.save('./raw_images/test_dummy.jpg')
print("Created dummy image at ./raw_images/test_dummy.jpg")
