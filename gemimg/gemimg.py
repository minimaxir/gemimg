import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional, Union

import httpx
from dotenv import load_dotenv
from PIL import Image

from .grid import Grid
from .utils import (
    _validate_aspect,
    b64_to_img,
    img_b64_part,
    img_to_b64,
    save_images_batch,
)

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class GemImg:
    api_key: str = field(default=os.getenv("GEMINI_API_KEY"), repr=False)
    client: httpx.Client = field(default_factory=httpx.Client, repr=False)
    model: str = "gemini-2.5-flash-image"
    base_url: str = field(
        default="https://generativelanguage.googleapis.com", repr=False
    )

    def __post_init__(self):
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is required. Pass it as `api_key`, set it as an environment variable or in .env file."
            )

    @property
    def is_pro(self) -> bool:
        """Check if the model is a pro variant."""
        return "-pro" in self.model

    def generate(
        self,
        prompt: Optional[str] = None,
        imgs: Optional[Union[str, Image.Image, List[str], List[Image.Image]]] = None,
        aspect_ratio: str = "1:1",
        resize_inputs: bool = True,
        save: bool = True,
        save_dir: str = "",
        temperature: float = 1.0,
        webp: bool = False,
        n: int = 1,
        store_prompt: bool = False,
        image_size: str = "2K",
        system_prompt: Optional[str] = None,
        grid: Optional[Grid] = None,
    ) -> Optional["ImageGen"]:
        if not prompt and not imgs:
            raise ValueError("Either 'prompt' or 'imgs' must be provided")

        # If grid is provided, use its aspect_ratio and image_size
        if grid is not None:
            if not self.is_pro:
                raise ValueError("Grid generation requires a Pro model")
            aspect_ratio = grid.aspect_ratio
            image_size = grid.image_size

        if n > 1:
            if temperature == 0:
                raise ValueError(
                    "Generating multiple images at temperature = 0.0 is redundant."
                )
            # Exclude 'self' from locals to avoid conflicts when passing as kwargs
            kwargs = {k: v for k, v in locals().items() if k != "self"}
            return self._generate_multiple(**kwargs)

        parts = []

        if imgs:
            # Ensure imgs is a list
            if isinstance(imgs, (str, Image.Image)):
                imgs = [imgs]

            img_b64_strings = [img_to_b64(img, resize_inputs) for img in imgs]
            parts.extend([img_b64_part(b64_str) for b64_str in img_b64_strings])

        if prompt:
            parts.append({"text": prompt.strip()})

        query_params = {
            "generationConfig": {
                "temperature": temperature,
                "imageConfig": {
                    "aspectRatio": _validate_aspect(aspect_ratio, self.is_pro)
                },
                "responseModalities": ["Image"],
            },
            "contents": [{"parts": parts}],
        }

        if self.is_pro:
            if image_size not in ["1K", "2K", "4K"]:
                raise ValueError("image_size must be one of '1K', '2K', or '4K'")
            query_params["generationConfig"]["imageConfig"]["imageSize"] = image_size
            if system_prompt:
                query_params["system_instruction"] = {
                    "parts": [{"text": system_prompt.strip()}]
                }

        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        api_url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"

        try:
            response = self.client.post(
                api_url, json=query_params, headers=headers, timeout=180
            )
        except httpx.TimeoutException:
            logger.error("Request Timeout")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            return None

        response_data = response.json()
        if err := response_data.get("error"):
            logger.error(f"API Response Error: {err['code']} — {err['message']}")
            return None

        usage_metadata = response_data["usageMetadata"]
        # Check for prohibited content
        candidates = response_data["candidates"][0]
        finish_reason = candidates.get("finishReason")
        if finish_reason in ["PROHIBITED_CONTENT", "NO_IMAGE"]:
            logger.error(f"Image was not generated due to {finish_reason}.")
            return None

        if "content" not in candidates:
            logger.error("No image is present in the response.")
            return None

        response_parts = candidates["content"]["parts"]

        output_images = [
            b64_to_img(part["inlineData"]["data"])
            for part in response_parts
            if "inlineData" in part
        ]

        # If grid is provided, slice the generated image(s) into subimages
        output_subimages = []
        if grid is not None:
            output_subimages = [
                sliced for img in output_images for sliced in grid.slice_image(img)
            ]

        output_image_paths = []
        output_subimage_paths = []
        if save:
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
            response_id = response_data["responseId"]
            file_extension = "webp" if webp else "png"
            save_kwargs = {
                "response_id": response_id,
                "save_dir": save_dir,
                "file_extension": file_extension,
                "store_prompt": store_prompt,
                "prompt": prompt,
            }

            if grid is not None:
                if grid.save_original_image:
                    output_image_paths = save_images_batch(output_images, **save_kwargs)
                output_subimage_paths = save_images_batch(
                    output_subimages, **save_kwargs
                )
            else:
                output_image_paths = save_images_batch(output_images, **save_kwargs)

        return ImageGen(
            images=output_images,
            image_paths=output_image_paths,
            usages=[
                Usage(
                    prompt_tokens=usage_metadata.get("promptTokenCount", -1),
                    completion_tokens=usage_metadata.get("candidatesTokenCount", -1),
                )
            ],
            subimages=output_subimages,
            subimage_paths=output_subimage_paths,
        )

    def _generate_multiple(self, n: int, **kwargs) -> "ImageGen":
        """Helper to generate multiple images by accumulating results."""
        n = kwargs.pop("n")
        result = None
        for _ in range(n):
            gen_result = self.generate(n=1, **kwargs)
            if result is None:
                result = gen_result
            else:
                result += gen_result
        return result


@dataclass
class Usage:
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class ImageGen:
    images: List[Image.Image] = field(default_factory=list)
    image_paths: List[str] = field(default_factory=list)
    usages: List[Usage] = field(default_factory=list)
    subimages: List[Image.Image] = field(default_factory=list)
    subimage_paths: List[str] = field(default_factory=list)

    @property
    def image(self) -> Optional[Image.Image]:
        return self.images[-1] if self.images else None

    @property
    def image_path(self) -> Optional[str]:
        return self.image_paths[-1] if self.image_paths else None

    @property
    def usage(self) -> Optional[Usage]:
        return self.usages[0] if self.usages else None

    def __add__(self, other: "ImageGen") -> "ImageGen":
        if isinstance(other, ImageGen):
            return ImageGen(
                images=self.images + other.images,
                image_paths=self.image_paths + other.image_paths,
                usages=self.usages + other.usages,
                subimages=self.subimages + other.subimages,
                subimage_paths=self.subimage_paths + other.subimage_paths,
            )
        raise TypeError("Can only add ImageGen instances.")

    def __repr__(self) -> str:
        img_info = f"images={len(self.images)}"
        if self.images:
            img = self.images[0]
            img_info += f" ({img.width}x{img.height})"
        subimg_info = ""
        if self.subimages:
            subimg = self.subimages[0]
            subimg_info = (
                f", subimages={len(self.subimages)} ({subimg.width}x{subimg.height})"
            )
        usage_info = ""
        if self.usages:
            total_tokens = sum(u.total_tokens for u in self.usages)
            usage_info = f", total_tokens={total_tokens}"
        return f"ImageGen({img_info}{subimg_info}{usage_info})"
