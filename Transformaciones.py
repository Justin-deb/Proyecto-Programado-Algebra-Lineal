from PIL import Image
import numpy as np
import math

def RotateImage(image: Image.Image, degree: float) -> Image.Image:
    # Convert angle from degrees to radians and precompute trig values
    theta = math.radians(degree)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    # Convert source image to a NumPy RGBA array (rows=height, cols=width)
    src = np.array(image.convert("RGBA"))
    height, width = src.shape[:2]

    # Prepare destination array with the same shape and dtype as source
    dst = np.zeros_like(src)

    # Compute image center in (x, y) coordinates using pixel-center alignment
    # Using (width-1)/2 and (height-1)/2 centers on the pixel grid properly.
    cx = (width - 1) / 2.0   # center x (column)
    cy = (height - 1) / 2.0  # center y (row)

    # Inverse mapping: for each pixel in destination, find corresponding source pixel
    for i in range(height):        # i -> destination row (y)
        for j in range(width):     # j -> destination column (x)
            # Destination coordinates relative to center
            x_out = j - cx
            y_out = i - cy

            # Apply inverse rotation (rotate by -theta) to map dest -> source
            x_src =  cos_t * x_out + sin_t * y_out
            y_src = -sin_t * x_out + cos_t * y_out

            # Convert back to absolute source indices (column, row), rounding for NN
            j_src = int(round(x_src + cx))  # source column (x)
            i_src = int(round(y_src + cy))  # source row (y)

            # Bounds check: rows compare to height, columns compare to width
            if 0 <= i_src < height and 0 <= j_src < width:
                # Copy nearest-neighbor pixel from source to destination
                dst[i, j] = src[i_src, j_src]
            # else: leave dst[i,j] as zero (transparent/black) for pixels outside source

    # Convert NumPy array back to a PIL Image and return
    return Image.fromarray(dst)

def resizeImage(image:Image.Image,max_width:int,max_height:int) -> Image.Image:
    src_arr = np.array(image.convert("RGBA"), dtype=np.uint8)
    src_h = src_arr.shape[0]   # source height (rows)
    src_w = src_arr.shape[1]   # source width  (cols)

    # Protect against zero-dimension images
    if src_w == 0 or src_h == 0:
        # Return a 1x1 transparent image with same mode as original
        empty = np.zeros((1, 1, 4), dtype=np.uint8)
        out_img = Image.fromarray(empty, mode="RGBA")
        if image.mode in ("RGB", "L"):
            out_img = out_img.convert(image.mode)
        return out_img

    # Compute scale factor that fits image inside (max_width x max_height)
    scale_w = max_width / src_w
    scale_h = max_height / src_h
    scale = scale_w if scale_w < scale_h else scale_h  # min(scale_w, scale_h) without tuple

    # Compute destination width and height as separate integers (no tuple)
    dst_w = int(round(src_w * scale))
    dst_h = int(round(src_h * scale))

    # Ensure at least 1 pixel in each dimension
    if dst_w < 1:
        dst_w = 1
    if dst_h < 1:
        dst_h = 1

    # Prepare destination buffer (RGBA)
    dst = np.zeros((dst_h, dst_w, 4), dtype=np.uint8)

    # Compute scale factors mapping destination pixel centers -> source coordinates
    scale_x = src_w / dst_w
    scale_y = src_h / dst_h

    # Nearest-neighbor sampling: loop over destination pixels
    for i in range(dst_h):                 # i -> destination row (y)
        # continuous source y coordinate for this row (pixel-center mapping)
        src_y = (i + 0.5) * scale_y - 0.5
        y_nearest = int(round(src_y))
        # clamp y index
        if y_nearest < 0:
            y_nearest = 0
        elif y_nearest >= src_h:
            y_nearest = src_h - 1

        for j in range(dst_w):             # j -> destination column (x)
            src_x = (j + 0.5) * scale_x - 0.5
            x_nearest = int(round(src_x))
            # clamp x index
            if x_nearest < 0:
                x_nearest = 0
            elif x_nearest >= src_w:
                x_nearest = src_w - 1

            # copy pixel from source to destination
            dst[i, j] = src_arr[y_nearest, x_nearest]

    # Convert back to PIL Image and restore original mode if needed
    out_img = Image.fromarray(dst, mode="RGBA")
    if image.mode in ("RGB", "L"):
        out_img = out_img.convert(image.mode)

    return out_img

def adjustContrast(image:Image.Image,factor:float) -> Image.Image:
    if factor == 1.0:
        return image.copy()

    src_mode = image.mode
    # Work in RGBA so we always have 4 channels to handle alpha safely
    src = np.array(image.convert("RGBA"), dtype=np.int16)  # use int16 to avoid overflow
    h, w = src.shape[:2]

    # Vectorized: apply transformation to RGB channels at once
    rgb = src[..., :3]                      # shape (h, w, 3)
    alpha = src[..., 3:]                    # shape (h, w, 1)

    # Move values around midpoint 128, multiply, then shift back
    adjusted_rgb = (rgb - 128) * factor + 128

    # Clip to valid byte range and convert back to uint8
    adjusted_rgb = np.clip(adjusted_rgb, 0, 255).astype(np.uint8)

    # Reassemble and preserve alpha channel unchanged
    dst = np.concatenate([adjusted_rgb, alpha.astype(np.uint8)], axis=2)

    # Convert back to PIL Image and restore original mode if needed
    out = Image.fromarray(dst, mode="RGBA")
    if src_mode in ("RGB", "L"):
        out = out.convert(src_mode)
    return out

