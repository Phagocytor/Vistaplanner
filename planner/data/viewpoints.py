"""Initial curated viewpoints for the Paris fireworks example."""

from planner.models import Viewpoint


PARIS_FIREWORKS_VIEWPOINTS: tuple[Viewpoint, ...] = (
    Viewpoint("Champ-de-Mars", 2.2982, 48.8561, 10, 8, "premium", "Close, immersive view; arrive very early."),
    Viewpoint("Jardins du Trocadéro", 2.2897, 48.8621, 10, 6, "view", "Iconic frontal view; limited shade."),
    Viewpoint("Parc de Belleville", 2.3869, 48.8717, 9, 10, "premium", "Elevated panorama with trees and lawns."),
    Viewpoint("Esplanade des Invalides", 2.3134, 48.8567, 8, 8, "premium", "Open space and a broad western perspective."),
    Viewpoint("Berges de Seine — Passy", 2.2867, 48.8570, 8, 6, "view", "Seine-side perspective; space may fill quickly."),
    Viewpoint("Île aux Cygnes", 2.2878, 48.8517, 8, 8, "premium", "Calmer riverside setting with mature trees."),
    Viewpoint("Parc André-Citroën", 2.2765, 48.8422, 6, 10, "comfort", "Large green space; distant view."),
    Viewpoint("Parc de Saint-Cloud", 2.2186, 48.8429, 10, 10, "premium", "Dominant, spacious panorama; verify opening and access."),
    Viewpoint("Mont Valérien", 2.2235, 48.8703, 10, 8, "premium", "High panoramic viewpoint, outside central Paris."),
    Viewpoint("Terrasse de l'Observatoire de Meudon", 2.2296, 48.8126, 8, 10, "premium", "Quiet elevated setting; distant view."),
)

