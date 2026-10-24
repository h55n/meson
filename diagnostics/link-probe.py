import json, os, shutil, subprocess, sys, runpy
from pathlib import Path
outdir=Path(os.environ['RUNNER_TEMP'])/'link-probe'
outdir.mkdir(exist_ok=True)
if len(sys.argv)>1 and sys.argv[1]=='child':
 import mesonbuild.linkers.detect as ld
 original=ld.Popen_safe
 def traced(args,*a,**kw):
  p,o,e=original(args,*a,**kw)
  with (outdir/'raw-probes.jsonl').open('a',encoding='utf-8') as f:
   f.write(json.dumps({'pid':os.getpid(),'args':args,'returncode':p.returncode,'stdout':o,'stderr':e})+'\n')
  return p,o,e
 ld.Popen_safe=traced
 sys.argv=['meson.py']+sys.argv[2:]
 runpy.run_path('meson.py',run_name='__main__')
else:
 envkeys=['PATH','INCLUDE','LIB','LIBPATH','VCToolsVersion','VSCMD_ARG_TGT_ARCH','VSCMD_VER','ImageVersion','ImageOS','PROCESSOR_ARCHITECTURE','CC','CXX','OBJC','LDFLAGS']
 (outdir/'environment.json').write_text(json.dumps({k:os.environ.get(k) for k in envkeys},indent=2),encoding='utf-8')
 for name,args in [('clang',['clang','--version']),('link',['link','/logo','--version']),('clang-link',['clang','-Wl,/logo,--version'])]:
  for i in range(10):
   p=subprocess.run(args,capture_output=True,text=True)
   with (outdir/'direct-probes.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'name':name,'iteration':i,'args':args,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})+'\n')
 for i in range(10):
  build=outdir/f'build-{i}'
  commands=[[sys.executable,__file__,'child','setup',str(build),'test cases/objc/3 objc args','--backend=ninja'],[sys.executable,'meson.py','compile','-C',str(build)]]
  for stage,args in enumerate(commands):
   p=subprocess.run(args,capture_output=True,text=True)
   (outdir/f'iteration-{i}-stage-{stage}.log').write_text(p.stdout+'\nSTDERR:\n'+p.stderr,encoding='utf-8')
   print('iteration',i,'stage',stage,'returncode',p.returncode,flush=True)
   if p.returncode: break
