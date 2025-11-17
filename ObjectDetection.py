from PIL import Image
import numpy as np
from collections import deque
import math

def get_shape_and_area(pil_image: Image.Image,
                       min_component_area: int = 20,
                       foreground: str = "auto"):
    img = pil_image.convert("L")
    arr = np.array(img, dtype=np.uint8)
    bw = arr < 128

    if foreground == "auto":
        n_black = np.count_nonzero(bw)
        is_foreground_black = n_black <= arr.size - n_black
    elif foreground == "black":
        is_foreground_black = True
    elif foreground == "white":
        is_foreground_black = False
    else:
        raise ValueError("foreground must be 'auto', 'black', or 'white'")

    mask = bw if is_foreground_black else ~bw
    if not mask.any():
        return {"shape": "none", "area_px": 0}

    h, w = mask.shape
    visited = np.zeros_like(mask, bool)
    dirs = [(1,0),(-1,0),(0,1),(0,-1)]
    largest_component = []
    ys, xs = np.nonzero(mask)

    for k in range(len(ys)):
        y0, x0 = int(ys[k]), int(xs[k])
        if visited[y0, x0]:
            continue
        q = deque([(y0, x0)])
        visited[y0, x0] = True
        comp = []
        while q:
            y,x = q.popleft()
            comp.append((x,y))
            for dy,dx in dirs:
                ny, nx = y+dy, x+dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not visited[ny, nx]:
                    visited[ny, nx] = True
                    q.append((ny, nx))
        if len(comp) > len(largest_component):
            largest_component = comp

    pixel_count = len(largest_component)
    if pixel_count < min_component_area:
        return {"shape": "none", "area_px": 0}

    # convex hull (monotone chain)
    pts = sorted(set(largest_component))
    if len(pts) < 3:
        return {"shape": "none", "area_px": pixel_count}
    def cross(o,a,b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for p in pts:
        while len(lower)>=2 and cross(lower[-2], lower[-1], p) <= 0: lower.pop()
        lower.append(p)
    upper=[]
    for p in reversed(pts):
        while len(upper)>=2 and cross(upper[-2], upper[-1], p) <= 0: upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:
        return {"shape": "none", "area_px": pixel_count}

    # helpers: perimeter, shoelace, RDP, angle
    def perimeter(poly):
        return sum(math.hypot(poly[(i+1)%len(poly)][0]-poly[i][0], poly[(i+1)%len(poly)][1]-poly[i][1]) for i in range(len(poly)))
    def shoelace(poly):
        if len(poly) < 3: return 0.0
        s = sum(poly[i][0]*poly[(i+1)%len(poly)][1] - poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))
        return abs(s)*0.5
    def rdp(pts, eps):
        if len(pts) < 3: return pts[:]
        x1,y1 = pts[0]; x2,y2 = pts[-1]
        def dist(p):
            x0,y0 = p
            num = abs((y2-y1)*x0 - (x2-x1)*y0 + x2*y1 - y2*x1)
            den = math.hypot(y2-y1, x2-x1)
            return num/den if den!=0 else 0.0
        idx, maxd = 0, 0.0
        for i in range(1,len(pts)-1):
            d = dist(pts[i])
            if d > maxd: maxd, idx = d, i
        if maxd <= eps: return [pts[0], pts[-1]]
        left = rdp(pts[:idx+1], eps); right = rdp(pts[idx:], eps)
        return left[:-1] + right
    def angle(a,b,c):
        bax, bay = a[0]-b[0], a[1]-b[1]
        bcx, bcy = c[0]-b[0], c[1]-b[1]
        la = math.hypot(bax, bay); lb = math.hypot(bcx, bcy)
        if la*lb == 0: return 0.0
        cosv = max(-1.0, min(1.0, (bax*bcx+bay*bcy)/(la*lb)))
        return math.degrees(math.acos(cosv))

    per = perimeter(hull)
    eps = max(1.0, per * 0.01)
    simplified = rdp(hull, eps)
    if len(simplified) < 3: simplified = hull

    # pixel perimeter (edge pixel count)
    comp_set = set(largest_component)
    pixel_perimeter = sum(1 for x,y in largest_component if any((x+dx,y+dy) not in comp_set for dx,dy in dirs))
    n_vertices = len(simplified)

    # 1. Triangle
    if n_vertices == 3:
        return {"shape": "Triangulo", "area_px": pixel_count}

    # 2. Quad heuristics (square / rectangle / simplified triangle)
    if n_vertices == 4:
        def dist(a,b): return math.hypot(a[0]-b[0], a[1]-b[1])
        sides = [dist(simplified[i], simplified[(i+1)%4]) for i in range(4)]
        side_ratio = max(sides)/min(sides) if min(sides)>1e-6 else float('inf')
        angles = [angle(simplified[i-1], simplified[i], simplified[(i+1)%4]) for i in range(4)]
        angle_dev = sum(abs(a-90.0) for a in angles)/4.0

        if side_ratio <= 1.15 and angle_dev < 15.0:
            return {"shape": "Cuadrado", "area_px": pixel_count}
        if angle_dev < 25.0:
            return {"shape": "Rectangulo", "area_px": pixel_count}
        if any(a > 160.0 for a in angles):
            return {"shape": "Triangulo", "area_px": pixel_count}

        full_area = shoelace(simplified)
        for i in range(4):
            tri = [p for idx,p in enumerate(simplified) if idx!=i]
            if abs(full_area - shoelace(tri)) <= max(0.08*full_area, 2.0):
                return {"shape": "Triangulo", "area_px": pixel_count}

    # 3. Circle fallback / circularity checks
    if pixel_perimeter > 1e-6:
        circularity = (4.0 * math.pi * float(pixel_count)) / (pixel_perimeter * pixel_perimeter)
        if n_vertices not in (3,4):
            return {"shape": "Circulo", "area_px": pixel_count}
        if n_vertices == 4 and circularity < 0.65:
            return {"shape": "Circulo", "area_px": pixel_count}
        if circularity > 0.70:
            return {"shape": "Circulo", "area_px": pixel_count}

    return {"shape": "none", "area_px": pixel_count}
