"""VistaPlanner - Application de bureau.

Cette fenetre appelle directement les fonctions deja presentes dans le
dossier planner/ (le meme code que la ligne de commande). Aucune logique
metier n'est dupliquee ici : ce fichier ne fait que construire des
formulaires et afficher les resultats.
"""

from __future__ import annotations

import json
import threading
import traceback
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog

from planner.config import DEFAULT_BASENAME, DEFAULT_OUTPUT_DIRECTORY
from planner.data.viewpoints import PARIS_FIREWORKS_VIEWPOINTS
from planner.exporters.geojson import write_amenities_geojson, write_geojson
from planner.exporters.html_map import write_html_map
from planner.exporters.kml import write_kml
from planner.models import Event
from planner.providers.geojson import read_amenities_geojson
from planner.providers.overpass import (
    DEFAULT_ENDPOINT,
    FEATURE_TAGS,
    TRANSPORT_TAGS,
    OverpassClient,
    OverpassError,
)
from planner.scoring import score_location

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class LogBox(ctk.CTkTextbox):
    """Zone de texte en lecture seule pour afficher les resultats et erreurs."""

    def log(self, message: str) -> None:
        self.configure(state="normal")
        self.insert("end", message + "\n")
        self.configure(state="disabled")
        self.see("end")

    def clear(self) -> None:
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")


def run_in_background(button: ctk.CTkButton, log: LogBox, task) -> None:
    """Execute `task` dans un thread separe pour ne pas geler la fenetre,
    puis affiche le resultat ou l'erreur dans le journal."""

    def wrapper():
        button.configure(state="disabled")
        try:
            task()
        except Exception as error:  # noqa: BLE001 - on veut tout attraper pour l'afficher
            log.log(f"Erreur : {error}")
            log.log(traceback.format_exc(limit=2))
        finally:
            button.configure(state="normal")

    threading.Thread(target=wrapper, daemon=True).start()


def choose_save_path(entry: ctk.CTkEntry, filetypes, default_name: str) -> None:
    path = filedialog.asksaveasfilename(
        defaultextension="",
        filetypes=filetypes,
        initialfile=default_name,
    )
    if path:
        entry.delete(0, "end")
        entry.insert(0, path)


def choose_open_path(entry: ctk.CTkEntry, filetypes) -> None:
    path = filedialog.askopenfilename(filetypes=filetypes)
    if path:
        entry.delete(0, "end")
        entry.insert(0, path)


def labeled_entry(parent, label_text: str, default: str = "") -> ctk.CTkEntry:
    ctk.CTkLabel(parent, text=label_text).pack(anchor="w", padx=16, pady=(10, 2))
    entry = ctk.CTkEntry(parent, placeholder_text=label_text)
    if default:
        entry.insert(0, default)
    entry.pack(fill="x", padx=16)
    return entry


