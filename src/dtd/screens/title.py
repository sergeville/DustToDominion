"""The Title Screen (spec 08: Title Screen).

Background handling (the shared ``Background`` helper: background image
if one resolves, random starfield otherwise), the title display, and
the menu column - New Game, Continue, Options and Exit Game. The
font/theme ChoiceLists that were temporarily hosted here for manual
testing have moved to the Options screen (spec 08, as amended by
spec 13): the Theme this screen receives is built by main from the
latest config before each screen is instantiated, and this screen uses
it as-is - it never rebuilds or persists one.

The title display is a ``Label`` widget (spec 08: Title, as amended by
spec 10): centered text, selected, fixed 80pt design-space, non-opaque,
no border. It is drawn as screen chrome between the background and the
menu widgets - the spec's paint order - rather than registered with the
UIManager, because a Label ignores the mouse entirely and the menu's
widget list stays exactly the menu.

All display text on this screen is resolved from language keys via the
LanguageManager at construction time (spec 16: Caller decides) - the
constants in game_constants carry the dotted keys, the Widgets receive
the resolved text, and a language changed on the Options screen lands
here on the next screen transition (main builds a brand-new screen).

Each screen starts its own music (spec 08: Title Screen audio, as
amended by spec 13): the first ``TITLE_SCREEN_MUSIC_IDS`` track that
resolves is requested in the constructor; the main loop stops it on any
transition. ESC and the button clicks ride the base-class plumbing
(spec 08: Code layout): ``_esc_action`` is QUIT, and the callbacks
record their intent in ``_pending_action``.
"""
from __future__ import annotations

import random

import pygame

from dtd import audio, game_constants
from dtd.campaign import Campaign
from dtd.campaign_store import CampaignStore, SaveError
from dtd.language import get_language_manager
from dtd.resource_loader import ResourceLoader
from dtd.screens.background import Background
from dtd.screens.base import Screen, ScreenAction
from dtd.ui import Theme, UIManager, Widget
from dtd.widgets.button import Button
from dtd.widgets.label import Label


