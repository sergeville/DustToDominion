"""Render bilingual campaign views and exercise scaled clicks in isolated state.

Run from any directory with the project interpreter. Printed output directory
contains synthetic screenshots/checkpoints only; real user saves are untouched.
"""
import os, json, tempfile, sys
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
repo=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo/'src'))
os.chdir(repo)
root=Path(tempfile.mkdtemp(prefix='dtd-fleet-validation-'))
os.environ['DUST_TO_DOMINION_HOME']=str(root/'home')
os.environ['DUST_TO_DOMINION_CONFIG']=str(root/'home'/'game.json')
import pygame
from dtd.resource_loader import ResourceLoader
from dtd.audio import init_audio_manager
from dtd.language import init_language_manager
from dtd.ui import Theme
from dtd.campaign import Campaign
from dtd.campaign_store import CampaignStore, SaveError
from dtd.screens.title import TitleScreen
from dtd.screens.campaign import CampaignScreen
from dtd.screens.base import ScreenAction
pygame.init(); pygame.display.set_mode((1280,720))
loader=ResourceLoader();loader.load(None);init_audio_manager(loader,None)
report=[]
def click(screen, button):
    scale=pygame.display.get_surface().get_width()/1920
    pos=tuple(int(v*scale) for v in button.rect.center)
    for kind in (pygame.MOUSEBUTTONDOWN,pygame.MOUSEBUTTONUP):
        screen.update([pygame.event.Event(kind,pos=pos,button=1)])
    return screen.handle([])
def snap(screen,label,locale,width):
    surf=pygame.display.get_surface();surf.fill((0,0,0));screen.draw(surf)
    pygame.image.save(surf,str(root/f'{locale}-{width}-{label}.png'))
for locale in ('en-us','de'):
    init_language_manager(loader,locale)
    theme=Theme('','',loader)
    for width,height in ((1280,720),(1920,1080),(2560,1440)):
        pygame.display.set_mode((width,height))
        path=root/f'checkpoint-final-{locale}-{width}.json'
        store=CampaignStore(path)
        title=TitleScreen(theme,loader);title.store=store
        snap(title,'title',locale,width)
        assert click(title,title._ui.widgets[1]) is None
        assert title._message
        snap(title,'load-error',locale,width)
        assert click(title,title._ui.widgets[0]) is ScreenAction.SHOW_CAMPAIGN
        title=TitleScreen(theme,loader);title.store=store
        assert click(title,title._ui.widgets[0]) is None and title._confirming
        snap(title,'replace-confirm',locale,width)
        assert click(title,title._modal_ui.widgets[1]) is None and not title._confirming
        assert click(title,title._ui.widgets[1]) is ScreenAction.SHOW_CAMPAIGN
        title=TitleScreen(theme,loader);title.store=store
        click(title,title._ui.widgets[0]);assert title._confirming
        assert click(title,title._modal_ui.widgets[0]) is ScreenAction.SHOW_CAMPAIGN
        class FailedStore:
            def exists(self): return False
            def save(self, campaign): raise SaveError('simulated write failure')
        failed_title=TitleScreen(theme,loader);failed_title.store=FailedStore()
        assert click(failed_title,failed_title._ui.widgets[0]) is None
        snap(failed_title,'save-error',locale,width)
        # Live station with all fleet and crew owned exposes their actual UI state.
        campaign=Campaign(credits=1500,support_ships=2,miner=True,engineer=True,lifetime_sales=1500)
        station=CampaignScreen(theme,loader,campaign,store)
        snap(station,'owned-ships',locale,width)
        for supports in (0,1,2):
            campaign.support_ships=supports
            station._fleet()
            snap(station,'fleet-'+str(supports),locale,width)
            assert station.mode=='fleet'
            click(station,station._ui.widgets[0])
            assert station.mode=='station'
        normal_store=station.store
        station.store=FailedStore()
        station._save();snap(station,'station-save-error',locale,width)
        station.store=normal_store
        save=next(b for b in station._ui.widgets if b.text==station._t('save'))
        click(station,save);assert store.load().ship_count==3
        launch=station._ui.widgets[0]
        click(station,launch);assert station.mode=='flight'
        snap(station,'flight',locale,width)
        station.update([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE)])
        snap(station,'pause',locale,width)
        click(station,station._ui.widgets[0]);assert station.mode=='flight'
        # Return by E and exercise sell through a physically scaled click.
        station.expedition.cargo=[0,0]
        station.update([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e)])
        click(station,station._ui.widgets[0]);assert station.mode=='station'
        sell=station._ui.widgets[3]
        before=campaign.credits;click(station,sell)
        assert campaign.credits==before+26
        report.append({'locale':locale,'resolution':[width,height],'title_new_continue_confirm_cancel':True,'station_save_launch_pause_resume_dock_sell':True})
(root/'report.json').write_text(json.dumps(report,indent=2))
print(root)
print(json.dumps(report,indent=2))
pygame.quit()
