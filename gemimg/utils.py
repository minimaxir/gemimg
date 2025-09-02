import base64
import io
from typing import Union

from PIL import Image


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
