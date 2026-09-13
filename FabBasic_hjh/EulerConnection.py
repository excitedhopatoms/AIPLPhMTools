import numpy as np
import gdsfactory as gf
from scipy.optimize import least_squares


# ============================================================
# Basic utilities
# ============================================================

def _normalize_angle(angle):
    """Normalize angle to [-pi, pi)."""
    return (angle + np.pi) % (2 * np.pi) - np.pi


def _angle_diff(a, b):
    """Smallest signed angle a-b."""
    return _normalize_angle(a - b)


def _rotate(points, angle):
    """Rotate Nx2 points by angle."""
    c = np.cos(angle)
    s = np.sin(angle)

    R = np.array([
        [c, -s],
        [s,  c],
    ])

    return points @ R.T


# ============================================================
# Euler / clothoid segment
# ============================================================

def _integrate_euler_segment(
    length,
    radius,
    theta_total,
    n=100,
):
    """
    Generate a symmetric Euler bend.

    Curvature:
        0 -> kmax -> 0

    Parameters
    ----------
    length : float
        Total length of the Euler bend.

    radius : float
        Minimum radius at maximum curvature.

    theta_total : float
        Total turning angle [rad].

    n : int
        Number of sampling points.

    Returns
    -------
    points : (N, 2)
        Centerline coordinates.
    """

    if abs(theta_total) < 1e-12:
        x = np.linspace(0, length, n)
        y = np.zeros_like(x)
        return np.column_stack([x, y])

    sign = np.sign(theta_total)
    theta = abs(theta_total)

    # Symmetric Euler bend:
    #
    # first half:
    #   curvature increases linearly
    #
    # second half:
    #   curvature decreases linearly
    #
    # Total angle:
    #
    # theta = kmax * L / 2
    #
    # where kmax = 1/R
    #
    # Therefore:
    #
    # theta = L / (2R)
    #
    # but this corresponds to a pure triangular curvature profile.

    kmax = 1.0 / radius

    L_euler = theta / kmax

    # If requested total length is too short,
    # use the minimum Euler length.
    if length < L_euler:
        length = L_euler

    # Add constant curvature section if needed.
    L_transition = L_euler / 2
    L_arc = length - 2 * L_transition

    # Curvature slope
    alpha = kmax / L_transition

    # Sampling by arc length
    s = np.linspace(0, length, n)

    k = np.zeros_like(s)

    mask1 = s <= L_transition
    k[mask1] = alpha * s[mask1]

    mask2 = (s > L_transition) & (s <= L_transition + L_arc)
    k[mask2] = kmax

    mask3 = s > L_transition + L_arc
    k[mask3] = kmax - alpha * (
        s[mask3] - L_transition - L_arc
    )

    # Integrate curvature -> angle
    ds = s[1] - s[0]

    phi = np.zeros_like(s)

    for i in range(1, len(s)):
        phi[i] = phi[i - 1] + 0.5 * (
            k[i - 1] + k[i]
        ) * ds

    phi *= sign

    # Integrate tangent -> x,y
    x = np.zeros_like(s)
    y = np.zeros_like(s)

    for i in range(1, len(s)):
        x[i] = x[i - 1] + 0.5 * (
            np.cos(phi[i - 1])
            + np.cos(phi[i])
        ) * ds

        y[i] = y[i - 1] + 0.5 * (
            np.sin(phi[i - 1])
            + np.sin(phi[i])
        ) * ds

    return np.column_stack([x, y])


# ============================================================
# Euler bend with arbitrary initial direction
# ============================================================

def _make_euler_segment(
    start,
    heading,
    length,
    radius,
    angle,
    n=100,
):
    """
    Create an Euler bend starting at arbitrary position and angle.
    """

    pts = _integrate_euler_segment(
        length=length,
        radius=radius,
        theta_total=angle,
        n=n,
    )

    pts = _rotate(pts, heading)
    pts += np.asarray(start)

    return pts


# ============================================================
# Build a G2-like Euler route
# ============================================================

