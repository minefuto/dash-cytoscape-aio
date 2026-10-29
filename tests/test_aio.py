import pytest

from dash_cytoscape_aio import CytoscapeAIO


def test_requires_id() -> None:
    with pytest.raises(ValueError):
        CytoscapeAIO([{"data": {"source": "a", "target": "b"}}])


def test_zoom_max_positive() -> None:
    with pytest.raises(ValueError):
        CytoscapeAIO([], zoom_max=0)


def test_props_merge() -> None:
    aio = CytoscapeAIO(
        [{"data": {"id": "a"}}],
        cytoscape_props={
            "layout": {"name": "cose"},
            "id": "x",
            "boxSelectionEnabled": False,
        },
        multiselect_props={"placeholder": "p", "value": ["z"]},
        info_props={"p": "xl", "id": "y", "style": {"maxWidth": 500}},
        aio_id="t",
    )
    assert isinstance(aio.children, list)
    cy, overlay, info_box, store, override, _ = aio.children
    ms, zoom, info_toggle, theme_toggle = overlay.children.children
    info = info_box.children
    assert cy.id == CytoscapeAIO.ids.cytoscape("t")
    assert cy.layout == {"name": "cose"}
    assert cy.boxSelectionEnabled is False
    assert ms.placeholder == "p"
    assert ms.value == []
    assert ms.searchable is True
    assert zoom.variant == "filled"
    assert cy.stylesheet == store.data["stylesheet"]
    assert cy.stylesheet == [{"selector": "node", "style": {"label": "data(label)"}}]
    assert override.id == CytoscapeAIO.ids.style_override("t")
    assert info.id == CytoscapeAIO.ids.info("t")
    assert info.p == "xl"
    assert info.shadow == "md"
    assert info.style == {"maxWidth": 500, "maxHeight": 300, "overflow": "auto"}
    assert info_toggle.id == CytoscapeAIO.ids.info_toggle("t")
    assert info_toggle.variant == "filled"
    assert theme_toggle.id == CytoscapeAIO.ids.theme_toggle("t")


def test_clientside_js_served() -> None:
    from dash import Dash

    app = Dash(__name__)
    app.layout = CytoscapeAIO([], aio_id="t")
    client = app.server.test_client()
    html = client.get("/").get_data(as_text=True)
    path = "/_dash-component-suites/dash_cytoscape_aio/cytoscape_aio"
    assert path in html
    src = html[html.index(path) :].split('"')[0]
    res = client.get(src)
    assert res.status_code == 200
    assert b"dash_clientside.cytoscape_aio" in res.data


def test_edge_text_in_store() -> None:
    aio = CytoscapeAIO([], edge_text=["{a}", "{b}"], aio_id="t")
    assert isinstance(aio.children, list)
    store = aio.children[3]
    assert store.data["edgeText"] == ["{a}", "{b}"]
    assert store.data["edgeTextSep"] == ":"


def test_override_selected_in_store() -> None:
    for flag in (False, True):
        aio = CytoscapeAIO([], override_selected=flag)
        assert isinstance(aio.children, list)
        assert aio.children[3].data["overrideSelected"] is flag
