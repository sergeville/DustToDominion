"""Spec20 layout fixtures; synthetic state, isolated saves, not human play proof."""
import json
import os
from pathlib import Path
import sys
import tempfile

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / 'src'))
os.chdir(repo)
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
root = Path(tempfile.mkdtemp(prefix='dtd-feedback-'))
os.environ['DUST_TO_DOMINION_HOME'] = str(root / 'home')
os.environ['DUST_TO_DOMINION_CONFIG'] = str(root / 'home/game.json')
import pygame
from dtd.audio import init_audio_manager
from dtd.language import init_language_manager
from dtd.resource_loader import ResourceLoader
from dtd.campaign import Campaign, STATION_X, STATION_Y
from dtd.campaign_store import CampaignStore
from dtd.screens.campaign import CampaignScreen
from dtd.ui import Theme

pygame.init()
pygame.display.set_mode((1280, 720))
loader = ResourceLoader()
loader.load(None)
init_audio_manager(loader, None)
report = []
for locale in ('en-us', 'de'):
    init_language_manager(loader, locale)
    for size in ((1280, 720), (1920, 1080), (2560, 1440)):
        surface = pygame.display.set_mode(size)
        for view in ('fresh', 'mining', 'return', 'bottom-edge', 'fleet'):
            campaign = Campaign()
            screen = CampaignScreen(Theme('default', '', loader), loader, campaign,
                                    CampaignStore(root / 'fixture.json'))
            if view == 'fleet':
                screen._fleet()
            else:
                screen._launch(1)
                run = screen.expedition
                if view == 'mining':
                    rock = run.asteroids[0]
                    run.x, run.y = rock.x + 120, rock.y + 60
                    screen._aim = (rock.x, rock.y)
                    screen.update([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE),
                                   pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w)])
                    screen.advance(.1)
                elif view == 'return':
                    run.x, run.y = 1000, 500
                    run.cargo = [0] * campaign.capacity
                elif view == 'bottom-edge':
                    run.x, run.y = STATION_X, STATION_Y + 65
            screen.draw(surface)
            filename = f'{locale}-{size[0]}-{view}.png'
            pygame.image.save(surface, str(root / filename))
            report.append(filename)
(root / 'report.json').write_text(json.dumps(report, indent=2))
pygame.quit()
print(root)
