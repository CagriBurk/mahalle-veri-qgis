# Mahalle Veri: QGIS plugin

A QGIS plugin that loads neighbourhood-level data packages into QGIS in one click. Every
package states its sources and dates, and the layers come pre-styled:

- population density map (neighbourhoods without data shown in grey),
- district boundaries and labels,
- education, health and emergency assembly points,
- public transport stops and parks,
- an optional OpenStreetMap basemap.

Packages are downloaded once from a catalogue and are used only after their SHA-256 checksum
is verified. Licences, attributions and production warnings are shown inside the plugin.
Currently one package is available: **İzmir**. Supports QGIS 3.34+ and QGIS 4.x.

**Install:** download `mahalle_veri_qgis-<version>.zip` from [Releases](../../releases), then in
QGIS use *Plugins → Manage and Install Plugins → Install from ZIP*, and open
*Vector → Mahalle Veri*.

Data packages: [mahalle-veri-paketler](https://github.com/CagriBurk/mahalle-veri-paketler)
(ODbL 1.0, © OpenStreetMap contributors). Plugin licence: GNU GPL v2 or later.

---

## Türkçe

Mahalle düzeyindeki veri paketlerini tek tıkla QGIS'e yükler. Her paketin kaynağı ve tarihi bellidir. Katmanlar hazır stillerle gelir:

- nüfus yoğunluğu haritası (veri olmayan mahalleler gri),
- ilçe sınırları ve ilçe adları,
- eğitim, sağlık ve toplanma alanı donatıları,
- toplu ulaşım durakları,
- parklar,
- isteğe bağlı OpenStreetMap altlığı.

Paketin kaynakları, lisansları ve üretim uyarıları eklentide görünür.

Şu an yalnızca **İzmir** paketi var.

## Kurulum

1. [Releases](../../releases) sayfasından `mahalle_veri_qgis-<sürüm>.zip` dosyasını indirin.
2. QGIS'te **Eklentiler → Eklentileri Yönet ve Kur → ZIP'ten Kur** yolundan zip'i seçin.
3. **Vektör → Mahalle Veri → Mahalle veri paketini yükle…** komutunu açın.
   - **Katalogdan indir:** Önce **Yenile**'ye basın, paketi seçin, sonra **İndir ve yükle**'ye basın. Paket QGIS profil klasörüne bir kez iner; SHA-256 özeti doğrulanmadan kullanılmaz.
   - **Dosyadan yükle:** Elinizdeki bir `.gpkg` paketini seçin.

QGIS 3.34 ve üstü ile QGIS 4.x desteklenir.

## Veri

Paketler [mahalle-veri-paketler](https://github.com/CagriBurk/mahalle-veri-paketler) deposunda yayımlanır.
- Lisans: **ODbL 1.0**, © OpenStreetMap katkıcıları.
- Diğer kaynaklar (İzmir Büyükşehir Belediyesi Açık Veri Portalı, TÜİK) ve lisansları her paketin `metadata` tablosunda yazar.

## Lisans

Eklentinin lisansı GNU GPL v2 veya üstüdür (bkz. `LICENSE`). Paketleri üreten araç ayrı ve kapalı kaynaklıdır; bu depoda yer almaz.

Hata bildirimi ve öneriler için [Issues](../../issues) sayfasını kullanabilirsiniz.
