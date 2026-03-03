import math
import os
import random
import pygame
import game.config as config
from game.ui.buttons import BaseButton
from game.theme import theme_manager


_SHIP_IMAGE_CACHE = {}
_SHIP_RENDER_CACHE = {}

_THEME_STATUS_ICON_MAP = {
    "MODERN": {
        "napalm": "napalm.png",
    },
    "PIRATE": {
        "napalm": "griechisches_feuer.png",
    },
}

_STATUS_ICON_CACHE = {}
_UI_SPRITE_CACHE = {}

_THEME_UI_SPRITE_MAP = {
    "MODERN": {
        "water": "ui_modern_water_cell.png",
        "ship_fallback": "ui_modern_ship_cell.png",
        "hit": "ui_generic_hit.png",
        "miss": "ui_generic_miss.png",
        "destroyed": "ui_generic_destroyed.png",
        "scan": "ui_generic_scan.png",
        "scan_found": "ui_generic_scan_found.png",
        "player_marker": "ui_generic_player_marker.png",
        "title_art": "ui_modern_title_art.png",
    },
    "PIRATE": {
        "water": "ui_pirate_water_cell.png",
        "ship_fallback": "ui_pirate_ship_cell.png",
        "hit": "ui_generic_hit.png",
        "miss": "ui_generic_miss.png",
        "destroyed": "ui_generic_destroyed.png",
        "scan": "ui_generic_scan.png",
        "scan_found": "ui_generic_scan_found.png",
        "player_marker": "ui_generic_player_marker.png",
        "title_art": "ui_pirate_title_art.png",
    },
}


def _get_ui_sprite(sprite_name):
    theme_name = theme_manager.current.name
    theme_filename = _THEME_UI_SPRITE_MAP.get(theme_name, {}).get(sprite_name)

    if not theme_filename:
        return None

    cache_key = ("ui", theme_filename)
    if cache_key not in _UI_SPRITE_CACHE:
        sprite_path = os.path.join("images", theme_filename)
        if not os.path.exists(sprite_path):
            return None
        try:
            _UI_SPRITE_CACHE[cache_key] = pygame.image.load(sprite_path).convert_alpha()
        except pygame.error:
            return None

    sprite_surface = _UI_SPRITE_CACHE.get(cache_key)
    if sprite_surface is not None:
        return sprite_surface

    return None


def scale_sprite_to_cell(sprite_surface, cell_size, fill_ratio=1.0):
    """Skaliert ein Sprite proportional auf die Zellgröße und erhält das Seitenverhältnis."""
    if sprite_surface is None:
        return None

    if fill_ratio <= 0:
        fill_ratio = 1.0

    target = max(1, int(round(cell_size * fill_ratio)))
    src_w, src_h = sprite_surface.get_size()
    if src_w <= 0 or src_h <= 0:
        return None

    scale_factor = min(target / src_w, target / src_h)
    scaled_w = max(1, int(round(src_w * scale_factor)))
    scaled_h = max(1, int(round(src_h * scale_factor)))
    return pygame.transform.smoothscale(sprite_surface, (scaled_w, scaled_h))

def _get_status_icon(icon_name):
    theme_name = theme_manager.current.name
    theme_filename = _THEME_STATUS_ICON_MAP.get(theme_name, {}).get(icon_name)
    generic_filename = f"ui_generic_{icon_name}.png"

    for filename in (theme_filename, generic_filename):
        if not filename:
            continue

        cache_key = ("status", filename)
        if cache_key not in _STATUS_ICON_CACHE:
            icon_path = os.path.join("images", filename)
            if not os.path.exists(icon_path):
                continue
            try:
                _STATUS_ICON_CACHE[cache_key] = pygame.image.load(icon_path).convert_alpha()
            except pygame.error:
                continue

        icon_surface = _STATUS_ICON_CACHE.get(cache_key)
        if icon_surface is not None:
            return icon_surface

    return None

_THEME_SHIP_IMAGE_MAP = {
    "MODERN": {
        "Schlachtschiff": "Schlachtschiff(5x1).png",
        "Kreuzer": "Kreuzer(4x1).png",
        "Zerstörer": "Zerstoerer(3x1).png",
        "U-Boot": "U-Boot(2x1).png",
        "Flugzeugträger": "Flugzeugträger(3x2).png",
    },
    "PIRATE": {
        "Schlachtschiff": "Flaggschiff(5x1).png",
        "Kreuzer": "Galeone(4x1).png",
        "Zerstörer": "Fregatte(3x1).png",
        "U-Boot": "Schaluppe(2x1).png",
        "Flugzeugträger": "Moerser_Brigg(3x2).png",
    },
}


