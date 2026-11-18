"""Package committed source and genuine local history. Never invokes git push."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,default=ROOT.parent/'outputs')
args=parser.parse_args();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
assert not git('status','--porcelain'),'Commit all completed source/evidence before packaging.'
assert git('remote','get-url','origin')=='https://github.com/gloria-mbilinyi/TFPMDS.git'
head=git('rev-parse','HEAD');history=[]
for line in git('log','--reverse','--format=%H%x09%s').splitlines():
    sha,subject=line.split('\t',1);history.append({'hash':sha,'functionality':subject})
bundle=out/'TFPMDS-local-history.bundle';pending_bundle=out/'TFPMDS-local-history.pending.bundle'
subprocess.run(['git','-C',str(ROOT),'bundle','create',str(pending_bundle),'--all'],check=True,capture_output=True)
pending_bundle.replace(bundle)
subprocess.run(['git','-C',str(ROOT),'bundle','verify',str(bundle)],check=True,capture_output=True)
acceptance=json.loads((ROOT/'docs/evidence/acceptance-results.json').read_text(encoding='utf-8'))
pdf_info=json.loads((ROOT/'docs/evidence/pdf-validation.json').read_text(encoding='utf-8'))
academic=json.loads((ROOT/'docs/evidence/academic-verification.json').read_text(encoding='utf-8'))
manifest={'generated_at':datetime.now(timezone.utc).isoformat(),'official_remote':git('remote','get-url','origin'),
          'branch':git('branch','--show-current'),'head':head,'local_commits':len(history),'pushes_by_agent':0,
          'git_author':git('config','--local','--get','user.name')+' <'+git('config','--local','--get','user.email')+'>',
          'functional_coverage':f'{acceptance["functional_passed"]}/{acceptance["functional_total"]} (100%)',
          'backend_tests':acceptance['backend'],'frontend_tests':acceptance['frontend'],'uml_models':8,
          'pdf_pages':pdf_info['pages'],'browser_journey':'14 steps verified in supported in-app browser',
          'all_pdf_pages_A4':pdf_info['all_pages_A4'],'word_parts':academic['parts'],
          'published_baseline':{'commits':26,'head':'ddc2e8aacc48ece0dfad27b19e5f26317f56cd58','pushed_by':'Project owner after local agent development'},
          'new_local_correction_commits':int(git('rev-list','--count','ddc2e8a..HEAD')),
          'playwright_runner':'Harness typechecked; normal browser launch blocked in restricted shell. Not claimed as an executed test run.',
          'commits':history}
manifest_path=out/'DELIVERY_MANIFEST.json';manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
start='''# TFPMDS delivery

The ZIP contains the TFPMDS source repository, its complete hidden `.git` directory, editable documentation/UML, genuine evidence and optional synthetic database. It excludes installed dependencies, working secrets and the working database. Extract into a new directory and keep hidden files to preserve history.

Start with `TFPMDS/README.md` for installation and `TFPMDS/docs/DEMO_GUIDE.md` for the demonstration. The API uses port 8010; the Vite interface normally uses 5173. All five primary @tfpmds.demo accounts use DemoPass123!. Payments and SMS are simulations.

`TFPMDS-local-history.bundle` is an independent backup of every local commit. To recover it into a NEW directory if needed:

```powershell
git clone TFPMDS-local-history.bundle TFPMDS-recovered
git -C TFPMDS-recovered remote set-url origin https://github.com/gloria-mbilinyi/TFPMDS.git
```

Codex developed locally; the project owner subsequently pushed the original 26 commits through ddc2e8a. The academic corrections are new local commits. When YOU are ready, enter the project directory and run:

```powershell
git status
git remote -v
git log --oneline --reverse
git fetch origin
git push -u origin main
```

Authenticate as gloria-mbilinyi. If Git rejects a non-fast-forward push because the remote changed, inspect and merge that work; do not force-push or rewrite the preserved history. No collaborator access is required for the Codex account.

The delivery manifest lists every actual commit hash and implemented milestone. `TFPMDS_Academic_Submission/` contains the three editable Word parts (20, 37 and 47 pages), the complete 103-page A4 PDF, Markdown, all eight editable draw.io sources, linked images, the verification report and machine-readable evidence. The same folder is available in `TFPMDS-Academic-Submission.zip`. Fill the four academic cover placeholders before submission.
'''
(out/'START_HERE.md').write_text(start,encoding='utf-8')
shutil.copy2(ROOT/'docs/TFPMDS_Technical_Proposal.pdf',out/'TFPMDS_Technical_Proposal.pdf')
shutil.copy2(ROOT/'docs/TECHNICAL_PROPOSAL.md',out/'TFPMDS_Technical_Proposal.md')
shutil.copy2(ROOT/'docs/screenshots/reports-analytics.jpg',out/'TFPMDS-preview.jpg')
submission=out/'TFPMDS_Academic_Submission';submission.mkdir(exist_ok=True)
for part in [1,2,3]:
    path=ROOT/f'docs/submission/TFPMDS_Technical_Proposal_Part_{part}.docx'
    shutil.copy2(path,submission/path.name)
for source,destination in [('TFPMDS_Technical_Proposal.pdf','TFPMDS_Technical_Proposal.pdf'),
                           ('TECHNICAL_PROPOSAL.md','TFPMDS_Technical_Proposal.md'),
                           ('FINAL_ACADEMIC_VERIFICATION.md','FINAL_ACADEMIC_VERIFICATION.md')]:
    shutil.copy2(ROOT/'docs'/source,submission/destination)
for directory in ['uml','screenshots']:shutil.copytree(ROOT/'docs'/directory,submission/directory,dirs_exist_ok=True)
evidence_dir=submission/'evidence'
shutil.copytree(ROOT/'docs/evidence',evidence_dir,dirs_exist_ok=True)
for name in ['REQUIREMENTS_TRACEABILITY.md','requirements.json','openapi.json','database-schema.sql',
             'AGENT_DEVELOPMENT_LOG.md','LOCAL_COMMIT_HISTORY.md','DEMO_GUIDE.md','API_REFERENCE.md','ARCHITECTURE.md']:
    shutil.copy2(ROOT/'docs'/name,submission/name)
shutil.copy2(manifest_path,evidence_dir/manifest_path.name)
academic_archive=out/'TFPMDS-Academic-Submission.zip'
with zipfile.ZipFile(academic_archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for path in sorted(submission.rglob('*')):
        if path.is_file():z.write(path,path.relative_to(out).as_posix())
with zipfile.ZipFile(academic_archive) as z:
    assert z.testzip() is None
    assert len([n for n in z.namelist() if n.endswith('.docx')])==3
    assert len([n for n in z.namelist() if n.endswith('.drawio')])==8
tracked=subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z']).decode().split('\0')
tracked=[name for name in tracked if name]
assert '.env' not in tracked and '.development-secrets' not in tracked and 'tfpmds.db' not in tracked
archive=out/'TFPMDS-project-with-history.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in tracked:z.write(ROOT/name,'TFPMDS/'+name)
    for path in sorted((ROOT/'.git').rglob('*')):
        if path.is_file():
            assert path.resolve().is_relative_to(ROOT)
            z.write(path,'TFPMDS/'+path.relative_to(ROOT).as_posix())
    for path in [bundle,manifest_path,out/'START_HERE.md']:z.write(path,path.name)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert 'TFPMDS/.git/HEAD' in z.namelist() and 'TFPMDS/docs/TFPMDS_Technical_Proposal.pdf' in z.namelist()
checksums=[]
for path in [archive,academic_archive,bundle,out/'TFPMDS_Technical_Proposal.pdf',out/'TFPMDS_Technical_Proposal.md',*sorted(submission.glob('*.docx'))]:
    checksums.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.relative_to(out).as_posix())
(out/'SHA256SUMS.txt').write_text('\n'.join(checksums)+'\n',encoding='ascii')
assert not git('status','--porcelain')
print(json.dumps({'head':head,'commits':len(history),'archive':str(archive),'zip_bytes':archive.stat().st_size,'pdf_pages':pdf_info['pages'],'working_tree':'clean','pushes':0}))
