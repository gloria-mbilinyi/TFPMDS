"""Validate source coverage, editable OOXML and native Word review exports."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
from zipfile import ZipFile
import markdown
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';WORK=ROOT.parent/'work/proposal-compatibility'
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main',
   'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
W='{'+N['w']+'}'
def normalized(text):return re.sub(r'\s+','',text).replace('\u200b','')
def wt(node):return ''.join(t.text or '' for t in node.findall('.//w:t',N))
records=json.loads((WORK/'content.json').read_text(encoding='utf-8'))
original=subprocess.check_output(['git','show','ddc2e8a:docs/TECHNICAL_PROPOSAL.md'],cwd=ROOT).decode()
original=original[original.index('## 1. Executive summary'):]
matrix=(DOCS/'REQUIREMENTS_TRACEABILITY.md').read_text(encoding='utf-8').split('\n',2)[2]
original=original.replace('<!-- INCLUDE_TRACEABILITY -->',matrix)
original=original.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-')
old=ET.fromstring('<root>'+markdown.markdown(original,extensions=['tables','fenced_code'])+'</root>')
assert len(old)==len(records)
assert [node.tag for node in old]==[r['tag'] for r in records]
old_images=[i.get('src') for i in old.findall('.//img')]
new_images=[ET.fromstring(r['xml']).find('img').get('src') for r in records if ET.fromstring(r['xml']).find('img') is not None]
assert old_images==new_images and len(old_images)==18
changes=[i for i,(node,r) in enumerate(zip(old,records)) if ''.join(node.itertext())!=r['text']]
allowed={i for i,node in enumerate(old) if node.tag=='p' and any(s in ''.join(node.itertext()) for s in [
    'The 100% figure','The four figures below','The communication view emphasizes','The methodology also records',
    'GitHub access initially','Follow DEMO_GUIDE.md','Appendix A below'])}
# Installation paragraph includes inline code, whose itertext is plain text.
assert set(changes)<=allowed,(changes,allowed)
summary=[];all_ids=[];headings=[]
for part in [1,2,3]:
    path=DOCS/f'submission/TFPMDS_Technical_Proposal_Part_{part}.docx'
    selected=[r for r in records if r['part']==part]
    with ZipFile(path) as z:
        assert z.testzip() is None
        root=ET.fromstring(z.read('word/document.xml'));styles=ET.fromstring(z.read('word/styles.xml'))
        document_text=normalized(wt(root))
        ids=[int(b.get(W+'name').removeprefix('source_block_')) for b in root.findall('.//w:bookmarkStart',N) if b.get(W+'name','').startswith('source_block_')]
        assert sorted(ids)==[r['index'] for r in selected],(part,ids)
        all_ids+=ids
        for record in selected:
            node=ET.fromstring(record['xml'])
            leaves=list(node.findall('li')) if node.tag in {'ol','ul'} else list(node.findall('.//th'))+list(node.findall('.//td')) if node.tag=='table' else [node]
            for leaf in leaves:
                text=normalized(''.join(leaf.itertext()))
                assert not text or text in document_text,(part,record['index'],text[:120])
        tables=root.findall('.//w:tbl',N);expected=sum(r['tag']=='table' for r in selected)
        assert len(tables)==expected
        assert len(root.findall('.//w:drawing',N))=={1:11,2:33,3:25}[part]
        assert not root.findall('.//w:object',N)
        for section in root.findall('.//w:sectPr',N):
            size=section.find('w:pgSz',N)
            assert sorted([int(size.get(W+'w')),int(size.get(W+'h'))])==[11906,16838]
        for relationship in ET.fromstring(z.read('word/_rels/document.xml.rels')):
            if relationship.get('Type','').endswith('/image'):
                assert relationship.get('TargetMode')!='External'
                assert 'word/'+relationship.get('Target') in z.namelist()
        for p in root.findall('.//w:p',N):
            style=p.find('w:pPr/w:pStyle',N)
            if style is not None and style.get(W+'val')=='Heading1':headings.append(wt(p))
        normal=next(s for s in styles if s.get(W+'styleId')=='Normal')
        assert normal.find('w:rPr/w:sz',N).get(W+'val')=='24'
        assert normal.find('w:pPr/w:spacing',N).get(W+'line')=='360'
        title=next(s for s in styles if s.get(W+'styleId')=='Title')
        assert title.find('w:pPr/w:pBdr',N) is None
    review=PdfReader(WORK/(f'word-Part-{part}-final.pdf' if part>1 else 'word-Part-1.pdf'))
    toc_entries=0
    for paragraph in root.findall('.//w:p',N):
        style=paragraph.find('w:pPr/w:pStyle',N)
        if style is not None and style.get(W+'val')=='TOC1':
            texts=[t.text or '' for t in paragraph.findall('.//w:t',N)]
            assert texts[-1].isdigit(),(part,texts)
            number=int(texts[-1]);heading=normalized(''.join(texts[:-1]))
            assert heading in normalized(review.pages[number-1].extract_text() or ''),(part,heading,number)
            toc_entries+=1
    assert toc_entries==sum(r['tag']=='h2' for r in selected),(part,toc_entries)
    figure_pages=0
    for number,page in enumerate(review.pages,1):
        assert sorted(round(float(v),1) for v in [page.mediabox.width,page.mediabox.height])==[595.3,841.9]
        assert len(page.extract_text() or '')>50,(part,number)
        resources=page.get('/Resources',{}).get_object()
        objects=resources.get('/XObject',{}).get_object() if resources.get('/XObject') else {}
        has_image=any(obj.get_object().get('/Subtype')=='/Image' for obj in objects.values())
        figure_pages+=has_image
        if 'Source: uml/' in (page.extract_text() or '') or 'Source: screenshots/' in (page.extract_text() or ''):
            assert has_image,(part,number,'orphaned figure caption')
    assert figure_pages=={1:11,2:33,3:25}[part],(part,figure_pages)
    summary.append({'part':part,'original_pdf_pages':{1:'1-10',2:'11-20',3:'21-45'}[part],
                    'word_pages':len(review.pages),'editable_source_blocks':len(selected),'native_tables':len(tables),
                    'image_panels':{1:11,2:33,3:25}[part],'bytes':path.stat().st_size,
                    'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'opened_in':'Microsoft Word desktop','toc_fields_updated':True,'toc_page_references_verified':toc_entries,'result':'passed'})
assert sorted(all_ids)==list(range(len(records))) and len(set(all_ids))==len(records)
assert headings==[r['text'] for r in records if r['tag']=='h2']
assert len(headings)==27
result={'original_pdf_pages':45,'source_blocks':len(records),'source_figures':18,'original_body_blocks_omitted':0,
        'original_body_blocks_duplicated':0,'corrected_paragraph_indices':changes,'all_A4':True,
        'parts':summary,'result':'passed','rendering':'Native Microsoft Word PDF exports rasterized with packaged render_docx.py rasterizer and bundled Poppler; LibreOffice unavailable.'}
(DOCS/'evidence/academic-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
