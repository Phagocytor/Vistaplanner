# VistaPlanner

VistaPlanner prepares practical, portable maps for outdoor events. It starts with a
curated list of viewpoints and exports it to formats accepted by Google My Maps,
Google Earth, and most GIS tools.

## Status

This early release exports a curated viewpoint map and can fetch practical
OpenStreetMap amenities. Transport, routing, scoring, and safety-data providers
will be added in later iterations.

## Quick start

VistaPlanner uses only the Python standard library for this first release.

```bash
python -m planner build --event "Feu d'artifice Paris" --location "Tour Eiffel"
```

The command writes these files by default:

```text
output/paris-fireworks.kml
output/paris-fireworks.geojson
```

To install a reusable command-line entry point:

```bash
python -m pip install -e .
vistaplanner build --event "Feu d'artifice Paris" --location "Tour Eiffel"
```

## Scan OpenStreetMap amenities

`scan` uses the public Overpass API to collect toilets, drinking-water points,
benches, picnic tables, parks, gardens, and cycle-rental locations around a
coordinate. The result is a GeoJSON file that can be imported into Google My
Maps or inspected in a GIS tool.

```bash
vistaplanner scan --lat 48.8584 --lon 2.2945 --radius 800 \
  --output output/tour-eiffel-amenities.geojson
```

Public OpenStreetMap data can be incomplete, and endpoint capacity can vary.
The CLI only makes a focused request; use an alternative Overpass endpoint via
`--endpoint` if the default one is temporarily unavailable.

## Scan public transport

`transport` creates a separate layer for stations, metro entrances, tram stops,
and bus stops. These are OpenStreetMap positions, not service-status data; check
the operator's official notices before relying on them on event day.

```bash
vistaplanner transport --lat 48.8584 --lon 2.2945 --radius 1_500 \
  --output output/tour-eiffel-transport.geojson
```

## Score a waiting location

`score` combines the local OpenStreetMap evidence into transparent 0–10 scores:

- **comfort**: toilets, drinking water, benches, green space, picnic tables,
  and bike-share stations;
- **access**: metro entrances, stations, tram stops, and bus stops;
- **overall**: 60% comfort and 40% access.

It is not a prediction of visibility, crowd levels, operational closures, or
safety. The generated JSON report includes the counts used in the calculation.

```bash
vistaplanner score --lat 48.8584 --lon 2.2945 --radius 800 \
  --output output/tour-eiffel-score.json
```

When an Overpass endpoint is busy, retain the two layers already downloaded and
calculate the score without any network request:

```bash
vistaplanner score-files \
  --amenities output/tour-eiffel-amenities.geojson \
  --transport output/tour-eiffel-transport.geojson \
  --output output/tour-eiffel-score.json
```

## Create an interactive map

Create a Leaflet HTML map with separate viewpoint, amenity, and transport
layers. Open the generated file in a browser; an internet connection is needed
there to load the basemap and Leaflet assets.

```bash
vistaplanner map \
  --event "Feu d'artifice Paris" \
  --amenities output/tour-eiffel-amenities.geojson \
  --transport output/tour-eiffel-transport.geojson \
  --output output/tour-eiffel-map.html
```

## Included data

The `build` command currently exports ten curated Paris-area viewpoints for the
2026 fireworks planning example. Their scores are editorial starter data, not
live crowd, access, or safety advice. Always check official event instructions
before travelling.

## Development

```bash
python -m unittest discover
python -m planner --help
```

## License

MIT. See [LICENSE](LICENSE).