class BuildTab(ctk.CTkFrame):
    """Onglet 'build' : exporte les points de vue en KML + GeoJSON."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.event = labeled_entry(self, "Nom de l'evenement", "Feu d'artifice Paris")
        self.location = labeled_entry(self, "Lieu", "Tour Eiffel")
        self.radius = labeled_entry(self, "Rayon de planification (km)", "8")
        self.output_dir = labeled_entry(self, "Dossier de sortie", str(DEFAULT_OUTPUT_DIRECTORY))
        self.basename = labeled_entry(self, "Nom de base des fichiers", DEFAULT_BASENAME)

        self.button = ctk.CTkButton(self, text="Generer KML + GeoJSON", command=self.run)
        self.button.pack(pady=16)
        self.log = LogBox(self, height=140)
        self.log.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def run(self):
        def task():
            self.log.clear()
            event = Event(
                name=self.event.get(),
                location=self.location.get(),
                radius_km=float(self.radius.get() or 8),
            )
            output_dir = Path(self.output_dir.get())
            output_dir.mkdir(parents=True, exist_ok=True)
            basename = self.basename.get() or DEFAULT_BASENAME
            kml_path = output_dir / f"{basename}.kml"
            geojson_path = output_dir / f"{basename}.geojson"
            write_kml(kml_path, event, PARIS_FIREWORKS_VIEWPOINTS)
            write_geojson(geojson_path, event, PARIS_FIREWORKS_VIEWPOINTS)
            self.log.log(f"{len(PARIS_FIREWORKS_VIEWPOINTS)} points de vue exportes")
            self.log.log(f"KML : {kml_path}")
            self.log.log(f"GeoJSON : {geojson_path}")

        run_in_background(self.button, self.log, task)


class ScanTab(ctk.CTkFrame):
    """Onglet 'scan' / 'transport' : interroge OpenStreetMap (Overpass)."""

    def __init__(self, parent, mode: str):
        super().__init__(parent, fg_color="transparent")
        self.mode = mode  # "scan" (commodites) ou "transport"
        default_output = f"output/{'amenities' if mode == 'scan' else 'transport'}.geojson"

        self.lat = labeled_entry(self, "Latitude", "48.8584")
        self.lon = labeled_entry(self, "Longitude", "2.2945")
        self.radius = labeled_entry(self, "Rayon (metres)", "800")

        ctk.CTkLabel(self, text="Fichier de sortie").pack(anchor="w", padx=16, pady=(10, 2))
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16)
        self.output = ctk.CTkEntry(row, placeholder_text="Fichier de sortie")
        self.output.insert(0, default_output)
        self.output.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            row, text="...", width=32,
            command=lambda: choose_save_path(
                self.output, [("GeoJSON", "*.geojson")], Path(default_output).name
            ),
        ).pack(side="left", padx=(6, 0))

        self.endpoint = labeled_entry(self, "Endpoint Overpass", DEFAULT_ENDPOINT)

        label = "Scanner les commodites" if mode == "scan" else "Scanner les transports"
        self.button = ctk.CTkButton(self, text=label, command=self.run)
        self.button.pack(pady=16)
        self.log = LogBox(self, height=140)
        self.log.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def run(self):
        def task():
            self.log.clear()
            self.log.log("Interrogation d'OpenStreetMap, cela peut prendre quelques secondes...")
            feature_tags = TRANSPORT_TAGS if self.mode == "transport" else FEATURE_TAGS
            try:
                client = OverpassClient(endpoint=self.endpoint.get())
                amenities = client.scan(
                    float(self.lat.get()),
                    float(self.lon.get()),
                    int(self.radius.get()),
                    feature_tags=feature_tags,
                )
            except (OverpassError, ValueError) as error:
                self.log.log(f"Erreur : {error}")
                return
            output_path = Path(self.output.get())
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_amenities_geojson(output_path, amenities)
            self.log.log(f"{len(amenities)} elements exportes vers {output_path}")

        run_in_background(self.button, self.log, task)


class ScoreTab(ctk.CTkFrame):
    """Onglet 'score' : calcule un score de confort/acces a partir de
    fichiers deja exportes (equivalent de 'score-files')."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        def file_row(label_text, filetypes):
            ctk.CTkLabel(self, text=label_text).pack(anchor="w", padx=16, pady=(10, 2))
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=16)
            entry = ctk.CTkEntry(row, placeholder_text=label_text)
            entry.pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="...", width=32,
                command=lambda: choose_open_path(entry, filetypes),
            ).pack(side="left", padx=(6, 0))
            return entry

        self.amenities = file_row("Fichier commodites (GeoJSON)", [("GeoJSON", "*.geojson")])
        self.transport = file_row("Fichier transports (GeoJSON)", [("GeoJSON", "*.geojson")])

        ctk.CTkLabel(self, text="Fichier de sortie (score)").pack(anchor="w", padx=16, pady=(10, 2))
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16)
        self.output = ctk.CTkEntry(row, placeholder_text="Fichier de sortie")
        self.output.insert(0, "output/location-score.json")
        self.output.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            row, text="...", width=32,
            command=lambda: choose_save_path(
                self.output, [("JSON", "*.json")], "location-score.json"
            ),
        ).pack(side="left", padx=(6, 0))

        self.button = ctk.CTkButton(self, text="Calculer le score", command=self.run)
        self.button.pack(pady=16)
        self.log = LogBox(self, height=140)
        self.log.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def run(self):
        def task():
            self.log.clear()
            try:
                amenities = read_amenities_geojson(Path(self.amenities.get()))
                transport = read_amenities_geojson(Path(self.transport.get()))
            except (ValueError, OSError) as error:
                self.log.log(f"Erreur : {error}")
                return
            result = score_location(amenities, transport)
            output_path = Path(self.output.get())
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(result.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
            )
            self.log.log(f"Confort : {result.comfort}/10")
            self.log.log(f"Acces : {result.access}/10")
            self.log.log(f"Global : {result.overall}/10")
            self.log.log(f"Rapport : {output_path}")

        run_in_background(self.button, self.log, task)