class TitleScreen(Screen):
    """The screen shown after a successful startup (spec 08).

    The supplied ``Theme`` is built by main from the latest game config
    right before this screen is instantiated (spec 04, as amended by
    spec 13), so a fresh TitleScreen always reflects the latest
    persisted theme and font. This screen uses the Theme as-is.

    ``rng`` is injected by tests for deterministic starfield generation
    (spec 08: Testing); production code passes nothing.
    """

    #: ESC on the Title Screen is equivalent to clicking the Exit Game
    #: button (spec 08 stage 4).
    _esc_action = ScreenAction.QUIT

    def __init__(
        self,
        theme: Theme,
        resource_loader: ResourceLoader,
        rng: random.Random | None = None,
    ) -> None:
        self.store = CampaignStore()
        self.campaign = None
        self._confirming = False
        self._message = ""
        self._modal_ui = UIManager(theme)
        self._theme = theme
        self._resource_loader = resource_loader
        # Per-screen UIManager (spec 04, as amended by spec 08): the
        # widget list is screen-scoped state, so it is created here and
        # dies with this object.
        self._ui = UIManager(theme)
        # Exactly one background is active (spec 08: Background): the
        # first image resource that resolves, or a generated starfield.
        self._background = Background(
            resource_loader,
            game_constants.TITLE_SCREEN_BACKGROUND_IMAGE_IDS,
            rng if rng is not None else random.Random(),
        )
        # The title Label (spec 08: Title, as amended by spec 10).
        self._title = self._build_title()
        self._build_menu()
        self._build_modal()
        # Spec 08: Title Screen audio, as amended by spec 13: each screen
        # is responsible for starting its own music; the main loop stops
        # it on any transition. No candidate resolving is a silent no-op
        # (spec 05: play_music_first_match).
        audio.get_audio_manager().play_music_first_match(
            game_constants.TITLE_SCREEN_MUSIC_IDS
        )

    def update(self, events: list[pygame.event.Event]) -> None:
        # The starfield twinkle is the only per-frame state (spec 08:
        # Background), then the widget broadcast.
        self._background.advance()
        if self._confirming:
            if any(e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE for e in events):
                self._cancel_new()
            else:
                self._modal_ui.update(events)
        else:
            self._ui.update(events)

    def draw(self, surface: pygame.Surface) -> None:
        # Paint order per spec 08: Code layout - background, title, then
        # the menu widgets. The title Label receives this screen's
        # current Theme on every frame.
        self._background.draw(surface)
        self._title.draw(surface, self._theme)
        self._ui.draw(surface)
        if self._message:
            self._draw_message(surface, self._message, 560)
        if self._confirming:
            shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 225))
            surface.blit(shade, (0, 0))
            self._draw_message(surface, self._text("campaign.replace_confirm"), 400)
            self._modal_ui.draw(surface)

    # -- title (spec 08: Title, as amended by spec 10) ----------------------

    def _build_title(self) -> Label:
        """The title Label, configured per spec 08: Title.

        The five characteristics the spec names: centered text, selected
        (which is what puts the ``foregroundSelected`` theme color on
        the title), a fixed 80pt design-space point size, non-opaque,
        and no border. The rect is the upper half of the screen in
        design space; the Label's vertical centering then lands the
        text at a quarter of the screen height, exactly where the old
        direct-rendered title sat.
        """
        title = Label(
            pygame.Rect(0, 0, game_constants.DESIGN_W, game_constants.DESIGN_H // 2),
            text=get_language_manager().get_string(
                game_constants.TITLE_SCREEN_TITLE_TEXT
            ),
            border_width=0,
        )
        title.set_text_centered(True)
        title.set_font_point_size(game_constants.TITLE_SCREEN_TITLE_FONT_PT)
        title.set_opaque(False)
        title.selected = True
        return title

    # -- menu (spec 08: Buttons and options, as amended by spec 13) ---------

    def _build_menu(self) -> None:
        """Create and register the menu options (spec 08: Buttons and
        options, as amended by spec 13): the Options button above the
        Exit Game button, in one centered vertical column.
        """
        option_rect = pygame.Rect(
            0,
            0,
            game_constants.MENU_OPTION_WIDTH,
            game_constants.MENU_OPTION_HEIGHT,
        )
        options_button = Button(
            option_rect.copy(),
            text=get_language_manager().get_string(game_constants.OPTIONS_LABEL),
            border_width=game_constants.MENU_OPTION_BORDER_WIDTH,
            on_click=self._request_options,
        )
        exit_game = Button(
            option_rect.copy(),
            text=get_language_manager().get_string(game_constants.EXIT_GAME_LABEL),
            border_width=game_constants.MENU_OPTION_BORDER_WIDTH,
            on_click=self._request_quit,
        )
        new_game = Button(option_rect.copy(), text=self._text("campaign.new_game"),
                          border_width=game_constants.MENU_OPTION_BORDER_WIDTH,
                          on_click=self._request_new)
        continue_game = Button(option_rect.copy(), text=self._text("campaign.continue"),
                               border_width=game_constants.MENU_OPTION_BORDER_WIDTH,
                               on_click=self._request_continue)
        options = [new_game, continue_game, options_button, exit_game]
        self._layout_as_centered_column(options)
        self._ui.widgets.extend(options)

    def _layout_as_centered_column(self, options: list[Widget]) -> None:
        """Stack options into one vertical column, centered horizontally
        and vertically in the lower half of the screen (spec 08).
        """
        width = game_constants.MENU_OPTION_WIDTH
        height = game_constants.MENU_OPTION_HEIGHT
        spacing = game_constants.MENU_OPTION_SPACING
        column_height = len(options) * height + (len(options) - 1) * spacing
        left = (game_constants.DESIGN_W - width) // 2
        # Middle of the lower half: three quarters of the design height.
        top = game_constants.DESIGN_H * 3 // 4 - column_height // 2
        for index, option in enumerate(options):
            option.rect = pygame.Rect(
                left, top + index * (height + spacing), width, height
            )

    def _request_quit(self) -> None:
        """Record the Exit Game intent for the base-class ``handle``."""
        self._pending_action = ScreenAction.QUIT

    def _request_options(self) -> None:
        """Record the Options intent for the base-class ``handle``
        (spec 08, as amended by spec 13)."""
        self._pending_action = ScreenAction.SHOW_OPTIONS_SCREEN

    def _text(self, key: str) -> str:
        return get_language_manager().get_string(key)

    def _draw_message(self, surface: pygame.Surface, text: str, top: int) -> None:
        label = Label(pygame.Rect(100, top, 1720, 110), text=text, border_width=0)
        label.set_text_centered(True)
        label.set_font_point_size(28)
        label.set_opaque(False)
        label.draw(surface, self._theme)

    def _build_modal(self) -> None:
        self._modal_ui.widgets = [
            Button(pygame.Rect(470, 570, 470, 70), text=self._text("campaign.confirm_new"),
                   on_click=self._start_new),
            Button(pygame.Rect(980, 570, 470, 70), text=self._text("campaign.cancel"),
                   on_click=self._cancel_new),
        ]

    def handle(self, events: list[pygame.event.Event]) -> ScreenAction | None:
        # ESC cancels replacement; it must not also quit on that same event.
        if self._confirming:
            return None
        if getattr(self, "_cancelled_modal", False):
            self._cancelled_modal = False
            return None
        return super().handle(events)

    def _cancel_new(self) -> None:
        self._confirming = False
        self._cancelled_modal = True

    def _request_new(self) -> None:
        try:
            exists = self.store.exists()
        except SaveError:
            self._message = self._text("campaign.load_error")
            return
        if exists:
            self._confirming = True
            self._message = ""
        else:
            self._start_new()

    def _start_new(self) -> None:
        try:
            if self.store.exists():
                self.store.preserve_existing()
            campaign = Campaign()
            self.store.save(campaign)
        except SaveError:
            self._confirming = False
            self._message = self._text("campaign.save_error")
            return
        self.campaign = campaign
        self._confirming = False
        self._pending_action = ScreenAction.SHOW_CAMPAIGN

    def _request_continue(self) -> None:
        try:
            self.campaign = self.store.load()
        except SaveError:
            self._message = self._text("campaign.load_error")
            return
        self._pending_action = ScreenAction.SHOW_CAMPAIGN
