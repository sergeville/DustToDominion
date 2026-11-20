"""Earned gameplay with actual SDL disk-driver mixed audio, never device loopback.

Video timing follows the emitted PCM byte clock. It holds the last rendered
frame between observations; no audio stretching or offline event mixing occurs.
"""
import argparse
import array
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import time
import wave

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('camera_evidence', ROOT/'docs/reviews/2026-11-20-camera/validate.py')
camera = importlib.util.module_from_spec(spec)
spec.loader.exec_module(camera)
from dtd import audio

RATE, CHANNELS, FPS = 44100, 2, 30
BYTES_PER_SECOND = RATE * CHANNELS * 2


class Recorder:
    def __init__(self, folder, raw):
        self.folder, self.raw = folder, raw
        self.current = None
        self.clips, self.events = [], []
        self.done = set()

    def position(self):
        return self.raw.stat().st_size if self.raw.exists() else 0

    def start(self, name, screen):
        if self.current or name in self.done:
            return
        # Launch already cleared sounds; let queued disk-driver buffers drain.
        time.sleep(.2)
        path = self.folder/(name+'-video.mp4')
        log = (self.folder/(name+'-encode.log')).open('wb')
        process = subprocess.Popen(['/usr/local/bin/ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning',
            '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', '1920x1080',
            '-framerate', str(FPS), '-i', 'pipe:0', '-an', '-c:v', 'libx264',
            '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p', str(path)],
            stdin=subprocess.PIPE, stdout=log, stderr=log)
        surface = camera.p.display.get_surface()
        screen.draw(surface)
        self.current = {'name': name, 'raw_start': self.position(),
            'wall_start': time.monotonic(), 'process': process, 'log': log,
            'frames': 0, 'frame': camera.p.image.tobytes(surface, 'RGB'), 'ticks': 0}

    def sync(self, screen):
        if self.current is None:
            return
        item = self.current
        target = int((self.position()-item['raw_start']) / BYTES_PER_SECOND * FPS)
        while item['frames'] <= target:
            item['process'].stdin.write(item['frame'])
            item['frames'] += 1
        surface = camera.p.display.get_surface()
        screen.draw(surface)
        item['frame'] = camera.p.image.tobytes(surface, 'RGB')

    def finish(self, screen):
        if self.current is None:
            return
        # Let the real docking/sale cue finish, retaining a documented menu hold.
        end = time.monotonic() + 1.1
        while time.monotonic() < end:
            self.sync(screen)
            time.sleep(.01)
        self.sync(screen)
        item = self.current
        item['raw_end'] = self.position()
        item['wall_duration'] = time.monotonic()-item['wall_start']
        item['process'].stdin.close()
        assert item['process'].wait(timeout=30) == 0
        item['log'].close()
        self.done.add(item['name'])
        self.clips.append({key: value for key, value in item.items()
                           if key not in ('process', 'log', 'frame')})
        self.current = None

    def encode_audio(self):
        raw = self.raw.read_bytes()
        for item in self.clips:
            pcm = raw[item['raw_start']:item['raw_end']]
            assert len(pcm) % 4 == 0
            name = item['name']
            wav_path = self.folder/(name+'.wav')
            with wave.open(str(wav_path), 'wb') as output:
                output.setnchannels(CHANNELS)
                output.setsampwidth(2)
                output.setframerate(RATE)
                output.writeframes(pcm)
            values = array.array('h', pcm)
            item.update({'audio_seconds': len(pcm)/BYTES_PER_SECOND,
                'video_seconds': item['frames']/FPS,
                'peak': max(map(abs, values))/32768,
                'rms': math.sqrt(sum(v*v for v in values)/len(values))/32768,
                'clipped_samples': sum(abs(v) >= 32767 for v in values),
                'nonzero_samples': sum(v != 0 for v in values)})
            item['audio_minus_wall_seconds'] = item['audio_seconds']-item['wall_duration']
            item['video_minus_audio_seconds'] = item['video_seconds']-item['audio_seconds']
            with (self.folder/(name+'-mux.log')).open('wb') as log:
                subprocess.run(['/usr/local/bin/ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning',
                    '-i', str(self.folder/(name+'-video.mp4')), '-i', str(wav_path),
                    '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac',
                    '-b:a', '192k', '-movflags', '+faststart',
                    str(self.folder/(name+'.mp4'))], stdout=log, stderr=log, check=True)
            item['files'] = {suffix: {'file': name+suffix,
                'sha256': hashlib.sha256((self.folder/(name+suffix)).read_bytes()).hexdigest()}
                for suffix in ('.wav', '.mp4', '-video.mp4')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('interim', 'final'), required=True)
    args = parser.parse_args()
    folder = OUT/args.phase
    folder.mkdir(exist_ok=True)
    raw = folder/'session-audio.raw'
    if raw.exists():
        raw.unlink()
    os.environ['SDL_AUDIODRIVER'] = 'disk'
    os.environ['SDL_DISKAUDIOFILE'] = str(raw)
    camera.p.mixer.pre_init(frequency=RATE, size=-16, channels=CHANNELS, buffer=512)
    camera.p.init()
    assert camera.p.mixer.get_init() == (RATE, -16, CHANNELS)
    camera.p.display.set_mode((1920, 1080))
    loader = camera.qa.ResourceLoader()
    loader.load(None)
    camera.qa.init_audio_manager(loader, None)
    recorder = Recorder(folder, raw)
    manager = audio.get_audio_manager()
    play = manager.play_game_sfx
    def observe(resource_id):
        recorder.events.append({'resource_id': resource_id,
            'raw_byte_offset': recorder.position(),
            'clip': None if recorder.current is None else recorder.current['name'],
            'kind': 'request through actual AudioManager; PCM independently captures mixer output'})
        return play(resource_id)
    manager.play_game_sfx = observe
    set_loops = manager.set_active_loops
    previous_loops = set()
    def observe_loops(resource_ids):
        nonlocal previous_loops
        result = set_loops(resource_ids)
        active = set(manager._loops.active_ids())
        if active != previous_loops:
            recorder.events.append({'resource_ids': sorted(active),
                'raw_byte_offset': recorder.position(),
                'clip': None if recorder.current is None else recorder.current['name'],
                'kind': 'actual loop registry transition after AudioManager call'})
            previous_loops = active
        return result
    manager.set_active_loops = observe_loops
    advance = camera.qa.CampaignScreen.advance
    def recorded_advance(screen, dt):
        run = screen.expedition
        if screen.mode == 'flight' and run is not None:
            name = ('earned-mining-trip' if run.sector == 1 and screen.campaign.lifetime_sales == 0
                    else 'earned-combat' if run.sector == 2 else None)
            if name:
                recorder.start(name, screen)
        began = time.monotonic()
        result = advance(screen, dt)
        if recorder.current:
            recorder.current['ticks'] += 1
            recorder.sync(screen)
            time.sleep(max(0., dt-(time.monotonic()-began)))
        return result
    camera.qa.CampaignScreen.advance = recorded_advance
    capture = camera.capture
    def observed_capture(screen, surface, output, name, origin):
        result = capture(screen, surface, output, name, origin)
        if name == 'trip-docked':
            # Retain the actual result screen long enough to hear its real cue.
            end = time.monotonic() + .85
            while time.monotonic() < end:
                recorder.sync(screen)
                time.sleep(.01)
        if name in ('trip-sold', 'combat-docked'):
            recorder.sync(screen)
            recorder.finish(screen)
        return result
    camera.capture = observed_capture
    report = {'base_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'provenance': 'actual SDL disk-driver software mixer PCM plus SDL dummy framebuffers; event-driven earned gameplay; no device loopback, physical input or listening acceptance',
        'audio_driver': 'disk', 'video_driver': camera.p.display.get_driver(),
        'sample_rate': RATE, 'sample_bits': 16, 'channels': CHANNELS, 'requested_mixer_buffer': 512,
        'video_fps': FPS, 'video_pixels': [1920, 1080], 'world_canvas': [1920, 1080],
        'alignment': 'video clock follows observed emitted PCM file bytes; previous framebuffer held until next observation; resolution limited by disk-buffer writes and render polling; no audio stretching',
        'editing': '200ms stationary pre-roll after existing launch cleanup before each clip; separate continuous clips omit intervening progression sorties; trip docking hold0.85wallseconds and final menu holds1.1wallseconds; all source video frames and PCM retained; final video and PCM durations differ by less than one frame; AAC encoder padding possible',
        'source_sha256': {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
                          for f in sorted((ROOT/'src/dtd').rglob('*.py'))},
        'resource_sha256': {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
                            for f in sorted((ROOT/'resources').rglob('*')) if f.is_file()}}
    try:
        report['earned'] = camera.earned_play(loader, folder)
    finally:
        manager.stop_loops()
        camera.p.quit()
    recorder.encode_audio()
    for kind in ('source_sha256', 'resource_sha256'):
        assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest
                   for name, digest in report[kind].items()), 'Source changed during capture'
    report['sources_unchanged_during_capture'] = True
    report['clips'] = recorder.clips
    report['audio_requests'] = recorder.events
    report['raw'] = {'file': raw.name, 'bytes': raw.stat().st_size,
                     'sha256': hashlib.sha256(raw.read_bytes()).hexdigest()}
    (folder/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Earned trip, combat and actual SDL disk audio captured', flush=True)


if __name__ == '__main__':
    main()
