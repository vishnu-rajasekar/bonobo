import json
import sys
from fnmatch import fnmatch
from math import cos
from math import pi
from math import sin
from math import sqrt
from pathlib import Path

from compas.geometry import Circle, Frame, Line, Point

try:
    from PySide6.QtCore import Qt
except Exception:  # pragma: no cover - environment dependent
    Qt = None
try:
    from PySide6.QtGui import QAction
except Exception:  # pragma: no cover - environment dependent
    QAction = None

try:
    from compas_viewer import Viewer
except Exception as error:  # pragma: no cover - environment dependent
    Viewer = None
    VIEWER_IMPORT_ERROR = error
else:
    VIEWER_IMPORT_ERROR = None


RUNS_SOURCE_SELECTOR = None
RUNS_SOURCE_DIRS = (
    ("experiments", "vector_gs_kernel_v1_runs"),
    ("experiments", "vector_gs_kernel_v1_runs_policy_compare", "weighted"),
    ("experiments", "vector_gs_kernel_v1_runs_policy_compare", "uniform"),
    ("experiments", "vector_gs_kernel_v1_runs_benchmark_hardened", "weighted"),
    ("experiments", "vector_gs_kernel_v1_runs_benchmark_hardened", "uniform"),
)


def _vector_magnitude(vec3):
    return sqrt(float(vec3[0]) * float(vec3[0]) + float(vec3[1]) * float(vec3[1]) + float(vec3[2]) * float(vec3[2]))


def _rotate_z(vec, angle_rad):
    c = cos(angle_rad)
    s = sin(angle_rad)
    return [vec[0] * c - vec[1] * s, vec[0] * s + vec[1] * c, vec[2]]


def _arrow_head_lines(end, unit_dir, head_len):
    back = [-unit_dir[0] * head_len, -unit_dir[1] * head_len, -unit_dir[2] * head_len]
    left = _rotate_z(back, 20.0 * pi / 180.0)
    right = _rotate_z(back, -20.0 * pi / 180.0)
    left_point = [end[0] + left[0], end[1] + left[1], end[2] + left[2]]
    right_point = [end[0] + right[0], end[1] + right[1], end[2] + right[2]]
    return (
        Line(Point(*end), Point(*left_point)),
        Line(Point(*end), Point(*right_point)),
    )


def _add(viewer, obj, name=None, color=None, **kwargs):
    params = dict(kwargs)
    if color is not None:
        if isinstance(obj, Point):
            params.setdefault("pointcolor", color)
        elif isinstance(obj, Line):
            params.setdefault("linecolor", color)
        else:
            params.setdefault("color", color)
    if name is not None:
        params.setdefault("name", name)
    if hasattr(viewer, "add") and callable(getattr(viewer, "add")):
        return viewer.add(obj, **params)
    return viewer.scene.add(obj, **params)


def _safe_text(viewer, position, label, color):
    _add(viewer, Point(*position), pointsize=6, name=label, show_name=True, color=color)


def _load_kernel_runs(repo_root):
    run_dirs = []
    selector = None if RUNS_SOURCE_SELECTOR in (None, "", "None") else str(RUNS_SOURCE_SELECTOR)
    searched_roots = []
    for parts in RUNS_SOURCE_DIRS:
        runs_dir = repo_root.joinpath(*parts)
        searched_roots.append(str(runs_dir))
        if not runs_dir.exists():
            continue
        for path in sorted([p for p in runs_dir.iterdir() if p.is_dir()]):
            if selector and not fnmatch(path.name, selector):
                continue
            if (path / "kernel_run.json").exists():
                run_dirs.append(path)

    if not run_dirs:
        if selector:
            raise FileNotFoundError(
                "No kernel run directories with kernel_run.json matched selector '{0}' in: {1}".format(
                    selector, searched_roots
                )
            )
        raise FileNotFoundError("No kernel run directories with kernel_run.json found in: {0}".format(searched_roots))
    return sorted(run_dirs)


