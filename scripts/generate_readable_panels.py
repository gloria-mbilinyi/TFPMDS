"""Readable A4 interaction excerpts derived from the canonical 84 messages.

These are publication views, not additional assignment UML models. Canonical
draw.io sources retain the complete combined-fragment geometry and all objects.
"""
import math
from collections import defaultdict
import copy
import xml.etree.ElementTree as ET
from pathlib import Path
from uml_canvas import Canvas, GREEN, MUTED
from uml_interactions import PARTICIPANTS, catalogue
from proposal_layout import WORK, ROOT


def groups(messages):
    result=[]; current=[]; actors=set()
    for message in messages:
        added={message['source'],message['target']}
        if current and (len(current)==6 or len(actors|added)>7):
            result.append(current);current=[];actors=set()
        current.append(message);actors|=added
    if current:result.append(current)
    return result


def interaction_panels(relative):
    phase=int(Path(relative).stem.rsplit('-',1)[1])
    kind='sequence' if 'sequence-' in relative else 'communication'
    selected=[m for m in catalogue() if m['phase']==phase]
    result=[]; target=WORK/'readable';target.mkdir(parents=True,exist_ok=True)
    source_path=ROOT/'docs'/'uml'/f'{kind}.drawio'
    native=ET.parse(source_path);native_root=native.getroot()
    for page in list(native_root):
        if page.get('id','').startswith(f'a4-{kind}-{phase}-'):native_root.remove(page)
    batches=groups(selected)
    for part,messages in enumerate(batches,1):
        names=[k for k in PARTICIPANTS if any(k in (m['source'],m['target']) for m in messages)]
        c=Canvas(f'{kind}-{phase}-{part}',f'{kind} process {phase}',1380,830)
        c.header(f'TFPMDS | {messages[0]["process"]}',
                 f'{kind.title()} excerpt {part}/{len(batches)}. Same object identities and message numbers as the single canonical model.')
        if kind=='sequence':
            positions={key:100+i*1180/max(1,len(names)-1) for i,key in enumerate(names)}
            for key,x in positions.items():
                c.rect(x-83,130,166,76,PARTICIPANTS[key],size=19,bold=True,fill='#edf3eb')
                c.line([(x,206),(x,780)],dashed=True,arrow='none',color='#adbbaf')
            for row,m in enumerate(messages):
                y=265+row*88;x1=positions[m['source']];x2=positions[m['target']]
                c.rect(35,y-45,1310,40,f'{m["number"]} {m["label"]}',size=20,stroke='white',align='center')
                if m['kind']=='call':c.rect(x2-7,y-4,14,25,size=1,fill='#d7e8d5')
                c.line([(x1,y+5),(x2,y+5)],dashed=m['kind']=='return',arrow='block' if m['kind']=='call' else 'open')
        else:
            # A bounded collaboration view avoids tiny link numbers and crowded
            # all-process networks; every exact message is printed beneath it.
            points={key:(690+490*math.cos(2*math.pi*i/len(names)),
                         335+165*math.sin(2*math.pi*i/len(names))) for i,key in enumerate(names)}
            links=defaultdict(list)
            for m in messages:links[(m['source'],m['target'],m['kind'])].append(m['number'])
            for (source,destination,message_kind),numbers in links.items():
                a,b=points[source],points[destination]
                dx,dy=b[0]-a[0],b[1]-a[1];distance=max(1,math.hypot(dx,dy))
                p=(a[0]+dx/distance*100-dy/distance*12,a[1]+dy/distance*45+dx/distance*12)
                q=(b[0]-dx/distance*100-dy/distance*12,b[1]-dy/distance*45+dx/distance*12)
                c.line([p,q],', '.join(numbers),dashed=message_kind=='return',arrow='block' if message_kind=='call' else 'open',size=20)
            for key,(x,y) in points.items():c.rect(x-110,y-40,220,80,': '+PARTICIPANTS[key],size=19,bold=True,fill='#edf3eb',rounded=True)
            for row,m in enumerate(messages):
                label=f'{m["number"]}  {PARTICIPANTS[m["source"]]} -> {PARTICIPANTS[m["target"]]}: {m["label"]}'
                c.text(35,555+row*34,1310,34,label,size=18)
        c.text(35,790,1310,32,'Solid filled = call; dashed open = return; solid open = logical notification/callback. Repeated lifelines/objects retain their identity.',size=17,color=MUTED)
        path=target/f'{kind}-{phase}-{part}.png';c.render(scale=1.5).save(path,optimize=True)
        page=copy.deepcopy(c.file.find('diagram'))
        page.set('id',f'a4-{kind}-{phase}-{part}')
        page.set('name',f'A4 process {phase} excerpt {part}')
        native_root.append(page)
        result.append({'path':str(path),'row':part,'rows':len(batches),'col':1,'cols':1,
                       'source':relative,'messages':[m['number'] for m in messages],
                       'caption':f'Messages {messages[0]["number"]} to {messages[-1]["number"]}'})
    native.write(source_path,encoding='utf-8',xml_declaration=True)
    return result
