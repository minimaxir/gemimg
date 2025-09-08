# gemimg

gemimg is a lightweight (<400 LoC) Python package for easily interfacing with Google's Gemini API and the Gemini 2.5 Flash Image (a.k.a. Nano Banana) with robust features. This tool allows for:

- Create images with only a few lines of code!
- Handles image I/O, including multi-image I/O and image encoding/decoding.
- Utilities for common use cases, such as saving, resizing, and compositing multiple images.

Although Gemini 2.5 Flash Image can be used for free in Google AI Studio or Google Gemini, those interfaces place a visible watermark on their outputs and have generation limits. Using gemimg and the Gemini API directly, not only do you have more programmatic control over the generation.

## Installation

gemimg can be installed [from PyPI](https://pypi.org/project/gemimg/):

```sh
pip3 install gemimg
```

```sh
uv pip install gemimg
```

## Demo

First, you will need to get a Gemini API key (from a project which has billing information), or a free applicable API key.

```py3
from gemimg import GemImg

g = GemImg(api_key="AI...")
```

You can also pass the API key by storing it in an `.env` file with a `GEMINI_API_KEY` field in the working directory (recommended), or by setting the environment variable of `GEMINI_API_KEY` directly to the API key.

Now, you can generate images with a simple text prompt!

```py3
gen = g.generate("A kitten with prominent purple-and-green fur.")
```

The generated image is stored as a `PIL.Image` object and can be retrieved for example with `gen.image` for passing again to Gemini 2.5 Flash Image for further edits. By default, `generate()` also automatically saves the generated image as a PNG file in the current working directory. You can save a WEBP instead by specifying `webp=True`, change the save directory by specifying `save_dir`, or disable the saving behavior with `save=False`.

Due to Gemini 2.5 Flash Image's multimodal text encoder, you can create nuanced prompts including details and positioning that are not as effective in Flux or Midjourney:

```py3
prompt = """
Create an image of a three-dimensional pancake in the shape of a skull, garnished on top with blueberries and maple syrup.
"""

gen = g.generate(prompt)
```

![](/docs/notebooks/gens/7fm8aJD0Lp6ymtkPpqvn0QU@0.5x.webp)

Gemini 2.5 Flash Image allows you to make highly-targeted edits to images. With gemimg, you can pass along the image you just generated very easily for editing.

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

You can also input two (or more!) images/image paths to do things like combine images or put the object from Image A into Image B without having to train a [LoRA](https://huggingface.co/docs/diffusers/training/lora). For example, take this selfie of myself, and a fantasy lava pool generated with gemimg:

![](/docs/notebooks/gens/composite_max.webp)

```py3
edit_prompt = """
Make the person in the first image stand waist-deep in the lava of the second image. The person's arms are raise high in cheer.

The lighting of the person must match that of the second image.
"""

gen = g.generate(edit_prompt, ["max_woolf.webp", gen_volcano.image])
```

![](/docs/notebooks/gens/6HC-aLCQKc3Vz7IP9eeDyAI@0.5x.webp)

You can also guide the generation with an input image, similar to [ControlNet](https://github.com/lllyasviel/ControlNet) implementations. Giving Gemini 2.5 Flash Image this input drawing and prompt:

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

This is just the tip of the iceberg of things you can do with Gemini 2.5 Flash Image (a blog post is coming shortly). And that's not even getting into JSON prompting of the model, which can offer _extremely_ granular control of the generation. ([Jupyter Notebook](docs/notebooks/character_json.ipynb))

## Gemini 2.5 Flash Image Model Limitations

- Gemini 2.5 Flash Image does not support aspect ratio control, despite developer examples implying such. Prompt engineering the text to generate in a specific ratio does _not_ have any effect. The only method to control the aspect ratio is to provide it as an input image, as the generated image tends to follow the same aspect ration.
- Gemini 2.5 Flash Image cannot do style transfer, e.g. `turn me into Studio Ghibli`, and seems to ignore commands that try to do so. Google's developer documentation example of style transfer unintentionally demonstrates this by incorrectly applying the specified style. The only way to shift the style is to generate a completely new image.
  - This also causes issues with the "put subject from Image A into Image B" use case if either are a different style.
- Gemini 2.5 Flash Image does have moderation in the form of both prompt moderation and post-generation image moderation, although it's more leient than typical for Google's services. In the former case, the `gen.text` will indicate the refusal reason. In the latter case, a `PROHIBITED_CONTENT` error will be thrown.
- Gemini 2.5 Flash Image is unsurprisingly bad at free-form text generation, both in terms of text fidelity and frequency of typos. However, a workaround is to provide the rendered text as an input image, and ask the model to composite it with another image.
- Yes, both a) LLM-style prompt engineering with emphasis on specific words with Markdown-formatting and b) old-school AI image style quality enhancements such as `award-winning` and `DSLR camera` are both _extremely_ effective with Gemini 2.5 Flash Image, due to its text encoder and likely training data set which can now accurately discriminate such impacts. I've tried generations both with and without those tricks and the tricks definitely have an impact.

## Miscellaneous Notes

- gemimg is intended to be bespoke and very tightly scoped. **Support for other image generation APIs and/or endpoints will not be supported**, unless they follow the identical APIs (i.e. a hypothetical `gemini-3-flash-image`). As this repository is designed to be future-proof, there likely will not be many updates other than bug/compatability fixes.
- gemimg intentionally does not support true multiturn conversations within a single thread as a) the technical lift for doing so would no longer make this package lightweight and b) it is unclear if it's actually better for the typical use cases.
- By default, input images to `generate()` are resized such that their max dimension is 768px while maintaining the aspect ratio. This is done a) as a sanity safeguard against providing a massive image and b) Gemini processes images in tiles of 768x768px, so this forces the input to be 1 tile which should lower costs and improve consistency. If you want to disable this behavior, set `resize_inputs=False`.
- Do not question my example image prompts. I assure you, there is a specific reason or objective for every model input and prompt engineering trick. There is a method to my madness...although in this case I confess its more madness than method.

## Roadmap

- Async support (for parallel calls and [FastAPI](https://fastapi.tiangolo.com) support)
- Additional model parameters if the Gemini API supports them.

## Maintainer/Creator

Max Woolf ([@minimaxir](https://minimaxir.com))

_Max's open-source projects are supported by his [Patreon](https://www.patreon.com/minimaxir) and [GitHub Sponsors](https://github.com/sponsors/minimaxir). If you found this project helpful, any monetary contributions to the Patreon are appreciated and will be put to good creative use._

## License

MIT
