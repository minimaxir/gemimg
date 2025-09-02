import os
from dataclasses import dataclass, field
from typing import List, Union

import httpx
from dotenv import load_dotenv
from PIL import Image

from .utils import b64_to_img, img_b64_part, img_to_b64

load_dotenv()


@dataclass
class GemImg:
    api_key: str = field(default=os.getenv("GEMINI_API_KEY"), repr=False)
    client: httpx.Client = field(default_factory=httpx.Client, repr=False)
    model: str = "gemini-2.5-flash-image-preview"

    def __post_init__(self):
        assert self.api_key, "GEMINI_API_KEY is not provided or defined in .env."

    def generate(
        self,
        prompt: str = None,
        imgs: Union[str, Image.Image, List[str], List[Image.Image]] = None,
        resize_inputs: bool = True,
        save: bool = True,
        temperature: float = 1.0,
        webp: bool = False,
        n: int = 1,
    ):
        assert prompt or imgs, "Need `prompt` or `imgs` to generate."

        if n > 1:
            assert temperature != 0.0, (
                "Generating multiple images at temperature = 0.0 is redundant."
            )
            return self.generate_n(n=n, **locals())

        parts = []

        if imgs:
            # if user doesn't input a list
            if isinstance(imgs, str) or isinstance(imgs, Image.Image):
                imgs = [imgs]

            img_b64s = [img_to_b64(x, resize_inputs) for x in imgs]
            parts.append([img_b64_part(x) for x in img_b64s])

        if prompt:
            parts.append({"text": prompt.strip()})

        query_params = {
            "generationConfig": {
                "temperature": temperature,
            },
            "contents": [{"parts": parts}],
        }

        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

        try:
            r = self.client.post(
                api_url, json=query_params, headers=headers, timeout=120
            )
        except httpx.exceptions.Timeout:
            print("Request Timeout")
            return None

        r_json = r.json()

        # check if no image was returned due to prohibited generation
        finish_reason = r_json["candidates"][0].get("finishReason")
        if finish_reason == "PROHIBITED_CONTENT":
            print(f"Image was not generated due to {finish_reason}.")
            return None

        response_parts = r_json["candidates"][0]["content"]["parts"]

        out_texts = []
        out_imgs = []
        out_img_paths = []

        # Gemini's API returns both text and image data in parts.
        # Multiple image generations are possible.
        for part in response_parts:
            if part.get("text"):
                out_texts.append(part["text"])
            elif part.get("inlineData"):
                out_imgs.append(b64_to_img(part["inlineData"]["data"]))

        if save:
            response_id = r_json["responseId"]
            out_type = "webp" if webp else "png"
            if len(out_imgs) == 1:
                out_img_path = f"{response_id}.{out_type}"
                out_imgs[0].save(out_img_path)
                out_img_paths.append(out_img_path)
            elif len(out_imgs) > 1:
                for i, img in enumerate(out_imgs):
                    out_img_path = f"{response_id}-{i}.{out_type}"
                    img.save(out_img_path)
                    out_img_paths.append(out_img_path)

        return ImageGen(texts=out_texts, images=out_imgs, image_paths=out_img_paths)

    def generate_n(self, n: int, **args):
        img = self.generate(n=1, **args)
        for _ in range(n - 1):
            img += self.generate(n=1, **args)
        return img


@dataclass
class ImageGen:
    texts: List[str] = field(default_factory=list)
    images: List[Image.Image] = field(default_factory=list)
    image_paths: List[str] = field(default_factory=list)

    @property
    def image(self):
        return self.images[0] if self.images else None

    @property
    def image_path(self):
        return self.image_paths[0] if self.image_paths else None

    @property
    def text(self):
        return self.texts[0] if self.texts else None

    def __add__(self, other):
        if isinstance(other, ImageGen):
            return ImageGen(
                images=self.images + other.images,
                image_paths=self.image_paths + other.image_paths,
            )
        else:
            raise TypeError("Unsupported operand type(s) for +")
