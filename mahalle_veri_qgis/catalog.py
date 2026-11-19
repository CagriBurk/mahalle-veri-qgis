"""Package catalogue (katalog.json) on the plugin side. Pure Python, no QGIS
imports, so it is tested with plain pytest; downloading is in remote.py.

The catalogue is published next to the packages in the public data
repository. Each entry carries the file's size and SHA-256, so a package is
used only if it arrives intact.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

DEFAULT_URL = "https://github.com/CagriBurk/mahalle-veri-paketler/releases/download/katalog/katalog.json"
SETTINGS_KEY = "mahalle_veri/katalog_url"  # QgsSettings override (tests, mirrors)
SCHEMA_VERSION = 1
REQUIRED = ("id", "il_adi", "yil", "dosya", "url", "boyut", "sha256", "olusturma_tarihi")


class CatalogError(ValueError):
    """Catalogue or package problem, with a message fit for the user."""


def parse(data: bytes) -> list[dict]:
    """Valid entries of a catalogue, newest first; invalid entries are skipped."""
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise CatalogError("Katalog okunamadı (geçerli bir JSON değil).") from None
    if not isinstance(doc, dict) or not isinstance(doc.get("paketler"), list):
        raise CatalogError("Katalog biçimi tanınmadı.")
    if int(doc.get("surum", 0)) > SCHEMA_VERSION:
        raise CatalogError("Katalog bu eklenti sürümünden yeni; eklentiyi güncelleyin.")
    entries = [e for e in doc["paketler"] if isinstance(e, dict) and all(k in e for k in REQUIRED)]
    for e in entries:
        if not _safe_name(e["id"]) or not _safe_name(e["dosya"]) or not str(e["dosya"]).endswith(".gpkg"):
            raise CatalogError(f"Katalogda geçersiz dosya adı: {e['dosya']!r}")
    return sorted(entries, key=lambda e: e["olusturma_tarihi"], reverse=True)


def _safe_name(name) -> bool:
    """A plain file/folder name: no path separators, no '..', not hidden."""
    name = str(name)
    return bool(name) and "/" not in name and "\\" not in name and ".." not in name and not name.startswith(".")


def label(e: dict) -> str:
    day = str(e["olusturma_tarihi"])[:10]
    text = f"{e['il_adi']} {e['yil']} · {day} · {int(e['boyut']) / 1e6:.1f} MB"
    if e.get("uyarilar"):
        text += f" · {len(e['uyarilar'])} uyarı"
    return text


def describe(e: dict) -> str:
    lines = [f"Lisans: {e.get('lisans', '?')} · araç sürümü {e.get('arac_surumu', '?')}"]
    if e.get("eslesme_orani") is not None:
        lines.append(f"Nüfus eşleşmesi: %{float(e['eslesme_orani']) * 100:.1f}")
    for w in e.get("uyarilar", []):
        lines.append(f"Uyarı: {w}")
    for n in e.get("notlar", []):
        lines.append(f"Not: {n}")
    sources = e.get("kaynaklar") or []
    if sources:
        lines.append("Kaynaklar: " + "; ".join(str(s.get("kaynak")) for s in sources))
    return "\n".join(lines)


def local_path(folder: Path, e: dict) -> Path:
    return Path(folder) / e["id"] / e["dosya"]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def is_verified(path: Path, sha256: str) -> bool:
    return Path(path).is_file() and sha256_of(path) == sha256


def save_verified(path: Path, data: bytes, sha256: str) -> Path:
    """Write ``data`` to ``path`` only if its SHA-256 matches (atomic rename)."""
    if hashlib.sha256(data).hexdigest() != sha256:
        raise CatalogError("İndirilen dosya katalogdaki özetle (SHA-256) uyuşmuyor; bozuk ya da eksik indi.")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_bytes(data)
    tmp.replace(path)
    return path
