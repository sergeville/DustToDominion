"""The playable campaign surface: station, expedition and exclusive overlays.

All drawing uses the established 1920x1080 design space. The simulation and
persistence stay outside the screen; widgets only issue model commands.
"""
from __future__ import annotations

import math
import copy
import random

import pygame

from dtd.campaign import (Campaign, InputState, STATION_X, STATION_Y,
                          DOCK_RADIUS, SAFE_RADIUS, MINE_RANGE)
from dtd.campaign_store import SaveError
from dtd.language import get_language_manager
from dtd.screens.base import Screen, ScreenAction
from dtd.ui import UIManager, current_scale
from dtd.widgets.button import Button

_BG = (7, 13, 25)
_PANEL = (13, 26, 43)
_LINE = (38, 68, 87)
_WHITE = (225, 238, 242)
_MUTED = (139, 165, 182)
_CYAN = (85, 220, 220)
_GOLD = (246, 195, 100)
_RED = (246, 106, 110)
_ORE = ((111, 185, 207), (241, 182, 88), (182, 131, 246))
_STEP = 1 / 60


class CampaignScreen(Screen):
    """A session-owned Campaign rendered through a transient Screen."""

    def __init__(self, theme, loader, campaign: Campaign, store) -> None:
        self._theme, self._loader = theme, loader
        self.campaign, self.store = campaign, store
        self.expedition = None
        self.mode = "station"
        self.message = ""
        self.error = ""
        self._keys: set[int] = set()
        self._firing = False
        self._aim = (960.0, 350.0)
        self._accumulator = 0.0
        self._pending_action = None
        self._button_theme = copy.copy(theme)
        # Preserve the selected font/theme when customized; the stock bright-blue
        # widget background gets a subdued cockpit variant for this surface.
        if theme.get_theme_resource_id() == "default":
            for key, color in {"foregroundNormal": _CYAN, "backgroundNormal": (19, 48, 61),
                               "foregroundHover": _WHITE, "backgroundHover": (29, 76, 91),
                               "foregroundDisabled": (110, 133, 150), "backgroundDisabled": (17, 29, 43)}.items():
                setattr(self._button_theme, key, pygame.Color(color))
            self._button_theme.cornerRadius = 7
        self._ui = UIManager(theme)
        self._canvas = pygame.Surface((1920, 1080))
        self._fonts = {}
        rng = random.Random(47)
        self._stars = [(rng.randrange(1920), rng.randrange(1080), rng.randrange(35, 90))
                       for _ in range(180)]
        self._victory_shown = campaign.won
        self._rebuild()

    def _t(self, key: str, **values) -> str:
        return get_language_manager().get_string("campaign." + key).format(**values)

    def _clear_input(self) -> None:
        self._keys.clear()
        self._firing = False
        self._accumulator = 0.0

    def _button(self, rect, text, callback, enabled=True) -> None:
        button = Button(pygame.Rect(rect), text=text, border_width=1, on_click=callback)
        size = 26
        while size > 16 and self._theme.get_font(size).size(text)[0] > rect[2] - 24:
            size -= 1
        button.set_font_point_size(size)
        button.set_theme_override(self._button_theme)
        button.enabled = enabled
        self._ui.widgets.append(button)

    def _rebuild(self) -> None:
        # Replace the whole manager: overlays never share an input layer.
        self._ui = UIManager(self._theme)
        if self.mode == "station":
            for sector in range(1, 4):
                self._button((80, 410 + (sector - 1) * 132, 510, 58),
                             self._t("launch", sector=sector),
                             lambda s=sector: self._launch(s),
                             sector <= self.campaign.unlocked_sector)
            self._button((700, 394, 510, 58), self._t("sell", value=self.campaign.cargo_value()),
                         lambda: self._station_action("sell"), bool(self.campaign.cargo))
            self._button((700, 470, 510, 58), self._t("repair"),
                         lambda: self._station_action("repair"),
                         self.campaign.hull < self.campaign.max_hull and self.campaign.credits > 0)
            for i, item in enumerate(("cargo", "laser", "hull")):
                self._purchase_button(item, (700, 570 + i * 84, 510, 58))
            for i, item in enumerate(("ship", "miner", "engineer")):
                self._purchase_button(item, (1320, 410 + i * 132, 510, 58))
            self._button((80, 974, 300, 58), self._t("save"), self._save)
            self._button((1540, 974, 300, 58), self._t("title"), self._title)
        elif self.mode == "paused":
            self._button((660, 600, 600, 66), self._t("resume"), self._resume)
            self._button((660, 688, 600, 66), self._t("abandon"), self._confirm_abandon)
        elif self.mode == "abandon":
            self._button((660, 600, 600, 66), self._t("cancel"), self._pause)
            self._button((660, 688, 600, 66), self._t("confirm_abandon"), self._abandon)
        elif self.mode in ("result", "victory"):
            self._button((660, 600, 600, 66), self._t("continue"), self._station)
            self._button((660, 688, 600, 66), self._t("title"), self._title)

    def _purchase_button(self, item, rect) -> None:
        price = self.campaign.price(item)
        label = self._t(item)
        text = self._t("purchase", item=label, price=price) if price is not None else self._t("owned", item=label)
        self._button(rect, text, lambda: self._station_action(item),
                     price is not None and self.campaign.credits >= price)

    def _save(self) -> bool:
        try:
            self.store.save(self.campaign)
        except SaveError:
            # Keep the live campaign and last checkpoint. Technical details belong
            # in the store log; the player receives an actionable localized error.
            self.error = self._t("save_failed")
            return False
        self.error = ""
        self.message = self._t("saved")
        return True

    def _station_action(self, action: str) -> None:
        if self.mode != "station":
            return
        if action == "sell":
            amount = self.campaign.sell()
            self.message = self._t("sold", value=amount)
        elif action == "repair":
            self.campaign.repair()
        else:
            if not self.campaign.buy(action):
                return
        notice = self.message
        self._save()
        self.message = notice
        if self.campaign.victory and not self._victory_shown:
            self._victory_shown = True
            self.campaign.won = True
            self.mode = "victory"
            self._save()
        self._rebuild()

    def _launch(self, sector: int) -> None:
        self.expedition = self.campaign.launch(sector)
        self.mode = "flight"
        self.message = ""
        self._clear_input()
        self._rebuild()

    def _pause(self) -> None:
        self.mode = "paused"
        self._clear_input()
        self._rebuild()

    def _resume(self) -> None:
        self.mode = "flight"
        self._clear_input()
        self._rebuild()

    def _confirm_abandon(self) -> None:
        self.mode = "abandon"
        self._clear_input()
        self._rebuild()

    def _abandon(self) -> None:
        self._finish(True)

    def _finish(self, defeated=False) -> None:
        run = self.expedition
        if run is None:
            return
        self.campaign.finish_run(run, defeated=defeated)
        self.message = self._t("defeat_body" if defeated or run.defeated else "docked_body")
        self.mode = "result"
        if self.campaign.victory and not self._victory_shown:
            self._victory_shown = True
            self.campaign.won = True
            self.mode = "victory"
        self._clear_input()
        notice = self.message
        self._save()
        self.message = notice
        self.expedition = None
        self._rebuild()

    def _station(self) -> None:
        self.mode = "station"
        self._clear_input()
        self._rebuild()

    def _title(self) -> None:
        if self._save():
            self._pending_action = ScreenAction.SHOW_TITLE_SCREEN

    def update(self, events) -> None:
        # Process each event once. A transition discards the rest of its batch;
        # a launch/resume click cannot also fire a weapon or trigger another UI.
        # Focus loss is a lifecycle event, even when it trails a click that
        # changes modes. Never let event-batch suppression discard that pause.
        if any(event.type == pygame.WINDOWFOCUSLOST for event in events):
            self._clear_input()
            if self.expedition is not None:
                self._pause()
            return
        for event in events:
            before = self.mode
            if event.type == pygame.WINDOWFOCUSLOST and self.mode == "flight":
                self._pause()
                break
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.mode == "flight":
                    self._pause()
                elif self.mode == "paused":
                    self._resume()
                elif self.mode == "abandon":
                    self._pause()
                break
            if self.mode == "flight":
                if event.type == pygame.KEYDOWN:
                    self._keys.add(event.key)
                    if event.key == pygame.K_e and self.expedition.request_dock():
                        self._finish()
                elif event.type == pygame.KEYUP:
                    self._keys.discard(event.key)
                elif event.type == pygame.MOUSEMOTION:
                    self._aim = current_scale().mouse(event.pos)
                elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and event.button == 1:
                    self._aim = current_scale().mouse(event.pos)
                    self._firing = event.type == pygame.MOUSEBUTTONDOWN
            else:
                self._ui.update([event])
            if self.mode != before:
                break

    def advance(self, dt: float) -> None:
        if self.mode != "flight" or self.expedition is None:
            return
        if not math.isfinite(dt) or dt <= 0:
            return
        keys = self._keys
        controls = InputState(
            move_x=int(bool(keys & {pygame.K_d, pygame.K_RIGHT})) - int(bool(keys & {pygame.K_a, pygame.K_LEFT})),
            move_y=int(bool(keys & {pygame.K_s, pygame.K_DOWN})) - int(bool(keys & {pygame.K_w, pygame.K_UP})),
            mining=pygame.K_SPACE in keys, firing=self._firing,
            aim_x=self._aim[0], aim_y=self._aim[1])
        self._accumulator += min(dt, 0.25)
        while self._accumulator + 1e-10 >= _STEP:
            self._accumulator -= _STEP
            self.expedition.step(_STEP, controls)
            if self.expedition.finished:
                self._finish(self.expedition.defeated)
                break

    def _text(self, text, x, y, size=28, color=_WHITE, width=None) -> None:
        if size not in self._fonts:
            self._fonts[size] = self._theme.get_font(size)
        font = self._fonts[size]
        if width:
            words, lines, line = text.split(), [], ""
            for word in words:
                proposed = (line + " " + word).strip()
                if line and font.size(proposed)[0] > width:
                    lines.append(line)
                    line = word
                else:
                    line = proposed
            lines.append(line)
        else:
            lines = [text]
        for line in lines:
            self._canvas.blit(font.render(line, True, color), (x, y))
            y += size + 9

    def _panel(self, rect) -> None:
        pygame.draw.rect(self._canvas, _PANEL, rect, border_radius=12)
        pygame.draw.rect(self._canvas, _LINE, rect, 1, border_radius=12)

    def _bar(self, x, y, width, fraction, color) -> None:
        pygame.draw.rect(self._canvas, _LINE, (x, y, width, 10), border_radius=5)
        pygame.draw.rect(self._canvas, color, (x, y, max(0, int(width * min(1, fraction))), 10), border_radius=5)

    def draw(self, surface) -> None:
        self._canvas.fill(_BG)
        for x, y, light in self._stars:
            self._canvas.set_at((x, y), (light, light, light + 15))
        if self.expedition is not None:
            self._draw_flight()
        else:
            self._draw_station()
        if self.mode in ("paused", "abandon", "result", "victory"):
            shade = pygame.Surface((1920, 1080), pygame.SRCALPHA)
            shade.fill((0, 6, 16, 200))
            self._canvas.blit(shade, (0, 0))
            self._panel((530, 260, 860, 570))
            heading = {"paused": "paused", "abandon": "abandon", "result": "result", "victory": "victory"}[self.mode]
            self._text(self._t(heading), 600, 310, 42, _GOLD if self.mode == "victory" else _CYAN, 730)
            body = self.message if self.mode == "result" else self._t(self.mode + "_body")
            self._text(body, 600, 395, 27, _WHITE, 720)
        if self.error:
            self._panel((60, 850, 1800, 108))
            self._text(self.error, 90, 868, 27, _RED, 1740)
        elif self.message and self.mode == "station":
            self._text(self.message, 420, 994, 25, _CYAN, 1000)
        if surface.get_size() == self._canvas.get_size():
            surface.blit(self._canvas, (0, 0))
        else:
            pygame.transform.smoothscale(self._canvas, surface.get_size(), surface)
        self._ui.draw(surface)

    def _draw_station(self) -> None:
        c = self.campaign
        self._text(self._t("station"), 70, 48, 48, _CYAN)
        self._text(self._t("station_subtitle"), 72, 112, 25, _MUTED)
        self._text(self._t("credits", value=c.credits), 1340, 58, 38, _GOLD)
        self._panel((60, 180, 1800, 108))
        stats = (("hull_stat", f"{int(c.hull)}/{c.max_hull}"),
                 ("cargo_stat", f"{len(c.cargo)}/{c.capacity}"),
                 ("fleet_stat", f"{c.ship_count}/3"),
                 ("crew_stat", f"{int(c.miner) + int(c.engineer)}/2"))
        for i, (key, value) in enumerate(stats):
            self._text(self._t(key), 90 + i * 450, 198, 23, _MUTED)
            self._text(value, 90 + i * 450, 231, 33)
        for x in (60, 680, 1300):
            self._panel((x, 315, 560, 510))
        self._text(self._t("sectors"), 80, 335, 32, _CYAN)
        self._text(self._t("workshop"), 700, 335, 32, _CYAN)
        self._text(self._t("operation"), 1320, 335, 32, _CYAN)
        for i in range(3):
            self._text(self._t("sector_" + str(i + 1)), 82, 480 + i * 132, 21,
                       _MUTED if i == 0 else _GOLD, 510)
        self._text(self._t("ship_note"), 1320, 480, 21, _MUTED, 500)
        self._text(self._t("miner_note"), 1320, 612, 21, _MUTED, 500)
        self._text(self._t("engineer_note"), 1320, 744, 21, _MUTED, 500)
        self._panel((60, 850, 1800, 100))
        self._text(self._t("objective"), 80, 866, 26, _GOLD, 1750)
        progress = (min(c.ship_count / 3, 1) + (int(c.miner) + int(c.engineer)) / 2 + min(c.credits / 1200, 1)) / 3
        self._bar(80, 924, 1750, progress, _GOLD)

    def _ship(self, x, y, heading, color, size=26) -> None:
        points = []
        for angle, length in ((0, size * 1.4), (2.45, size), (math.pi, size * .45), (-2.45, size)):
            points.append((x + math.cos(heading + angle) * length, y + math.sin(heading + angle) * length))
        pygame.draw.polygon(self._canvas, _PANEL, points)
        pygame.draw.polygon(self._canvas, color, points, 3)
        pygame.draw.circle(self._canvas, color, (int(x), int(y)), 5)

    def _draw_flight(self) -> None:
        run, c = self.expedition, self.campaign
        # Station safe region is visible, with a nested docking beacon.
        pygame.draw.circle(self._canvas, (14, 36, 43), (STATION_X, STATION_Y), SAFE_RADIUS)
        pygame.draw.circle(self._canvas, _LINE, (STATION_X, STATION_Y), SAFE_RADIUS, 1)
        pygame.draw.circle(self._canvas, _CYAN, (STATION_X, STATION_Y), DOCK_RADIUS, 2)
        pygame.draw.rect(self._canvas, _LINE, (STATION_X - 48, STATION_Y - 22, 96, 44), 3)
        pygame.draw.rect(self._canvas, _CYAN, (STATION_X - 22, STATION_Y - 48, 44, 96), 3)
        for rock in run.asteroids:
            points = [(rock.x + math.cos(i * math.tau / 9) * rock.radius * (0.85 + (i % 3) * .08),
                       rock.y + math.sin(i * math.tau / 9) * rock.radius * (0.85 + (i % 3) * .08)) for i in range(9)]
            pygame.draw.polygon(self._canvas, (28, 40, 54), points)
            pygame.draw.polygon(self._canvas, _ORE[rock.ore], points, 3)
            self._bar(rock.x - 28, rock.y + rock.radius + 10, 56, rock.health / rock.max_health, _ORE[rock.ore])
        for pickup in run.pickups:
            x, y = pickup.x, pickup.y
            pygame.draw.polygon(self._canvas, _ORE[pickup.ore], [(x, y-10), (x+8, y), (x, y+10), (x-8, y)])
        if pygame.K_SPACE in self._keys and self.mode == "flight" and len(run.cargo) < c.capacity:
            candidates = [a for a in run.asteroids if math.hypot(a.x-run.x, a.y-run.y) <= MINE_RANGE]
            if candidates:
                target = min(candidates, key=lambda a: math.hypot(a.x-run.x, a.y-run.y))
                pygame.draw.line(self._canvas, _CYAN, (run.x, run.y), (target.x, target.y), 3)
        for enemy in run.enemies:
            self._ship(enemy.x, enemy.y, enemy.heading, _RED, 24)
            self._bar(enemy.x-25, enemy.y+34, 50, enemy.hull/75, _RED)
        for shot in run.projectiles:
            pygame.draw.circle(self._canvas, _GOLD if shot.friendly else _RED, (int(shot.x), int(shot.y)), 5)
        self._ship(run.x, run.y, run.heading, _WHITE)
        if self.mode == "flight":
            ax, ay = map(int, self._aim)
            pygame.draw.circle(self._canvas, _MUTED, (ax, ay), 13, 1)
            pygame.draw.line(self._canvas, _MUTED, (ax-18, ay), (ax+18, ay), 1)
            pygame.draw.line(self._canvas, _MUTED, (ax, ay-18), (ax, ay+18), 1)
        self._panel((30, 24, 1860, 135))
        self._text(self._t("sector_title", sector=run.sector), 60, 45, 32, _CYAN)
        self._text(self._t("danger" if run.sector > 1 else "safe"), 60, 96, 24, _RED if run.sector > 1 else _MUTED)
        self._text(self._t("hull_value", value=int(run.hull), maximum=c.max_hull), 640, 45, 28)
        self._bar(640, 113, 400, run.hull/c.max_hull, _RED if run.hull < 30 else _CYAN)
        self._text(self._t("cargo_value", count=len(run.cargo), capacity=c.capacity), 1130, 45, 28, _GOLD)
        self._bar(1130, 113, 400, len(run.cargo)/c.capacity, _GOLD)
        self._text(self._t("credits", value=c.credits), 1590, 65, 27, _GOLD)
        self._panel((30, 982, 1860, 78))
        self._text(self._t("controls"), 60, 1008, 24, _WHITE)
        hint = "dock_hint" if run.dock_ready else "return_hint" if len(run.cargo) >= c.capacity else "mine_hint"
        self._text(self._t(hint), 550, 932, 25, _CYAN, 1200)
