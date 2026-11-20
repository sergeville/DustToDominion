"""Interim native SDL pointer/toggle diagnostic, not physical-user acceptance."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'));os.chdir(ROOT)
OUT=Path(__file__).resolve().parent/'native-pointer-fixed';OUT.mkdir(exist_ok=True)
os.environ.pop('SDL_VIDEODRIVER',None);os.environ['SDL_AUDIODRIVER']='dummy'
scratch=tempfile.TemporaryDirectory(prefix='dtd-native-pointer-')
os.environ['DUST_TO_DOMINION_HOME']=scratch.name
os.environ['DUST_TO_DOMINION_CONFIG']=str(Path(scratch.name)/'game.json')
import pygame as p
from dtd.main import _init_pygame, _pump_app_events
from dtd.main_window import MainWindow
from dtd.resource_loader import ResourceLoader
from dtd.audio import init_audio_manager
from dtd.language import init_language_manager
from dtd.ui import Theme,current_scale
from dtd.campaign import Campaign
from dtd.campaign_store import CampaignStore
from dtd.screens.campaign import CampaignScreen
from pygame._sdl2.video import Window,Renderer


def renderer_metrics():
    window=Window.from_display_module()
    lib=ctypes.CDLL(p.base.__file__)
    lib.SDL_GetWindowFromID.argtypes=[ctypes.c_uint32];lib.SDL_GetWindowFromID.restype=ctypes.c_void_p
    lib.SDL_GetRenderer.argtypes=[ctypes.c_void_p];lib.SDL_GetRenderer.restype=ctypes.c_void_p
    lib.SDL_GetRendererOutputSize.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int)]
    ptr=lib.SDL_GetRenderer(lib.SDL_GetWindowFromID(window.id))
    if not ptr:return {'renderer':'none (unscaled software window surface)'}
    width,height=ctypes.c_int(),ctypes.c_int()
    assert lib.SDL_GetRendererOutputSize(ptr,ctypes.byref(width),ctypes.byref(height))==0
    renderer=Renderer.from_window(window)
    return {'output_pixels':[width.value,height.value], 'logical_size':renderer.logical_size,
            'scale':renderer.scale,'viewport':list(renderer.get_viewport()),
            'content_origin_in_window':renderer.coordinates_to_window((0,0)),
            'content_end_in_window':renderer.coordinates_to_window(p.display.get_surface().get_size())}

_init_pygame();loader=ResourceLoader();loader.load(None);init_audio_manager(loader,None);init_language_manager(loader,'en-us')
window=MainWindow();report={'kind':'interim native SDL warp/events, no physical user input; dummy audio',
 'base_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
 'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((ROOT/'src/dtd').rglob('*.py'))},
 'desktop_before':p.display.get_desktop_sizes(),'phases':[]}
try:
 window.open();screen=CampaignScreen(Theme('default','',loader),loader,Campaign(),CampaignStore(Path(scratch.name)/'campaign.json'))
 screen._launch(1);screen.expedition.x,screen.expedition.y=960,400
 for phase in ('windowed','fullscreen','returned'):
  if phase!='windowed':
   before=p.display.is_fullscreen()
   toggle=[p.event.Event(p.KEYDOWN,key=p.K_F11)]
   screen.update(toggle);screen.handle(toggle);_pump_app_events(window,toggle,screen)
   assert p.display.is_fullscreen()!=before
  else:
   Window.from_display_module().focus()
   deadline=time.monotonic()+.35
   while time.monotonic()<deadline:
    screen.update(p.event.get());screen.draw(p.display.get_surface());p.display.flip();time.sleep(.01)
   if screen.mode == 'paused':screen.update([p.event.Event(p.KEYDOWN,key=p.K_ESCAPE)])
   p.mouse.set_pos((1152,486))
  events_seen=[];deadline=time.monotonic()+.35
  while time.monotonic()<deadline:
   batch=p.event.get();events_seen += [{'type':p.event.event_name(e.type),**({'pos':e.pos} if hasattr(e,'pos') else {})} for e in batch]
   if any(e.type==p.QUIT for e in batch):raise RuntimeError('Owned probe closed')
   screen.update(batch);screen.draw(p.display.get_surface());p.display.flip();time.sleep(.01)
  actual=current_scale().mouse(p.mouse.get_pos())
  row={'phase':phase,'window_pixels':p.display.get_window_size(),'backing_pixels':p.display.get_surface().get_size(),
    'renderer':renderer_metrics(),'mouse_backing':p.mouse.get_pos(),'mouse_logical':actual,
    'stored_cursor':screen._cursor,'cursor_delta':[screen._cursor[i]-actual[i] for i in range(2)],
    'aim_world':screen._aim,'expected_aim_from_current_mouse':screen._camera.screen_to_world(actual),
    'mode':screen.mode,'events':events_seen}
  report['phases'].append(row);print(json.dumps(row),flush=True)
  if screen.mode == 'paused':
   screen.update([p.event.Event(p.KEYDOWN,key=p.K_ESCAPE)])
   screen.update([]);screen.draw(p.display.get_surface());p.display.flip()
   actual=current_scale().mouse(p.mouse.get_pos())
   resumed={'phase':phase+'-resume-without-motion','mode':screen.mode,'mouse_logical':actual,
     'stored_cursor':screen._cursor,'cursor_delta':[screen._cursor[i]-actual[i] for i in range(2)],
     'aim_world':screen._aim,'expected_aim_from_current_mouse':screen._camera.screen_to_world(actual)}
   report['phases'].append(resumed);print(json.dumps(resumed),flush=True)
 report['desktop_after']=p.display.get_desktop_sizes();assert report['desktop_after']==report['desktop_before']
 report['passed_desktop_restore']=True
finally:
 window.close();scratch.cleanup();(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
