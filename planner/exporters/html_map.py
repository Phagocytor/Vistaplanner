"""Generate a resilient interactive Leaflet map without Python dependencies."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Iterable

from planner.models import Amenity, Event, Viewpoint


def _safe_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def write_html_map(
    path: Path,
    event: Event,
    viewpoints: Iterable[Viewpoint],
    amenities: Iterable[Amenity],
    transport: Iterable[Amenity],
) -> None:
    """Write an HTML map with independently switchable data layers."""
    viewpoint_data = [
        {
            "name": item.name,
            "lat": item.latitude,
            "lon": item.longitude,
            "category": item.category,
            "view": item.view_score,
            "comfort": item.comfort_score,
            "notes": item.notes,
        }
        for item in viewpoints
    ]
    amenity_data = [_amenity_data(item) for item in amenities]
    transport_data = [_amenity_data(item) for item in transport]
    path.write_text(_html_document(event, viewpoint_data, amenity_data, transport_data), encoding="utf-8")


def _amenity_data(item: Amenity) -> dict[str, object]:
    return {"name": item.name, "lat": item.latitude, "lon": item.longitude, "category": item.category}


def _html_document(
    event: Event,
    viewpoints: list[dict[str, object]],
    amenities: list[dict[str, object]],
    transport: list[dict[str, object]],
) -> str:
    template = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__TITLE__ — VistaPlanner</title>
  <style>
    html, body, #map { height: 100%; margin: 0; }
    #map { font-family: system-ui, sans-serif; }
    .legend { background: #fff; padding: 8px 10px; border-radius: 4px; line-height: 1.45; }
    .map-error { display: grid; place-items: center; height: 100%; padding: 30px; box-sizing: border-box; text-align: center; background: #f6f7f9; color: #212529; }
  </style>
</head>
<body>
<div id="map" aria-label="Carte interactive VistaPlanner"></div>
<script>
const viewpoints = __VIEWPOINTS__;
const amenities = __AMENITIES__;
const transport = __TRANSPORT__;
const mapElement = document.getElementById('map');

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[character]));
}

function showMapError() {
  mapElement.innerHTML = '<div class="map-error"><div><h2>Carte indisponible hors ligne</h2><p>Les données ont bien été exportées, mais ce navigateur ne peut pas charger le fond de carte interactif.</p><p>Vérifie ta connexion Internet puis rouvre ce fichier.</p></div></div>';
}

function loadStylesheet(url) {
  const stylesheet = document.createElement('link');
  stylesheet.rel = 'stylesheet';
  stylesheet.href = url;
  document.head.appendChild(stylesheet);
}

function loadScript(url, onload, onerror) {
  const script = document.createElement('script');
  script.src = url;
  script.onload = onload;
  script.onerror = onerror;
  document.head.appendChild(script);
}

function renderMap() {
  if (!window.L) { showMapError(); return; }
  const map = L.map('map');
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
  const colours = {premium:'#198754', view:'#0d6efd', comfort:'#d99a00', toilets:'#7b2cbf', drinking_water:'#0096c7', bench:'#6c757d', park:'#2a9d4b', garden:'#57cc99', picnic_table:'#ad7f1f', bicycle_rental:'#e76f51', station:'#dc3545', metro_entrance:'#b02a37', tram_stop:'#fd7e14', bus_stop:'#6f42c1'};
  function marker(item, radius) {
    return L.circleMarker([item.lat, item.lon], {radius, color: colours[item.category] || '#495057', fillOpacity: 0.8})
      .bindPopup(`<strong>${escapeHtml(item.name)}</strong><br>${escapeHtml(item.category)}`);
  }
  const viewpointLayer = L.layerGroup(viewpoints.map(item => marker(item, 9).bindPopup(`<strong>${escapeHtml(item.name)}</strong><br>Vue : ${item.view}/10 · Confort : ${item.comfort}/10<br>${escapeHtml(item.notes)}`))).addTo(map);
  const amenityLayer = L.layerGroup(amenities.map(item => marker(item, 5))).addTo(map);
  const transportLayer = L.layerGroup(transport.map(item => marker(item, 6))).addTo(map);
  L.control.layers(null, {'Points de vue': viewpointLayer, 'Équipements': amenityLayer, 'Transports': transportLayer}, {collapsed:false}).addTo(map);
  const positions = viewpoints.concat(amenities, transport).map(item => [item.lat, item.lon]);
  if (positions.length) { map.fitBounds(positions, {padding:[25,25]}); } else { map.setView([48.8566, 2.3522], 12); }
  const legend = L.control({position:'bottomleft'});
  legend.onAdd = () => {
    const div = L.DomUtil.create('div', 'legend');
    div.innerHTML = '<strong>VistaPlanner</strong><br>🟢 Premium · 🔵 Vue · 🟡 Confort<br>Données OpenStreetMap : à vérifier avant l’événement';
    return div;
  };
  legend.addTo(map);
}

function loadLeaflet() {
  loadStylesheet('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css');
  loadScript(
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
    renderMap,
    () => {
      loadStylesheet('https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css');
      loadScript('https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js', renderMap, showMapError);
    }
  );
}

loadLeaflet();
</script>
</body>
</html>"""
    return (
        template.replace("__TITLE__", escape(event.name))
        .replace("__VIEWPOINTS__", _safe_json(viewpoints))
        .replace("__AMENITIES__", _safe_json(amenities))
        .replace("__TRANSPORT__", _safe_json(transport))
    )
