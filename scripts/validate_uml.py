"""Validate genuine editable XML, shared interactions and implementation contracts."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.domain import ORDER_STATES, SHIPMENT_TRANSITIONS

OUT=ROOT/'docs'/'uml'
expected={'sequence','communication','purchase-order-state','shipment-state','package-overview',
          'classes-identity-produce','classes-orders-payments','classes-logistics-notifications'}
assert {p.stem for p in OUT.glob('*.drawio')}==expected
documents={}
for name in sorted(expected):
    root=ET.parse(OUT/(name+'.drawio')).getroot()
    assert root.tag=='mxfile' and len(root.findall('diagram'))==1
    cells=root.findall('.//mxCell');ids=[cell.get('id') for cell in cells]
    assert len(ids)==len(set(ids)),f'Duplicate cell IDs in {name}'
    assert any(cell.get('edge')=='1' for cell in cells)
    for cell in cells:
        for endpoint in ['source','target']:
            if cell.get(endpoint):assert cell.get(endpoint) in ids
    im=Image.open(OUT/(name+'.png'));im.verify()
    documents[name]=root
catalogue=json.loads((OUT/'interaction-catalogue.json').read_text(encoding='utf-8'))
assert len(catalogue['participants'])==15
assert len(catalogue['messages'])==84
for name in ['sequence','communication']:
    values='\n'.join(cell.get('value','') for cell in documents[name].findall('.//mxCell'))
    for message in catalogue['messages']:
        assert message['number'] in values and message['label'] in values,(name,message['number'])
    for participant in catalogue['participants'].values():assert participant in values
for guard in ['registration valid','registration invalid','account approved','produce available','quantity sufficient',
              'farmer accepts','farmer rejects','payment successful','payment failed','transporter assigned','delivery confirmed']:
    assert f'[{guard}]' in (OUT/'sequence.drawio').read_text(encoding='utf-8')
for name,states in [('purchase-order-state',ORDER_STATES),('shipment-state',SHIPMENT_TRANSITIONS)]:
    root=documents[name];ids={cell.get('id') for cell in root.findall('.//mxCell')}
    assert all('state_'+state in ids for state in states)
    assert 'initial' in ids and any(identity.startswith('final') for identity in ids)
shipment_edges={(cell.get('source','').removeprefix('state_'),cell.get('target','').removeprefix('state_'))
                for cell in documents['shipment-state'].findall('.//mxCell') if cell.get('edge')=='1'}
for state,destinations in SHIPMENT_TRANSITIONS.items():
    for destination in destinations:assert (state,destination) in shipment_edges
dependencies=json.loads((OUT/'package-dependencies.json').read_text(encoding='utf-8'))
def visit(node,path):
    assert node not in path,f'Circular package dependency: {path+[node]}'
    for child in dependencies.get(node,[]):visit(child,path+[node])
for node in dependencies:visit(node,[])
print('PASS: 8 editable draw.io files; 8 PNGs; 84 matching messages; all required guards; exact shipment graph; acyclic package dependencies.')
