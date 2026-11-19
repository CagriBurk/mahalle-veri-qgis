"""Load a mahalle-veri GeoPackage into a QGIS project with ready-made styles.

Uses only the PyQGIS API (works on QGIS 3.34+ / Qt5 and QGIS 4 / Qt6): no
geopandas or other heavy dependency, as the project plan requires.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from qgis.core import (
    QgsCategorizedSymbolRenderer,
    QgsClassificationJenks,
    QgsFillSymbol,
    QgsMarkerSymbol,
    QgsPalLayerSettings,
    QgsProject,
    QgsRasterLayer,
    QgsRendererCategory,
    QgsRuleBasedRenderer,
    QgsStyle,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
)

from . import spec as S


def _uri(path: Path, name: str) -> str:
    return f"{Path(path).as_posix()}|layername={name}"


def _graduated(layer: QgsVectorLayer, ls: S.LayerSpec) -> None:
    """Jenks classes as rules, plus an ELSE rule so features without data stay visible."""
    o = ls.options
    ranges = QgsClassificationJenks().classes(layer, ls.field, int(o.get("classes", 5)))
    ramp = QgsStyle.defaultStyle().colorRamp(o.get("ramp", "YlOrRd"))
    root = QgsRuleBasedRenderer.Rule(None)
    n = max(len(ranges), 1)
    for i, r in enumerate(ranges):
        color = ramp.color(i / (n - 1) if n > 1 else 1.0).name() if ramp else "#fd8d3c"
        sym = QgsFillSymbol.createSimple({"color": color, "outline_color": "#7f7f7f", "outline_width": "0.1"})
        lower_op = ">=" if i == 0 else ">"
        expr = f'"{ls.field}" {lower_op} {r.lowerBound()} AND "{ls.field}" <= {r.upperBound()}'
        label = f"{r.lowerBound():,.0f} – {r.upperBound():,.0f}".replace(",", ".")
        root.appendChild(QgsRuleBasedRenderer.Rule(sym, 0, 0, expr, label))
    other = QgsFillSymbol.createSimple({
        "color": o.get("no_data_color", "#d9d9d9"), "outline_color": "#7f7f7f", "outline_width": "0.1",
        "style": "b_diagonal",
    })
    else_rule = QgsRuleBasedRenderer.Rule(other, 0, 0, "", o.get("no_data_label", "Veri yok"))
    else_rule.setIsElse(True)
    root.appendChild(else_rule)
    layer.setRenderer(QgsRuleBasedRenderer(root))


def _outline(layer: QgsVectorLayer, ls: S.LayerSpec) -> None:
    o = ls.options
    sym = QgsFillSymbol.createSimple({"style": "no", "outline_color": o.get("color", "#222222"),
                                      "outline_width": str(o.get("width", 0.6))})
    layer.renderer().setSymbol(sym)
    if ls.field:
        settings = QgsPalLayerSettings()
        settings.fieldName = ls.field
        settings.enabled = True
        fmt = settings.format()
        fmt.setSize(9)
        settings.setFormat(fmt)
        layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
        layer.setLabelsEnabled(True)


def _categorized(layer: QgsVectorLayer, ls: S.LayerSpec) -> None:
    cats = []
    for value, (color, label) in ls.options["categories"].items():
        sym = QgsMarkerSymbol.createSimple({"name": "circle", "color": color, "size": "1.8",
                                            "outline_color": "#ffffff", "outline_width": "0.2"})
        cats.append(QgsRendererCategory(value, sym, label))
    layer.setRenderer(QgsCategorizedSymbolRenderer(ls.field, cats))


def _fill(layer: QgsVectorLayer, ls: S.LayerSpec) -> None:
    sym = QgsFillSymbol.createSimple({"color": ls.options.get("color", "#4daf4a"), "outline_style": "no"})
    sym.setOpacity(float(ls.options.get("opacity", 1.0)))
    layer.renderer().setSymbol(sym)


STYLERS = {"graduated": _graduated, "outline": _outline, "categorized": _categorized, "fill": _fill}


def osm_basemap() -> QgsRasterLayer:
    uri = f"type=xyz&url={quote(S.OSM_TILE_URL, safe=':/')}&zmin=0&zmax=19"
    return QgsRasterLayer(uri, "OpenStreetMap", "wms")


def load_package(path: str | Path, project: QgsProject | None = None, add_basemap: bool = True) -> dict:
    """Add the package's layers under one group; returns {"group", "layers", "skipped", "sources"}."""
    project = project or QgsProject.instance()
    path = Path(path)
    specs = S.plan(path)
    if not specs:
        raise ValueError(f"{path.name} bir mahalle-veri paketi değil (tanınan katman yok).")
    root = project.layerTreeRoot()
    group = root.insertGroup(0, S.group_title(path, [s.name for s in specs]))
    loaded, skipped = {}, []
    for ls in specs:
        layer = QgsVectorLayer(_uri(path, ls.name), ls.title, "ogr")
        if not layer.isValid():
            skipped.append(ls.name)
            continue
        styler = STYLERS.get(ls.kind)
        if styler is not None:
            styler(layer, ls)
        project.addMapLayer(layer, False)
        node = group.addLayer(layer)
        node.setItemVisibilityChecked(ls.visible)
        loaded[ls.name] = layer
    if add_basemap:
        base = osm_basemap()
        if base.isValid():
            project.addMapLayer(base, False)
            root.insertLayer(len(root.children()), base)  # bottom of the tree
            loaded["osm_basemap"] = base
        else:
            skipped.append("osm_basemap")
    return {"group": group, "layers": loaded, "skipped": skipped, "sources": S.read_sources(path)}
