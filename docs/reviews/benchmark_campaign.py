"""Offscreen drawing benchmark; isolated synthetic state, no native FPS claim."""
import os, tempfile, time, json, sys
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['DUST_TO_DOMINION_HOME']=tempfile.mkdtemp(prefix='dtd-frame-home-')
repo=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo/'src'))
os.chdir(repo)
os.environ['DUST_TO_DOMINION_CONFIG']=str(Path(os.environ['DUST_TO_DOMINION_HOME'])/'game.json')
import pygame
from dtd.resource_loader import ResourceLoader
from dtd.audio import init_audio_manager
from dtd.language import init_language_manager
from dtd.campaign import Campaign
from dtd.campaign_store import CampaignStore
from dtd.screens.campaign import CampaignScreen
from dtd.ui import Theme
pygame.init();pygame.display.set_mode((1280,720))
loader=ResourceLoader();loader.load(None);init_audio_manager(loader,None);init_language_manager(loader)
results=[]
for size in ((1280,720),(1920,1080),(2560,1440)):
 surface=pygame.display.set_mode(size)
 for mode in ('station','flight'):
  screen=CampaignScreen(Theme('default','',loader),loader,Campaign(),CampaignStore())
  if mode=='flight':screen._launch(1)
  assert screen.mode==mode
  assert (screen.expedition is not None)==(mode=='flight')
  for _ in range(10):screen.draw(surface)
  timings=[]
  for _ in range(120):
   start=time.perf_counter();screen.draw(surface);timings.append((time.perf_counter()-start)*1000)
  results.append({'size':size,'view':mode,'median_ms':round(sorted(timings)[60],2),'p95_ms':round(sorted(timings)[114],2)})
pygame.quit()
print(json.dumps(results,indent=2))
