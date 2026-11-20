"""One drawing boundary from 1920x1080 layout to native 16:9 pixels.

Neither helper owns gameplay state. Layout, hit testing and the following camera
remain in design coordinates; only final rasterization passes through these.
"""
import pygame


class NativeDraw:
    def __init__(self, size=(1920, 1080)):
        self.scale = size[0] / 1920

    def point(self, point):
        return tuple(round(value * self.scale) for value in point)

    def length(self, value):
        return value * self.scale

    def bounds(self, rect):
        rect = pygame.Rect(rect)
        left, top = self.point(rect.topleft)
        right, bottom = self.point(rect.bottomright)
        return pygame.Rect(left, top, right-left, bottom-top)

    def stroke(self, width):
        return max(1, round(width*self.scale)) if width else 0

    def rect(self, surface, color, rect, width=0, border_radius=0):
        return pygame.draw.rect(surface, color, self.bounds(rect), self.stroke(width),
                                border_radius=round(border_radius*self.scale))

    def line(self, surface, color, start, end, width=1):
        return pygame.draw.line(surface, color, self.point(start), self.point(end), self.stroke(width))

    def lines(self, surface, color, closed, points, width=1):
        return pygame.draw.lines(surface, color, closed, [self.point(p) for p in points], self.stroke(width))

    def circle(self, surface, color, center, radius, width=0):
        return pygame.draw.circle(surface, color, self.point(center),
                                  max(0, round(self.length(radius))), self.stroke(width))

    def polygon(self, surface, color, points, width=0):
        return pygame.draw.polygon(surface, color, [self.point(p) for p in points], self.stroke(width))


class RenderCamera:
    """Compose output scale with a logical Camera without changing its state."""
    def __init__(self, camera, scale):
        self.camera, self.scale = camera, scale

    def world_to_screen(self, point):
        return tuple(value*self.scale for value in self.camera.world_to_screen(point))

    def screen_to_world(self, point):
        return self.camera.screen_to_world(tuple(value/self.scale for value in point))

    def scale_length(self, value):
        return self.camera.scale_length(value)*self.scale

    def is_visible(self, point, radius=0):
        return self.camera.is_visible(point, radius)
