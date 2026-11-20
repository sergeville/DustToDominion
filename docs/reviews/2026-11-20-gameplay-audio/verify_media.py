"""Decode both final streams, retain ffprobe facts and actual video samples."""
from pathlib import Path
import hashlib
import json
import subprocess

OUT = Path(__file__).resolve().parent / 'final'
run = json.loads((OUT/'report.json').read_text())
report = {}
for clip in run['clips']:
    name = clip['name']
    video = OUT/(name+'.mp4')
    probe = json.loads(subprocess.check_output(['/usr/local/bin/ffprobe', '-v', 'error',
        '-show_streams', '-show_format', '-of', 'json', str(video)], text=True))
    decoded = subprocess.run(['/usr/local/bin/ffmpeg', '-v', 'error', '-i', str(video),
        '-f', 'null', '-'], capture_output=True, text=True)
    assert decoded.returncode == 0 and not decoded.stderr
    streams = {s['codec_type']: s for s in probe['streams']}
    assert streams['video']['codec_name'] == 'h264'
    assert int(streams['video']['nb_frames']) == clip['frames']
    assert (streams['video']['width'], streams['video']['height']) == (1920, 1080)
    assert streams['audio']['codec_name'] == 'aac'
    assert streams['audio']['sample_rate'] == '44100' and streams['audio']['channels'] == 2
    samples = []
    wanted = ('mining_loop',) if name == 'earned-mining-trip' else ('weapon', 'destruction')
    for cue in wanted:
        events = [e for e in run['audio_requests'] if e['clip'] == name and
                  any(cue+'.wav' in resource for resource in e.get('resource_ids', [e.get('resource_id', '')]))]
        assert events, (name, cue)
        event = events[0]
        timestamp = max(0., (event['raw_byte_offset']-clip['raw_start'])/(44100*4)+.05)
        path = OUT/(name+'-decoded-'+cue+'.png')
        subprocess.run(['/usr/local/bin/ffmpeg', '-y', '-v', 'error', '-ss', str(timestamp),
            '-i', str(video), '-frames:v', '1', str(path)], check=True)
        samples.append({'cue': cue, 'seconds': timestamp, 'file': path.name,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    report[name] = {'probe': probe, 'decode_exit': decoded.returncode,
                    'decode_stderr': decoded.stderr, 'samples': samples}
(OUT/'media-validation.json').write_text(json.dumps(report, indent=2)+'\n')
print('Both H264/AAC clips fully decoded; all video frames retained; samples saved')
