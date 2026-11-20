"""Before native rasterization: matched synthetic fixtures, real old renderer."""
import hashlib, importlib.util, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent/'baseline'
spec=importlib.util.spec_from_file_location('camera_evidence',ROOT/'docs/reviews/2026-11-20-camera/validate.py')
camera=importlib.util.module_from_spec(spec);spec.loader.exec_module(camera)
p=camera.p;qa=camera.qa
report={'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
 'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((ROOT/'src/dtd').rglob('*.py'))},
 'resource_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((ROOT/'resources').rglob('*')) if f.is_file()},
 'captures':[], 'provenance':'pre-change synthetic matched fixtures; dummy output; old1920x1080 canvas upscaled, physical-resolution text; no native4K claim'}
subprocess.run(['git','archive','--format=tar','-o',str(OUT/'product-source.tar'),report['revision'],'src','tests/test_campaign_acceptance.py','tests/test_camera_acceptance.py'],check=True)
p.init();loader=qa.ResourceLoader();loader.load(None);qa.init_audio_manager(loader,None);qa.init_language_manager(loader,'en-us')
for size in ((2560,1440),(3840,2160)):
 surface=p.display.set_mode(size)
 for view in ('mining','combat','station','fleet'):
  screen=camera.matched_scene(loader,view,1.5) if view in ('mining','combat') else qa.scene(loader,view)
  item=camera.capture(screen,surface,OUT,f'en-us-{size[0]}-{view}','matched synthetic before fixture; no injected progression claim')
  item['canvas_pixels']=list(screen._canvas.get_size());report['captures'].append(item)
assert all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in report['source_sha256'].items())
report['sources_unchanged_during_capture']=True
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');p.quit()
print('Eight before captures and immutable source archive retained')
