import uuid
from typing import Any

import dash_cytoscape as cyto
import dash_mantine_components as dmc
from dash import (
    MATCH,
    ClientsideFunction,
    Input,
    Output,
    State,
    clientside_callback,
    dcc,
    hooks,
    html,
)
from dash.dependencies import Wildcard
from dash_iconify import DashIconify

AioId = str | Wildcard


def _id(subcomponent: str, aio_id: AioId) -> dict[str, AioId]:
    return {"component": "CytoscapeAIO", "subcomponent": subcomponent, "aio_id": aio_id}


class CytoscapeAIO(html.Div):
    class ids:
        @staticmethod
        def cytoscape(aio_id: AioId) -> dict[str, AioId]:
            return _id("cytoscape", aio_id)

        @staticmethod
        def multiselect(aio_id: AioId) -> dict[str, AioId]:
            return _id("multiselect", aio_id)

        @staticmethod
        def zoom(aio_id: AioId) -> dict[str, AioId]:
            return _id("zoom", aio_id)

        @staticmethod
        def zoom_icon(aio_id: AioId) -> dict[str, AioId]:
            return _id("zoom_icon", aio_id)

        @staticmethod
        def info(aio_id: AioId) -> dict[str, AioId]:
            return _id("info", aio_id)

        @staticmethod
        def info_toggle(aio_id: AioId) -> dict[str, AioId]:
            return _id("info_toggle", aio_id)

        @staticmethod
        def theme_toggle(aio_id: AioId) -> dict[str, AioId]:
            return _id("theme_toggle", aio_id)

        @staticmethod
        def theme_icon(aio_id: AioId) -> dict[str, AioId]:
            return _id("theme_icon", aio_id)

        @staticmethod
        def store(aio_id: AioId) -> dict[str, AioId]:
            return _id("store", aio_id)

        @staticmethod
        def style_override(aio_id: AioId) -> dict[str, AioId]:
            return _id("style_override", aio_id)

        @staticmethod
        def theme(aio_id: AioId) -> dict[str, AioId]:
            return _id("theme", aio_id)

    def __init__(
        self,
        elements: list[dict[str, Any]],
        cytoscape_props: dict[str, Any] | None = None,
        multiselect_props: dict[str, Any] | None = None,
        info_props: dict[str, Any] | None = None,
        overlay_style: dict[str, Any] | None = None,
        style: dict[str, Any] | None = None,
        node_label: str = "{id}",
        edge_label: str = "{id}",
        edge_text: list[str] | None = None,
        edge_text_sep: str = ":",
        zoom_max: float = 2,
        override_selected: bool = False,
        aio_id: str | None = None,
    ) -> None:
        if not isinstance(elements, list):
            raise TypeError("elements must be a list")
        for element in elements:
            if element.get("data", {}).get("id") is None:
                raise ValueError(f"element without data.id: {element}")
        if zoom_max <= 0:
            raise ValueError("zoom_max must be positive")

        aio_id = aio_id or str(uuid.uuid4())
        stylesheet = (cytoscape_props or {}).get(
            "stylesheet", [{"selector": "node", "style": {"label": "data(label)"}}]
        )
        cytoscape_props = {
            "style": {"width": "100%", "height": "100%"},
            "boxSelectionEnabled": True,
            **(cytoscape_props or {}),
            "id": self.ids.cytoscape(aio_id),
            "elements": elements,
            "stylesheet": stylesheet,
        }
        multiselect_props = {
            "searchable": True,
            "clearable": True,
            "placeholder": "Select nodes / edges",
            "w": 480,
            "maxDropdownHeight": 300,
            "radius": 1000,
            **(multiselect_props or {}),
            "id": self.ids.multiselect(aio_id),
            "data": [],
            "value": [],
        }
        info_props = {
            "shadow": "md",
            "p": "sm",
            "withBorder": True,
            **(info_props or {}),
            "id": self.ids.info(aio_id),
        }
        info_props["style"] = {
            "maxWidth": 320,
            "maxHeight": 300,
            "overflow": "auto",
            **info_props.get("style", {}),
        }
        super().__init__(
            [
                cyto.Cytoscape(**cytoscape_props),
                html.Div(
                    dmc.Group(
                        [
                            dmc.MultiSelect(**multiselect_props),
                            dmc.ActionIcon(
                                DashIconify(
                                    id=self.ids.zoom_icon(aio_id),
                                    icon="tabler:zoom-in",
                                    width=20,
                                ),
                                id=self.ids.zoom(aio_id),
                                variant="filled",
                                size="input-sm",
                                color="#0169D9",
                                radius=1000,
                            ),
                            dmc.ActionIcon(
                                DashIconify(icon="tabler:info-circle", width=20),
                                id=self.ids.info_toggle(aio_id),
                                variant="filled",
                                size="input-sm",
                                color="#0169D9",
                                radius=1000,
                            ),
                            dmc.ActionIcon(
                                DashIconify(
                                    id=self.ids.theme_icon(aio_id),
                                    icon="tabler:moon",
                                    width=20,
                                ),
                                id=self.ids.theme_toggle(aio_id),
                                variant="default",
                                size="input-sm",
                                color="#0169D9",
                                radius=1000,
                            ),
                        ],
                        gap=8,
                        align="flex-start",
                        wrap="nowrap",
                    ),
                    style={
                        "position": "absolute",
                        "top": 10,
                        "left": 10,
                        "zIndex": 10,
                        **(overlay_style or {}),
                    },
                    **{"data-cytoscape-aio-overlay": aio_id},
                ),
                html.Div(
                    dmc.Paper(**info_props),
                    style={
                        "position": "absolute",
                        "display": "none",
                        "width": "max-content",
                        "zIndex": 10,
                    },
                    **{"data-cytoscape-aio-info": aio_id},
                ),
                dcc.Store(
                    id=self.ids.store(aio_id),
                    data={
                        "node": node_label,
                        "edge": edge_label,
                        "stylesheet": stylesheet,
                        "zoomMax": zoom_max,
                        "edgeText": edge_text,
                        "edgeTextSep": edge_text_sep,
                        "overrideSelected": override_selected,
                    },
                ),
                dcc.Store(id=self.ids.style_override(aio_id), data={}),
                dcc.Store(id=self.ids.theme(aio_id)),
            ],
            style={"position": "relative", "height": "100vh", **(style or {})},
            **{"data-cytoscape-aio": aio_id},
        )