def _build_euler_route(
    p0,
    a0,
    p1,
    a1,
    radius,
    turn1,
    turn2,
    straight_length,
    n=100,
):
    """
    Construct:

        Euler(turn1)
            +
        straight
            +
        Euler(turn2)

    The two Euler sections have opposite / arbitrary turning
    angles as determined by the optimizer.
    """

    # First Euler
    # For the first bend we use approximately half of turn1
    # as transition geometry.
    L1 = max(
        abs(turn1) * radius,
        1e-6,
    )

    pts1_local = _integrate_euler_segment(
        length=L1,
        radius=radius,
        theta_total=turn1,
        n=max(20, n // 2),
    )

    pts1 = _rotate(pts1_local, a0)
    pts1 += p0

    p_after_1 = pts1[-1]

    a_after_1 = a0 + turn1

    # Straight
    p_after_straight = (
        p_after_1
        + straight_length
        * np.array([
            np.cos(a_after_1),
            np.sin(a_after_1),
        ])
    )

    # Second Euler bend
    L2 = max(
        abs(turn2) * radius,
        1e-6,
    )

    pts2_local = _integrate_euler_segment(
        length=L2,
        radius=radius,
        theta_total=turn2,
        n=max(20, n // 2),
    )

    pts2 = _rotate(
        pts2_local,
        a_after_1,
    )

    pts2 += p_after_straight

    return np.vstack([
        pts1,
        pts2[1:],
    ])


# ============================================================
# Numerical solver
# ============================================================

def _solve_euler_geometry(
    p0,
    a0,
    p1,
    a1,
    radius,
):
    """
    Solve for two Euler turning angles and a straight section.

    Unknowns:
        turn1
        turn2
        straight_length

    Conditions:
        final x = p1.x
        final y = p1.y
        final angle = a1
    """

    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)

    d = np.linalg.norm(p1 - p0)

    delta_angle = _angle_diff(a1, a0)

    # Initial guess
    turn1_0 = delta_angle / 2
    turn2_0 = delta_angle / 2

    straight0 = max(
        d - radius * abs(delta_angle),
        radius,
    )

    x0 = np.array([
        turn1_0,
        turn2_0,
        straight0,
    ])

    def residual(x):
        turn1, turn2, Ls = x

        # Keep straight length positive.
        Ls = max(Ls, 0)

        pts = _build_euler_route(
            p0=p0,
            a0=a0,
            p1=p1,
            a1=a1,
            radius=radius,
            turn1=turn1,
            turn2=turn2,
            straight_length=Ls,
            n=80,
        )

        end = pts[-1]

        # Final orientation
        final_angle = (
            a0
            + turn1
            + turn2
        )

        return np.array([
            (end[0] - p1[0]) / max(d, 1.0),
            (end[1] - p1[1]) / max(d, 1.0),
            _angle_diff(
                final_angle,
                a1,
            ),
        ])

    # Bounds
    #
    # Allow fairly large arbitrary angles.
    lower = np.array([
        -2 * np.pi,
        -2 * np.pi,
        0.0,
    ])

    upper = np.array([
        2 * np.pi,
        2 * np.pi,
        20 * d + 1000,
    ])

    result = least_squares(
        residual,
        x0,
        bounds=(lower, upper),
        xtol=1e-12,
        ftol=1e-12,
        gtol=1e-12,
        max_nfev=3000,
    )

    if not result.success:
        raise RuntimeError(
            "Euler route solver failed:\n"
            f"{result.message}"
        )

    error = np.linalg.norm(
        residual(result.x)
    )

    if error > 1e-5:
        raise RuntimeError(
            "Euler route could not satisfy "
            f"the two ports accurately. "
            f"Residual = {error:.3e}"
        )

    return result.x


# ============================================================
# Centerline curvature check
# ============================================================

def _calculate_curvature(points):
    """
    Calculate curvature from sampled centerline.
    """

    points = np.asarray(points)

    x = points[:, 0]
    y = points[:, 1]

    dx = np.gradient(x)
    dy = np.gradient(y)

    ddx = np.gradient(dx)
    ddy = np.gradient(dy)

    numerator = np.abs(
        dx * ddy - dy * ddx
    )

    denominator = (
        dx**2 + dy**2
    ) ** 1.5

    denominator[
        denominator < 1e-15
    ] = np.inf

    curvature = numerator / denominator

    radius = np.full_like(
        curvature,
        np.inf,
    )

    mask = curvature > 1e-12

    radius[mask] = (
        1.0 / curvature[mask]
    )

    return curvature, radius


# ============================================================
# Main public function
# ============================================================

def connect_ports_euler(
    port1,
    port2,
    min_radius=50.0,
    width=None,
    layer=None,
    npoints=1000,
    cross_section=None,
    allow_large_bend=False,
):
    """
    Connect two arbitrary gdsfactory ports
    using an Euler/clothoid based smooth route.

    Parameters
    ----------
    port1 : gf.Port
        Starting port.

    port2 : gf.Port
        Ending port.

    min_radius : float
        Minimum allowed bending radius [um].

    width : float | None
        Waveguide width.

        If None, use port1.width.

    layer : tuple | None
        GDS layer.

        If None, use port1.layer.

    npoints : int
        Number of centerline sampling points.

    cross_section : gf.CrossSectionSpec | None
        Optional gdsfactory cross section.

    allow_large_bend : bool
        Whether to allow solver solutions
        with extremely large turning angles.

    Returns
    -------
    component : gf.Component

        Routed waveguide component.
    """

    p0 = np.asarray(
        port1.center,
        dtype=float,
    )

    p1 = np.asarray(
        port2.center,
        dtype=float,
    )

    a0 = np.deg2rad(
        float(port1.orientation)
    )

    a1 = np.deg2rad(
        float(port2.orientation)
    )

    if width is None:
        width = port1.width

    if layer is None:
        layer = port1.layer

    # --------------------------------------------------------
    # Basic checks
    # --------------------------------------------------------

    distance = np.linalg.norm(
        p1 - p0
    )

    if distance < 1e-6:
        raise ValueError(
            "The two ports are at the same position."
        )

    if min_radius <= 0:
        raise ValueError(
            "min_radius must be > 0."
        )

    # --------------------------------------------------------
    # Solve geometry
    # --------------------------------------------------------

    turn1, turn2, Ls = (
        _solve_euler_geometry(
            p0=p0,
            a0=a0,
            p1=p1,
            a1=a1,
            radius=min_radius,
        )
    )

    if not allow_large_bend:

        if abs(turn1) > np.pi:
            raise ValueError(
                f"First Euler bend angle "
                f"is too large: "
                f"{np.rad2deg(turn1):.2f} deg"
            )

        if abs(turn2) > np.pi:
            raise ValueError(
                f"Second Euler bend angle "
                f"is too large: "
                f"{np.rad2deg(turn2):.2f} deg"
            )

    # --------------------------------------------------------
    # Generate final centerline
    # --------------------------------------------------------

    points = _build_euler_route(
        p0=p0,
        a0=a0,
        p1=p1,
        a1=a1,
        radius=min_radius,
        turn1=turn1,
        turn2=turn2,
        straight_length=Ls,
        n=max(
            100,
            npoints // 2,
        ),
    )

    # --------------------------------------------------------
    # Check actual curvature
    # --------------------------------------------------------

    curvature, radius = (
        _calculate_curvature(points)
    )

    finite_radius = radius[
        np.isfinite(radius)
    ]

    if len(finite_radius) > 0:
        actual_min_radius = np.min(
            finite_radius
        )
    else:
        actual_min_radius = np.inf

    # Numerical differentiation may produce
    # a slightly smaller radius than requested.
    if actual_min_radius < (
        0.98 * min_radius
    ):
        raise RuntimeError(
            "Generated route violates "
            "minimum radius.\n"
            f"Requested: "
            f"{min_radius:.3f} um\n"
            f"Actual: "
            f"{actual_min_radius:.3f} um"
        )

    # --------------------------------------------------------
    # Create component
    # --------------------------------------------------------

    c = gf.Component(
        name="euler_connection"
    )

    # --------------------------------------------------------
    # Extrude centerline
    # --------------------------------------------------------

    if cross_section is not None:

        xs = gf.get_cross_section(
            cross_section
        )

        path = gf.Path(
            points
        )

        wg = path.extrude(
            cross_section=xs
        )

    else:

        path = gf.Path(
            points
        )

        wg = path.extrude(
            width=width,
            layer=layer,
        )

    c.add_ref(wg)

    # --------------------------------------------------------
    # Add ports
    # --------------------------------------------------------

    c.add_port(
        name="o1",
        center=p0,
        width=width,
        orientation=port1.orientation,
        layer=layer,
    )

    c.add_port(
        name="o2",
        center=p1,
        width=width,
        orientation=port2.orientation,
        layer=layer,
    )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    c.info["route_type"] = "Euler"
    c.info["min_radius_requested"] = min_radius
    c.info["min_radius_actual"] = actual_min_radius
    c.info["turn1_deg"] = np.rad2deg(turn1)
    c.info["turn2_deg"] = np.rad2deg(turn2)
    c.info["straight_length"] = Ls
    c.info["port_distance"] = distance

    return c

__all__ = ['connect_ports_euler']