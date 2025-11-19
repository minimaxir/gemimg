import argparse
import os
from pathlib import Path

from .gemimg import GemImg
from .utils import save_image


def main():
    """CLI for generating images with GemImg."""
    parser = argparse.ArgumentParser(description="Generate images using the Gemini API.")

    parser.add_argument("prompt", help="The text prompt for image generation.")
    parser.add_argument(
        "-i",
        "--input-images",
        nargs="+",
        help="Optional paths to input images.",
        default=[],
    )
    parser.add_argument(
        "-o",
        "--output-file",
        help="Optional output filename. Defaults to output.png, output-2.png, etc.",
        default=None,
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("GEMINI_API_KEY"),
        help="API key for the Gemini API. Defaults to the GEMINI_API_KEY environment variable.",
    )
    parser.add_argument(
        "--model", default="gemini-2.5-flash-image", help="The model to use."
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("GOOGLE_GEMINI_BASE_URL"),
        help="Alternative Gemini API endpoint for your organization.",
    )
    parser.add_argument(
        "--aspect-ratio", default="1:1", help="Aspect ratio of the generated image."
    )
    parser.add_argument(
        "--no-resize",
        action="store_false",
        dest="resize_inputs",
        help="Do not resize input images.",
    )
    parser.add_argument(
        "--output-dir", default="", help="Directory to save the generated images."
    )
    parser.add_argument(
        "--temperature", type=float, default=1.0, help="Generation temperature."
    )
    parser.add_argument("--webp", action="store_true", help="Save as WEBP instead of PNG.")
    parser.add_argument(
        "-n", type=int, default=1, help="Number of images to generate."
    )
    parser.add_argument(
        "--store-prompt",
        action="store_true",
        help="Store the prompt in the image metadata.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force overwrite of existing files.",
    )

    args = parser.parse_args()

    if not args.api_key:
        parser.error(
            "API key is required. Provide it with --api-key or set the GEMINI_API_KEY environment variable."
        )

    if args.base_url:
        base_url = args.base_url
    else:
        base_url = "https://generativelanguage.googleapis.com"

    gem_img = GemImg(api_key=args.api_key, model=args.model, base_url=base_url)

    # We call generate with save=False to handle file saving manually.
    result = gem_img.generate(
        prompt=args.prompt,
        imgs=args.input_images,
        aspect_ratio=args.aspect_ratio,
        resize_inputs=args.resize_inputs,
        save=False,  # This is important
        temperature=args.temperature,
        webp=args.webp,
        n=args.n,
        store_prompt=args.store_prompt,
    )

    if result and result.images:
        ext = "webp" if args.webp else "png"
        
        # Determine base output path and name
        output_path = Path(args.output_dir)
        if args.output_file:
            base_name = Path(args.output_file).stem
            # If an extension is provided in the output file, it overrides the --webp flag
            if Path(args.output_file).suffix:
                ext = Path(args.output_file).suffix[1:]
        else:
            base_name = "output"

        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        # Save the generated images
        for i, img in enumerate(result.images):
            # Determine the initial proposed path
            if len(result.images) > 1:
                # For multiple images, always append index
                current_base = f"{base_name}-{i + 1}"
            else:
                # For a single image, use the base name
                current_base = base_name

            final_path = output_path / f"{current_base}.{ext}"
            
            # If not forcing overwrite, check for existence and find a unique name
            if not args.force:
                counter = 1
                while final_path.exists():
                    # If path exists, append a counter
                    final_path = output_path / f"{current_base}-{counter}.{ext}"
                    counter += 1

            save_image(img, str(final_path), args.store_prompt, args.prompt)
            print(f"Image saved to {final_path}")
    else:
        print("Failed to generate image.")


if __name__ == "__main__":
    main()
