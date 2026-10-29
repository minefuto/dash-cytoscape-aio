import random

import dash_mantine_components as dmc
from dash import (
    Dash,
    Input,
    Output,
    _dash_renderer,
    callback,
    clientside_callback,
    dcc,
)

from dash_cytoscape_aio import CytoscapeAIO

rng = random.Random(0)
SITES = ["tokyo", "osaka"]
elements: list[dict] = []


def node(id: str, type: str, site: str) -> None:
    elements.append(
        {
            "data": {
                "id": id,
                "label": f"{site}-{id}",
                "type": type,
                "site": site,
                "ip": f"10.{len(elements) // 250}.{len(elements) % 250}.1",
            }
        }
    )


def link(a: str, b: str, bandwidth: int) -> None:
    elements.append(
        {
            "data": {
                "id": f"{a}_{b}",
                "source": a,
                "target": b,
                "bandwidth": f"{bandwidth}G",
            }
        }
    )


cores = [f"core-{i}" for i in range(1, 3)]
for c in cores:
    node(c, "core", "tokyo")
link(*cores, 400)

dists = [f"dist-{i}" for i in range(1, 5)]
for i, d in enumerate(dists):
    node(d, "dist", SITES[i // 2])
    for c in cores:
        link(c, d, 100)
for a, b in zip(dists[::2], dists[1::2]):
    link(a, b, 100)

accs = [f"acc-{i}" for i in range(1, 9)]
for i, a in enumerate(accs):
    pair = i // 4 * 2
    node(a, "access", SITES[pair // 2])
    link(dists[pair], a, 40)
    link(dists[pair + 1], a, 40)
for a, b in zip(rng.sample(accs, 2), rng.sample(accs, 2)):
    if a != b:
        link(a, b, 10)

for i in range(1, 13):
    s = f"srv-{i}"
    homes = rng.sample(accs, 2 if rng.random() < 0.25 else 1)
    node(s, "server", SITES[accs.index(homes[0]) // 4])
    for a in homes:
        link(a, s, rng.choice([1, 10]))

ids = [e["data"]["id"] for e in elements]
node_ids = [e["data"]["id"] for e in elements if "source" not in e["data"]]
edge_ids = [i for i in ids if i not in node_ids]

stylesheet = [
    {"selector": "node", "style": {"label": "data(label)", "font-size": 8}},
    {"selector": "[type = 'core']", "style": {"shape": "octagon"}},
    {"selector": "[type = 'dist']", "style": {"shape": "diamond"}},
    {"selector": "[type = 'access']", "style": {"shape": "round-rectangle"}},
    {"selector": "edge", "style": {"width": 1, "curve-style": "bezier"}},
    {"selector": "[bandwidth = '40G']", "style": {"width": 2}},
    {"selector": "[bandwidth = '100G']", "style": {"width": 4}},
    {"selector": "[bandwidth = '400G']", "style": {"width": 6}},
]

_dash_renderer._set_react_version("19.2.4")
app = Dash(__name__)
app.layout = dmc.MantineProvider(
    [
        CytoscapeAIO(
            elements,
            cytoscape_props={"layout": {"name": "cose"}, "stylesheet": stylesheet},
            multiselect_props={"placeholder": "Search"},
            node_label="{id}: {label}",
            edge_label="{source} -> {target} ({bandwidth})",
            aio_id="graph",
            zoom_max=5,
        ),
        dmc.Switch(
            id="dark",
            label="Dark",
            checked=True,
            style={"position": "absolute", "top": 16, "right": 16, "zIndex": 10},
        ),
        dcc.Interval(id="tick", interval=1000),
    ],
    id="provider",
    forceColorScheme="dark",
)

clientside_callback(
    "dark => dark ? 'dark' : 'light'",
    Output("provider", "forceColorScheme"),
    Input("dark", "checked"),
)


@callback(
    Output(CytoscapeAIO.ids.info("graph"), "children"),
    Input(CytoscapeAIO.ids.cytoscape("graph"), "selectedNodeData"),
    Input(CytoscapeAIO.ids.cytoscape("graph"), "selectedEdgeData"),
)
def info(nodes: list[dict] | None, edges: list[dict] | None) -> object:
    picked = (nodes or []) + (edges or [])
    if len(picked) != 1:
        return f"{len(picked)} items selected" if picked else None
    return dmc.Table(
        data={"body": [[k, str(v)] for k, v in picked[0].items()]},
        withRowBorders=False,
    )


@callback(
    Output(CytoscapeAIO.ids.style_override("graph"), "data"),
    Input("tick", "n_intervals"),
)
def highlight(_: int | None) -> dict[str, dict[str, str]]:
    node = random.choice(node_ids)
    edge = random.choice(edge_ids)
    return {node: {"background-color": "orange"}, edge: {"line-color": "orange"}}


if __name__ == "__main__":
    app.run(debug=True)