class MapTab(ctk.CTkFrame):
    """Onglet 'map' : construit la carte HTML interactive (Leaflet)."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.event = labeled_entry(self, "Nom de l'evenement", "Feu d'artifice Paris")
        self.location = labeled_entry(self, "Lieu", "Tour Eiffel")

        def file_row(label_text, filetypes):
            ctk.CTkLabel(self, text=label_text).pack(anchor="w", padx=16, pady=(10, 2))
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=16)
            entry = ctk.CTkEntry(row, placeholder_text=label_text)
            entry.pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="...", width=32,
                command=lambda: choose_open_path(entry, filetypes),
            ).pack(side="left", padx=(6, 0))
            return entry

        self.amenities = file_row("Fichier commodites (GeoJSON)", [("GeoJSON", "*.geojson")])
        self.transport = file_row("Fichier transports (GeoJSON)", [("GeoJSON", "*.geojson")])

        ctk.CTkLabel(self, text="Fichier de sortie (carte HTML)").pack(anchor="w", padx=16, pady=(10, 2))
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16)
        self.output = ctk.CTkEntry(row, placeholder_text="Fichier de sortie")
        self.output.insert(0, "output/event-map.html")
        self.output.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            row, text="...", width=32,
            command=lambda: choose_save_path(self.output, [("HTML", "*.html")], "event-map.html"),
        ).pack(side="left", padx=(6, 0))

        self.button = ctk.CTkButton(self, text="Creer la carte interactive", command=self.run)
        self.button.pack(pady=16)
        self.log = LogBox(self, height=140)
        self.log.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def run(self):
        def task():
            self.log.clear()
            try:
                amenities = read_amenities_geojson(Path(self.amenities.get()))
                transport = read_amenities_geojson(Path(self.transport.get()))
            except (ValueError, OSError) as error:
                self.log.log(f"Erreur : {error}")
                return
            event = Event(name=self.event.get(), location=self.location.get())
            output_path = Path(self.output.get())
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_html_map(output_path, event, PARIS_FIREWORKS_VIEWPOINTS, amenities, transport)
            self.log.log(f"Carte interactive : {output_path}")
            self.log.log("Ouvrez ce fichier dans un navigateur (connexion internet requise pour le fond de carte).")

        run_in_background(self.button, self.log, task)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VistaPlanner")
        self.geometry("560x620")
        self.minsize(480, 520)

        ctk.CTkLabel(
            self, text="VistaPlanner", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(16, 0))
        ctk.CTkLabel(
            self,
            text="Cartes portables pour evenements en exterieur",
            text_color="gray60",
        ).pack(pady=(0, 12))

        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        tab_build = tabs.add("Construire")
        tab_scan = tabs.add("Commodites")
        tab_transport = tabs.add("Transports")
        tab_score = tabs.add("Score")
        tab_map = tabs.add("Carte")

        BuildTab(tab_build).pack(fill="both", expand=True)
        ScanTab(tab_scan, mode="scan").pack(fill="both", expand=True)
        ScanTab(tab_transport, mode="transport").pack(fill="both", expand=True)
        ScoreTab(tab_score).pack(fill="both", expand=True)
        MapTab(tab_map).pack(fill="both", expand=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()
