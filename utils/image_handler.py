from PIL import Image
import os


class ImageHandler:
    def get_image_paths(self, directory, supported_extensions=('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        """Load all images from a directory."""
        if not os.path.exists(directory):
            return []

        images = [f for f in os.listdir(
            directory) if f.lower().endswith(supported_extensions)]
        return [os.path.join(directory, img) for img in images]

    def resize_image(self, image, size=(400, 300)):
        """Resize the currently loaded image."""
        if image:
            return image.resize(size, Image.LANCZOS)
        return None

    def resize_image_with_aspect_ratio(self, image, max_width=400, max_height=300):
        if image:
            width, height = image.size
            new_width, new_height = self.get_fitting_dimensions(width, height, max_width, max_height)
            return image.resize((new_width, new_height), Image.LANCZOS)
        return None
    
    def get_fitting_dimensions(self, original_width, original_height, max_width=400, max_height=300):
        aspect_ratio = original_width / original_height

        # Initialize new dimensions
        new_width = original_width
        new_height = original_height

        # Check if the image needs to be resized
        if original_width > max_width or original_height > max_height:
            # Determine scaling factor
            width_scale = max_width / original_width
            height_scale = max_height / original_height
            scale = min(width_scale, height_scale)  # Use the smaller scale to maintain aspect ratio
            
            # Calculate new dimensions
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
        else:
            # If the image is within the max dimensions, return original dimensions
            new_width = original_width
            new_height = original_height

        return new_width, new_height
