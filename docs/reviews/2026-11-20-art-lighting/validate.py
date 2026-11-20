"""Reuse the independent camera/event harness for the artwork/lighting pass.

Optional --record encodes actual earned-route framebuffers, not generated art.
Separate clips omit the intervening progression sorties explicitly.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('camera_evidence', ROOT/'docs/reviews/2026-11-20-camera/validate.py')
camera = importlib.util.module_from_spec(spec)
spec.loader.exec_module(camera)
camera.OUTPUT = OUTPUT


class Recording:
    def __init__(self, directory):
        self.directory = directory
        self.writers = {}
        self.counts = {}
        self.ticks = {}
        self.done = set()

    def frame(self, name, surface):
        if name not in self.writers:
            executable = shutil.which('ffmpeg')
            if executable is None:
                raise RuntimeError('--record requires an existing ffmpeg; no encoder installed')
            log = (self.directory/(name+'.ffmpeg.log')).open('wb')
            command = [executable, '-y', '-hide_banner', '-loglevel', 'warning',
                       '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', '1920x1080',
                       '-framerate', '30', '-i', 'pipe:0', '-an', '-c:v', 'libx264',
                       '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p',
                       '-movflags', '+faststart', str(self.directory/(name+'.mp4'))]
            self.writers[name] = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=log, stderr=log), log
            self.counts[name] = 0
        assert surface.get_size() == (1920, 1080)
        self.writers[name][0].stdin.write(camera.p.image.tobytes(surface, 'RGB'))
        self.counts[name] += 1

    def advance(self, screen, dt):
        run = screen.expedition
        if run is None or screen.mode != 'flight':
            return
        name = 'earned-mining-trip' if run.sector == 1 and screen.campaign.lifetime_sales == 0 else 'earned-combat' if run.sector == 2 else None
        if name is None or name in self.done:
            return
        assert abs(dt-1/60) < 1e-12, 'Recording cadence must match fixed simulation steps'
        self.ticks[name] = self.ticks.get(name, 0)+1
        if self.ticks[name] % 2 == 0:
            surface = camera.p.display.get_surface()
            screen.draw(surface)
            self.frame(name, surface)

    def finish_scene(self, name, surface):
        if name not in self.writers or name in self.done:
            return
        # One explicitly documented second of frozen menu output at each end.
        for _ in range(30):
            self.frame(name, surface)
        self.done.add(name)

    def close(self):
        records = []
        for name, (process, log) in self.writers.items():
            process.stdin.close()
            code = process.wait(timeout=60)
            log.close()
            assert code == 0, f'ffmpeg failed for {name}: {code}'
            path = self.directory/(name+'.mp4')
            records.append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'frames': self.counts[name], 'fps': 30, 'fixed_simulation_hz': 60,
                            'simulation_ticks_recorded': self.ticks[name],
                            'pixels': [1920, 1080], 'world_canvas': [1920, 1080],
                            'audio': False, 'native_input': False,
                            'end_menu_freeze_seconds': 1,
                            'provenance': 'actual SDL dummy framebuffers from continuous event-earned route; sampled every second 60Hz step; two separate clips omit intervening progression sorties'})
        return records


def main():
    focused = '--focused' in sys.argv
    if focused:
        sys.argv.remove('--focused')
        camera.qa.SIZES = ((1280, 720), (1920, 1080))
    record = '--record' in sys.argv
    if record:
        sys.argv.remove('--record')
        if '--earned' not in sys.argv:
            raise SystemExit('--record requires --earned')
    phase = sys.argv[sys.argv.index('--phase')+1]
    output = OUTPUT/phase
    output.mkdir(parents=True, exist_ok=True)
    recorder = Recording(output) if record else None
    if recorder:
        original_advance = camera.qa.CampaignScreen.advance
        original_capture = camera.capture
        def advance(screen, dt):
            result = original_advance(screen, dt)
            recorder.advance(screen, dt)
            return result
        def capture(screen, surface, folder, name, origin):
            item = original_capture(screen, surface, folder, name, origin)
            if name == 'trip-sold':
                recorder.finish_scene('earned-mining-trip', surface)
            elif name == 'combat-docked':
                recorder.finish_scene('earned-combat', surface)
            return item
        camera.qa.CampaignScreen.advance = advance
        camera.capture = capture
    try:
        camera.main()
    finally:
        recordings = recorder.close() if recorder else None
    report_path = output/'report.json'
    report = json.loads(report_path.read_text())
    if focused and '--benchmark-only' not in sys.argv:
        camera.p.init()
        surface = camera.p.display.set_mode((3840, 2160))
        loader = camera.qa.ResourceLoader()
        loader.load(None)
        camera.qa.init_audio_manager(loader, None)
        camera.qa.init_language_manager(loader, 'en-us')
        report['resolution_captures'] = []
        for view in ('mining', 'combat'):
            screen = camera.matched_scene(loader, view, 1.5)
            report['resolution_captures'].append(camera.capture(screen, surface, output,
                f'en-us-3840-{view}-z1.5', 'synthetic matched state; targeted offscreen4K output; world remains1080p'))
        camera.p.quit()
    report['comparison_baseline_commit'] = '05251648c6f185002c03f1fbf060dfbc0fa09bb4'
    if '--benchmark-only' not in sys.argv:
        report['matrix_output_sizes'] = list(camera.qa.SIZES)
    report['resource_sha256'] = {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
                                for f in sorted((ROOT/'resources').rglob('*')) if f.is_file()}
    source_art = ROOT/'assets/source/realistic'
    names = ('asteroid_iron_c', 'asteroid_gold_b', 'asteroid_crystal_b',
             'prospector_v2', 'rival_v2', 'station_v2')
    paths = [source_art/'manifest.json', source_art/'README.md']
    paths += [source_art/(name+suffix) for name in names for suffix in ('.png', '.prompt.txt')]
    report['source_art_sha256'] = {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
                                   for f in paths}
    if recordings is not None:
        report['recordings'] = recordings
    report_path.write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
