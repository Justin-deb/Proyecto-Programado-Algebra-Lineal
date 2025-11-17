from PIL import Image
import numpy as np
import math

def RotateImage(image: Image.Image, degree: float) -> Image.Image:
    """Nearest-neighbor rotate around image center, preserving RGBA output."""
    theta = math.radians(degree)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    src = np.array(image.convert("RGBA"))
    h, w = src.shape[:2]
    if h == 0 or w == 0:
        return Image.fromarray(src)

    cx = (w - 1) / 2.0
    cy = (h - 1) / 2.0

    ys, xs = np.indices((h, w))
    x_out = xs - cx
    y_out = ys - cy

    x_src =  cos_t * x_out + sin_t * y_out
    y_src = -sin_t * x_out + cos_t * y_out

    j_src = np.rint(x_src + cx).astype(int)
    i_src = np.rint(y_src + cy).astype(int)

    valid = (i_src >= 0) & (i_src < h) & (j_src >= 0) & (j_src < w)
    dst = np.zeros_like(src)
    dst[valid] = src[i_src[valid], j_src[valid]]

    return Image.fromarray(dst)

def resizeImage(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    """Nearest-neighbor resize preserving mode (handles RGB/L and alpha)."""
    src_arr = np.array(image.convert("RGBA"), dtype=np.uint8)
    src_h, src_w = src_arr.shape[:2]
    if src_w == 0 or src_h == 0:
        return Image.new(image.mode, (1, 1))

    scale = min(max_width / src_w, max_height / src_h)
    dst_w = max(1, int(round(src_w * scale)))
    dst_h = max(1, int(round(src_h * scale)))

    # map dest centers to source coordinates, nearest neighbor
    dst_x = (np.arange(dst_w) + 0.5) * (src_w / dst_w) - 0.5
    dst_y = (np.arange(dst_h) + 0.5) * (src_h / dst_h) - 0.5
    j_src = np.rint(dst_x).clip(0, src_w - 1).astype(int)
    i_src = np.rint(dst_y).clip(0, src_h - 1).astype(int)

    dst = src_arr[i_src[:, None], j_src[None, :]]
    out = Image.fromarray(dst, mode="RGBA")
    if image.mode in ("RGB", "L"):
        out = out.convert(image.mode)
    return out

def adjustContrast(image: Image.Image, factor: float) -> Image.Image:
    """Adjust contrast around midpoint 128; preserves alpha and original mode."""
    if factor == 1.0:
        return image.copy()

    src_mode = image.mode
    arr = np.array(image.convert("RGBA")).astype(np.int16)  # avoid overflow
    rgb = arr[..., :3].astype(np.float32)
    alpha = arr[..., 3:]

    adjusted = (rgb - 128.0) * factor + 128.0
    adjusted = np.clip(np.rint(adjusted), 0, 255).astype(np.uint8)

    dst = np.concatenate([adjusted, alpha.astype(np.uint8)], axis=2)
    out = Image.fromarray(dst, mode="RGBA")
    if src_mode in ("RGB", "L"):
        out = out.convert(src_mode)
    return out

def grayScale(image: Image.Image) -> Image.Image:
    """Convert image to grayscale, preserving alpha as 'LA' if present."""
    if image.mode == "L":
        return image.copy()
    if image.mode == "LA":
        return image.copy()

    has_alpha = "A" in image.mode
    img = image.convert("RGBA") if has_alpha else image.convert("RGB")
    arr = np.array(img).astype(np.float32)

    rgb = arr[..., :3]
    # If floats in 0..1, scale up
    if np.issubdtype(arr.dtype, np.floating) and rgb.size and rgb.max() <= 1.0:
        rgb = rgb * 255.0

    weights = np.array([0.299, 0.587, 0.114], dtype=np.float32)
    gray = (rgb * weights).sum(axis=2)
    gray_u8 = np.clip(np.rint(gray), 0, 255).astype(np.uint8)

    if has_alpha:
        alpha = arr[..., 3].astype(np.uint8)
        out = np.stack([gray_u8, alpha], axis=2)
        return Image.fromarray(out, mode="LA")
    return Image.fromarray(gray_u8, mode="L")

def blackAndWhite(image: Image.Image) -> Image.Image:
    """Simple threshold at 128; preserves alpha channel if present (returns 'LA')."""
    img = image.convert("RGBA")
    arr = np.array(img)
    rgb = arr[..., :3].astype(np.float32)
    gray = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]).astype(np.uint8)
    bw = np.where(gray >= 128, 255, 0).astype(np.uint8)
    alpha = arr[..., 3]
    # If original had no alpha, return 'L' image; else 'LA'
    try:
        has_alpha = 'A' in image.getbands()
    except Exception:
        has_alpha = False

    if has_alpha:
        out = np.stack([bw, alpha], axis=2)
        return Image.fromarray(out, mode="LA")
    return Image.fromarray(bw, mode="L")