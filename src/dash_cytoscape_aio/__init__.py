from importlib.metadata import version

from dash_cytoscape_aio.aio import CytoscapeAIO

__version__ = version("dash-cytoscape-aio")
__all__ = ["CytoscapeAIO"]
