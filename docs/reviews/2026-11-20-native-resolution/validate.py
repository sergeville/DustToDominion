"""Independent native-resolution evidence. Synthetic pairs and earned event play are separate.

The earned route is copied from camera/validate.py with only its output size parameterized.
The SDL dummy driver produces actual native-resolution rasters, not native monitor evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess

ROOT=Path(__file__).resolve().parents[3]
OUTPUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('camera_evidence',ROOT/'docs/reviews/2026-11-20-camera/validate.py')
camera=importlib.util.module_from_spec(spec);spec.loader.exec_module(camera)
p=camera.p;qa=camera.qa;CameraPlayer=camera.CameraPlayer

def hashes(folder):
    return {str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(folder.rglob('*')) if f.is_file() and '__pycache__' not in str(f)}

def capture(screen,surface,output,name,origin):
    item=camera.capture(screen,surface,output,name,origin)
    assert screen._canvas is surface, 'Native scene must draw directly into supplied output'
    item['canvas_pixels']=list(screen._canvas.get_size())
    item['direct_target']=True
    item['sprite_cache']=screen._art.cache_info
    return item

def earned_play(loader, output, size):
    p.display.set_mode(size)
    qa.init_language_manager(loader, 'en-us')
    p.event.clear()
    player = CameraPlayer(loader)
    player.click('new_game')
    captures = []
    def snap(name):
        captures.append(capture(player.screen, p.display.get_surface(), output, name,
                                'pygame-event-earned progression; no injected game state'))
    player.click('launch', sector=1)
    assert player.screen._camera.zoom == 1.5
    snap('trip-fresh')
    run = player.screen.expedition
    rock = run.asteroids[0]
    player.travel(rock.x+120, rock.y)
    player.aim(rock.x, rock.y)
    player.key(p.K_SPACE)
    player.screen.advance(1/60)
    assert rock.health == 2 and len(run.pickups) == 1
    snap('trip-mining')
    player.key(p.K_SPACE, False)
    player.travel(rock.x, rock.y)
    player.key(p.K_SPACE)
    for _ in range(180):
        player.screen.advance(1/60)
        if rock not in run.asteroids and len(run.cargo) == 3:
            break
    else:
        raise AssertionError('Event-earned mining/collection failed')
    player.key(p.K_SPACE, False)
    snap('trip-collected')
    player.travel(qa.STATION_X, qa.STATION_Y)
    player.key(p.K_e)
    assert player.screen.mode == 'result' and qa.CampaignStore().load().cargo == [0, 0, 0]
    snap('trip-docked')
    player.click('continue')
    player.click('sell', value=30)
    assert player.screen.campaign.credits == 110 and qa.CampaignStore().load().credits == 110
    snap('trip-sold')
    trip = {'passed': True, 'ore': 3, 'credits_before': 80, 'credits_after': 110}
    # Continue the same earned campaign; two full sorties unlock the fringe.
    player.mine_and_sell_sortie()
    player.purchase('cargo')
    player.mine_and_sell_sortie()
    assert player.screen.campaign.lifetime_sales == 330
    player.purchase('laser')
    banked = player.screen.campaign.credits
    player.click('launch', sector=2)
    player.travel(350, 540)
    run = player.screen.expedition
    snap('combat-approach')
    enemy = run.enemies[0]
    player.aim(enemy.x, enemy.y, pressed=True)
    for frame in range(300):
        if not run.enemies:
            break
        enemy = run.enemies[0]
        player.aim(enemy.x, enemy.y)
        player.screen.advance(1/60)
        assert player.screen.mode == 'flight', player.diagnostic()
        if frame == 5:
            snap('combat-firing')
    else:
        raise AssertionError('Earned rival did not fall to aimed fire')
    player.aim(enemy.x, enemy.y, pressed=False)
    assert run.bounty == 70 and run.hull > 0
    assert player.screen.campaign.credits == banked
    snap('combat-defeated-rival')
    player.dock()
    assert player.screen.campaign.credits == banked+70
    assert qa.CampaignStore().load().credits == banked+70
    snap('combat-docked')
    player.click('title')
    player.click('continue')
    assert player.screen.campaign.credits == banked+70
    snap('menu-station')
    player.click('view_fleet')
    snap('menu-fleet')
    player.click('fleet_back')
    return {'trip': trip, 'combat': {'passed': True, 'earned_lifetime_sales': 330,
            'bounty': 70, 'banked_before': banked, 'banked_after': banked+70,
            'continued_checkpoint_verified': True,
            'visible_target_firing_samples': len(player.firing_view_samples),
            'firing_view_min': [min(v[i] for v in player.firing_view_samples) for i in (0, 1)],
            'firing_view_max': [max(v[i] for v in player.firing_view_samples) for i in (0, 1)]},
            'captures': captures, 'native_input': False}


def contacts(output):
    font=p.font.Font(None,24)
    for locale in ('en-us','de'):
      for width in (2560,3840):
        names=[f'{locale}-{width}-{view}-z{zoom}' for view in ('mining','combat') for zoom in (1,1.5,2)]
        names += [f'{locale}-{width}-{view}' for view in ('station','fleet','navigation-z2')]
        sheet=p.Surface((1800,1086));sheet.fill((5,10,20))
        for index,name in enumerate(names):
            x=(index%3)*600;y=(index//3)*362
            source=p.image.load(str(output/(name+'.png')))
            sheet.blit(p.transform.smoothscale(source,(600,338)),(x,y+24))
            sheet.blit(font.render(name,True,(230,240,245)),(x+5,y+3))
        p.image.save(sheet,str(output/f'contact-{locale}-{width}.png'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark-only',action='store_true')
    args=parser.parse_args()
    output=OUTPUT/'final';output.mkdir(exist_ok=True)
    p.init();p.display.set_mode((1920,1080))
    loader=qa.ResourceLoader();loader.load(None);qa.init_audio_manager(loader,None)
    report_path=output/'report.json'
    if args.benchmark_only:
        report=json.loads(report_path.read_text())
        assert hashes(ROOT/'src/dtd')==report['source_sha256']
        qa.init_language_manager(loader,'en-us')
        report['benchmark']=qa.benchmark(loader)
        report_path.write_text(json.dumps(report,indent=2)+'\n')
        p.quit();print('Benchmark appended; same source hashes verified',flush=True);return
    report={'base_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
       'source_sha256':hashes(ROOT/'src/dtd'),'resource_sha256':hashes(ROOT/'resources'),
       'driver':p.display.get_driver(),'python':platform.python_version(),'pygame':p.version.ver,
       'SDL':list(p.get_sdl_version()),'provenance':'actual native-resolution offscreen rasters; synthetic fixtures and event-earned play separate; no OS input or 4K monitor claim',
       'captures':[],'navigation_captures':[],'earned':{}}
    for size in ((2560,1440),(3840,2160)):
        folder=output/f'earned-{size[0]}';folder.mkdir(exist_ok=True)
        isolated=qa.HOME/str(size[0]);isolated.mkdir(exist_ok=True)
        os.environ['DUST_TO_DOMINION_HOME']=str(isolated)
        os.environ['DUST_TO_DOMINION_CONFIG']=str(isolated/'game.json')
        report['earned'][str(size[0])]=earned_play(loader,folder,size)
        print(f'Earned trip/combat/save/reload passed at {size}',flush=True)
    for locale in ('en-us','de'):
      qa.init_language_manager(loader,locale)
      for size in ((2560,1440),(3840,2160)):
        surface=p.display.set_mode(size)
        for zoom in (1,1.5,2):
          for view in ('mining','combat'):
            screen=camera.matched_scene(loader,view,zoom)
            report['captures'].append(capture(screen,surface,output,f'{locale}-{size[0]}-{view}-z{zoom}',
                'exact serialized matched model fixture; synthetic'))
        for view in ('station','fleet'):
            screen=qa.scene(loader,view)
            report['captures'].append(capture(screen,surface,output,f'{locale}-{size[0]}-{view}',
                'matched menu fixture; synthetic'))
        screen=camera.matched_scene(loader,'combat',2);run=screen.expedition
        run.x,run.y=960,190;run.enemies=[camera.Enemy(42,960,520),camera.Enemy(43,1550,240)]
        run.projectiles=[];screen._keys.clear();screen._visual_time=10
        report['navigation_captures'].append(capture(screen,surface,output,f'{locale}-{size[0]}-navigation-z2',
            'synthetic legal positions; offscreen station/rival and enlarged actor avoidance'))
    contacts(output)
    assert hashes(ROOT/'src/dtd')==report['source_sha256']
    assert hashes(ROOT/'resources')==report['resource_sha256']
    report['source_and_resources_unchanged_during_capture']=True
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    allitems=report['captures']+report['navigation_captures']+[i for earned in report['earned'].values() for i in earned['captures']]
    print(json.dumps({'captures':len(allitems),'layout_warnings':sum(len(i['layout_warnings']) for i in allitems),
       'world_bounds_warnings':sum(len(i['world_bounds_warnings']) for i in allitems)}),flush=True)
    p.quit()

if __name__=='__main__':main()
