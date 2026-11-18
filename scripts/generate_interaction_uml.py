from collections import defaultdict
import json
import math

from PIL import Image

from uml_canvas import Canvas, OUT, GREEN, MUTED
from uml_interactions import PARTICIPANTS, PHASES, catalogue


def sequence():
    messages=catalogue();width=2480;spacing=158;start=100;row=49
    positions={key:start+i*spacing for i,key in enumerate(PARTICIPANTS)}
    cursor=225;bounds=[]
    for phase,(title,items) in enumerate(PHASES,1):
        height=len(items)*row+115
        bounds.append((cursor,height));cursor+=height+45
    c=Canvas('sequence','Comprehensive sequence diagram',width,cursor+70)
    c.header('TFPMDS | Comprehensive UML sequence diagram','Four processes in one interaction model. Calls: solid filled arrow. Returns: dashed open arrow. Logical notifications/callbacks: open arrow.')
    for key,label in PARTICIPANTS.items():
        x=positions[key]
        c.rect(x-72,138,144,65,label,size=13,bold=True,fill='#edf3eb')
        c.line([(x,203),(x,cursor)],dashed=True,arrow='none',color='#adbbaf')
    for phase,((title,items),(top,height)) in enumerate(zip(PHASES,bounds),1):
        c.rect(30,top-8,width-60,42,f'{phase}. {title}',fill='#e5eee1',size=19,bold=True,align='left')
        for item in [m for m in messages if m['phase']==phase]:
            y=top+85+(item['index']-1)*row;x1=positions[item['source']];x2=positions[item['target']]
            if item['kind']=='call':c.rect(x2-6,y-9,12,29,fill='#d7e8d5',stroke=GREEN,size=1)
            c.line([(x1,y),(x2,y)],dashed=item['kind']=='return',arrow='block' if item['kind']=='call' else 'open',
                   color='#315e46' if item['kind']!='return' else '#7c8e80')
            label=f'{item["number"]} {item["label"]}'
            w=max(280,min(820,abs(x2-x1)-18));left=max(35,min((x1+x2-w)/2,width-w-35))
            c.rect(left,y-35,w,29,label,fill='#ffffff',stroke='#ffffff',size=12,align='center')
        # Combined fragments are transparent frames above the interaction geometry.
        fragments={
            1:[(6,9,'alt [registration valid]',8,'[registration invalid]'),(18,21,'opt [account approved]',None,'')],
            2:[(8,12,'alt [produce available] and [quantity sufficient]',11,'[stock insufficient]'),(13,18,'opt [order created]',None,''),(15,16,'alt [farmer accepts]',15,'[farmer rejects]')],
            3:[(7,9,'alt completion entry',7,'[buyer simulation path]'),(11,17,'alt [payment successful]',14,'[payment failed] / [payment cancelled]'),(18,20,'opt [payment successful] view receipt',None,'')],
            4:[(5,8,'opt [approved transporter available]',None,''),(9,17,'loop [per tracking milestone and party enquiry]',None,''),(18,25,'opt [delivery confirmed]',None,'')],
        }[phase]
        for first,last,label,separator,guard in fragments:
            y=top+85+(first-1)*row-39;h=(last-first)*row+46
            c.rect(38,y,width-76,h,label,kind='frame',fill='none',stroke='#7f9983',size=12)
            if separator:
                sy=top+85+(separator-1)*row+6
                c.line([(39,sy),(width-39,sy)],dashed=True,arrow='none',color='#9aaa9b')
                c.rect(47,sy+2,445,24,guard,fill='white',stroke='white',size=12,align='left')
    c.text(40,cursor+5,width-80,50,'Implementation note: asynchronous arrows express logical notifications. The local mock logs notifications in the same request transaction; no external SMS or queue is running.',size=14,color=MUTED)
    path=c.save();image=Image.open(path);scale=image.width/width
    previews=OUT/'previews';previews.mkdir(exist_ok=True)
    for number,(top,height) in enumerate(bounds,1):
        # Repeat lifeline heads on each readable PDF panel, preserving one canonical diagram.
        head=image.crop((0,0,image.width,round(218*scale)))
        panel=image.crop((0,round((top-10)*scale),image.width,round((top+height+10)*scale)))
        result=Image.new('RGB',(image.width,head.height+panel.height),'white');result.paste(head,(0,0));result.paste(panel,(0,head.height));result.save(previews/f'sequence-process-{number}.png',optimize=True)
    return bounds


