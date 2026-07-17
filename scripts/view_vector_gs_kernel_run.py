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
    from PySide6.QtWidgets import QLabel
except Exception:  # pragma: no cover - environment dependent
    QLabel = None

try:
    from compas_viewer import Viewer
    from compas_viewer.scene import Tag
except Exception as error:  # pragma: no cover - environment dependent
    Viewer = None
    Tag = None
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
PRIMARY_RUNS_SOURCE_DIR = RUNS_SOURCE_DIRS[0]
NODE_POINT_SIZE = 15.0
TENSION_COLOR = (0.78, 0.24, 0.30)
COMPRESSION_COLOR = (0.08, 0.30, 0.47)
LOAD_COLOR = (0.00, 0.65, 0.84)
REACTION_COLOR = (0.00, 0.62, 0.45)
TEMPORARY_COLOR = (0.90, 0.62, 0.00)
UNKNOWN_MEMBER_COLOR = (0.48, 0.48, 0.48)


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


def _kernel_run_dirs(runs_dir, selector=None):
    if not runs_dir.exists():
        return []
    run_dirs = []
    for path in sorted([p for p in runs_dir.iterdir() if p.is_dir()]):
        if selector and not fnmatch(path.name, selector):
            continue
        if (path / "kernel_run.json").exists():
            run_dirs.append(path)
    return run_dirs


def _run_group_key(run_dir):
    name = run_dir.name
    if "_seed_" in name:
        return name.split("_seed_", 1)[0]
    return name


def _latest_group(run_dirs):
    if not run_dirs:
        return []
    latest_key = max(_run_group_key(run_dir) for run_dir in run_dirs)
    return sorted([run_dir for run_dir in run_dirs if _run_group_key(run_dir) == latest_key])