def _load_payload(run_dir):
    with open(run_dir / "kernel_run.json", "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    payload["run_dir"] = run_dir
    return payload


def _node_map(payload):
    return {node["node_id"]: node for node in payload["assembly"]["nodes"]}


def _scene_counts(payload):
    nodes = payload["assembly"]["nodes"]
    return {
        "nodes": len(nodes),
        "members": len(payload["assembly"]["members"]),
        "supports": len([node for node in nodes if node["type"] == "support"]),
        "active": len([node for node in nodes if node.get("active")]),
    }


def _metric_summary(payload):
    metrics = payload.get("final_metrics") or {}
    support = metrics.get("support_connectivity") or {}
    validity = metrics.get("benchmark_validity") or {}
    invalid_reasons = list(validity.get("invalid_reasons") or [])
    return {
        "equilibrium_reached": bool(metrics.get("equilibrium_reached", False)),
        "benchmark_complete": bool(metrics.get("benchmark_complete", False)),
        "support_connected": bool(support.get("support_connected", False)),
        "geometrically_valid": bool(validity.get("geometrically_valid", False)),
        "invalid_reasons": invalid_reasons,
        "invalid_reason_label": ",".join(invalid_reasons) if invalid_reasons else "none",
    }


def _add_support_symbol(viewer, xyz, scale=1.0):
    x, y, z = xyz
    frame = Frame.worldXY()
    frame.point = Point(x, y, z)
    circle = Circle(0.15 * scale, frame)
    viewer.scene.add(circle, color=(0, 0, 0))

    p1 = Point(x - 0.4 * scale, y - 0.6 * scale, z)
    p2 = Point(x + 0.4 * scale, y - 0.6 * scale, z)
    p3 = Point(x, y, z)
    viewer.scene.add(Line(p1, p2), color=(0, 0, 0))
    viewer.scene.add(Line(p2, p3), color=(0, 0, 0))
    viewer.scene.add(Line(p3, p1), color=(0, 0, 0))


def _add_force_arrow(viewer, xyz, vector, color, scale=1.0, name="Force", linewidth=3):
    mag = _vector_magnitude(vector)
    if mag <= 1e-12:
        return
    unit = [vector[0] / mag, vector[1] / mag, vector[2] / mag]
    start = [xyz[0], xyz[1], xyz[2]]
    end = [xyz[0] + unit[0] * scale, xyz[1] + unit[1] * scale, xyz[2] + unit[2] * scale]
    _add(viewer, Line(Point(*start), Point(*end)), name=name, color=color, linewidth=linewidth)
    l1, l2 = _arrow_head_lines(end, unit, 0.15 * scale)
    _add(viewer, l1, name=name, color=color, linewidth=linewidth)
    _add(viewer, l2, name=name, color=color, linewidth=linewidth)


def _frame_scene(viewer, payload):
    coords = [list(node["coordinate"]) for node in payload["assembly"]["nodes"]]
    boundary = payload["assembly"].get("boundary") or {}
    coords.append(list(boundary.get("min", [-6.0, -1.0, 0.0])))
    coords.append(list(boundary.get("max", [6.0, 6.0, 0.0])))
    xs = [point[0] for point in coords]
    ys = [point[1] for point in coords]
    zs = [point[2] for point in coords]
    _add(viewer, Point(min(xs), min(ys), min(zs)), name="_frame_min", color=(1.0, 1.0, 1.0), pointsize=0.1)
    _add(viewer, Point(max(xs), max(ys), max(zs)), name="_frame_max", color=(1.0, 1.0, 1.0), pointsize=0.1)


class KernelRunViewer:
    def __init__(self, viewer, run_dirs):
        self.viewer = viewer
        self.run_dirs = list(run_dirs)
        self.current_index = len(self.run_dirs) - 1
        self._statusbar = None

    def init_controls(self):
        self._statusbar = self.viewer.ui.statusbar.widget
        self._add_toolbar_action("Prev", "View previous kernel run", self.show_previous_run)
        self._add_toolbar_action("Next", "View next kernel run", self.show_next_run)
        self._install_key_navigation()

    def _add_toolbar_action(self, text, tooltip, action):
        toolbar = self.viewer.ui.toolbar.widget
        if QAction is None:
            qaction = toolbar.addAction(text)
            qaction.setToolTip(tooltip)
            qaction.triggered.connect(action)
            return qaction
        qaction = QAction(text, toolbar)
        qaction.setToolTip(tooltip)
        qaction.triggered.connect(action)
        toolbar.addAction(qaction)
        return qaction

    def _install_key_navigation(self):
        if Qt is None:
            return
        renderer = self.viewer.renderer
        original = renderer.keyPressEvent
        browser = self

        def keypress(event):
            if event.key() == Qt.Key_Left:
                browser.show_previous_run()
                event.accept()
                return
            if event.key() == Qt.Key_Right:
                browser.show_next_run()
                event.accept()
                return
            original(event)

        renderer.keyPressEvent = keypress

    def show_previous_run(self):
        self.current_index = (self.current_index - 1) % len(self.run_dirs)
        self.render_current_run()

    def show_next_run(self):
        self.current_index = (self.current_index + 1) % len(self.run_dirs)
        self.render_current_run()

    def render_current_run(self):
        payload = _load_payload(self.run_dirs[self.current_index])
        self._clear_scene()
        self._draw_payload(payload)
        if self.viewer.running:
            self.viewer.renderer.rebuild_buffers()
            self.viewer.renderer.update()
            self.viewer.ui.sidebar.update()
        self._set_status(payload)
        self._print_summary(payload)

    def _clear_scene(self):
        for sceneobject in list(self.viewer.scene.objects):
            self.viewer.scene.remove(sceneobject, rebuild_buffers=False)

    def _set_status(self, payload):
        if self._statusbar is None:
            return
        counts = _scene_counts(payload)
        metrics = _metric_summary(payload)
        message = (
            "{0} ({1}/{2}) | nodes={3} members={4} active={5} residual={6} "
            "| benchmark_complete={7} valid={8} support_connected={9}"
        ).format(
            payload["run_dir"].name,
            self.current_index + 1,
            len(self.run_dirs),
            counts["nodes"],
            counts["members"],
            counts["active"],
            payload["assembly"]["residual_magnitude"],
            metrics["benchmark_complete"],
            metrics["geometrically_valid"],
            metrics["support_connected"],
        )
        self._statusbar.showMessage(message)

    def _print_summary(self, payload):
        counts = _scene_counts(payload)
        metrics = _metric_summary(payload)
        print("run_dir:", payload["run_dir"], flush=True)
        print("nodes:", counts["nodes"], flush=True)
        print("members:", counts["members"], flush=True)
        print("active_nodes:", counts["active"], flush=True)
        print("residual_magnitude:", payload["assembly"]["residual_magnitude"], flush=True)
        print("equilibrium_reached:", metrics["equilibrium_reached"], flush=True)
        print("benchmark_complete:", metrics["benchmark_complete"], flush=True)
        print("support_connected:", metrics["support_connected"], flush=True)
        print("geometrically_valid:", metrics["geometrically_valid"], flush=True)
        print("invalid_reasons:", metrics["invalid_reasons"], flush=True)
        print("rule_sequence:", [step["rule"] for step in payload["trace"]], flush=True)

    def _draw_payload(self, payload):
        node_by_id = _node_map(payload)

        for node in payload["assembly"]["nodes"]:
            xyz = [float(value) for value in node["coordinate"]]
            if node["type"] == "support":
                _add_support_symbol(self.viewer, xyz, scale=0.5)
            else:
                _add(self.viewer, Point(*xyz), name="Node", color=(0.15, 0.15, 0.15), pointsize=8)

            for force in node.get("forces", []):
                vector = [float(value) for value in force.get("vector", [0.0, 0.0, 0.0])]
                kind = force.get("kind")
                if kind == "applied":
                    _add_force_arrow(self.viewer, xyz, vector, color=(0.1, 0.35, 0.9), scale=0.6, name="Load")
                elif kind == "temporary":
                    _add_force_arrow(self.viewer, xyz, vector, color=(0.85, 0.15, 0.15), scale=0.5, name="TempForce", linewidth=2.5)

        for member in payload["assembly"]["members"]:
            start_node = node_by_id.get(member["start_node"])
            end_node = node_by_id.get(member["end_node"])
            if start_node is None or end_node is None:
                continue
            p1 = [float(value) for value in start_node["coordinate"]]
            p2 = [float(value) for value in end_node["coordinate"]]
            _add(self.viewer, Line(Point(*p1), Point(*p2)), name="Member", color=(0.15, 0.15, 0.15), linewidth=3)

        coords = [node["coordinate"] for node in payload["assembly"]["nodes"]]
        if coords:
            metrics = _metric_summary(payload)
            cx = sum(point[0] for point in coords) / len(coords)
            cy = sum(point[1] for point in coords) / len(coords)
            cz = sum(point[2] for point in coords) / len(coords)
            run_label = "Kernel Run {0}/{1}: {2}".format(self.current_index + 1, len(self.run_dirs), payload["run_dir"].name)
            state_label = "state={0} residual={1}".format(payload["assembly"]["state"], payload["assembly"]["residual_magnitude"])
            completion_label = "benchmark_complete={0} valid={1} support_connected={2}".format(
                metrics["benchmark_complete"],
                metrics["geometrically_valid"],
                metrics["support_connected"],
            )
            invalid_label = "invalid_reasons={0}".format(metrics["invalid_reason_label"])
            rule_label = "rules: {0}".format(", ".join(step["rule"] for step in payload["trace"][:5]))
            _safe_text(self.viewer, (cx + 0.5, cy + 0.5, cz + 0.5), run_label, (0.0, 0.0, 0.0))
            _safe_text(self.viewer, (cx + 0.5, cy + 1.0, cz + 0.5), state_label, (0.1, 0.1, 0.1))
            _safe_text(self.viewer, (cx + 0.5, cy + 1.5, cz + 0.5), completion_label, (0.1, 0.1, 0.1))
            _safe_text(self.viewer, (cx + 0.5, cy + 2.0, cz + 0.5), invalid_label, (0.45, 0.05, 0.05))
            _safe_text(self.viewer, (cx + 0.5, cy + 2.5, cz + 0.5), rule_label, (0.1, 0.1, 0.1))

        _frame_scene(self.viewer, payload)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    run_dirs = _load_kernel_runs(repo_root)

    if Viewer is None:
        print("viewer_error: compas_viewer import failed: {0}".format(VIEWER_IMPORT_ERROR), file=sys.stderr)
        return 1

    viewer = Viewer()
    browser = KernelRunViewer(viewer, run_dirs)
    browser.init_controls()
    browser.render_current_run()

    try:
        viewer.show()
    except Exception as error:  # pragma: no cover - environment dependent
        print("viewer_error: {0}".format(error), file=sys.stderr)
        print("viewer_note: kernel run summary printed above; viewer failed after scene construction.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
