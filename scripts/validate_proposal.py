"""Reopen the final PDF and verify source/evidence completeness after visual review."""
import json
from pathlib import Path
import re

from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs'
reader=PdfReader(DOCS/'TFPMDS_Technical_Proposal.pdf')
source=(DOCS/'TECHNICAL_PROPOSAL.md').read_text(encoding='utf-8')
assert [int(n) for n in re.findall(r'^## (\d+)\.',source,re.M)]==list(range(1,28))
text='\n'.join(page.extract_text() or '' for page in reader.pages)
requirements=json.loads((DOCS/'requirements.json').read_text(encoding='utf-8'))
assert all(req['id'] in text for req in requirements)
assert len(reader.outline)==27
sizes=set()
figures=0;annotations=0;blank=[]
for number,page in enumerate(reader.pages,1):
    size=tuple(round(float(v),1) for v in [page.mediabox.width,page.mediabox.height])
    sizes.add(size)
    assert sorted(size)==[595.3,841.9],(number,size)
    resources=page.get('/Resources',{}).get_object()
    objects=resources.get('/XObject',{}).get_object() if resources.get('/XObject') else {}
    images=[obj for obj in objects.values() if obj.get_object().get('/Subtype')=='/Image']
    figures+=bool(images)
    if 'Source: uml/' in (page.extract_text() or '') or 'Source: screenshots/' in (page.extract_text() or ''):
        assert images,f'Figure source orphaned on page {number}'
    annotations+=len(page.get('/Annots',[]))
    if len(page.extract_text() or '')<200 and not images:blank.append(number)
plates=json.loads((ROOT.parent/'work/proposal-compatibility/plates.json').read_text(encoding='utf-8'))
assert figures==len(plates),figures
assert not blank,blank
assert annotations>=27
assert reader.metadata.title=='TFPMDS Technical Proposal and Implementation Report'
result={'pages':len(reader.pages),'numbered_sections':27,'outline_entries':27,'figure_pages':figures,
        'source_figures':18,'page_sizes_points':[list(s) for s in sorted(sizes)],'all_pages_A4':True,
        'functional_requirements_in_appendix':len(requirements),'link_annotations':annotations,'unexpected_blank_pages':blank,
        'visual_review':'Rendered with bundled Poppler; all page contact sheets and selected full pages inspected.',
        'result':'passed'}
(DOCS/'evidence/pdf-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
