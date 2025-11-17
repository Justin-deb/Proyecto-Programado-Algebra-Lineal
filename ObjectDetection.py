from PIL import Image
import numpy as np
from collections import deque
import math

def get_shape_and_area(pil_image: Image.Image,
                       min_component_area: int = 20,
                       foreground: str = "auto"):
    """
    Detect shape and area for a black-and-white image.

    Returns a dict with keys:
      - shape: "circle" | "triangle" | "square" | "rectangle" | "none"
      - area_px: int (pixel count of the detected shape)
      - area_geom: float (polygon area from simplified hull)
    """
    img = pil_image.convert("L")
    arr = np.array(img, dtype=np.uint8)

    bw_image = arr < 128

    if foreground == "auto":
        n_black = np.count_nonzero(bw_image)
        n_white = arr.size - n_black
        is_foreground_black = n_black <= n_white
    elif foreground == "black":
        is_foreground_black = True
    elif foreground == "white":
        is_foreground_black = False
    else:
        raise ValueError("foreground must be 'auto', 'black', or 'white'")

    mask = bw_image if is_foreground_black else ~bw_image
    if not mask.any():
        return {"shape": "none", "area_px": 0, "area_geom": 0.0}

    h, w = mask.shape

    visited = np.zeros_like(mask, dtype=bool)
    largest_component = []
    largest_size = 0

    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    ys, xs = np.nonzero(mask)

    for idx in range(len(ys)):
        y0, x0 = int(ys[idx]), int(xs[idx])
        if visited[y0, x0]:
            continue

        q = deque([(y0, x0)])
        visited[y0, x0] = True
        component = []

        while q:
            y, x = q.popleft()
            component.append((x, y))
            for dy, dx in dirs:
                ny, nx = y + dy, x + dx
                if (0 <= ny < h and 0 <= nx < w and
                    mask[ny, nx] and not visited[ny, nx]):
                    visited[ny, nx] = True
                    q.append((ny, nx))

        if len(component) > largest_size:
            largest_size = len(component)
            largest_component = component

    pixel_count = len(largest_component)
    if pixel_count < min_component_area:
        return {"shape": "none", "area_px": 0, "area_geom": 0.0}

    def convex_hull(points):
        pts = sorted(set(points))
        if len(pts) <= 2:
            return pts

        def cross(o, a, b):
            return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

        lower = []
        for p in pts:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)

        upper = []
        for p in reversed(pts):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)

        return lower[:-1] + upper[:-1]

    def polygon_perimeter(poly):
        if len(poly) < 2:
            return 0.0
        s = 0.0
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i+1) % len(poly)]
            s += math.hypot(x2-x1, y2-y1)
        return s

    def shoelace_area(poly):
        if len(poly) < 3:
            return 0.0
        s = 0
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i+1) % n]
            s += x1*y2 - x2*y1
        return abs(s) * 0.5

    def ramer_douglas_peucker(points, eps):
        if len(points) < 3:
            return points[:]

        x1, y1 = points[0]
        x2, y2 = points[-1]

        def point_line_dist(pt):
            x0, y0 = pt
            num = abs((y2-y1)*x0 - (x2-x1)*y0 + x2*y1 - y2*x1)
            den = math.hypot(y2-y1, x2-x1)
            return num/den if den != 0 else 0.0

        maxd = 0.0
        idx = 0
        for i in range(1, len(points)-1):
            d = point_line_dist(points[i])
            if d > maxd:
                maxd = d
                idx = i

        if maxd <= eps:
            return [points[0], points[-1]]

        left = ramer_douglas_peucker(points[:idx+1], eps)
        right = ramer_douglas_peucker(points[idx:], eps)
        return left[:-1] + right

    def angle_between(a, b, c):
        bax = a[0]-b[0]
        bay = a[1]-b[1]
        bcx = c[0]-b[0]
        bcy = c[1]-b[1]

        dot = bax*bcx + bay*bcy
        la = math.hypot(bax, bay)
        lb = math.hypot(bcx, bcy)

        if la*lb == 0:
            return 0.0

        cosv = max(-1.0, min(1.0, dot/(la*lb)))
        return math.degrees(math.acos(cosv))

    hull = convex_hull(largest_component)
    if len(hull) < 3:
        return {"shape": "none", "area_px": pixel_count, "area_geom": 0.0}

    perimeter = polygon_perimeter(hull)
    eps = max(1.0, perimeter * 0.01)
    simplified_poly = ramer_douglas_peucker(hull, eps)
    if len(simplified_poly) < 3:
        simplified_poly = hull

    area_geom = shoelace_area(simplified_poly)

    def calculate_pixel_perimeter(component):
        component_set = set(component)
        perimeter = 0
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for x, y in component:
            for dx, dy in dirs:
                if (x + dx, y + dy) not in component_set:
                    perimeter += 1
        return perimeter

    pixel_perimeter = calculate_pixel_perimeter(largest_component)
    n_vertices = len(simplified_poly)

    # 1. Triangle
    if n_vertices == 3:
        return {"shape": "triangle", "area_px": pixel_count, "area_geom": float(area_geom)}

    # 2. Quad (square / rectangle) and triangle heuristics
    if n_vertices == 4:
        def distance(p1, p2):
            return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

        sides = [distance(simplified_poly[i], simplified_poly[(i+1)%4])
                 for i in range(4)]
        side_min = min(sides)
        side_max = max(sides)
        side_ratio = (side_max / side_min) if side_min > 1e-6 else float('inf')

        angles = [angle_between(simplified_poly[i-1], simplified_poly[i],
                               simplified_poly[(i+1)%4]) for i in range(4)]
        angle_deviation = sum(abs(a - 90.0) for a in angles) / 4.0

        if side_ratio <= 1.15 and angle_deviation < 15.0:
            return {"shape": "square", "area_px": pixel_count, "area_geom": float(area_geom)}

        if angle_deviation < 25.0:
            return {"shape": "rectangle", "area_px": pixel_count, "area_geom": float(area_geom)}

        # near-collinear vertex -> triangle
        collinear_thresh = 160.0
        if any(a > collinear_thresh for a in angles):
            return {"shape": "triangle", "area_px": pixel_count, "area_geom": float(area_geom)}

        # 3-vertex approximation test
        full_area = shoelace_area(simplified_poly)
        rel_tol = 0.08
        abs_tol = 2.0
        for i in range(4):
            tri = [p for idx, p in enumerate(simplified_poly) if idx != i]
            tri_area = shoelace_area(tri)
            if abs(full_area - tri_area) <= max(rel_tol * full_area, abs_tol):
                return {"shape": "triangle", "area_px": pixel_count, "area_geom": float(area_geom)}

    # 3. Circle (fallback or many-vertex shapes)
    if pixel_perimeter > 1e-6:
        circularity = (4.0 * math.pi * float(pixel_count)) / (pixel_perimeter * pixel_perimeter)
        if n_vertices != 3 and n_vertices != 4:
            return {"shape": "circle", "area_px": pixel_count, "area_geom": float(area_geom)}
        if n_vertices == 4 and circularity < 0.65:
            return {"shape": "triangle", "area_px": pixel_count, "area_geom": float(area_geom)}
        if circularity > 0.70:
            return {"shape": "circle", "area_px": pixel_count, "area_geom": float(area_geom)}

    return {"shape": "none", "area_px": pixel_count, "area_geom": float(area_geom)}
