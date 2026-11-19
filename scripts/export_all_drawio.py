"""Package the existing, editor-verified TFPMDS UML sources without redrawing.

The exported XML/PNGs are exact copies. Draw.io opening evidence is reused only
when the source SHA256 matches the exact bytes observed in that editor check.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/'docs/uml'
NAME='TFPMDS_ALL_DRAWIO_DIAGRAMS'
FILES=[
    ('sequence','01_Sequence_Diagram'),
    ('communication','02_Communication_Diagram'),
    ('purchase-order-state','03_Purchase_Order_State_Machine'),
    ('shipment-state','04_Shipment_State_Machine'),
    ('package-overview','05_Overview_Package_Diagram'),
    ('classes-identity-produce','06_Identity_Produce_Package_Classes'),
    ('classes-orders-payments','07_Orders_Payments_Package_Classes'),
    ('classes-logistics-notifications','08_Logistics_Notifications_Package_Classes'),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()


def inspect_xml(path):
    root=ET.parse(path).getroot()
    assert root.tag=='mxfile'
    pages=root.findall('diagram')
    assert pages
    result=[]
    for page in pages:
        model=page.find('mxGraphModel')
        assert model is not None, 'Expected genuine uncompressed editable mxGraph XML.'
        cells=model.findall('./root/mxCell')
        ids=[cell.get('id') for cell in cells]
        assert len(ids)==len(set(ids)) and {'0','1'}<=set(ids)
        vertices=[c for c in cells if c.get('vertex')=='1']
        edges=[c for c in cells if c.get('edge')=='1']
        assert vertices and edges
        fonts=[]
        for cell in cells:
            for reference in ['source','target','parent']:
                if cell.get(reference):assert cell.get(reference) in ids
            style=cell.get('style','')
            assert 'image=' not in style and not style.startswith('image;'), 'Flattened image cell found.'
            if cell.get('value'):
                match=re.search(r'fontSize=([0-9.]+)',style)
                if match:fonts.append(float(match[1]))
            if cell.get('edge')=='1':
                geometry=cell.find('mxGeometry');assert geometry is not None
                for end,point in [('source','sourcePoint'),('target','targetPoint')]:
                    assert cell.get(end) or geometry.find(f"mxPoint[@as='{point}']") is not None
        result.append({'name':page.get('name'),'shapes':len(vertices),'connectors':len(edges),
                       'text_labels':sum(bool(c.get('value')) for c in cells),
                       'minimum_explicit_label_font_size':min(fonts) if fonts else None})
    return result


def copy_preserving_user_edits(source,destination):
    if destination.exists():
        assert digest(source)==digest(destination),f'Refusing to overwrite a changed export: {destination}'
    else:shutil.copy2(source,destination)
    assert digest(source)==digest(destination)


def export(output_dir):
    # This includes the shared messages, guards, states, domain transition graph
    # and dependency checks used by the technical proposal.
    subprocess.run([__import__('sys').executable,str(ROOT/'scripts/validate_uml.py')],check=True,cwd=ROOT)
    folder=output_dir/NAME;previews=folder/'PNG_PREVIEWS'
    previews.mkdir(parents=True,exist_ok=True)
    evidence_path=ROOT/'docs/evidence/uml-editor-verification.json'
    editor=json.loads(evidence_path.read_text(encoding='utf-8'))
    checks={item['file']:item for item in editor['models']}
    records=[]
    for source_name,export_name in FILES:
        source=SOURCES/f'{source_name}.drawio'
        png=SOURCES/f'{source_name}.png'
        check=checks[source.name]
        assert digest(source)==check['sha256'],f'Editor evidence is stale for {source.name}; reopen it in draw.io.'
        assert check['drawio_editor_open_check']=='passed'
        pages=inspect_xml(source)
        assert len(pages)==check['editable_pages']
        assert pages[0]['shapes']==check['primary_shapes']
        assert pages[0]['connectors']==check['primary_connectors']
        with Image.open(png) as image:
            assert image.format=='PNG' and image.width>=3000
            size=image.size;image.verify()
        destination=folder/f'{export_name}.drawio'
        preview=previews/f'{export_name}.png'
        copy_preserving_user_edits(source,destination)
        copy_preserving_user_edits(png,preview)
        assert inspect_xml(destination)==pages
        records.append({'file':destination.name,'project_source':'docs/uml/'+source.name,
                        'XML_sha256':digest(destination),'PNG':'PNG_PREVIEWS/'+preview.name,
                        'PNG_sha256':digest(preview),'PNG_pixels':size,'editable_pages':len(pages),
                        'pages':pages,'source_copy':'byte-identical','independent_document':True,
                        'drawio_open_verification':'Passed editor check for these exact contents; SHA256 reconfirmed during this export.'})
    assert len(list(folder.glob('*.drawio')))==8
    assert len(list(previews.glob('*.png')))==8
    # Stable primary views are the requested eight diagrams. The two interaction
    # files also retain the same additional editable A4 publication pages.
    catalogue=json.loads((SOURCES/'interaction-catalogue.json').read_text(encoding='utf-8'))
    for source_name,_ in FILES[:2]:
        root=ET.parse(SOURCES/f'{source_name}.drawio').getroot()
        values='\n'.join(c.get('value','') for c in root.find('diagram').findall('.//mxCell'))
        assert all(m['number'] in values and m['label'] in values for m in catalogue['messages'])
        assert all(label in values for label in catalogue['participants'].values())
    (folder/'DRAWIO_EDITOR_VERIFICATION.json').write_bytes(evidence_path.read_bytes())
    instructions='''TFPMDS ALL EDITABLE DRAW.IO DIAGRAMS

Open https://app.diagrams.net/ in your browser, or use the draw.io desktop app.
Choose File > Open from > Device, then select any numbered .drawio file.
If the startup screen asks where to store files, choose Device.

Each .drawio file is a complete independent XML document with editable shapes,
connectors and labels. Drag shapes to move them. Double-click a label to edit
its text. Use File > Save / Save as to retain your own modified copy.

Files 01 and 02 contain 17 editable pages each. The first tab is the complete
comprehensive diagram; the other tabs contain larger A4 process excerpts.
Files 03 through 08 have one primary diagram page each.

PNG_PREVIEWS contains eight high-resolution images of the complete primary
diagram pages. PNGs are previews; edit the .drawio files. The additional A4
excerpts are preserved as editable native pages inside files 01 and 02.

The XML and PNG files are unchanged copies of the existing TFPMDS project
sources/exports, under the requested numbered names. Existing PNG previews were
generated from the authored diagram geometry. The exact XML contents already
passed draw.io web editor opening checks; this export reconfirms those hashes,
validates every page, checks source content and verifies the ZIP. The editor
check is recorded in DRAWIO_EDITOR_VERIFICATION.json; it is not presented as a
new UI session. VERIFICATION_REPORT.json contains the export checks and mapping.

All original messages, guards, states, class relationships and source pages are
preserved. These models match the technical proposal and implemented system.
Payments and SMS in the project remain simulations. No GitHub push was made.
'''
    (folder/'README_OPEN_IN_DRAWIO.txt').write_text(instructions,encoding='utf-8')
    manifest={'verified_at_EAT':datetime.now(timezone(timedelta(hours=3))).isoformat(),
              'project_revision':git('rev-parse','HEAD'),'editable_diagrams':8,'PNG_previews':8,
              'messages_in_each_interaction_model':len(catalogue['messages']),
              'participants_in_each_interaction_model':len(catalogue['participants']),
              'editor_verification_basis':'Existing observed draw.io editor openings of the exact same XML bytes, reconfirmed by SHA256. No unnecessary diagram recreation.',
              'all_pages_have_native_shapes_and_connectors':True,'all_source_content_preserved':True,
              'files':records,'result':'passed','pushes':0}
    (folder/'VERIFICATION_REPORT.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    checksums=[]
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name!='SHA256SUMS.txt':
            checksums.append(digest(path)+'  '+path.relative_to(folder).as_posix())
    (folder/'SHA256SUMS.txt').write_text('\n'.join(checksums)+'\n',encoding='ascii')
    archive=output_dir/(NAME+'.zip');pending=archive.with_suffix('.pending.zip')
    with zipfile.ZipFile(pending,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in sorted(folder.rglob('*')):
            if path.is_file():z.write(path,path.relative_to(output_dir).as_posix())
    with zipfile.ZipFile(pending) as z:
        assert z.testzip() is None
        expected={str(p.relative_to(output_dir)).replace('\\','/') for p in folder.rglob('*') if p.is_file()}
        assert set(z.namelist())==expected
        assert sum(name.endswith('.drawio') for name in z.namelist())==8
        assert sum(name.endswith('.png') for name in z.namelist())==8
        for path in folder.rglob('*'):
            if path.is_file():
                assert hashlib.sha256(z.read(path.relative_to(output_dir).as_posix())).hexdigest()==digest(path)
    pending.replace(archive)
    print(json.dumps({'folder':str(folder),'ZIP':str(archive),'ZIP_bytes':archive.stat().st_size,
                      'editable_diagrams':8,'high_resolution_PNGs':8,'XML_pages_validated':sum(r['editable_pages'] for r in records),
                      'editor_verified_content_hashes':'8/8 matched','ZIP_integrity':'passed','pushes':0}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT.parent/'outputs')
    args=parser.parse_args();export(args.output_dir.resolve())