def grayScale(image: Image.Image) -> Image.Image:
    """
    Convert a PIL Image (or image-like) to grayscale, preserving alpha if present.
    Returns a PIL.Image in mode 'L' (no alpha) or 'LA' (grayscale + alpha).
    """
    # If given a PIL Image, handle common modes explicitly to avoid re-scaling issues
    if isinstance(image, Image.Image):
        # Already 8-bit grayscale -> return a copy unchanged
        if image.mode == "L":
            return image.copy()

        # Already grayscale with alpha -> return a copy unchanged
        if image.mode == "LA":
            return image.copy()

        # Bilevel (1) -> convert to L
        if image.mode == "1":
            return image.convert("L")

        # Decide whether original had alpha
        had_alpha = "A" in image.mode

        # Convert to RGB/RGBA so np.array yields predictable channel layout
        if had_alpha:
            img = image.convert("RGBA")
        else:
            img = image.convert("RGB")

        arr = np.array(img)  # shape (H, W, 3) or (H, W, 4)

    else:
        # Not a PIL Image: assume it's array-like and convert
        arr = np.asarray(image)
        # if 2D, treat as grayscale; if it's 3D but channels==4 we treat alpha as present
        had_alpha = (arr.ndim == 3 and arr.shape[2] == 4)

        # If 2D numpy array, handle scaling for float/integer types below

    # If grayscale-like 2D array (already single-channel)
    if arr.ndim == 2:
        if np.issubdtype(arr.dtype, np.floating):
            # floats: if values look like 0..1 then scale to 0..255, otherwise assume already absolute
            mx = float(np.max(arr)) if arr.size else 0.0
            if mx <= 1.0:
                arr = (arr * 255.0).round()
        else:
            # integer types: if >255 scale down preserving range
            mx = int(np.max(arr)) if arr.size else 0
            if mx > 255:
                # scale down to 0..255
                arr = (arr.astype(np.float64) / mx * 255.0).round()

        gray_u8 = np.clip(arr, 0, 255).astype(np.uint8)
        # Preserve alpha only if caller passed a 2-channel array (rare). If original input was PIL LA we already returned earlier.
        if arr.ndim == 2:
            return Image.fromarray(gray_u8, mode="L")

    # Now arr has ndim == 3 (channels present)
    if arr.ndim == 3:
        ch = arr.shape[2]

        # If 1-channel stored as 3D (rare), squeeze
        if ch == 1:
            gray_u8 = arr[..., 0].astype(np.uint8)
            return Image.fromarray(gray_u8, mode="L")

        # If 2 channels, assume (L,A)
        if ch == 2:
            l = arr[..., 0]
            a = arr[..., 1].astype(np.uint8)
            # scale luminance if needed
            if np.issubdtype(l.dtype, np.floating) and l.max() <= 1.0:
                l = (l * 255.0).round()
            l = np.clip(l, 0, 255).astype(np.uint8)
            out = np.stack([l, a], axis=2)
            return Image.fromarray(out, mode="LA")

        # For 3+ channels: treat first three as RGB
        if ch >= 3:
            # Convert RGB to float
            rgb = arr[..., :3].astype(np.float32)

            # If floats in 0..1, scale to 0..255
            if np.issubdtype(arr.dtype, np.floating):
                if rgb.size and rgb.max() <= 1.0:
                    rgb = rgb * 255.0

            # Luminance weights (Rec. 601)
            weights = np.array([0.299, 0.587, 0.114], dtype=np.float32)

            gray = (rgb * weights).sum(axis=2)

            gray_u8 = np.clip(np.round(gray), 0, 255).astype(np.uint8)

            # If an alpha channel exists, keep it
            if ch >= 4:
                alpha = arr[..., 3].astype(np.uint8)
                out_arr = np.stack([gray_u8, alpha], axis=2)
                return Image.fromarray(out_arr, mode="LA")
            else:
                return Image.fromarray(gray_u8, mode="L")
    
def blackAndWhite(image:Image.Image) -> Image.Image:
    # Convert to RGBA array so alpha (if present) is preserved separately
    arr = np.array(image.convert("RGBA"), dtype=np.uint8)  # shape (H, W, 4)
    # detect whether original image had an alpha channel
    try:
        has_alpha = 'A' in image.getbands()
    except Exception:
        has_alpha = False
    h, w = arr.shape[0], arr.shape[1]

    # Compute grayscale luminance using luminosity formula
    rgb = arr[..., :3].astype(np.float32)
    gray = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]).astype(np.uint8)

    thr = 128
    # fixed or otsu: simple thresholding (vectorized)
    bw = np.where(gray >= thr, 255, 0).astype(np.uint8)

    # Reattach alpha channel if original had alpha; keep alpha unchanged
    alpha = arr[..., 3]
    if has_alpha:
        out_arr = np.stack([bw, alpha], axis=2)  # shape (H, W, 2) -> mode "LA"
        return Image.fromarray(out_arr, mode="LA")
    else:
        return Image.fromarray(bw, mode="L")