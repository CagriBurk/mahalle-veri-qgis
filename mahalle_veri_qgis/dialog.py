"""The plugin's single dialog: download a package from the catalogue or pick a
local file, load it, and show its sources and warnings."""

from __future__ import annotations

from pathlib import Path

from qgis.gui import QgsFileWidget
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from . import catalog as C
from . import spec as S
from .loader import load_package


class LoadDialog(QDialog):
    def __init__(self, parent=None, start_dir: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Mahalle Veri: paketi yükle")
        self.setMinimumWidth(560)
        self.entries: list[dict] = []
        layout = QVBoxLayout(self)

        # 1) from the catalogue (central pool)
        box = QGroupBox("Katalogdan indir", self)
        col = QVBoxLayout(box)
        row = QHBoxLayout()
        self.combo = QComboBox(box)
        self.combo.setPlaceholderText("Kataloğu görmek için 'Yenile'ye basın")
        self.combo.currentIndexChanged.connect(self._describe)
        row.addWidget(self.combo, 1)
        self.refresh_button = QPushButton("Yenile", box)
        self.refresh_button.clicked.connect(self.refresh_catalog)
        row.addWidget(self.refresh_button)
        col.addLayout(row)
        self.entry_info = QLabel("", box)
        self.entry_info.setWordWrap(True)
        self.entry_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        col.addWidget(self.entry_info)
        self.download_button = QPushButton("İndir ve yükle", box)
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.download_and_load)
        col.addWidget(self.download_button)
        layout.addWidget(box)

        # 2) from a local file
        box2 = QGroupBox("Dosyadan yükle", self)
        col2 = QVBoxLayout(box2)
        col2.addWidget(QLabel("GeoPackage (<code>mahalle-veri paketle</code> çıktısı):", box2))
        self.file = QgsFileWidget(box2)
        self.file.setFilter("GeoPackage (*.gpkg)")
        if start_dir:
            self.file.setDefaultRoot(start_dir)
        col2.addWidget(self.file)
        self.file_button = QPushButton("Dosyayı yükle", box2)
        self.file_button.clicked.connect(self.load)
        col2.addWidget(self.file_button)
        layout.addWidget(box2)

        self.basemap = QCheckBox("OpenStreetMap altlığını ekle", self)
        self.basemap.setChecked(True)
        layout.addWidget(self.basemap)

        layout.addWidget(QLabel("Kaynaklar, kaynak gösterimi ve uyarılar:", self))
        self.sources = QPlainTextEdit(self)
        self.sources.setReadOnly(True)
        self.sources.setPlaceholderText("Paket yüklenince kaynaklar burada görünür.")
        layout.addWidget(self.sources)

        self.status = QLabel("", self)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # catalogue -----------------------------------------------------------
    def _busy(self, text: str) -> None:
        self.status.setText(text)
        QApplication.processEvents()

    def refresh_catalog(self) -> None:
        from . import remote

        self._busy("Katalog indiriliyor…")
        try:
            self.entries = remote.fetch_catalog()
        except C.CatalogError as exc:
            self.entries = []
            self.status.setText(str(exc))
        else:
            self.status.setText(f"Katalogda {len(self.entries)} paket var." if self.entries
                                else "Katalog boş.")
        self.combo.clear()
        for e in self.entries:
            self.combo.addItem(C.label(e))
        if self.entries:
            self.combo.setCurrentIndex(0)  # with a placeholder Qt leaves it at -1
        self.download_button.setEnabled(bool(self.entries))
        self._describe()

    def _describe(self, *_) -> None:
        i = self.combo.currentIndex()
        self.entry_info.setText(C.describe(self.entries[i]) if 0 <= i < len(self.entries) else "")

    def download_and_load(self) -> None:
        from . import remote

        i = self.combo.currentIndex()
        if not 0 <= i < len(self.entries):
            self.status.setText("Önce katalogdan bir paket seçin.")
            return
        entry = self.entries[i]
        self._busy(f"İndiriliyor: {entry['dosya']} ({int(entry['boyut']) / 1e6:.1f} MB)…")
        try:
            path = remote.download_package(entry)
        except C.CatalogError as exc:
            self.status.setText(str(exc))
            return
        self.file.setFilePath(str(path))
        self._load_path(path)

    # local file ------------------------------------------------------------
    def load(self) -> None:
        path = Path(self.file.filePath() or "")
        if not path.is_file():
            self.status.setText("Önce bir .gpkg dosyası seçin.")
            return
        self._load_path(path)

    def _load_path(self, path: Path) -> None:
        try:
            result = load_package(path, add_basemap=self.basemap.isChecked())
        except ValueError as exc:
            self.status.setText(str(exc))
            return
        info = S.read_info(path)
        lines = [f"- {s.get('kaynak')}: {s.get('lisans')} (yayın {str(s.get('yayin_tarihi') or '?')[:10]})"
                 for s in result["sources"]]
        notes = [f"Uyarı: {w}" for w in info["uyarilar"]] + [f"Not: {n}" for n in info["notlar"]]
        text = S.attribution_text(result["sources"]) + "\n\n" + "\n".join(lines)
        if notes:
            text += "\n\n" + "\n".join(notes)
        self.sources.setPlainText(text)
        loaded = [n for n in result["layers"] if n != "osm_basemap"]
        msg = f"{len(loaded)} katman yüklendi."
        if result["skipped"]:
            msg += f" Yüklenemeyen: {', '.join(result['skipped'])}."
        self.status.setText(msg)
