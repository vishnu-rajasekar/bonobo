from compas.datastructures import Network


class StructuralGraph:
    def __init__(self):
        self.network = Network()
        self.stage = 0
        self.units = "meters"

        self.version = "0.3"
        self.profile = "planar_truss"
        self.assumptions = {
            "dimension": 3,
            "behavior": "axial_only"
        }
        self.boundary = None
        self.loadcases = []
        self.targets = []
        self.channels_enabled = []

    # ---------- Metadata Setters ----------

    def set_profile(self, profile):
        self.profile = profile

    def set_assumptions(self, dimension=3, behavior="axial_only"):
        self.assumptions = {
            "dimension": dimension,
            "behavior": behavior
        }

    def set_boundary_polygon_xy(self, xy):
        self.boundary = {
            "type": "polygon_xy",
            "xy": [[float(x), float(y)] for x, y in xy]
        }

    def set_channels_enabled(self, names):
        self.channels_enabled = list(names)


    # ---------- Node API ----------

    def add_node(self, key, xyz, fixed=None, **attributes):
        if fixed is None:
            fixed = [0, 0, 0]

        if len(fixed) != 3:
            raise ValueError("fixed must be length 3: [ux, uy, uz]")

        temp_force = attributes.pop("temp_force", [0, 0, 0])
        if len(temp_force) != 3:
            raise ValueError("temp_force must be length 3: [fx, fy, fz]")
        forces = attributes.pop("forces", [])

        self.network.add_node(
            key,
            xyz=[float(x) for x in xyz],
            fixed=list(fixed),
            temp_force=[float(x) for x in temp_force],
            forces=list(forces),
            attributes=dict(attributes)
        )

    def add_edge(self, u, v, family="bar", **attributes):
        self.network.add_edge(
            u,
            v,
            family=family,
            attributes=dict(attributes)
        )

    def add_load(self, node_key, vector):
        if len(vector) != 3:
            raise ValueError("vector must be length 3: [fx, fy, fz]")
        if not self.network.has_node(node_key):
            raise KeyError("node does not exist: {0}".format(node_key))

        self.loadcases.append(
            {
                "node": str(node_key),
                "vector": [float(x) for x in vector],
            }
        )

    def get_loads(self, node_key=None):
        if node_key is None:
            return list(self.loadcases)
        node_key = str(node_key)
        return [load for load in self.loadcases if load.get("node") == node_key]

    def set_temp_force(self, node_key, vec3):
        if len(vec3) != 3:
            raise ValueError("temp_force must be length 3: [fx, fy, fz]")
        self.network.node_attribute(node_key, "temp_force", [float(x) for x in vec3])

    def get_temp_force(self, node_key):
        temp_force = self.network.node_attribute(node_key, "temp_force")
        if temp_force is None:
            return [0.0, 0.0, 0.0]
        return [float(x) for x in temp_force]

    def add_force_to_node(self, node_key, force):
        forces = self.network.node_attribute(node_key, "forces") or []
        forces.append(force)
        self.network.node_attribute(node_key, "forces", forces)

    def get_node_forces(self, node_key):
        return list(self.network.node_attribute(node_key, "forces") or [])



    # ---------- Serialization ----------

    def to_json(self):
        return {
            "schema": "StructuralGraph",
            "version": self.version,
            "metadata": {
                    "stage": self.stage,
                    "units": self.units,
                    "profile": self.profile,
                    "assumptions": self.assumptions,
                    "boundary": self.boundary,
                    "loadcases": self.loadcases,
                    "targets": self.targets,
                    "channels": {
                    "enabled": self.channels_enabled
                }
            },
            "nodes": {
                str(k): {
                    "xyz": list(self.network.node_attribute(k, "xyz")),
                    "fixed": list(self.network.node_attribute(k, "fixed")),
                    "attributes": self._node_json_attributes(k)

                }
                for k in self.network.nodes()
            },
            "edges": [
                {
                    "u": str(u),
                    "v": str(v),
                    "family": self.network.edge_attribute((u, v), "family"),
                    "attributes": self.network.edge_attribute((u, v), "attributes") or {}
                }
                for u, v in self.network.edges()
            ]
        }

    @classmethod
    def from_json(cls, data):
        g = cls()

        meta = data["metadata"]

        g.stage = meta.get("stage", 0)
        g.units = meta.get("units", "meters")

        g.version = data.get("version", "0.3")

        g.profile = meta.get("profile", "planar_truss")
        g.assumptions = meta.get(
            "assumptions",
            {"dimension": 3, "behavior": "axial_only"}
        )
        g.boundary = meta.get("boundary", None)
        g.loadcases = meta.get("loadcases", [])
        g.targets = meta.get("targets", [])
        g.channels_enabled = meta.get("channels", {}).get("enabled", [])

        # ---------- Load nodes ----------
        for k, n in data["nodes"].items():
            fixed = n.get("fixed", [0, 0, 0])
            if len(fixed) != 3:
                raise ValueError("Node fixed must be length 3 in schema v0.3")

            attrs = n.get("attributes", {})
            if not isinstance(attrs, dict):
                raise TypeError("Node attributes must be a dict")

            g.add_node(
                k,
                xyz=n["xyz"],
                fixed=fixed,
                **attrs
            )

        # ---------- Load edges ----------
        for e in data["edges"]:
            g.add_edge(
                e["u"],
                e["v"],
                family=e.get("family", "bar"),
                **(e.get("attributes") or {})
            )

        return g

    def _node_json_attributes(self, key):
        attrs = dict(self.network.node_attribute(key, "attributes") or {})
        temp_force = self.network.node_attribute(key, "temp_force")
        if temp_force is not None:
            attrs["temp_force"] = list(temp_force)
        return attrs
