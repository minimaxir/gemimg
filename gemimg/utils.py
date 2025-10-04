import base64
import io
import math
from typing import List, Optional, Tuple, Union

from PIL import Image

VALID_ASPECTS = [
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "4:5",
    "5:4",
    "9:16",
    "16:9",
    "21:9",
]


_VALID_ASPECTS_SET = set(VALID_ASPECTS)


def _validate_aspect(aspect_ratio: str) -> str:
    if aspect_ratio not in _VALID_ASPECTS_SET:
        raise ValueError(
            f"'{aspect_ratio}' is invalid. "
            f"Supported aspect ratios: {', '.join(VALID_ASPECTS)}"
        )
    return aspect_ratio


def resize_image(img: Image.Image, max_size: int = 768) -> Image.Image:
    """
    Resize an image so that its maximum dimension (width or height) is `max_size`
    while maintaining the aspect ratio.

    Args:
        img: The PIL Image to resize.
        max_size: The maximum size for the larger dimension.

    Returns:
        The resized PIL Image.
    """
    width, height = img.size

    # Determine scaling factor based on the larger dimension
    scale_factor = max_size / max(width, height)

    # Skip resizing if image is already smaller
    if scale_factor >= 1.0:
        return img

    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)


def img_to_b64(img: Union[str, Image.Image], resize: bool = True) -> str:
    """
    Convert an input image (or path to an image) to a base64-encoded string.

    Args:
        img: The image or path to the image.
        resize: Whether to resize the image before encoding.

    Returns:
        The base64-encoded string of the image.
    """
    if isinstance(img, str):
        img = Image.open(img)
    if resize:
        img = resize_image(img)

    with io.BytesIO() as buffer:
        img.save(buffer, format="WEBP")
        img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode("utf-8")


def b64_to_img(img_b64: str) -> Image.Image:
    """
    Convert a base64-encoded image string into a PIL Image object.

    Args:
        img_b64: The base64-encoded image string.

    Returns:
        The decoded PIL Image.
    """
    img_data = base64.b64decode(img_b64)
    return Image.open(io.BytesIO(img_data))


def img_b64_part(img_b64: str) -> dict:
    """
    Create the part formatting for a base64-encoded image for the Gemini API.

    Args:
        img_b64: The base64-encoded image string.

    Returns:
        A dictionary representing the API part.
    """
    return {"inline_data": {"mime_type": "image/webp", "data": img_b64}}


def composite_images(
    images: List[Union[str, Image.Image]],
    rows: Optional[int] = None,
    cols: Optional[int] = None,
    background_color: Union[str, Tuple[int, int, int]] = "white",
) -> Image.Image:
    """
    Composite multiple images into a single grid image.

    Args:
        images: List of file paths (strings) or PIL Image objects
        rows: Number of rows in the grid. If None, will be calculated based on cols
        cols: Number of columns in the grid. If None, will be calculated based on rows
        background_color: Background color for empty cells (default: "white")

    Returns:
        PIL Image object containing the composite grid

    Raises:
        ValueError: If no rows or cols specified, or if images list is empty
        FileNotFoundError: If a file path doesn't exist
    """

    if not images:
        raise ValueError("Images list cannot be empty")

    # Load all images and ensure they're PIL Image objects
    loaded_images: List[Image.Image] = []
    for img in images:
        if isinstance(img, str):
            # It's a file path
            loaded_images.append(Image.open(img))
        else:
            # It's already a PIL Image
            loaded_images.append(img)

    num_images = len(loaded_images)

    # Calculate grid dimensions
    if rows is None and cols is None:
        # Default to roughly square grid
        cols = math.ceil(math.sqrt(num_images))
        rows = math.ceil(num_images / cols)
    elif rows is None:
        rows = math.ceil(num_images / cols)
    elif cols is None:
        cols = math.ceil(num_images / rows)

    # Validate that grid can accommodate all images
    if rows * cols < num_images:
        raise ValueError(f"Grid size {rows}x{cols} too small for {num_images} images")

    # Get dimensions from the first image (assuming all are equal as per requirements)
    img_width, img_height = loaded_images[0].size

    # Create the composite image
    composite_width = cols * img_width
    composite_height = rows * img_height

    # Determine mode based on first image
    mode = loaded_images[0].mode
    composite = Image.new(mode, (composite_width, composite_height), background_color)

    # Place images in the grid
    for idx, img in enumerate(loaded_images):
        row = idx // cols
        col = idx % cols

        x_offset = col * img_width
        y_offset = row * img_height

        composite.paste(img, (x_offset, y_offset))

    return composite
