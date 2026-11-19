"""Mahalle Veri QGIS plugin (GPL-2.0-or-later)."""


def classFactory(iface):  # noqa: N802 (QGIS API name)
    from .plugin import MahalleVeriPlugin

    return MahalleVeriPlugin(iface)
