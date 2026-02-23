"""
Grafik-Generator für Schiffe-Versenken
Erstellt alle benötigten PNG-Grafiken programmatisch mit PIL
"""

from PIL import Image, ImageDraw, ImageFont
import os


class GraphicsGenerator:
    """Generiert alle Spielgrafiken"""

    CELL_SIZE = 40

    # Farben
    WATER_COLOR = (65, 105, 225)  # Royal Blue
    WATER_DARK = (50, 80, 180)
    SHIP_COLOR = (128, 128, 128)  # Grau
    SHIP_DARK = (90, 90, 90)
    HIT_COLOR = (220, 20, 60)  # Crimson
    MISS_COLOR = (255, 255, 255)  # Weiß
    DESTROYED_COLOR = (139, 0, 0)  # Dark Red

    def __init__(self, output_dir='images'):
        """Initialisiert den Generator"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_all(self):
        """Generiert alle Grafiken"""
        print("Generiere Grafiken...")
        self.generate_water()
        self.generate_ship_horizontal()
        self.generate_ship_vertical()
        self.generate_hit()
        self.generate_miss()
        self.generate_destroyed()
        self.generate_ship_end_h()
        self.generate_ship_end_v()
        print(f"Alle Grafiken wurden in '{self.output_dir}/' erstellt!")

    def generate_water(self):
        """Generiert Wasser-Tile"""
        size = self.CELL_SIZE
        img = Image.new('RGB', (size, size), self.WATER_COLOR)
        draw = ImageDraw.Draw(img)

        # Wellen-Effekt
        for i in range(0, size, 10):
            draw.line([(i, 0), (i + 5, 5), (i + 10, 0)],
                     fill=self.WATER_DARK, width=1)
            draw.line([(0, i), (5, i + 5), (0, i + 10)],
                     fill=self.WATER_DARK, width=1)

        # Rahmen
        draw.rectangle([0, 0, size-1, size-1], outline=(40, 70, 150), width=1)

        img.save(os.path.join(self.output_dir, 'water.png'))

    def generate_ship_horizontal(self):
        """Generiert horizontales Schiffsteil"""
        size = self.CELL_SIZE
        img = Image.new('RGBA', (size, size), (65, 105, 225, 255))
        draw = ImageDraw.Draw(img)

        # Schiffskörper
        margin = 5
        draw.rectangle([margin, margin + 8, size - margin, size - margin - 8],
                      fill=self.SHIP_COLOR, outline=self.SHIP_DARK, width=2)

        # Details
        draw.line([(size // 2, margin + 10), (size // 2, size - margin - 10)],
                 fill=self.SHIP_DARK, width=2)

        img.save(os.path.join(self.output_dir, 'ship_h.png'))

    def generate_ship_vertical(self):
        """Generiert vertikales Schiffsteil"""
        size = self.CELL_SIZE
        img = Image.new('RGBA', (size, size), (65, 105, 225, 255))
        draw = ImageDraw.Draw(img)

        # Schiffskörper
        margin = 5
        draw.rectangle([margin + 8, margin, size - margin - 8, size - margin],
                      fill=self.SHIP_COLOR, outline=self.SHIP_DARK, width=2)

        # Details
        draw.line([(margin + 10, size // 2), (size - margin - 10, size // 2)],
                 fill=self.SHIP_DARK, width=2)

        img.save(os.path.join(self.output_dir, 'ship_v.png'))

    def generate_ship_end_h(self):
        """Generiert horizontales Schiffsende"""
        size = self.CELL_SIZE
        img = Image.new('RGBA', (size, size), (65, 105, 225, 255))
        draw = ImageDraw.Draw(img)

        # Schiffskörper mit rundem Ende
        margin = 5
        draw.ellipse([margin, margin + 8, margin + 15, size - margin - 8],
                    fill=self.SHIP_COLOR, outline=self.SHIP_DARK)
        draw.rectangle([margin + 7, margin + 8, size - margin, size - margin - 8],
                      fill=self.SHIP_COLOR, outline=self.SHIP_DARK, width=2)

        img.save(os.path.join(self.output_dir, 'ship_end_h.png'))

    def generate_ship_end_v(self):
        """Generiert vertikales Schiffsende"""
        size = self.CELL_SIZE
        img = Image.new('RGBA', (size, size), (65, 105, 225, 255))
        draw = ImageDraw.Draw(img)

        # Schiffskörper mit rundem Ende
        margin = 5
        draw.ellipse([margin + 8, margin, size - margin - 8, margin + 15],
                    fill=self.SHIP_COLOR, outline=self.SHIP_DARK)
        draw.rectangle([margin + 8, margin + 7, size - margin - 8, size - margin],
                      fill=self.SHIP_COLOR, outline=self.SHIP_DARK, width=2)

        img.save(os.path.join(self.output_dir, 'ship_end_v.png'))

    def generate_hit(self):
        """Generiert Treffer-Symbol (rotes X)"""
        size = self.CELL_SIZE
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        margin = 8
        # Rotes X
        draw.line([(margin, margin), (size - margin, size - margin)],
                 fill=self.HIT_COLOR, width=5)
        draw.line([(size - margin, margin), (margin, size - margin)],
                 fill=self.HIT_COLOR, width=5)

        # Äußere Linie für besseren Kontrast
        draw.line([(margin, margin), (size - margin, size - margin)],
                 fill=(139, 0, 0), width=7)
        draw.line([(size - margin, margin), (margin, size - margin)],
                 fill=(139, 0, 0), width=7)
        draw.line([(margin, margin), (size - margin, size - margin)],
                 fill=self.HIT_COLOR, width=5)
        draw.line([(size - margin, margin), (margin, size - margin)],
                 fill=self.HIT_COLOR, width=5)

        img.save(os.path.join(self.output_dir, 'hit.png'))

    def generate_miss(self):
        """Generiert Fehlschuss-Symbol (weißer Kreis)"""
        size = self.CELL_SIZE
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        margin = 12
        # Weißer Kreis mit blauem Rand
        draw.ellipse([margin, margin, size - margin, size - margin],
                    fill=self.MISS_COLOR, outline=(30, 60, 120), width=3)

        img.save(os.path.join(self.output_dir, 'miss.png'))

    def generate_destroyed(self):
        """Generiert Symbol für versenktes Schiff"""
        size = self.CELL_SIZE
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Dunkles rotes X
        margin = 5
        draw.line([(margin, margin), (size - margin, size - margin)],
                 fill=self.DESTROYED_COLOR, width=6)
        draw.line([(size - margin, margin), (margin, size - margin)],
                 fill=self.DESTROYED_COLOR, width=6)

        img.save(os.path.join(self.output_dir, 'destroyed.png'))


def main():
    """Hauptfunktion zum Generieren aller Grafiken"""
    # Bestimme den richtigen Pfad zum images-Ordner
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    images_dir = os.path.join(project_root, 'images')

    generator = GraphicsGenerator(images_dir)
    generator.generate_all()


if __name__ == '__main__':
    main()
