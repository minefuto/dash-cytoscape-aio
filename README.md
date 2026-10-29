# dash-cytoscape-aio

An All-in-One (AIO) component for [dash-cytoscape](https://github.com/plotly/dash-cytoscape) with a floating
[dash-mantine-components](https://www.dash-mantine-components.com/) `MultiSelect` that stays in sync with the graph selection.

## Features

- **Selection sync**: selecting in the graph updates the `MultiSelect`, and vice versa. Items are grouped into Nodes / Edges
  and labeled with the `node_label` / `edge_label` templates.
- **Auto zoom**: the view animates to fit the selection, capped at `zoom_max` (default `2`).
  Toggle it with the zoom button next to the `MultiSelect`.
- **Info panel**: a popover placed next to the selection, avoiding other elements. Fill it with your own callback;
  it is hidden when the output is empty or the info button is off.

  ```python
  @callback(
      Output(CytoscapeAIO.ids.info("graph"), "children"),
      Input(CytoscapeAIO.ids.cytoscape("graph"), "selectedNodeData"),
      Input(CytoscapeAIO.ids.cytoscape("graph"), "selectedEdgeData"),
  )
  def info(nodes, edges):
      picked = (nodes or []) + (edges or [])
      return f"{len(picked)} selected" if picked else None
  ```

- **Style override**: write `{element_id: style}` to the override store to restyle elements on top of the stylesheet.
  Writing `{}` clears all overrides. Overrides do not apply to selected elements.

  ```python
  @callback(
      Output(CytoscapeAIO.ids.style_override("graph"), "data"),
      Input("button", "n_clicks"),
  )
  def highlight(_):
      return {"a": {"background-color": "orange"}}
  ```

- **Edge text**: pass `edge_text` (a list of templates) to write `data.aio_edge_text` on every edge, joined by
  `edge_text_sep` (default `":"`). The list is reversed when needed so that, with `text-rotation: autorotate`,
  the first part always sits on the source side and the last on the target side, even while dragging nodes.
  Empty parts are dropped.

  ```python
  edge_style = {"label": "data(aio_edge_text)", "text-rotation": "autorotate"}
  CytoscapeAIO(
      elements,
      cytoscape_props={"stylesheet": [{"selector": "edge", "style": edge_style}]},
      edge_text=["{source_port}", "{label}", "{target_port}"],
  )
  ```

- **Light / dark theme**: the default graph colors follow the Mantine color scheme. Your stylesheet still takes precedence.

## Usage

```python
import dash_mantine_components as dmc
from dash import Dash, _dash_renderer

from dash_cytoscape_aio import CytoscapeAIO

_dash_renderer._set_react_version("19.2.4")
app = Dash(__name__)
app.layout = dmc.MantineProvider(
    CytoscapeAIO(
        elements=[
            {"data": {"id": "a", "label": "Alpha"}},
            {"data": {"id": "b", "label": "Beta"}},
            {"data": {"id": "ab", "source": "a", "target": "b"}},
        ],
        cytoscape_props={"layout": {"name": "cose"}},
        multiselect_props={"placeholder": "Search"},
        node_label="{id}: {label}",
        edge_label="{source} -> {target}",
        aio_id="graph",
    )
)
```

Requires dash-mantine-components 3, which needs React 19 (`_set_react_version("19.2.4")` or `REACT_VERSION=19.2.4`).
The app must be wrapped in `dmc.MantineProvider`. Every element needs `data.id`.
Use `CytoscapeAIO.ids.cytoscape(aio_id)`, `CytoscapeAIO.ids.multiselect(aio_id)`, `CytoscapeAIO.ids.info(aio_id)`
and `CytoscapeAIO.ids.style_override(aio_id)` in your own callbacks.

## Development

```sh
uv sync
uv run python examples/app.py
uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pytest
```
