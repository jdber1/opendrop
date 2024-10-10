from PIL import Image
import os

class ImageHandler:
    def get_image_paths(self, directory, supported_extensions=('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        """Load all images from a directory."""
        if not os.path.exists(directory):
            return []

        images = [f for f in os.listdir(directory) if f.lower().endswith(supported_extensions)]
        return [os.path.join(directory, img) for img in images]

    def resize_image(self, image, size=(400, 300)):
        """Resize the currently loaded image."""
        if image:
            return image.resize(size, Image.LANCZOS)
        return None