def _normalize_ship_name(ship_name):
    base_name = ship_name.split(" #", 1)[0]
    return base_name.replace("ae", "ä").replace("oe", "ö").replace("ue", "ü")


def _get_ship_image(theme_name, ship_name):
    normalized_name = _normalize_ship_name(ship_name)
    file_name = _THEME_SHIP_IMAGE_MAP.get(theme_name, {}).get(normalized_name)
    if not file_name:
        return None

    cache_key = (theme_name, ship_name)
    if cache_key not in _SHIP_IMAGE_CACHE:
        image_path = os.path.join("images", file_name)
        if not os.path.exists(image_path):
            return None
        _SHIP_IMAGE_CACHE[cache_key] = pygame.image.load(image_path).convert_alpha()

    return _SHIP_IMAGE_CACHE[cache_key]


def _draw_ship_cell_image(screen, x, y, cell):
    if not cell.has_ship():
        return False

    ship = cell.ship
    coords = ship.get_coordinates()
    if not coords:
        return False

    min_row = min(r for r, _ in coords)
    min_col = min(c for _, c in coords)
    max_row = max(r for r, _ in coords)
    max_col = max(c for _, c in coords)

    grid_height = max_row - min_row + 1
    grid_width = max_col - min_col + 1

    local_row = cell.row - min_row
    local_col = cell.col - min_col
    if local_row < 0 or local_col < 0 or local_row >= grid_height or local_col >= grid_width:
        return False

    transformed = _get_transformed_ship_surface(
        ship,
        grid_width,
        grid_height,
        ship.orientation,
        ship_coords=coords,
    )
    if transformed is None:
        return False

    area = pygame.Rect(
        local_col * config.CELL_SIZE,
        local_row * config.CELL_SIZE,
        config.CELL_SIZE,
        config.CELL_SIZE,
    )
    screen.blit(transformed, (x, y), area=area)
    return True


