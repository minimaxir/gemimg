# gemimg

gemimg is a lightweight Python package for easily interfacing with Google's [Gemini API](https://ai.google.dev) and the [Nano Banana model](https://deepmind.google/models/gemini/image/) (a.k.a. Gemini 2.5 Flash Image) and Nano Banana Pro with robust features. This tool allows for:

- Create images in many aspect ratios with only a few lines of code!
- Minimal dependencies, and does not use Google's Client SDK.
- Handles image I/O, including multi-image I/O and image encoding/decoding.
- Generates images only: no irrelevant text output
- Utilities for common use cases, such as saving, resizing, and compositing multiple images.
- Allows [optionally storing the prompt](docs/notebooks/store_prompt_metadata.ipynb) in the PNG metadata.

Although Gemini 2.5 Flash Image can be used for free in [Google AI Studio](https://aistudio.google.com/) or [Google Gemini](https://gemini.google.com/), those interfaces place a visible watermark on their outputs and have generation limits. Using gemimg and the Gemini API directly, not only do you have more programmatic control over the generation, but it's much easier to do more complex inputs which increases productivity for power users.

## Installation

gemimg can be installed [from PyPI](https://pypi.org/project/gemimg/):

```sh
pip3 install gemimg
```

```sh
uv pip install gemimg
```

## Demo

First, you will need to get a Gemini API key (from a GCP project which has billing information), or a free applicable API key.

```py3
from gemimg import GemImg

g = GemImg(api_key="AI...")
```

You can also pass the API key by storing it in an `.env` file with a `GEMINI_API_KEY` field in the working directory (recommended), or by setting the environment variable of `GEMINI_API_KEY` directly to the API key.

If you want to generate from Nano Banana Pro, you can specify the `model`:

```py3
from gemimg import GemImg

g = GemImg(model="gemini-3-pro-image-preview")
```

Now, you can generate images with a simple text prompt!

```py3
gen = g.generate("A kitten with prominent purple-and-green fur.")
```

![](/docs/notebooks/gens/JP28aM2cFOODqtsPi7_J8A0@0.5x.webp)

The generated image is stored as a `PIL.Image` object and can be retrieved with `gen.image` for passing again to Nano Banana for further edits. By default, `generate()` also automatically saves the generated image as a PNG file in the current working directory. You can save a WEBP instead by specifying `webp=True`, change the save directory by specifying `save_dir`, or disable the saving behavior with `save=False`.

Due to Nano Banana's multimodal text encoder, you can create nuanced prompts including details and positioning that are not as consistent in Flux or Midjourney:

```py3
prompt = """
Create an image of a three-dimensional pancake in the shape of a skull, garnished on top with blueberries and maple syrup.
"""

gen = g.generate(prompt)
```

![](/docs/notebooks/gens/7fm8aJD0Lp6ymtkPpqvn0QU@0.5x.webp)

Nano Banana allows you to make highly-targeted edits to images. With gemimg, you can pass along the image you just generated very easily for editing.

```py3
edit_prompt = """
Make ALL of the following edits to the image:
- Put a strawberry in the left eye socket.
- Put a blackberry in the right eye socket.
- Put a mint garnish on top of the pancake.
- Change the plate to a plate-shaped chocolate-chip cookie.
- Add happy people to the background.
"""

gen_edit = g.generate(edit_prompt, gen.image)
```

![](/docs/notebooks/gens/Yfu8aIfpHufVz7IP4_WEsAc@0.5x.webp)

You may have noticed from the previous example that the prompt input is a Markdown dashed list. As a model based off of Gemini's text encoder, Nano Banana is extremely responsive to Markdown formatting compared to older text encoders used in traditional image generation models, and you can prompt engineer highly nuanced subject and compositional requirements, and Nano Banana follows them with very high accuracy:

```py3
prompt = """
Create an image featuring three specific kittens in three specific positions.

All of the kittens MUST follow these descriptions EXACTLY:
- Left: a kitten with prominent black-and-silver fur, wearing both blue denim overalls and a blue plain denim baseball hat.
- Middle: a kitten with prominent white-and-gold fur and prominent gold-colored long goatee facial hair, wearing a 24k-carat golden monocle.
- Right: a kitten with prominent #9F2B68-and-#00FF00 fur, wearing a San Franciso Giants sports jersey.

Aspects of the image composition that MUST be followed EXACTLY:
- All kittens MUST be positioned according to the "rule of thirds" both horizontally and vertically.
- All kittens MUST lay prone, facing the camera.
- All kittens MUST have heterochromatic eye colors matching their two specified fur colors.
- The image is shot on top of a bed in a multimillion-dollar Victorian mansion.
- The image is a Pulitzer Prize winning cover photo for The New York Times with neutral diffuse 3PM lighting for both the subjects and background that complement each other.
- NEVER include any text, watermarks, or line overlays.
"""

gen = g.generate(prompt, aspect_ratio="16:9")
```

![](docs/notebooks/gens/s57haPv7FsOumtkP1e_mqQM.webp)

You can also input two (or more!) images/image paths to do things like combine images or put an object from Image A into Image B without having to train a [LoRA](https://huggingface.co/docs/diffusers/training/lora). For example, here's a mirror selfie of myself, and a fantasy lava pool generated with gemimg that beckons me to claim its power:

![](/docs/notebooks/gens/composite_max.webp)

```py3
edit_prompt = """
Make the person in the first image stand waist-deep in the lava of the second image. The person's arms are raise high in cheer.

The lighting of the person must match that of the second image.
"""

gen = g.generate(edit_prompt, ["max_woolf.webp", gen_volcano.image])
```

![](/docs/notebooks/gens/6HC-aLCQKc3Vz7IP9eeDyAI@0.5x.webp)

You can also guide the generation with an input image, similar to [ControlNet](https://github.com/lllyasviel/ControlNet) implementations. Giving Gemini 2.5 Flash Image this handmade input drawing and prompt:

![](docs/files/pose_control_base.png)

```py3
prompt = """
Generate an image of characters playing a poker game sitting at a green felt table, directly facing the front. This new image MUST map ALL of the following characters to the poses and facial expressions represented by the specified colors of the provided image:
- Green: Spongebob SquarePants
- Red: Shadow the Hedgehog
- Purple: Pedro Pascal
- Pink: Taylor Swift
- Blue: The Mona Lisa
- Yellow: Evangelion Unit-01 from "Neon Genesis Evangelion"

The image is an award-winning highly-detailed painting, oil on oaken canvas. All characters MUST adhere to the oil on oaken canvas artistic style, even if this varies from their typical styles. All characters must be present individually in the image.
"""

gen = g.generate(prompt, "pose_control_base.png")
```

![](docs/notebooks/gens/qEC-aPT-Joahz7IP07Lo4Qw.webp)

[Jupyter Notebook which randomizes the character order](docs/notebooks/pose_control.ipynb).

This is just the tip of the iceberg of things you can do with Nano Banana (a blog post is coming shortly). By leveraging Nano Banana's long context window, you can even give it HTML and have it render a webpage ([Jupyter Notebook](/docs/notebooks/html_webpage.ipynb)). And that's not even getting into JSON prompting of the model, which can offer _extremely_ granular control of the generation. ([Jupyter Notebook](docs/notebooks/character_json.ipynb))

## Grid Generation

One cost-effective way to generate images is to generate multiple images simultaneously within a single generation at a higher resolution. Nano Banana Pro can generate a contiguous grid of images in a single API call without requiring shenanigans, which gemimg then automatically slices into individual images. This is cheaper than generating images one at a time through the base Nano Banana, and also benefits from the image quality improvements of Nano Banana Pro. ([Jupyter Notebook](docs/notebooks/grid_generation.ipynb))

```py3
from gemimg import GemImg, Grid

g = GemImg(model="gemini-3-pro-image")

# Create a 2x2 grid configuration
grid = Grid(rows=2, cols=2, image_size="2K")
```

The `Grid` class lets you specify:

- `rows` and `cols`: Grid dimensions
- `aspect_ratio`: Aspect ratio for the base grid (default: "1:1")
- `image_size`: "1K", "2K", or "4K" (default: "2K")
- `save_original_image`: Whether to also save the full grid image (default: True)

Now you can generate multiple images with a single call by describing a grid layout in your prompt:

```py3
# The prompt should mention the grid dimensions and the number of distinct total images
prompt = """
Generate a 2x2 contiguous grid showing the four seasons with the same composition across all images:
- Spring - cherry blossoms in a park
- Summer - sunny beach with palm trees
- Autumn - colorful fall foliage in a forest
- Winter - snowy mountain landscape
"""

gen = g.generate(prompt, grid=grid)
print(f"Generated {len(gen.subimages)} images")
```

The original grid image is stored in `gen.images`, while the sliced subimages are stored in `gen.subimages` and saved individually. For maximum cost efficiency, use a 4x4 grid with 4K resolution to generate 16 Nano-Banana-sized images in a single API call (~$0.015/image):

```py3
grid_4x4 = Grid(rows=4, cols=4, image_size="4K")
# grid_4x4.num_images = 16
# grid_4x4.output_resolution = (1024, 1024)
# grid_4x4.grid_resolution = (4096, 4096)
```

## Command-Line Interface

gemimg can also be used from the command line without writing Python code:

```sh
gemimg "A kitten with prominent purple-and-green fur."
```

```sh
python -m gemimg "A kitten with prominent purple-and-green fur."
```

Common options: `-i/--input-images`, `-o/--output-file`, `--aspect-ratio`, `--output-dir`, `-n` (number of images), `--webp`, `--store-prompt`, `-f/--force`. The API key can be provided via `--api-key` or the `GEMINI_API_KEY` environment variable.

## Gemini 2.5 Flash Image Model Notes

- Gemini 2.5 Flash Image cannot do style transfer, e.g. `turn me into Studio Ghibli`, and seems to ignore commands that try to do so. Google's [developer documentation example](https://ai.google.dev/gemini-api/docs/image-generation#3_style_transfer) of style transfer unintentionally demonstrates this by [incorrectly applying](https://x.com/minimaxir/status/1963431053193810129) the specified style. The only way to shift the style is to generate a completely new image in that style, which can still have mixed results if the source style is intrinsic.
  - This also causes issues with the "put subject from Image A into Image B" use case if either are a substantially different style.
- Gemini 2.5 Flash Image does have moderation in the form of both prompt moderation and post-generation image moderation, although it's more leient than typical for Google's services. If an image is moderated or otherwise not present in the output, a `PROHIBITED_CONTENT` or `NO_IMAGE` error will be logged: the function will return `None` to make it easier to detect and rerun if needed.
- Gemini 2.5 Flash Image is unsurprisingly bad at free-form text generation, both in terms of text fidelity and frequency of typos. However, a workaround is to provide the rendered text as an input image, and ask the model to composite it with another image.
- Yes, both a) LLM-style prompt engineering with with Markdown-formated lists and b) old-school AI image style quality syntatic sugar such as `award-winning` and `DSLR camera` are both _extremely_ effective with Gemini 2.5 Flash Image, due to its text encoder and larger training dataset which can now more accurately discriminate which specific image traits are present in an award-winning image and what traits aren't. I've tried generations both with and without those tricks and the tricks definitely have an impact. Google's developer documentation [encourages the latter](https://ai.google.dev/gemini-api/docs/image-generation#best-practices).
- Cherry-picking outputs, in the sense that multiple generations with the same prompt are needed to get one good output, is surprisingly minimal for an image-generation model and Google 2.5 Flash Image tends to correctly interpret the intent on the first try. Any obvious logical mistakes are consistently fixed with more prompt engineering. Most superflous prompts you see in the examples are cases where such a fix is applied.
- Although the [Gemini 2.5 Flash Image API schema](https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash#image) suggests that it supports system prompts, it doesn't appear to have any impact on the resulting output, so they are not supported in this package.

## Miscellaneous Notes

- gemimg is intended to be bespoke and very tightly scoped. **Compatibility for other image generation APIs and/or endpoints will not be supported**, unless they follow the identical APIs (i.e. a hypothetical `gemini-3-flash-image`). As this repository is designed to be future-proof, there likely will not be many updates other than bug/compatability fixes.
- gemimg intentionally does not support true multiturn conversations within a single conversational thread as:
  1. The technical lift for doing so would no longer make this package lightweight
  2. It is unclear if it's actually better for the typical use cases.
- gemimg intentionally does not support text output (and therefore the "interweaving" use case from the API examples) because:
  1. Text output slows down the image generation, which is the purpose of this package
  2. Text output can cause the model to rethink aspects of the generations, which adds undesirable entropy to the prompt.
  3. Interweaving follows the same issues as generating multiple images in a single call and is unreliable.
- By default, input images to `generate()` are resized such that their max dimension is 1024px while maintaining the aspect ratio. This is done a) as a sanity safeguard against providing a massive image and b) to ensure efficient processing. However, images that are already at valid Gemini API dimensions (e.g., 1024x1024 for 1:1 aspect ratio) are not unnecessarily resized. If you want to disable resizing altogether, set `resize_inputs=False`.
- Do not question my example image prompts. I assure you, there is a specific reason or objective for every model input and prompt engineering trick. There is a method to my madness...although for this particular project I confess its more madness than method.

## Roadmap

- Async support (for parallel calls and [FastAPI](https://fastapi.tiangolo.com) support)
- Additional model parameters if the Gemini API supports them.

## Maintainer/Creator

Max Woolf ([@minimaxir](https://minimaxir.com))

_Max's open-source projects are supported by his [Patreon](https://www.patreon.com/minimaxir) and [GitHub Sponsors](https://github.com/sponsors/minimaxir). If you found this project helpful, any monetary contributions to the Patreon are appreciated and will be put to good creative use._

## License

MIT
