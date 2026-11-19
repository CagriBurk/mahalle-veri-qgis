"""Downloads through QGIS's own network stack (respects the user's proxy and
SSL settings): the catalogue and the packages it lists."""

from __future__ import annotations

from pathlib import Path

from qgis.core import QgsApplication, QgsBlockingNetworkRequest, QgsSettings
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest

from . import catalog as C


def catalog_url() -> str:
    return str(QgsSettings().value(C.SETTINGS_KEY, C.DEFAULT_URL) or C.DEFAULT_URL)


def fetch(url: str, feedback=None) -> bytes:
    req = QgsBlockingNetworkRequest()
    err = req.get(QNetworkRequest(QUrl(url)), True, feedback)
    if err != QgsBlockingNetworkRequest.ErrorCode.NoError:
        raise C.CatalogError(f"İndirilemedi: {req.errorMessage() or url}")
    return bytes(req.reply().content())


def fetch_catalog(url: str | None = None) -> list[dict]:
    return C.parse(fetch(url or catalog_url()))


def download_dir() -> Path:
    return Path(QgsApplication.qgisSettingsDirPath()) / "mahalle_veri" / "paketler"


def download_package(entry: dict, folder: Path | None = None, feedback=None) -> Path:
    """Local copy of the package; downloaded only if missing or changed."""
    path = C.local_path(folder or download_dir(), entry)
    if C.is_verified(path, entry["sha256"]):
        return path
    return C.save_verified(path, fetch(entry["url"], feedback), entry["sha256"])
