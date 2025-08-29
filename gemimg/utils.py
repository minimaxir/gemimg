import base64
import io

from PIL import Image


def resize_image(img, max_size=768):
    """
    Resize an image so that its maximum dimension (width or height) is max_size
    while maintaining the aspect ratio.
    """

    # Get current dimensions
    width, height = img.size

    # Calculate the scaling factor
    if width > height:
        # Width is the larger dimension
        scale_factor = max_size / width
    else:
        # Height is the larger dimension
        scale_factor = max_size / height

    # Calculate new dimensions
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    # Resize the image
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # resized_img.save("test.png")
    return resized_img


def img_to_b64(img, resize=True):
    """
    Convert an input image (or path to an image) to base64.
    """
    if isinstance(img, str):
        img = Image.open(img)
    if resize:
        img = resize_image(img)

    buffered = io.BytesIO()
    img.save(buffered, format="WEBP")
    img_base64 = base64.b64encode(buffered.getvalue())
    img_base64_str = img_base64.decode("utf-8")
    return img_base64_str


def b64_to_img(img_b64: str):
    """
    Convert a base64 encoding of an image into a PIL Image object.
    """
    b64_bytes = io.BytesIO(base64.decodebytes(bytes(img_b64, "utf-8")))
    return Image.open(b64_bytes)


def img_b64_part(img_b64):
    """
    Part formatting for a base64 encoded image to the Gemini API.
    """
    part = {"inline_data": {"mime_type": "image/webp", "data": img_b64}}
    return part
