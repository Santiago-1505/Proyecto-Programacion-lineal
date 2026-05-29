"""
Solver gráfico para problemas de programación lineal en 2 variables.

Proporciona funciones puras para:
 - convertir restricciones a semiplanos (ax + by <= c)
 - calcular intersecciones relevantes
 - determinar la región factible usando intersección de semiplanos
 - evaluar la función objetivo en vértices factibles

La API principal es `solve_graphical(objetivo: str, tipo_opt: str, restricciones: list)`
que retorna un dict con la información necesaria para la UI.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional
import math

from core.modelo import Restriccion, TipoRestriccion
from core.parser.expresion import vectorizar_expresion, obtener_max_indice_variable

# Tolerancia numérica
EPS = 1e-9


@dataclass
class Line:
    a: float
    b: float
    c: float
    # original restriction index for labels
    idx: Optional[int] = None

    def is_vertical(self) -> bool:
        return abs(self.b) < EPS and abs(self.a) > EPS

    def is_horizontal(self) -> bool:
        return abs(self.a) < EPS and abs(self.b) > EPS


@dataclass
class HalfPlane:
    # represents ax + by <= c
    a: float
    b: float
    c: float
    idx: Optional[int] = None

    def contains(self, x: float, y: float, eps: float = EPS) -> bool:
        return self.a * x + self.b * y <= self.c + eps


@dataclass
class GraphicalResult:
    feasible_vertices: List[Tuple[float, float]]
    polygon: Optional[List[Tuple[float, float]]]
    is_bounded: bool
    infeasible: bool
    optimum_point: Optional[Tuple[float, float]]
    optimum_value: Optional[float]
    all_candidates: List[Tuple[float, float]]
    lines: List[Line]
    warnings: List[str]
    # rays: list of direction vectors (unit) indicating recession directions when unbounded
    rays: List[Tuple[float, float]] = None
    # Objective vector (c1, c2) for plotting the objective line
    obj_vec: Optional[Tuple[float, float]] = None


def _line_from_coeffs(a: float, b: float, c: float, idx: Optional[int] = None) -> Line:
    return Line(a, b, c, idx=idx)


def _halfplanes_from_restricciones(restricciones: List[Restriccion], include_nonnegativity: bool = True) -> Tuple[List[HalfPlane], List[Line]]:
    """Convierte la lista de Restriccion a halfplanes ax+by <= c.

    Devuelve lista de HalfPlane y lista de Line (ax+by=c) para cada restricción original.
    """
    halfplanes: List[HalfPlane] = []
    lines: List[Line] = []

    # Primero determinar número de variables para vectorizar
    max_idx = 0
    # intentar inferir desde restricciones
    for r in restricciones:
        max_idx = max(max_idx, obtener_max_indice_variable(r.lado_izquierdo))

    for i, r in enumerate(restricciones):
        vec = vectorizar_expresion(r.lado_izquierdo, max_idx)
        # Solo las primeras dos variables importan para el gráfico
        a = vec[0] if len(vec) >= 1 else 0.0
        b = vec[1] if len(vec) >= 2 else 0.0
        try:
            c = float(r.lado_derecho)
        except Exception:
            raise ValueError(f"Lado derecho de restricción debe ser numérico: {r.lado_derecho}")

        # Normalizar según tipo
        if r.tipo == TipoRestriccion.MENOR_IGUAL:
            halfplanes.append(HalfPlane(a, b, c, idx=i))
            lines.append(_line_from_coeffs(a, b, c, idx=i))
        elif r.tipo == TipoRestriccion.MAYOR_IGUAL:
            # multiply by -1 to convert to <=
            halfplanes.append(HalfPlane(-a, -b, -c, idx=i))
            lines.append(_line_from_coeffs(a, b, c, idx=i))
        elif r.tipo == TipoRestriccion.IGUALDAD:
            # equality -> both <= and >= (i.e., add -a,-b,-c)
            halfplanes.append(HalfPlane(a, b, c, idx=i))
            halfplanes.append(HalfPlane(-a, -b, -c, idx=i))
            lines.append(_line_from_coeffs(a, b, c, idx=i))
        else:
            raise ValueError(f"Tipo de restricción desconocido: {r.tipo}")

    if include_nonnegativity:
        # x >= 0 -> -1*x + 0*y <= 0  (i.e., -x <= 0)
        halfplanes.append(HalfPlane(-1.0, 0.0, 0.0, idx=None))
        # y >= 0 -> 0*x -1*y <= 0
        halfplanes.append(HalfPlane(0.0, -1.0, 0.0, idx=None))
        lines.append(_line_from_coeffs(1.0, 0.0, 0.0, idx=None))
        lines.append(_line_from_coeffs(0.0, 1.0, 0.0, idx=None))

    return halfplanes, lines


def _intersect_lines(l1: Line, l2: Line) -> Optional[Tuple[float, float]]:
    a1, b1, c1 = l1.a, l1.b, l1.c
    a2, b2, c2 = l2.a, l2.b, l2.c
    det = a1 * b2 - a2 * b1
    if abs(det) < EPS:
        return None
    x = (c1 * b2 - c2 * b1) / det
    y = (a1 * c2 - a2 * c1) / det
    if not (math.isfinite(x) and math.isfinite(y)):
        return None
    return (x, y)


def _pairwise_candidate_points(halfplanes: List[HalfPlane], lines: List[Line]) -> List[Tuple[float, float]]:
    # Build all pairwise intersections of lines (include lines built from halfplanes)
    pts = []
    n = len(lines)
    for i in range(n):
        for j in range(i + 1, n):
            p = _intersect_lines(lines[i], lines[j])
            if p is not None:
                pts.append(p)
    return pts


# --------------------- Half-Plane Intersection (HPI) ---------------------


@dataclass
class _HPLine:
    # Represent line for HPI with a point p and direction d (both tuples)
    p: Tuple[float, float]
    d: Tuple[float, float]
    a: float
    b: float
    c: float
    angle: float

    def point_at(self, t: float) -> Tuple[float, float]:
        return (self.p[0] + self.d[0] * t, self.p[1] + self.d[1] * t)


def _make_hpline_from_halfplane(hp: HalfPlane) -> _HPLine:
    a, b, c = hp.a, hp.b, hp.c
    # pick a point on the line ax+by=c
    if abs(a) > abs(b):
        p = (c / a, 0.0)
    else:
        if abs(b) < EPS:
            p = (0.0, 0.0)
        else:
            p = (0.0, c / b)
    # direction vector perpendicular to normal (a,b)
    # choose d = (-b, a)
    d = (-b, a)
    # ensure left side of directed line corresponds to ax+by <= c
    # for a test point q = p + d, compute sign = a*qx + b*qy - c
    q = (p[0] + d[0] * 1e-3, p[1] + d[1] * 1e-3)
    sign = a * q[0] + b * q[1] - c
    if sign > 0:
        # left side of d is ax+by >= c; flip direction
        d = (-d[0], -d[1])
    angle = math.atan2(d[1], d[0])
    return _HPLine(p=p, d=d, a=a, b=b, c=c, angle=angle)


def _line_intersection_hp(l1: _HPLine, l2: _HPLine) -> Optional[Tuple[float, float]]:
    # Solve p1 + t*d1 = p2 + s*d2
    (x1, y1), (dx1, dy1) = l1.p, l1.d
    (x2, y2), (dx2, dy2) = l2.p, l2.d
    det = dx1 * dy2 - dy1 * dx2
    if abs(det) < EPS:
        return None
    t = ((x2 - x1) * dy2 - (y2 - y1) * dx2) / det
    return (x1 + dx1 * t, y1 + dy1 * t)


def _is_outside(hp: HalfPlane, point: Tuple[float, float]) -> bool:
    x, y = point
    return hp.a * x + hp.b * y - hp.c > EPS


def halfplane_intersection(halfplanes: List[HalfPlane]) -> Tuple[str, Optional[List[Tuple[float, float]]]]:
    """Computa la intersección de semiplanos (HPI).

    Retorna una tupla (status, polygon) donde status es uno de:
      - 'bounded': polygon is a list of vertices (closed polygon)
      - 'empty': intersection is empty (no feasible point)
      - 'unbounded': intersection non-empty but unbounded
      - 'unknown': no reliable result

    polygon es None salvo cuando status == 'bounded'.
    """
    # Convert to HPLine
    hplines = [_make_hpline_from_halfplane(hp) for hp in halfplanes]
    # Sort by angle
    hplines.sort(key=lambda l: (round(l.angle, 12), l.angle))

    # Remove lines with same angle, keep the most restrictive
    filtered: List[_HPLine] = []
    for hl in hplines:
        if not filtered:
            filtered.append(hl)
            continue
        if abs(hl.angle - filtered[-1].angle) < 1e-12:
            # choose the one whose halfplane contains a point of the other line
            # test a point on hl.p whether it's inside filtered[-1]
            test_pt = hl.p
            hp1 = HalfPlane(hl.a, hl.b, hl.c)
            hp2 = HalfPlane(filtered[-1].a, filtered[-1].b, filtered[-1].c)
            if hp2.contains(test_pt[0], test_pt[1]):
                # filtered[-1] is less restrictive, replace it
                filtered[-1] = hl
            # else keep filtered[-1]
        else:
            filtered.append(hl)

    from collections import deque
    dq = deque()
    pts = deque()

    for hl in filtered:
        while len(dq) >= 2:
            inter = _line_intersection_hp(dq[-1], dq[-2])
            if inter is None:
                break
            if _is_outside(HalfPlane(hl.a, hl.b, hl.c), inter):
                dq.pop(); pts.pop()
            else:
                break
        while len(dq) >= 2:
            inter = _line_intersection_hp(dq[0], dq[1])
            if inter is None:
                break
            if _is_outside(HalfPlane(hl.a, hl.b, hl.c), inter):
                dq.popleft(); pts.popleft()
            else:
                break
        dq.append(hl)
        if len(dq) >= 2:
            inter = _line_intersection_hp(dq[-1], dq[-2])
            if inter is None:
                # parallel lines – check feasibility
                continue
            pts.append(inter)

    # Final cleanup
    while len(dq) > 2:
        inter = _line_intersection_hp(dq[-1], dq[-2])
        if inter is None:
            break
        if _is_outside(HalfPlane(dq[0].a, dq[0].b, dq[0].c), inter):
            dq.pop(); pts.pop()
        else:
            break

    if len(pts) == 0:
        return ('empty', None)

    # close polygon with intersection of first and last
    last_inter = _line_intersection_hp(dq[0], dq[-1])
    if last_inter is not None:
        pts.append(last_inter)

    polygon = list(pts)
    # verify that polygon points are inside all halfplanes
    for p in polygon:
        for hp in halfplanes:
            if _is_outside(hp, p):
                # numeric issue or empty
                return ('unknown', None)

    # Clean polygon via convex hull to remove duplicates / collinear repeats
    try:
        hull = _convex_hull(polygon)
    except Exception:
        hull = polygon

    # compute polygon area (shoelace)
    def _area(pts_list):
        if len(pts_list) < 3:
            return 0.0
        a = 0.0
        n = len(pts_list)
        for i in range(n):
            x1, y1 = pts_list[i]
            x2, y2 = pts_list[(i + 1) % n]
            a += x1 * y2 - x2 * y1
        return abs(a) * 0.5

    area = _area(hull)
    if area < 1e-9 or len(hull) < 3:
        # Degenerate polygon (likely wedge or point) — treat as unbounded
        return ('unbounded', None)

    return ('bounded', hull)


def _unique_points(points: List[Tuple[float, float]], eps: float = 1e-8) -> List[Tuple[float, float]]:
    uniq: List[Tuple[float, float]] = []
    for x, y in points:
        found = False
        for ux, uy in uniq:
            if abs(x - ux) <= eps and abs(y - uy) <= eps:
                found = True
                break
        if not found:
            uniq.append((x, y))
    return uniq


def _filter_feasible(points: List[Tuple[float, float]], halfplanes: List[HalfPlane], eps: float = EPS) -> List[Tuple[float, float]]:
    feasible = []
    for x, y in points:
        ok = True
        for hp in halfplanes:
            if not hp.contains(x, y, eps=eps):
                ok = False
                break
        if ok:
            feasible.append((x, y))
    return feasible


def _evaluate_objective_at_points(obj_vec: Tuple[float, float], points: List[Tuple[float, float]]) -> List[float]:
    c1, c2 = obj_vec
    vals = [c1 * x + c2 * y for x, y in points]
    return vals


def solve_graphical(objetivo: str, tipo_opt: str, restricciones: List[Restriccion], include_nonnegativity: bool = True) -> GraphicalResult:
    """Resuelve el problema en 2 variables usando método gráfico.

    Args:
        objetivo: cadena, p.ej. '2x1 + 3x2'
        tipo_opt: 'max' o 'min'
        restricciones: lista de Restriccion
        include_nonnegativity: incluir x,y >= 0

    Retorna: GraphicalResult
    """
    warnings: List[str] = []

    # Validar cantidad de variables en objetivo/restricciones
    max_idx = obtener_max_indice_variable(objetivo)
    for r in restricciones:
        max_idx = max(max_idx, obtener_max_indice_variable(r.lado_izquierdo))
    if max_idx < 2:
        # pad with zeros (still valid)
        pass
    if max_idx > 2:
        raise ValueError("El método gráfico sólo soporta exactamente 2 variables de decisión")

    halfplanes, lines = _halfplanes_from_restricciones(restricciones, include_nonnegativity=include_nonnegativity)

    # Use HPI to compute the exact polygon of intersection when possible
    status, polygon = halfplane_intersection(halfplanes)

    candidates = []
    feasible = []
    is_bounded = False

    if status == 'bounded' and polygon:
        # polygon returned: take its vertices as feasible candidates
        polygon_unique = _unique_points(polygon)
        candidates = polygon_unique
        feasible = _filter_feasible(candidates, halfplanes)
        feasible = _unique_points(feasible)
        is_bounded = True
    elif status == 'empty':
        return GraphicalResult(
            feasible_vertices=[],
            polygon=None,
            is_bounded=False,
            infeasible=True,
            optimum_point=None,
            optimum_value=None,
            all_candidates=[],
            lines=lines,
            warnings=["Región factible vacía"],
        )
    else:
        # status == 'unbounded' or 'unknown': fallback to pairwise intersections
        candidates = _pairwise_candidate_points(halfplanes, lines)
        candidates = _unique_points(candidates)
        feasible = _filter_feasible(candidates, halfplanes)
        feasible = _unique_points(feasible)

        # If still no feasible points, try a few test points to decide infeasibility
        if not feasible:
            test_points = [(0.0, 0.0)] + candidates[:3]
            any_ok = False
            for p in test_points:
                if all(hp.contains(p[0], p[1]) for hp in halfplanes):
                    any_ok = True
                    feasible.append(p)
                    break
            if not any_ok:
                return GraphicalResult(
                    feasible_vertices=[],
                    polygon=None,
                    is_bounded=False,
                    infeasible=True,
                    optimum_point=None,
                    optimum_value=None,
                    all_candidates=candidates,
                    lines=lines,
                    warnings=["Región factible vacía o no determinada"],
                )

    # Evaluate objective on feasible vertices
    # Build objective vector
    obj_vec_full = vectorizar_expresion(objetivo, 2)
    obj_vec = (obj_vec_full[0], obj_vec_full[1])

    vals = _evaluate_objective_at_points(obj_vec, feasible)
    if not vals:
        return GraphicalResult(
            feasible_vertices=[],
            polygon=None,
            is_bounded=False,
            infeasible=True,
            optimum_point=None,
            optimum_value=None,
            all_candidates=candidates,
            lines=lines,
            warnings=["No se encontraron valores de evaluación para la función objetivo"],
        )

    if tipo_opt.lower() == 'max':
        best_idx = int(max(range(len(vals)), key=lambda i: vals[i]))
    else:
        best_idx = int(min(range(len(vals)), key=lambda i: vals[i]))

    optimum_point = feasible[best_idx]
    optimum_value = vals[best_idx]

    # If HPI indicated unbounded, try to compute recession directions (rays)
    rays: List[Tuple[float, float]] = []
    if status == 'unbounded':
        # Recession cone approx: directions d such that a_i d_x + b_i d_y <= 0 for all halfplanes
        # Solve by sampling unit directions on circle and testing.
        for theta in [i * math.pi / 180.0 for i in range(0, 360, 10)]:
            dx, dy = math.cos(theta), math.sin(theta)
            ok = True
            for hp in halfplanes:
                if hp.a * dx + hp.b * dy > EPS:
                    ok = False
                    break
            if ok:
                rays.append((dx, dy))
        # reduce duplicates and keep unit vectors
        rays = _unique_points(rays, eps=1e-6)

    # If polygon not produced yet, attempt convex hull from feasible points
    if status != 'bounded':
        # If HPI indicated unboundedness, we should mark accordingly. If we couldn't
        # determine bounded polygon but convex hull exists, we use convex hull as a
        # plotting aid but keep is_bounded=False when status was 'unbounded'.
        try:
            polygon_hull = _convex_hull(feasible) if feasible else None
        except Exception:
            polygon_hull = None
        if status == 'unbounded':
            polygon = polygon_hull
            is_bounded = False
        elif status == 'unknown':
            polygon = polygon_hull
            is_bounded = bool(polygon_hull)
        else:
            polygon = polygon_hull
            is_bounded = bool(polygon_hull)

    return GraphicalResult(
        feasible_vertices=feasible,
        polygon=polygon,
        is_bounded=is_bounded,
        infeasible=False,
        optimum_point=optimum_point,
        optimum_value=optimum_value,
        all_candidates=candidates,
        lines=lines,
        warnings=warnings,
        rays=rays,
        obj_vec=obj_vec,
    )


def _convex_hull(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Computa la envolvente convexa 2D de un conjunto de puntos (Graham/Monotone chain).

    Retorna lista de puntos en orden (CW o CCW).
    """
    pts = sorted(points)
    if len(pts) <= 1:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= EPS:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= EPS:
            upper.pop()
        upper.append(p)

    # concat lower and upper to get full hull (exclude last point of each because it's repeated)
    hull = lower[:-1] + upper[:-1]
    return hull
