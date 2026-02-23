import pygame
import random
import math
from game.config import WINDOW_WIDTH, WINDOW_HEIGHT

# Create reusable procedural graphics

def draw_gradient_background(screen_surface, color_top, color_bottom):
    """Draws a vertical gradient background."""
    height = WINDOW_HEIGHT
    width = WINDOW_WIDTH
    for y in range(height):
        # Interpolate color
        progress = y / height
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * progress)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * progress)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * progress)
        
        pygame.draw.line(screen_surface, (r, g, b), (0, y), (width, y))

def draw_rounded_rect(surface, color, rect, radius=10, width=0, alpha=255):
    """Draws a rounded rect with optional alpha transparency."""
    if alpha < 255:
        shape_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shape_surf, (*color, alpha), shape_surf.get_rect(), border_radius=radius, width=width)
        surface.blit(shape_surf, rect.topleft)
    else:
        pygame.draw.rect(surface, color, rect, border_radius=radius, width=width)

class GlowButton:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x - width//2, y - height//2, width, height)
        self.text = text
        self.action = action
        self.hovered = False
        self.hover_progress = 0.0 # Für weiche Übergänge
        
    def is_hovered(self, mouse_x, mouse_y):
        return self.rect.collidepoint(mouse_x, mouse_y)
        
    def update(self, dt, mouse_x, mouse_y):
        self.hovered = self.is_hovered(mouse_x, mouse_y)
        if self.hovered:
            self.hover_progress = min(1.0, self.hover_progress + dt * 6.0)
        else:
            self.hover_progress = max(0.0, self.hover_progress - dt * 6.0)
            
    def click(self):
        if self.action:
            self.action()
            
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
        draw_rounded_rect(screen_surface, (100, 180, 255), self.rect, radius=12, width=2, alpha=int(100 + 155*self.hover_progress))
        
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
            surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
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
            angle = random.uniform(math.pi * 1.0, math.pi * 2.0) # Move upwards mostly
            speed = random.uniform(40, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed + 50 # Add some gravity effect
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
