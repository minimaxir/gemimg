"""Grid class for generating images in grid layouts with Nano Banana Pro."""

import logging
from dataclasses import dataclass
from typing import List, Tuple

from PIL import Image

from .utils import VALID_ASPECTS_PRO, _validate_aspect

logger = logging.getLogger(__name__)


@dataclass
class Grid:
    """Represents a grid configuration for multi-image generation.

    This class encapsulates grid parameters for generating multiple images
    in a single API call using Nano Banana Pro's grid generation capabilities.

    Attributes:
        rows: Number of rows in the grid
        cols: Number of columns in the grid
        aspect_ratio: Aspect ratio string (e.g., "1:1", "16:9")
        image_size: Output image size ("1K", "2K", or "4K")
        save_original_image: Whether to save the original grid image before slicing
    """

    rows: int
    cols: int
    aspect_ratio: str = "1:1"
    image_size: str = "2K"
    save_original_image: bool = True

    def __post_init__(self) -> None:
        """Validate grid parameters."""
        if self.rows < 1 or self.cols < 1:
            raise ValueError(
                f"Grid dimensions must be positive integers, got rows={self.rows}, cols={self.cols}"
            )

        if self.rows * self.cols > 16:
            logger.warning(
                f"Grid size {self.rows}x{self.cols} ({self.rows * self.cols} cells) exceeds 16 cells. "
                "This may result in poor image quality or generation failures."
            )

        _validate_aspect(self.aspect_ratio, is_pro=True)

        if self.image_size not in ["1K", "2K", "4K"]:
            raise ValueError(
                f"image_size must be one of '1K', '2K', or '4K', got {self.image_size}"
            )

    @property
    def num_images(self) -> int:
        """Number of images that will be generated in this grid.

        Returns:
            Total number of images (rows * cols)
        """
        return self.rows * self.cols

    @property
    def grid_resolution(self) -> Tuple[int, int]:
        """Total resolution of the full grid image (all cells combined).

        Returns:
            Tuple of (width, height) in pixels for the complete grid
        """
        base_resolution = VALID_ASPECTS_PRO[self.aspect_ratio]

        # Scale based on image_size
        if self.image_size == "1K":
            return base_resolution
        elif self.image_size == "2K":
            return (base_resolution[0] * 2, base_resolution[1] * 2)
        else:  # "4K"
            return (base_resolution[0] * 4, base_resolution[1] * 4)

    @property
    def output_resolution(self) -> Tuple[int, int]:
        """Output resolution for each individual image in the grid.

        This is the resolution of each cell in the grid, not the total grid size.

        Returns:
            Tuple of (width, height) in pixels for each generated image
        """
        grid_width, grid_height = self.grid_resolution
        return (grid_width // self.cols, grid_height // self.rows)

    def __repr__(self) -> str:
        """Return string representation of the Grid."""
        return (
            f"Grid(rows={self.rows}, cols={self.cols}, aspect_ratio='{self.aspect_ratio}', "
            f"image_size='{self.image_size}', num_images={self.num_images}, "
            f"output_resolution={self.output_resolution})"
        )

    def slice_image(self, img: Image.Image) -> List[Image.Image]:
        """Slice a grid image into individual subimages.

        Args:
            img: The full grid image to slice

        Returns:
            List of PIL Images, one for each cell in row-major order
        """
        width, height = img.size
        cell_width = width // self.cols
        cell_height = height // self.rows

        subimages = []
        for row in range(self.rows):
            for col in range(self.cols):
                left = col * cell_width
                upper = row * cell_height
                right = left + cell_width
                lower = upper + cell_height
                subimages.append(img.crop((left, upper, right, lower)))

        return subimages
