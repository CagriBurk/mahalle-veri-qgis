"""What the plugin loads and how it looks. Pure Python: no QGIS imports, so it
can be tested with plain pytest (tests/test_qgis_plugin_spec.py)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
import dataclasses
from dataclasses import dataclass
from pathlib import Path

OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
OSM_ATTRIBUTION = "© OpenStreetMap katkıcıları"


@dataclass(frozen=True)
class LayerSpec:
    name: str  # layer/table name inside the GeoPackage
    title: str  # Turkish title in the layer tree
    kind: str  # "graduated" | "outline" | "categorized" | "fill" | "table"
    field: str | None = None
    visible: bool = True
    options: dict = dataclasses.field(default_factory=dict)


# Top → bottom in the layer tree (QGIS draws the top one last, i.e. on top).
LAYERS: tuple[LayerSpec, ...] = (
    LayerSpec("durak", "Toplu ulaşım durakları", "categorized", "alt_kategori", visible=False,
              options={"categories": {
                  "metro": ("#d7301f", "Metro"),
                  "tramvay": ("#2ca25f", "Tramvay"),
                  "banliyo": ("#3182bd", "İZBAN (banliyö)"),
                  "vapur": ("#08519c", "Vapur iskelesi"),
                  "otobus": ("#bdbdbd", "Otobüs durağı"),
              }}),
    LayerSpec("donati", "Donatılar (eğitim, sağlık, toplanma)", "categorized", "kategori", visible=False,
              options={"categories": {
                  "egitim": ("#1f78b4", "Eğitim"),
                  "saglik": ("#e31a1c", "Sağlık"),
                  "toplanma": ("#33a02c", "Afet toplanma alanı"),
              }}),
    LayerSpec("park", "Parklar (OSM)", "fill", visible=False,
              options={"color": "#4daf4a", "opacity": 0.7}),
    LayerSpec("ilce", "İlçe sınırları", "outline", "ilce",
              options={"color": "#222222", "width": 0.6}),
    LayerSpec("mahalle", "Mahalleler: nüfus yoğunluğu (kişi/km²)", "graduated", "yogunluk",
              options={"classes": 5, "ramp": "YlOrRd", "no_data_label": "Nüfus verisi yok (OSB vb.)",
                       "no_data_color": "#d9d9d9"}),
    LayerSpec("ilce_yas", "İlçe yaş grupları (tablo)", "table", visible=False),
    LayerSpec("metadata", "Kaynaklar ve lisanslar (tablo)", "table", visible=False),
)


def _open(path: Path):
    """Read-only connection that is closed afterwards (Windows keeps open files locked)."""
    return closing(sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True))


def group_title(path: Path, layers: list[str]) -> str:
    stem = Path(path).stem  # e.g. izmir_mahalle_2023
    parts = stem.split("_")
    if len(parts) >= 3 and parts[1] == "mahalle":
        province = {"izmir": "İzmir"}.get(parts[0], parts[0].title())
        return f"Mahalle Veri: {province} {parts[2]}"
    return f"Mahalle Veri: {stem}"


def package_tables(path: Path) -> list[str]:
    """Layer and table names registered in the GeoPackage (gpkg_contents)."""
    with _open(path) as con:
        return [r[0] for r in con.execute("SELECT table_name FROM gpkg_contents ORDER BY table_name")]


def plan(path: Path) -> list[LayerSpec]:
    """Specs for the layers that exist in this package, in tree order."""
    present = set(package_tables(path))
    return [spec for spec in LAYERS if spec.name in present]


def read_sources(path: Path) -> list[dict]:
    """Rows of the package's metadata table (source, license, attribution, dates)."""
    cols = ("kaynak", "lisans", "atif", "yayin_tarihi", "indirme_tarihi", "arac_surumu", "koordinat_sistemi")
    with _open(path) as con:
        have = {r[1] for r in con.execute("PRAGMA table_info(metadata)")}
        if not have:
            return []
        use = [c for c in cols if c in have]
        rows = con.execute(f"SELECT {', '.join(use)} FROM metadata").fetchall()
    return [dict(zip(use, r)) for r in rows]


def read_info(path: Path) -> dict:
    """Warnings and notes from the package's paket_bilgisi table (empty for older packages)."""
    out = {"uyarilar": [], "notlar": []}
    with _open(path) as con:
        if not con.execute("PRAGMA table_info(paket_bilgisi)").fetchall():
            return out
        for key, value in con.execute("SELECT anahtar, deger FROM paket_bilgisi"):
            if key == "uyari":
                out["uyarilar"].append(value)
            elif key == "not":
                out["notlar"].append(value)
    return out


def attribution_text(sources: list[dict]) -> str:
    """Unique attributions, in order, one per line."""
    seen = dict.fromkeys(s.get("atif") for s in sources if s.get("atif"))
    return "\n".join(seen)
