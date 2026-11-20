"""Read-only campaign sound observer (spec 22); no simulation or save state."""
from dataclasses import dataclass

from dtd.audio import get_audio_manager
from dtd.campaign_guidance import mining_target

SOUNDS = {name: 'audio/campaign/'+name+'.wav' for name in (
    'thrust_loop', 'mining_loop', 'ore_pickup', 'weapon', 'impact',
    'destruction', 'docking', 'selling')}


@dataclass(frozen=True)
class StepSnapshot:
    position: tuple
    cargo: int
    hull: float
    fire_cooldown: float
    rocks: frozenset
    # Keep read-only references because a rival may fire and die in one tick.
    enemies: tuple


class CampaignAudio:
    """At most two loops and one cue/category per 0.08 simulation seconds.

    No queue: suppressed/muted events are discarded, never replayed. All audio
    goes through AudioManager's existing reserved channels and volume controls.
    The screen owns lifecycle stops and the final docking/defeat acknowledgement.
    """
    def __init__(self, manager=None):
        if manager is None:
            try:
                manager = get_audio_manager()
            except RuntimeError:
                pass  # Standalone screens/tests can deliberately omit audio.
        self.manager = manager
        self._time = 0.
        self._last = {}

    @staticmethod
    def snapshot(run):
        return StepSnapshot((run.x, run.y), len(run.cargo), run.hull,
                            run._fire_cooldown,
                            frozenset(rock.id for rock in run.asteroids),
                            tuple((enemy, enemy.hull, enemy.cooldown)
                                  for enemy in run.enemies))

    def cue(self, name):
        if self.manager is None or self._time-self._last.get(name, -1.) < .08-1e-9:
            return
        self._last[name] = self._time
        self.manager.play_game_sfx(SOUNDS[name])

    def stop(self):
        if self.manager is not None:
            self.manager.set_active_loops(frozenset())
            for resource_id in SOUNDS.values():
                self.manager.stop_sfx(resource_id)
        self._last.clear()
        self._time = 0.

    def after_step(self, before, run, controls, dt):
        self._time += dt
        if run.defeated:
            # _finish clears all transients, then acknowledges this death once.
            self.stop()
            return
        desired = set()
        if (run.x, run.y) != before.position:
            desired.add(SOUNDS['thrust_loop'])
        if controls.mining and mining_target(run.campaign, run) is not None:
            desired.add(SOUNDS['mining_loop'])
        if self.manager is not None:
            self.manager.set_active_loops(frozenset(desired))
        cues = set()
        if len(run.cargo) > before.cargo:
            cues.add('ore_pickup')
        if run._fire_cooldown > max(0., before.fire_cooldown-dt)+1e-9:
            cues.add('weapon')
        living = {enemy.id for enemy in run.enemies}
        for enemy, hull, cooldown in before.enemies:
            if enemy.cooldown > max(0., cooldown-dt)+1e-9:
                cues.add('weapon')
            if enemy.hull < hull:
                cues.add('impact')
            if enemy.id not in living and hull > 0:
                cues.add('destruction')
        if run.hull < before.hull:
            cues.add('impact')
        if before.rocks - {rock.id for rock in run.asteroids}:
            cues.add('destruction')
        # Stable priority: reserve channels for destruction/contact before pickup.
        for name in ('destruction', 'impact', 'weapon', 'ore_pickup'):
            if name in cues:
                self.cue(name)