def communication():
    width=2480;panelheight=1330;height=150+4*panelheight
    c=Canvas('communication','Corresponding communication diagram',width,height)
    c.header('TFPMDS | UML communication diagram','Same participating object identities and numbered messages as the sequence model. Four collaboration views form one diagram; link numbers refer to the complete message register on the right.')
    messages=catalogue()
    for phase,(title,items) in enumerate(PHASES,1):
        y0=155+(phase-1)*panelheight
        c.rect(30,y0,width-60,panelheight-25,f'Process {phase}: {title}',kind='frame',fill='none',size=20)
        selected=[m for m in messages if m['phase']==phase]
        names=list(dict.fromkeys([m['source'] for m in selected]+[m['target'] for m in selected]))
        # Put the interface in the center, collaborators on a ring. Identity reuse is explicit.
        points={'ui':(580,y0+600)}
        others=[n for n in names if n!='ui']
        for i,key in enumerate(others):
            angle=2*math.pi*i/max(1,len(others))-math.pi/2
            points[key]=(580+440*math.cos(angle),y0+620+450*math.sin(angle))
        pairs=defaultdict(list)
        for m in selected:pairs[(m['source'],m['target'],m['kind'])].append(m['number'])
        for index,((source,target,kind),numbers) in enumerate(pairs.items()):
            p,q=points[source],points[target]
            dx,dy=q[0]-p[0],q[1]-p[1];dist=max(1,math.hypot(dx,dy));off=(index%3-1)*12
            a=(p[0]+dx/dist*58-dy/dist*off,p[1]+dy/dist*35+dx/dist*off)
            b=(q[0]-dx/dist*58-dy/dist*off,q[1]-dy/dist*35+dx/dist*off)
            c.line([a,b],', '.join(numbers),dashed=kind=='return',arrow='block' if kind=='call' else 'open',color='#829a82',size=12)
        for key,(x,y) in points.items():c.rect(x-92,y-35,184,70,': '+PARTICIPANTS[key],fill='#edf3e9',size=14,bold=True,rounded=True)
        c.text(70,y0+1170,1040,80,'Objects repeat by process for readability; repeated labels denote the same object identity. Link labels retain the nested callback number 3.6.1. Solid/open/dashed arrows follow the sequence legend.',size=14,color=MUTED)
        c.text(1190,y0+55,1210,35,'NUMBERED MESSAGES ON THE COLLABORATION LINKS',size=15,bold=True,color=GREEN)
        for row,m in enumerate(selected):
            text=f'{m["number"]}  :{PARTICIPANTS[m["source"]]} → :{PARTICIPANTS[m["target"]]}\n{m["label"]}'
            c.rect(1190,y0+100+row*46,1210,44,text,fill='#f6f8f3' if row%2==0 else '#ffffff',stroke='#ffffff',size=12,align='left')
    path=c.save();im=Image.open(path);scale=im.width/width;previews=OUT/'previews'
    for phase in range(1,5):
        y0=155+(phase-1)*panelheight
        header=im.crop((0,0,im.width,round(145*scale)));part=im.crop((0,round(y0*scale),im.width,round((y0+panelheight)*scale)))
        result=Image.new('RGB',(im.width,header.height+part.height),'white');result.paste(header,(0,0));result.paste(part,(0,header.height));result.save(previews/f'communication-process-{phase}.png',optimize=True)


if __name__=='__main__':
    sequence();communication()
    (OUT/'interaction-catalogue.json').write_text(json.dumps({'participants':PARTICIPANTS,'messages':catalogue()},indent=2)+'\n',encoding='utf-8')
    print(f'Generated 1 sequence and 1 communication draw.io model, PNG exports and readable panels; {len(catalogue())} shared messages.')
