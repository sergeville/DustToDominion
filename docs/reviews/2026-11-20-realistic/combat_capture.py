"""Supplemental earned combat capture; uses isolated SDL-dummy QA bootstrap."""
import importlib.util
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import visual_upgrade_validation as qa
p = qa.pygame
p.init()
surface = p.display.set_mode((1920, 1080))
loader = qa.ResourceLoader()
loader.load(None)
qa.init_audio_manager(loader, None)
qa.init_language_manager(loader, 'en-us')
spec = importlib.util.spec_from_file_location('acceptance', qa.REPO/'tests/test_campaign_acceptance.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
player = module.PlayerClient(loader)
player.click('new_game')
player.mine_and_sell_sortie()
player.purchase('cargo')
player.mine_and_sell_sortie()
assert player.screen.campaign.lifetime_sales == 300
player.purchase('laser')
banked = player.screen.campaign.credits
player.click('launch', sector=2)
run = player.screen.expedition
player.travel(350, 540)
enemy = run.enemies[0]
player.aim(enemy.x, enemy.y, pressed=True)
output = Path(__file__).parent/'final'
captures = []
initial_hull = enemy.hull
hit_hull = None
for frame in range(300):
    if not run.enemies:
        break
    enemy = run.enemies[0]
    player.aim(enemy.x, enemy.y)
    player.screen.advance(1/60)
    assert player.screen.mode == 'flight'
    if hit_hull is None and enemy.hull < initial_hull:
        hit_hull = enemy.hull
        assert player.screen._impacts.items
        captures.append(qa.capture(player.screen, surface, output, 'combat-earned-hit', 'earned pygame-event combat, first observed rival hull reduction'))
else:
    raise AssertionError('Rival survived five seconds')
player.aim(enemy.x, enemy.y, pressed=False)
assert hit_hull is not None and run.bounty == 70 and run.hull > 0
captures.append(qa.capture(player.screen, surface, output, 'combat-earned-defeated', 'earned pygame-event combat, rival defeated'))
player.dock()
assert player.screen.campaign.credits == banked + 70
assert qa.CampaignStore().load().credits == banked + 70
report = {'passed': True, 'input': 'pygame events, SDL dummy; no native physical input',
          'progression_injected': False, 'lifetime_sales_to_unlock': 300,
          'initial_enemy_hull': initial_hull, 'enemy_hull_at_hit': hit_hull,
          'credits_before_bounty': banked, 'credits_after_dock': player.screen.campaign.credits,
          'captures': captures}
(output/'combat-earned-report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
p.quit()