def _get_transformed_ship_surface(ship, grid_width, grid_height, orientation, ship_coords=None):
    source_image = _get_ship_image(theme_manager.current.name, ship.name)
    if source_image is None:
        return None

    orientation_steps = orientation % config.ORIENTATION_COUNT
    render_key = (
        theme_manager.current.name,
        ship.name,
        orientation_steps,
        grid_width,
        grid_height,
        config.CELL_SIZE,
    )
    transformed = _SHIP_RENDER_CACHE.get(render_key)
    if transformed is not None:
        return transformed

    rotated = pygame.transform.rotate(source_image, -90 * orientation_steps)

    content_rect = rotated.get_bounding_rect(min_alpha=1)
    if content_rect.width > 0 and content_rect.height > 0:
        rotated = rotated.subsurface(content_rect).copy()
        target_width = grid_width * config.CELL_SIZE
        target_height = grid_height * config.CELL_SIZE
        source_width, source_height = rotated.get_size()

        min_breadth = max(1, config.CELL_SIZE // 2)
        if target_width >= target_height:
            scaled_width = target_width
            scaled_height = int(source_height * (scaled_width / max(1, source_width)))
            scaled_height = max(min_breadth, min(target_height, scaled_height))
        else:
            scaled_height = target_height
            scaled_width = int(source_width * (scaled_height / max(1, source_height)))
            scaled_width = max(min_breadth, min(target_width, scaled_width))

        scaled_ship = pygame.transform.smoothscale(rotated, (scaled_width, scaled_height))
        transformed = pygame.Surface((target_width, target_height), pygame.SRCALPHA)
        offset_x = (target_width - scaled_width) // 2
        offset_y = (target_height - scaled_height) // 2
        if ship.shape == "carrier_l":
            coords = ship_coords if ship_coords else ship.get_coordinates_at(0, 0, orientation)
            min_row = min(r for r, _ in coords)
            min_col = min(c for _, c in coords)
            local_rows = [r - min_row for r, _ in coords]
            local_cols = [c - min_col for _, c in coords]
            avg_row = sum(local_rows) / len(local_rows)
            avg_col = sum(local_cols) / len(local_cols)

            row_bias_px = int(round(((avg_row + 0.5) - (grid_height / 2)) * config.CELL_SIZE))
            col_bias_px = int(round(((avg_col + 0.5) - (grid_width / 2)) * config.CELL_SIZE))

            offset_x += col_bias_px
            offset_y += row_bias_px


        offset_x = max(0, min(offset_x, target_width - scaled_width))
        offset_y = max(0, min(offset_y, target_height - scaled_height))

        transformed.blit(scaled_ship, (offset_x, offset_y))
        _SHIP_RENDER_CACHE[render_key] = transformed
        return transformed


def draw_grid_cell(screen, x, y, cell, is_enemy=False, show_ships=True, ws_connected: bool = False):
    """Zeichnet eine Zelle als sprite"""
    theme = theme_manager.current
    cell_rect = pygame.Rect(x, y, config.CELL_SIZE, config.CELL_SIZE)

    water_sprite = _get_ui_sprite("water")
    if water_sprite:
        water_scaled = pygame.transform.smoothscale(water_sprite, (config.CELL_SIZE, config.CELL_SIZE))
        screen.blit(water_scaled, cell_rect)

    # Zeige enemy ship png nur bei schon zerstörten Schiffen
    should_show_ship = (
        cell.has_ship()
        and ((show_ships and not is_enemy) or (is_enemy and (show_ships or cell.status == config.CELL_DESTROYED)))
    )

    # Grid-Linien
    grid_color = theme.color_grid_player if not is_enemy else theme.color_grid_enemy
    pygame.draw.rect(screen, grid_color, cell_rect, 1)

    # Schiff
    if should_show_ship:
        ship_image_drawn = _draw_ship_cell_image(screen, x, y, cell)
        if not ship_image_drawn:
            ship_fallback = _get_ui_sprite("ship_fallback")
            if ship_fallback:
                ship_scaled = pygame.transform.smoothscale(ship_fallback, (config.CELL_SIZE, config.CELL_SIZE))
                screen.blit(ship_scaled, cell_rect)

    if cell.scan_marked and not cell.is_shot():
        scan_name = "scan_found" if cell.scan_found_ship else "scan"
        scan_sprite = _get_ui_sprite(scan_name)
        if scan_sprite:
            scan_scaled = scale_sprite_to_cell(scan_sprite, config.CELL_SIZE, fill_ratio=0.65)
            screen.blit(scan_scaled, scan_scaled.get_rect(center=cell_rect.center))

    if cell.napalm_marked and not cell.is_shot():
        icon = _get_status_icon("napalm")
        if icon:
            icon_surf = scale_sprite_to_cell(icon, config.CELL_SIZE, fill_ratio=0.78)
            screen.blit(icon_surf, icon_surf.get_rect(center=cell_rect.center))

    if cell.player_marker and not cell.is_shot() and not cell.scan_marked and not cell.napalm_marked:
        marker_sprite = _get_ui_sprite("player_marker")
        if marker_sprite:
            marker_scaled = scale_sprite_to_cell(marker_sprite, config.CELL_SIZE, fill_ratio=0.62)
            screen.blit(marker_scaled, marker_scaled.get_rect(center=cell_rect.center))

        # Hit/Miss
    if cell.status == config.CELL_HIT:
        hit_sprite = _get_ui_sprite("hit")
        if hit_sprite:
            hit_scaled = scale_sprite_to_cell(hit_sprite, config.CELL_SIZE, fill_ratio=0.9)
            screen.blit(hit_scaled, hit_scaled.get_rect(center=cell_rect.center))
    elif cell.status == config.CELL_MISS:
        miss_sprite = _get_ui_sprite("miss")
        if miss_sprite:
            miss_scaled = scale_sprite_to_cell(miss_sprite, config.CELL_SIZE, fill_ratio=0.55)
            screen.blit(miss_scaled, miss_scaled.get_rect(center=cell_rect.center))
    elif cell.status == config.CELL_DESTROYED:
        destroyed_sprite = _get_ui_sprite("destroyed")
        if destroyed_sprite:
            destroyed_scaled = scale_sprite_to_cell(destroyed_sprite, config.CELL_SIZE, fill_ratio=0.95)
            screen.blit(destroyed_scaled, destroyed_scaled.get_rect(center=cell_rect.center))


def draw_title_art(screen):
    """Zeichnet Artwork Sprite für menü"""
    center_x = config.WINDOW_WIDTH // 2
    title_sprite = _get_ui_sprite("title_art")
    if not title_sprite:
        return

    target_w = min(700, int(config.WINDOW_WIDTH * 0.45))
    scale_factor = target_w / max(1, title_sprite.get_width())
    target_h = max(1, int(title_sprite.get_height() * scale_factor))
    scaled = pygame.transform.smoothscale(title_sprite, (target_w, target_h))
    # Positioning zwischen Titel und Button-Zeile.
    max_bottom = config.MENU_BUTTON_Y - 35
    target_center_y = (config.MENU_SUBTITLE_Y + max_bottom) // 2
    rect = scaled.get_rect(center=(center_x, target_center_y))
    if rect.bottom > max_bottom:
        rect.bottom = max_bottom
    screen.blit(scaled, rect)


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