hooks.script(
    [{"relative_package_path": "cytoscape_aio.js", "namespace": "dash_cytoscape_aio"}]
)

clientside_callback(
    ClientsideFunction("cytoscape_aio", "sync"),
    Output(CytoscapeAIO.ids.multiselect(MATCH), "data"),
    Output(CytoscapeAIO.ids.multiselect(MATCH), "value"),
    Output(CytoscapeAIO.ids.cytoscape(MATCH), "elements"),
    Output(CytoscapeAIO.ids.cytoscape(MATCH), "selectedNodeData"),
    Output(CytoscapeAIO.ids.cytoscape(MATCH), "selectedEdgeData"),
    Input(CytoscapeAIO.ids.cytoscape(MATCH), "elements"),
    Input(CytoscapeAIO.ids.multiselect(MATCH), "value"),
    Input(CytoscapeAIO.ids.cytoscape(MATCH), "selectedNodeData"),
    Input(CytoscapeAIO.ids.cytoscape(MATCH), "selectedEdgeData"),
    State(CytoscapeAIO.ids.store(MATCH), "data"),
    State(CytoscapeAIO.ids.zoom(MATCH), "variant"),
)

clientside_callback(
    ClientsideFunction("cytoscape_aio", "toggleZoom"),
    Output(CytoscapeAIO.ids.zoom(MATCH), "variant"),
    Output(CytoscapeAIO.ids.zoom_icon(MATCH), "icon"),
    Input(CytoscapeAIO.ids.zoom(MATCH), "n_clicks"),
    State(CytoscapeAIO.ids.zoom(MATCH), "variant"),
    State(CytoscapeAIO.ids.multiselect(MATCH), "value"),
    State(CytoscapeAIO.ids.store(MATCH), "data"),
    prevent_initial_call=True,
)

clientside_callback(
    ClientsideFunction("cytoscape_aio", "applyStyleOverride"),
    Output(CytoscapeAIO.ids.cytoscape(MATCH), "stylesheet"),
    Input(CytoscapeAIO.ids.style_override(MATCH), "data"),
    Input(CytoscapeAIO.ids.theme(MATCH), "data"),
    State(CytoscapeAIO.ids.store(MATCH), "data"),
)

clientside_callback(
    ClientsideFunction("cytoscape_aio", "edgeText"),
    Input(CytoscapeAIO.ids.store(MATCH), "data"),
)

clientside_callback(
    ClientsideFunction("cytoscape_aio", "toggleInfo"),
    Output(CytoscapeAIO.ids.info_toggle(MATCH), "variant"),
    Input(CytoscapeAIO.ids.info_toggle(MATCH), "n_clicks"),
    State(CytoscapeAIO.ids.info_toggle(MATCH), "variant"),
    prevent_initial_call=True,
)

clientside_callback(
    ClientsideFunction("cytoscape_aio", "placeInfo"),
    Input(CytoscapeAIO.ids.info(MATCH), "children"),
    Input(CytoscapeAIO.ids.info_toggle(MATCH), "variant"),
)

clientside_callback(
    ClientsideFunction("cytoscape_aio", "toggleTheme"),
    Input(CytoscapeAIO.ids.theme_toggle(MATCH), "n_clicks"),
    prevent_initial_call=True,
)

clientside_callback(
    ClientsideFunction("cytoscape_aio", "themeIcon"),
    Output(CytoscapeAIO.ids.theme_icon(MATCH), "icon"),
    Input(CytoscapeAIO.ids.theme(MATCH), "data"),
)
