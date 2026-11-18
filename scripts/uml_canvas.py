"""Author genuine mxGraph XML and rasterize its same geometry without draw.io.

This deliberately small renderer supports the shapes emitted by generate_uml.py.
The editable XML is canonical. No screenshot or Mermaid conversion is used.
"""
from pathlib import Path
import math
import textwrap
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'uml'
GREEN = '#285b43'
INK = '#243b30'
MUTED = '#68786d'


def font(size, bold=False):
    for path in [Path('C:/Windows/Fonts') / ('arialbd.ttf' if bold else 'arial.ttf'),
                 Path('/usr/share/fonts/truetype/dejavu') / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]:
        if path.exists():
            return ImageFont.truetype(str(path), int(size))
    return ImageFont.load_default(size=int(size))


class Canvas:
    def __init__(self, name, title, width, height):
        self.name, self.width, self.height = name, width, height
        self.file = ET.Element('mxfile', host='app.diagrams.net', agent='TFPMDS XML author', version='24.7.17')
        diagram = ET.SubElement(self.file, 'diagram', id=name, name=title)
        self.model = ET.SubElement(diagram, 'mxGraphModel', dx='0', dy='0', grid='1', gridSize='10',
                                   guides='1', tooltips='1', connect='1', arrows='1', fold='1', page='1',
                                   pageScale='1', pageWidth=str(width), pageHeight=str(height), math='0', shadow='0')
        self.root = ET.SubElement(self.model, 'root')
        ET.SubElement(self.root, 'mxCell', id='0')
        ET.SubElement(self.root, 'mxCell', id='1', parent='0')
        self.commands=[]
        self.counter=1
        self.nodes={}

    def identity(self):
        self.counter+=1
        return f'c{self.counter}'

    def text(self, x, y, w, h, value, *, size=16, color=INK, bold=False, align='left'):
        identity=self.identity()
        style=f'text;html=0;whiteSpace=wrap;align={align};verticalAlign=middle;fontFamily=Arial;fontSize={size};fontColor={color};'
        if bold:style+='fontStyle=1;'
        cell=ET.SubElement(self.root,'mxCell',id=identity,value=value,style=style,vertex='1',parent='1')
        ET.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
        self.commands.append(('text',x,y,w,h,value,size,color,bold,align))
        return identity

    def rect(self, x, y, w, h, text='', *, fill='#ffffff', stroke='#b8c7ba', size=16, bold=False,
             rounded=False, kind='rect', align='center', key=None):
        identity=key or self.identity()
        style=f'whiteSpace=wrap;html=0;fontFamily=Arial;fontSize={size};fontColor={INK};fillColor={fill};strokeColor={stroke};align={align};verticalAlign=middle;spacing=8;'
        if bold: style+='fontStyle=1;'
        if rounded: style+='rounded=1;arcSize=15;'
        if kind=='frame': style+='shape=umlFrame;align=left;verticalAlign=top;labelPosition=inside;'
        if kind=='ellipse': style+='ellipse;'
        if kind=='package': style+='shape=folder;tabWidth=140;tabHeight=30;'
        cell=ET.SubElement(self.root,'mxCell',id=identity,value=text,style=style,vertex='1',parent='1')
        ET.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
        self.nodes[identity]=(x,y,w,h)
        self.commands.append(('rect',x,y,w,h,text,fill,stroke,size,bold,rounded,kind,align))
        return identity

    def text(self,x,y,w,h,value,*,size=16,color=INK,bold=False,align='left'):
        identity=self.identity()
        style=f'text;html=0;whiteSpace=wrap;strokeColor=none;fillColor=none;align={align};verticalAlign=middle;fontFamily=Arial;fontSize={size};fontColor={color};'
        if bold:style+='fontStyle=1;'
        cell=ET.SubElement(self.root,'mxCell',id=identity,value=value,style=style,vertex='1',parent='1')
        ET.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
        self.commands.append(('text',x,y,w,h,value,size,color,bold,align))
        return identity

    def line(self,points,label='',*,dashed=False,arrow='block',color=GREEN,size=14,source=None,target=None,label_box=None,start_arrow=None):
        identity=self.identity()
        style=f'edgeStyle=none;html=0;rounded=0;strokeColor={color};strokeWidth=1.5;fontFamily=Arial;fontSize={size};fontColor={INK};endArrow={arrow};endFill={0 if arrow=="open" else 1};labelBackgroundColor=#ffffff;'
        if dashed:style+='dashed=1;dashPattern=5 4;'
        if start_arrow:style+=f'startArrow={start_arrow};startFill={1 if start_arrow=="diamond" else 0};'
        attrs={'id':identity,'value':label,'style':style,'edge':'1','parent':'1'}
        if source:attrs['source']=source
        if target:attrs['target']=target
        cell=ET.SubElement(self.root,'mxCell',**attrs)
        geometry=ET.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'})
        ET.SubElement(geometry,'mxPoint',x=str(points[0][0]),y=str(points[0][1]),**{'as':'sourcePoint'})
        ET.SubElement(geometry,'mxPoint',x=str(points[-1][0]),y=str(points[-1][1]),**{'as':'targetPoint'})
        if len(points)>2:
            array=ET.SubElement(geometry,'Array',**{'as':'points'})
            for x,y in points[1:-1]:ET.SubElement(array,'mxPoint',x=str(x),y=str(y))
        if label_box:
            # Keep long link labels as independent editable text next to the link.
            cell.set('value','')
            self.text(*label_box,label,size=size)
        self.commands.append(('line',points,label if not label_box else '',dashed,arrow,color,size,start_arrow))
        return identity

    def header(self,title,subtitle):
        self.text(45,24,self.width-90,44,title,size=29,bold=True,color=GREEN)
        self.text(45,75,self.width-90,50,subtitle,size=15,color=MUTED)

    def save(self):
        OUT.mkdir(parents=True,exist_ok=True)
        ET.indent(self.file,space='  ')
        ET.ElementTree(self.file).write(OUT/(self.name+'.drawio'),encoding='utf-8',xml_declaration=True)
        self.render().save(OUT/(self.name+'.png'),optimize=True)
        return OUT/(self.name+'.png')

    def render(self,scale=1.5):
        im=Image.new('RGB',(round(self.width*scale),round(self.height*scale)),'white')
        draw=ImageDraw.Draw(im)
        def xy(points):return [(round(x*scale),round(y*scale)) for x,y in points]
        def text_box(x,y,w,h,value,size,color,bold=False,align='left'):
            face=font(size*scale,bold)
            lines=[]
            for paragraph in value.split('\n'):
                words=paragraph.split(' ');line=''
                for word in words:
                    trial=(line+' '+word).strip()
                    if line and draw.textlength(trial,font=face)>w*scale-10:
                        lines.append(line);line=word
                    else:line=trial
                lines.append(line)
            line_h=round(size*scale*1.28)
            top=y*scale+max(0,(h*scale-len(lines)*line_h)/2)
            for line in lines:
                tw=draw.textlength(line,font=face)
                left=x*scale+(w*scale-tw)/2 if align=='center' else x*scale+5
                draw.text((left,top),line,font=face,fill=color)
                top+=line_h
        for command in self.commands:
            if command[0]=='rect':
                _,x,y,w,h,value,fill,stroke,size,bold,rounded,kind,align=command
                bounds=xy([(x,y),(x+w,y+h)])
                method=draw.ellipse if kind=='ellipse' else draw.rounded_rectangle if rounded else draw.rectangle
                actual_fill=None if fill=='none' else fill
                if rounded:method(bounds,radius=12*scale,fill=actual_fill,outline=stroke,width=max(1,round(scale)))
                else:method(bounds,fill=actual_fill,outline=stroke,width=max(1,round(scale)))
                if kind in {'frame','package'}:
                    tab_w=min(w-8,max(100,len(value)*size*.5))
                    draw.rectangle(xy([(x,y),(x+tab_w,y+32)]),fill='#edf3eb',outline=stroke,width=round(scale))
                    text_box(x+5,y+2,tab_w-10,28,value,size,INK,bold)
                else:text_box(x+7,y+5,w-14,h-10,value,size,INK,bold,align)
            elif command[0]=='text':
                _,x,y,w,h,value,size,color,bold,align=command
                text_box(x,y,w,h,value,size,color,bold,align)
            else:
                _,points,label,dashed,arrow,color,size,start_arrow=command
                for p,q in zip(points,points[1:]):
                    if dashed:
                        length=math.dist(p,q)
                        for at in range(0,max(1,int(length)),12):
                            end=min(at+7,length)
                            if length:draw.line(xy([(p[0]+(q[0]-p[0])*at/length,p[1]+(q[1]-p[1])*at/length),(p[0]+(q[0]-p[0])*end/length,p[1]+(q[1]-p[1])*end/length)]),fill=color,width=max(1,round(scale)))
                    else:draw.line(xy([p,q]),fill=color,width=max(1,round(1.5*scale)))
                if arrow!='none':
                    p,q=points[-2:];angle=math.atan2(q[1]-p[1],q[0]-p[0]);length=10
                    a=(q[0]-length*math.cos(angle-.45),q[1]-length*math.sin(angle-.45));b=(q[0]-length*math.cos(angle+.45),q[1]-length*math.sin(angle+.45))
                    if arrow=='open':draw.line(xy([a,q,b]),fill=color,width=max(1,round(scale)))
                    else:draw.polygon(xy([a,q,b]),fill=color)
                if start_arrow:
                    p,q=points[:2];angle=math.atan2(q[1]-p[1],q[0]-p[0]);d=14
                    corners=[p,(p[0]+d*.5*math.cos(angle+.6),p[1]+d*.5*math.sin(angle+.6)),(p[0]+d*math.cos(angle),p[1]+d*math.sin(angle)),(p[0]+d*.5*math.cos(angle-.6),p[1]+d*.5*math.sin(angle-.6))]
                    draw.polygon(xy(corners),fill=color if start_arrow=='diamond' else 'white',outline=color)
                if label:
                    p,q=points[0],points[-1];w=min(550,max(80,len(label)*size*.52));x=(p[0]+q[0])/2-w/2;y=(p[1]+q[1])/2-28
                    face=font(size*scale);tw=draw.textlength(label,font=face)
                    draw.rectangle(xy([(x-3,y-2),(x+w+3,y+23)]),fill='white')
                    text_box(x,y,w,24,label,size,INK,False,'center')
        return im
