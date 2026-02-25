import math
import random
import pygame
import game.config as config
from game.ui.buttons import BaseButton
from game.theme import theme_manager


def draw_grid_cell(screen, x, y, cell, is_enemy=False, show_ships=True):
    """Zeichnet eine Zelle als sauberes Geometrie-Objekt, ohne fehlerhafte Bilder."""
    theme = theme_manager.current
    cell_rect = pygame.Rect(x, y, config.CELL_SIZE, config.CELL_SIZE)

    # Base Water Cell
    draw_rounded_rect(screen, theme.color_water, cell_rect, radius=4, alpha=150)

    # Schiff
    if show_ships and cell.has_ship() and not cell.is_shot():
        draw_rounded_rect(screen, theme.color_ship, cell_rect, radius=4, alpha=230)
        # Inner highlight
        inner = pygame.Rect(x + 4, y + 4, config.CELL_SIZE - 8, config.CELL_SIZE - 8)
        draw_rounded_rect(screen, theme.color_ship_border, inner, radius=2, alpha=100)

    # Status (Treffer/Fehlschuss) zeichnen
    if cell.status == 2:  # CELL_HIT
        draw_rounded_rect(screen, theme.color_hit, cell_rect, radius=4, alpha=180)
        pygame.draw.line(screen, config.COLOR_WHITE, (x + 8, y + 8),
                         (x + config.CELL_SIZE - 8, y + config.CELL_SIZE - 8), 3)
        pygame.draw.line(screen, config.COLOR_WHITE, (x + config.CELL_SIZE - 8, y + 8),
                         (x + 8, y + config.CELL_SIZE - 8), 3)
    elif cell.status == 3:  # CELL_MISS
        pygame.draw.circle(screen, theme.color_miss, (x + config.CELL_SIZE // 2, y + config.CELL_SIZE // 2), 6)
    elif cell.status == 4:  # CELL_DESTROYED
        draw_rounded_rect(screen, theme.color_destroyed, cell_rect, radius=4, alpha=220)
        pygame.draw.line(screen, (255, 100, 100), (x + 6, y + 6), (x + config.CELL_SIZE - 6, y + config.CELL_SIZE - 6),
                         5)
        pygame.draw.line(screen, (255, 100, 100), (x + config.CELL_SIZE - 6, y + 6), (x + 6, y + config.CELL_SIZE - 6),
                         5)

    # Grid-Linien (Subtle)
    grid_color = theme.color_grid_player if not is_enemy else theme.color_grid_enemy
    pygame.draw.rect(screen, grid_color, cell_rect, 1)


def draw_title_art(screen):
    """Zeichnet ein Artwork für das Titelmenü passend zum Theme."""
    center_x = config.WINDOW_WIDTH // 2
    theme = theme_manager.current

    if theme.name == "MODERN":
        # Glowing wireframe ship
        points = [
            (center_x - 250, 360 + 150),  # Back bottom
            (center_x + 150, 360 + 150),  # Front bottom
            (center_x + 250, 290 + 150),  # Bow tip
            (center_x + 80, 290 + 150),  # Front deck
            (center_x + 30, 230 + 150),  # Bridge top right
            (center_x - 70, 230 + 150),  # Bridge top left
            (center_x - 120, 290 + 150),  # Back deck
            (center_x - 250, 290 + 150),  # Back top
        ]
        pygame.draw.polygon(screen, (10, 25, 45), points)
        pygame.draw.polygon(screen, (50, 150, 255), points, 3)
        pygame.draw.circle(screen, (255, 50, 50), (int(center_x - 20), 220 + 150), 8)  # Radar glowing
        pygame.draw.line(screen, (100, 200, 255), (center_x + 80, 275 + 150), (center_x + 180, 260 + 150),
                         4)  # Cannon 1
        pygame.draw.line(screen, (100, 200, 255), (center_x - 120, 275 + 150), (center_x - 220, 275 + 150),
                         4)  # Cannon 2

    elif theme.name == "PIRATE":
        # Wooden Pirate Galleon
        hull = [
            (center_x - 200, 350),  # Back bottom
            (center_x + 150, 350),  # Front bottom
            (center_x + 250, 260),  # Bow tip
            (center_x - 220, 260),  # Back top
        ]
        pygame.draw.polygon(screen, (139, 69, 19), hull)  # SaddleBrown
        pygame.draw.polygon(screen, (101, 67, 33), hull, 4)  # Dark Brown outline

        # Masts
        pygame.draw.line(screen, (101, 67, 33), (center_x - 100, 260), (center_x - 100, 100), 8)
        pygame.draw.line(screen, (101, 67, 33), (center_x + 50, 260), (center_x + 50, 120), 8)
        pygame.draw.line(screen, (101, 67, 33), (center_x + 250, 260), (center_x + 320, 190), 6)  # Bowsprit

        # Sails
        sail1 = [(center_x - 100, 120), (center_x - 180, 240), (center_x - 20, 240)]
        sail2 = [(center_x + 50, 140), (center_x - 30, 250), (center_x + 130, 250)]
        pygame.draw.polygon(screen, (240, 230, 200), sail1)
        pygame.draw.polygon(screen, (240, 230, 200), sail2)
        pygame.draw.polygon(screen, (200, 190, 160), sail1, 2)
        pygame.draw.polygon(screen, (200, 190, 160), sail2, 2)

        # Cannons out the side
        for cx in [center_x - 150, center_x - 50, center_x + 50]:
            pygame.draw.circle(screen, (30, 30, 30), (cx, 300), 12)  # Port hole
            pygame.draw.circle(screen, (10, 10, 10), (cx, 300), 8)  # Inner

    # Water reflection
    for i in range(4):
        w = 500 - i * 120
        y = 390 + 150 + i * 15
        alpha = max(50, 200 - i * 50)
        surf = pygame.Surface((w, 4), pygame.SRCALPHA)
        # Use theme water color for reflection
        r, g, b = theme.color_water

        # Make reflection slightly brighter
        r = min(255, r + 50)
        g = min(255, g + 50)
        b = min(255, b + 50)

        surf.fill((r, g, b, alpha))
        screen.blit(surf, (center_x - w // 2, y))


def draw_text(surface, text, x, y, font_size, color, center=False):
    """Zeichnet Text auf eine Surface mit reinen Pygame-Funktionen."""
    font = pygame.font.Font(None, font_size)
    text_surf = font.render(text, True, color)
    if center:
        text_rect = text_surf.get_rect(center=(x, y))
    else:
        text_rect = text_surf.get_rect(topleft=(x, y))
    surface.blit(text_surf, text_rect)


# Create reusable procedural graphics

def draw_gradient_background(screen_surface, time_value=0.0):
    """Draws a vertical gradient background with procedural water caustics."""
    height = config.WINDOW_HEIGHT
    width = config.WINDOW_WIDTH
    theme = theme_manager.current
    color_top = theme.color_bg_top
    color_bottom = theme.color_bg_bottom

    # Introduce a slight color shift based on time for an "underwater" or "rippling" feel
    shift_r = int(math.sin(time_value * 2.0) * 10)
    shift_g = int(math.cos(time_value * 1.5) * 10)
    shift_b = int(math.sin(time_value * 1.0) * 15)

    r_top = max(0, min(255, color_top[0] + shift_r))
    g_top = max(0, min(255, color_top[1] + shift_g))
    b_top = max(0, min(255, color_top[2] + shift_b))

    r_bot = max(0, min(255, color_bottom[0] - shift_r))
    g_bot = max(0, min(255, color_bottom[1] - shift_g))
    b_bot = max(0, min(255, color_bottom[2] - shift_b))

    # Fast gradient rendering using a 1xHEIGHT subsurface scaled up
    gradient_surface = pygame.Surface((1, height))
    for y in range(height):
        progress = y / height
        r = int(r_top + (r_bot - r_top) * progress)
        g = int(g_top + (g_bot - g_top) * progress)
        b = int(b_top + (b_bot - b_top) * progress)
        gradient_surface.set_at((0, y), (r, g, b))

    gradient_surface = pygame.transform.scale(gradient_surface, (width, height))
    screen_surface.blit(gradient_surface, (0, 0))

    # Draw soft light reflections (Caustics simulation)
    # Using larger lines that move vertically
    if time_value > 0:
        caustic_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        for i in range(4):
            # Calculate position moving from top to bottom
            y_base = (time_value * 40 + i * (height / 4)) % height
            # Oscillate alpha
            alpha = int((math.sin(time_value * 2 + i) * 0.5 + 0.5) * 15)
            # Draw semi transparent thick horizontal band
            pygame.draw.rect(caustic_surface, (150, 200, 255, alpha), (0, y_base - 20, width, 40))

        screen_surface.blit(caustic_surface, (0, 0))


def draw_rounded_rect(surface, color, rect, radius=10, width=0, alpha=255):
    """Draws a rounded rect with optional alpha transparency."""
    if alpha < 255:
        shape_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shape_surf, (*color, alpha), shape_surf.get_rect(), border_radius=radius, width=width)
        surface.blit(shape_surf, rect.topleft)
    else:
        pygame.draw.rect(surface, color, rect, border_radius=radius, width=width)


class GlowButton(BaseButton):
    def __init__(self, x, y, width, height, text, action):
        super().__init__(x, y, width, height, text, action)
        self.hover_progress = 0.0  # Für weiche Übergänge

    def update(self, dt, mouse_x, mouse_y):
        super().update(dt, mouse_x, mouse_y)
        if self.hovered:
            self.hover_progress = min(1.0, self.hover_progress + dt * 6.0)
        else:
            self.hover_progress = max(0.0, self.hover_progress - dt * 6.0)

    def draw(self, screen_surface, default_color=(40, 80, 150), hover_color=(70, 130, 220)):
        # Calculate current color based on hover progress
        r = int(default_color[0] + (hover_color[0] - default_color[0]) * self.hover_progress)
        g = int(default_color[1] + (hover_color[1] - default_color[1]) * self.hover_progress)
        b = int(default_color[2] + (hover_color[2] - default_color[2]) * self.hover_progress)

        current_color = (r, g, b)

        # Draw shadow
        shadow_rect = self.rect.copy()
        shadow_rect.y += 4
        draw_rounded_rect(screen_surface, (0, 0, 0), shadow_rect, radius=12, alpha=100)

        # Draw button
        draw_rounded_rect(screen_surface, current_color, self.rect, radius=12)

        # Draw border
        draw_rounded_rect(screen_surface, (100, 180, 255), self.rect, radius=12, width=2,
                          alpha=int(100 + 155 * self.hover_progress))

        # Draw Text
        font = pygame.font.Font(None, 36)
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)

        # Text shadow
        text_shadow = font.render(self.text, True, (0, 0, 0))
        text_shadow_rect = text_shadow.get_rect(center=(self.rect.centerx + 1, self.rect.centery + 1))

        screen_surface.blit(text_shadow, text_shadow_rect)
        screen_surface.blit(text_surf, text_rect)


class Particle:
    def __init__(self, x, y, color, velocity, life, size):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.life = life
        self.max_life = life
        self.size = size

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surface):
        if self.life > 0:
            alpha = int((self.life / self.max_life) * 255)
            # Create a small surface per particle for alpha (might be slow for many, but fine for few)
            surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha), (self.size, self.size), self.size)
            surface.blit(surf, (int(self.x - self.size), int(self.y - self.size)))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def add_explosion(self, x, y, count=30, color=(255, 100, 50)):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 200)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.uniform(0.3, 0.8)
            size = random.uniform(2, 6)

            # Mix some yellow into the explosion
            p_color = (255, random.randint(100, 255), 0) if random.random() > 0.5 else color
            self.particles.append(Particle(x, y, p_color, (vx, vy), life, size))

    def add_splash(self, x, y, count=20):
        for _ in range(count):
            angle = random.uniform(math.pi * 1.0, math.pi * 2.0)  # Move upwards mostly
            speed = random.uniform(40, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed + 50  # Add some gravity effect
            life = random.uniform(0.3, 0.6)
            size = random.uniform(2, 5)

            color = (200, 220, 255) if random.random() > 0.5 else (100, 150, 255)
            self.particles.append(Particle(x, y, color, (vx, vy), life, size))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)