def _load_kernel_runs(repo_root):
    run_dirs = []
    selector = None if RUNS_SOURCE_SELECTOR in (None, "", "None") else str(RUNS_SOURCE_SELECTOR)
    searched_roots = []

    if selector is None:
        primary_dir = repo_root.joinpath(*PRIMARY_RUNS_SOURCE_DIR)
        searched_roots.append(str(primary_dir))
        latest_primary = _latest_group(_kernel_run_dirs(primary_dir))
        if latest_primary:
            return latest_primary

    for parts in RUNS_SOURCE_DIRS:
        runs_dir = repo_root.joinpath(*parts)
        searched_roots.append(str(runs_dir))
        run_dirs.extend(_kernel_run_dirs(runs_dir, selector=selector))

    if not run_dirs:
        if selector:
            raise FileNotFoundError(
                "No kernel run directories with kernel_run.json matched selector '{0}' in: {1}".format(
                    selector, searched_roots
                )
            )
        raise FileNotFoundError("No kernel run directories with kernel_run.json found in: {0}".format(searched_roots))
    if selector is None:
        return _latest_group(run_dirs)
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
        self.current_step_index = None
        self._statusbar = None
        self._info_overlay = None

    def init_controls(self):
        self._statusbar = self.viewer.ui.statusbar.widget
        if QLabel is not None:
            self._info_overlay = QLabel(self.viewer.renderer)
            self._info_overlay.move(12, 12)
            self._info_overlay.setStyleSheet(
                "background-color: rgba(255, 255, 255, 220); color: #222; padding: 8px; border: 1px solid #bbb;"
            )
        self._add_toolbar_action("Prev", "View previous kernel run", self.show_previous_run)
        self._add_toolbar_action("Next", "View next kernel run", self.show_next_run)
        self._add_toolbar_action("Prev Step", "View previous rule application", self.show_previous_step)
        self._add_toolbar_action("Next Step", "View next rule application", self.show_next_step)
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
            if event.key() == Qt.Key_Up:
                browser.show_previous_step()
                event.accept()
                return
            if event.key() == Qt.Key_Down:
                browser.show_next_step()
                event.accept()
                return
            original(event)

        renderer.keyPressEvent = keypress

    def show_previous_run(self):
        self.current_index = (self.current_index - 1) % len(self.run_dirs)
        self.current_step_index = None
        self.render_current_run()

    def show_next_run(self):
        self.current_index = (self.current_index + 1) % len(self.run_dirs)
        self.current_step_index = None
        self.render_current_run()

    def show_previous_step(self):
        payload = _load_payload(self.run_dirs[self.current_index])
        final_index = len(payload["trace"])
        current = final_index if self.current_step_index is None else self.current_step_index
        self.current_step_index = max(0, current - 1)
        self.render_current_run()

    def show_next_step(self):
        payload = _load_payload(self.run_dirs[self.current_index])
        final_index = len(payload["trace"])
        current = final_index if self.current_step_index is None else self.current_step_index
        self.current_step_index = min(final_index, current + 1)
        self.render_current_run()

    def _playback_payload(self, payload):
        trace = payload["trace"]
        final_index = len(trace)
        step_index = final_index if self.current_step_index is None else min(self.current_step_index, final_index)
        rendered = dict(payload)
        if trace and step_index == 0:
            rendered["assembly"] = trace[0].get("assembly_before", payload["assembly"])
        elif trace and step_index < final_index:
            rendered["assembly"] = trace[step_index - 1].get("assembly_after", payload["assembly"])
        rendered["playback_step_index"] = step_index
        rendered["playback_step_count"] = final_index
        rendered["playback_rule"] = "initial" if step_index == 0 else trace[step_index - 1]["rule"]
        rendered["playback_targets"] = [] if step_index == 0 else list(trace[step_index - 1].get("targets") or [])
        rendered["playback_selected_node"] = None if step_index == 0 else trace[step_index - 1].get("selected_active_node")
        rendered["playback_active_before"] = None if step_index == 0 else trace[step_index - 1].get("active_front_count_before")
        rendered["playback_active_after"] = None if step_index == 0 else trace[step_index - 1].get("active_front_count_after")
        rendered["playback_ray_combination"] = None if step_index == 0 else trace[step_index - 1].get("params", {}).get("ray_combination")
        transition = None if step_index == 0 else trace[step_index - 1]
        rendered["playback_phase_before"] = (
            rendered["assembly"].get("state") if transition is None else transition.get("phase_before")
        )
        rendered["playback_phase_after"] = (
            rendered["assembly"].get("state") if transition is None else transition.get("phase_after")
        )
        rendered["playback_phase_transition_reason"] = (
            None if transition is None else transition.get("phase_transition_reason")
        )
        visible_trace = trace[:step_index]
        rendered["playback_growth_step_count"] = sum(
            1 for item in visible_trace if item.get("phase_before") == "grow" and item.get("rule")
        )
        rendered["playback_closure_step_count"] = sum(
            1 for item in visible_trace if item.get("phase_before") == "close" and item.get("rule")
        )
        if step_index == 0:
            rendered["playback_transition_changed"] = False
            rendered["playback_form_changed"] = False
        else:
            transition = trace[step_index - 1]
            before = transition.get("assembly_before") or {}
            after = transition.get("assembly_after") or {}
            rendered["playback_transition_changed"] = before != after
            rendered["playback_form_changed"] = (
                before.get("nodes") != after.get("nodes") or before.get("members") != after.get("members")
            )
        rendered["playback_is_final"] = step_index == final_index
        if not rendered["playback_is_final"]:
            rendered["final_metrics"] = {}
        return rendered

    def render_current_run(self):
        payload = self._playback_payload(_load_payload(self.run_dirs[self.current_index]))
        was_running = self.viewer.running
        if was_running:
            # COMPAS redraws after every dynamic add. Build the complete scene first
            # so Tag objects can initialize before the first playback redraw.
            self.viewer.running = False
        try:
            self._clear_scene()
            self._draw_payload(payload)
        finally:
            self.viewer.running = was_running
        if was_running:
            self._initialize_node_labels()
            self.viewer.renderer.rebuild_buffers()
            self.viewer.renderer.update()
            self.viewer.ui.sidebar.update()
        self._set_status(payload)
        self._print_summary(payload)

    def _clear_scene(self):
        for sceneobject in list(self.viewer.scene.objects):
            self.viewer.scene.remove(sceneobject, rebuild_buffers=False)

    def _initialize_node_labels(self):
        for sceneobject in self.viewer.scene.objects:
            if Tag is not None and isinstance(getattr(sceneobject, "geometry", None), Tag):
                sceneobject.init()

    def _set_status(self, payload):
        if self._statusbar is None:
            return
        counts = _scene_counts(payload)
        metrics = _metric_summary(payload)
        message = (
            "{0} ({1}/{2}) | state={3}/{4} rule={5} | nodes={6} members={7} active={8} residual={9} "
            "| benchmark_complete={10} valid={11} support_connected={12}"
        ).format(
            payload["run_dir"].name,
            self.current_index + 1,
            len(self.run_dirs),
            payload["playback_step_index"],
            payload["playback_step_count"],
            payload["playback_rule"],
            counts["nodes"],
            counts["members"],
            counts["active"],
            payload["assembly"]["residual_magnitude"],
            metrics["benchmark_complete"] if payload["playback_is_final"] else "n/a",
            metrics["geometrically_valid"] if payload["playback_is_final"] else "n/a",
            metrics["support_connected"] if payload["playback_is_final"] else "n/a",
        )
        self._statusbar.showMessage(message)

        if self._info_overlay is not None:
            invalid_reasons = metrics["invalid_reason_label"]
            targets = ",".join(payload["playback_targets"]) or "none"
            transition_status = "changed" if payload["playback_transition_changed"] else "no-op"
            ray_combination = payload["playback_ray_combination"] or "n/a"
            termination_reason = payload.get("termination_reason") or payload["assembly"].get("metadata", {}).get("termination_reason") or "n/a"
            self._info_overlay.setText(
                "Kernel Run {0}/{1}: {2}\n"
                "rule state {3}/{4}: {5} nodes={6}\n"
                "transition={7} form_changed={8}\n"
                "selected_node={9} active_fronts={10}->{11} rays={12}\n"
                "phase={13}->{14} reason={15} growth={16} closure={17}\n"
                "state={18} residual={19}\n"
                "benchmark_complete={20} valid={21} support_connected={22}\n"
                "invalid_reasons={23} termination={24}".format(
                    self.current_index + 1,
                    len(self.run_dirs),
                    payload["run_dir"].name,
                    payload["playback_step_index"],
                    payload["playback_step_count"],
                    payload["playback_rule"],
                    targets,
                    transition_status,
                    payload["playback_form_changed"],
                    payload["playback_selected_node"] or "none",
                    payload["playback_active_before"] if payload["playback_active_before"] is not None else "n/a",
                    payload["playback_active_after"] if payload["playback_active_after"] is not None else "n/a",
                    ray_combination,
                    payload["playback_phase_before"],
                    payload["playback_phase_after"],
                    payload["playback_phase_transition_reason"] or "n/a",
                    payload["playback_growth_step_count"],
                    payload["playback_closure_step_count"],
                    payload["assembly"]["state"],
                    payload["assembly"]["residual_magnitude"],
                    metrics["benchmark_complete"] if payload["playback_is_final"] else "n/a",
                    metrics["geometrically_valid"] if payload["playback_is_final"] else "n/a",
                    metrics["support_connected"] if payload["playback_is_final"] else "n/a",
                    invalid_reasons if payload["playback_is_final"] else "n/a",
                    termination_reason if payload["playback_is_final"] else "n/a",
                )
            )
            self._info_overlay.adjustSize()
            self._info_overlay.raise_()
            self._info_overlay.show()

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
                _add(self.viewer, Point(*xyz), name="SupportNode", color=(0.0, 0.0, 0.0), pointsize=NODE_POINT_SIZE)
                _add_support_symbol(self.viewer, xyz, scale=0.5)
            else:
                _add(self.viewer, Point(*xyz), name="Node", color=(0.15, 0.15, 0.15), pointsize=NODE_POINT_SIZE)
            if Tag is not None:
                label_position = (xyz[0] + 0.08, xyz[1] + 0.08, xyz[2] + 0.08)
                _add(
                    self.viewer,
                    Tag(str(node["node_id"]), label_position, height=18, absolute_height=False),
                    name="NodeLabel",
                )

            for force in node.get("forces", []):
                vector = [float(value) for value in force.get("vector", [0.0, 0.0, 0.0])]
                kind = force.get("kind")
                if kind == "applied":
                    _add_force_arrow(self.viewer, xyz, vector, color=LOAD_COLOR, scale=0.6, name="Load")
                elif kind == "reaction":
                    _add_force_arrow(self.viewer, xyz, vector, color=REACTION_COLOR, scale=0.6, name="SolvedReaction", linewidth=3)
                elif kind == "temporary":
                    _add_force_arrow(self.viewer, xyz, vector, color=TEMPORARY_COLOR, scale=0.5, name="TempForce", linewidth=2.5)

        for member in payload["assembly"]["members"]:
            start_node = node_by_id.get(member["start_node"])
            end_node = node_by_id.get(member["end_node"])
            if start_node is None or end_node is None:
                continue
            p1 = [float(value) for value in start_node["coordinate"]]
            p2 = [float(value) for value in end_node["coordinate"]]
            force_class = member.get("force_class")
            if force_class is None:
                direction = (member.get("force") or {}).get("direction")
                force_class = "tension" if direction == 1 else "compression" if direction == -1 else "unknown"
            if force_class == "tension":
                color, linewidth, name = TENSION_COLOR, 1.5, "TensionMember"
            elif force_class == "compression":
                color, linewidth, name = COMPRESSION_COLOR, 4.5, "CompressionMember"
            else:
                color, linewidth, name = UNKNOWN_MEMBER_COLOR, 2.5, "UnclassifiedMember"
            _add(self.viewer, Line(Point(*p1), Point(*p2)), name=name, color=color, linewidth=linewidth)

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
