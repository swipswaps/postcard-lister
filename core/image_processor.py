import os
from PIL import Image

def resize_and_pad(image: Image.Image, size: int = 1600, bg_color: str = "#000000") -> Image.Image:
    """Resize image to fit within a square of 'size'x'size' while preserving aspect ratio and pad with bg_color."""
    original = image.copy()
    original.thumbnail((size, size), Image.Resampling.LANCZOS)

    padded = Image.new("RGB", (size, size), bg_color)
    offset = ((size - original.width) // 2, (size - original.height) // 2)
    padded.paste(original, offset)
    return padded

def resize_by_height(image: Image.Image, max_height: int = 1600) -> Image.Image:
    """Resize image proportionally to max height."""
    w, h = image.size
    if h > max_height:
        new_w = int((max_height / h) * w)
        return image.resize((new_w, max_height), Image.Resampling.LANCZOS)
    return image

def combine_side_by_side(front: Image.Image, back: Image.Image) -> Image.Image:
    """Combine front and back side by side, NOT padded."""
    front = resize_by_height(front)
    back = resize_by_height(back)

    height = max(front.height, back.height)
    combined = Image.new("RGB", (front.width + back.width, height), "#000000")
    combined.paste(front, (0, (height - front.height) // 2))
    combined.paste(back, (front.width, (height - back.height) // 2))
    return combined

def process_image_set(front_path: str, back_path: str, output_dir: str, index: int, bg_color: str = "#000000") -> dict:
    """Process front/back into padded individual images, a side-by-side vision image, and a square final upload."""
    try:
        os.makedirs(output_dir, exist_ok=True)

        with Image.open(front_path) as front, Image.open(back_path) as back:
            front = front.convert("RGB")
            back = back.convert("RGB")

            # === Padded individual 1600x1600 ===
            padded_front = resize_and_pad(front, 1600, bg_color)
            padded_back = resize_and_pad(back, 1600, bg_color)

            front_out = os.path.join(output_dir, f"front_{index}.jpg")
            back_out = os.path.join(output_dir, f"back_{index}.jpg")
            padded_front.save(front_out, format="JPEG", quality=95)
            padded_back.save(back_out, format="JPEG", quality=95)

            # === Vision image (side by side, not padded) ===
            vision_img = combine_side_by_side(front, back)
            vision_out = os.path.join(output_dir, f"vision_{index}.jpg")
            vision_img.save(vision_out, format="JPEG", quality=95)

            # === Final upload (padded square version of side by side) ===
            size = max(vision_img.width, vision_img.height)
            padded_final = Image.new("RGB", (size, size), bg_color)
            offset = ((size - vision_img.width) // 2, (size - vision_img.height) // 2)
            padded_final.paste(vision_img, offset)
            final_out = os.path.join(output_dir, f"final_{index}.jpg")
            padded_final.save(final_out, format="JPEG", quality=95)

            return {
                "front": front_out,
                "back": back_out,
                "vision": vision_out,
                "final": final_out
            }

    except Exception as e:
        print(f"❌ Error processing postcard images:\nFront: {front_path}\nBack: {back_path}\nError: {e}")
        return {}