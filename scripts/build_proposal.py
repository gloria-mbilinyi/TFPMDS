"""Typeset the editable Markdown proposal with readable large-format figures."""
from hashlib import sha1
from html import escape
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import markdown
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A1, A2, A3, A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, LongTable,
    NextPageTemplate, PageBreak, PageTemplate, Paragraph, Preformatted, Spacer, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs'
GREEN=colors.HexColor('#1d5038');INK=colors.HexColor('#293d30');MUTED=colors.HexColor('#788575')
REGULAR=Path('C:/Windows/Fonts/arial.ttf');BOLD=Path('C:/Windows/Fonts/arialbd.ttf');ITALIC=Path('C:/Windows/Fonts/ariali.ttf')
if not REGULAR.exists():
    REGULAR=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');BOLD=REGULAR.with_name('DejaVuSans-Bold.ttf');ITALIC=REGULAR.with_name('DejaVuSans-Oblique.ttf')
pdfmetrics.registerFont(TTFont('ReportSans',str(REGULAR)))
pdfmetrics.registerFont(TTFont('ReportSans-Bold',str(BOLD)))
pdfmetrics.registerFont(TTFont('ReportSans-Italic',str(ITALIC)))
pdfmetrics.registerFontFamily('ReportSans',normal='ReportSans',bold='ReportSans-Bold',italic='ReportSans-Italic',boldItalic='ReportSans-Bold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle('Body',fontName='ReportSans',fontSize=10,leading=15.3,textColor=INK,spaceAfter=10,allowWidows=0,allowOrphans=0))
styles.add(ParagraphStyle('Section',parent=styles['Body'],fontName='ReportSans-Bold',fontSize=17,leading=22,textColor=GREEN,spaceBefore=16,spaceAfter=13,keepWithNext=True))
styles.add(ParagraphStyle('Subsection',parent=styles['Body'],fontName='ReportSans-Bold',fontSize=12,leading=17,spaceBefore=12,spaceAfter=8,keepWithNext=True))
styles.add(ParagraphStyle('Small',parent=styles['Body'],fontSize=8.2,leading=12,textColor=MUTED))
styles.add(ParagraphStyle('Cell',parent=styles['Body'],fontSize=8.2,leading=11.5,spaceAfter=0,splitLongWords=True))
styles.add(ParagraphStyle('WideCell',parent=styles['Cell'],fontSize=9,leading=12.5))
styles.add(ParagraphStyle('TableHead',parent=styles['Cell'],fontName='ReportSans-Bold',textColor=colors.white))
styles.add(ParagraphStyle('FigureTitle',parent=styles['Section'],fontSize=18,leading=24,spaceBefore=0,spaceAfter=12))
styles.add(ParagraphStyle('CodeBlock',fontName='Courier',fontSize=8,leading=11,backColor=colors.HexColor('#f2f5ee'),borderPadding=9,spaceAfter=14))


class ProposalDoc(BaseDocTemplate):
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name=='Section':
            text=flowable.getPlainText();key='s-'+sha1(text.encode()).hexdigest()[:12]
            self.canv.bookmarkPage(key);self.canv.addOutlineEntry(text,key,level=0,closed=False)
            self.notify('TOCEntry',(0,text,self.page,key))


def page_header(canvas,doc):
    width,height=doc.pageTemplate.pagesize
    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#d7dfd1'))
    canvas.line(42,height-39,width-42,height-39)
    canvas.setFont('ReportSans-Bold',8);canvas.setFillColor(GREEN);canvas.drawString(44,height-29,'TFPMDS  |  TECHNICAL PROPOSAL AND IMPLEMENTATION REPORT')
    canvas.setFont('ReportSans',8);canvas.setFillColor(MUTED)
    canvas.drawString(44,27,'Academic prototype  |  Simulated payments and SMS  |  18 November 2026')
    canvas.drawRightString(width-44,27,str(doc.page));canvas.restoreState()


def cover(canvas,doc):
    width,height=A4;canvas.saveState();canvas.setFillColor(GREEN);canvas.rect(0,0,width,height,fill=1,stroke=0)
    canvas.setStrokeColor(colors.HexColor('#5c7a4f'));canvas.setLineWidth(1)
    for i in range(8):canvas.line(300+i*37,0,650+i*37,420)
    canvas.setFillColor(colors.HexColor('#b7c895'));canvas.circle(width-92,height-155,55,fill=1,stroke=0)
    canvas.setFillColor(colors.HexColor('#edf0da'));canvas.setFont('ReportSans-Bold',18);canvas.drawString(48,height-95,'TFPMDS')
    canvas.setFont('ReportSans',10);canvas.drawString(48,height-120,'COMPUTER ENGINEERING  /  SOFTWARE ENGINEERING PROJECT')
    title=Paragraph("Tanzania Farmers' Produce Marketing and Distribution System",ParagraphStyle('CoverTitle',fontName='ReportSans-Bold',fontSize=35,leading=42,textColor=colors.white))
    title.wrap(width-96,220);title.drawOn(canvas,48,height-350)
    canvas.setFont('ReportSans',16);canvas.drawString(48,height-405,'Technical proposal and implementation report')
    canvas.setFont('ReportSans',11);canvas.setFillColor(colors.HexColor('#c6d3b0'))
    for i,line in enumerate(['Working academic prototype  |  Version 1.0.0','Prepared under the direction of gloria-mbilinyi','Agent-assisted implementation by Codex','18 November 2026']):canvas.drawString(48,height-450-i*23,line)
    canvas.setStrokeColor(colors.HexColor('#64865a'));canvas.line(48,154,width-48,154)
    canvas.setFillColor(colors.HexColor('#d9e1c8'));canvas.setFont('ReportSans',9)
    canvas.drawString(48,125,'React / TypeScript / Tailwind CSS  +  FastAPI / SQLAlchemy / SQLite')
    canvas.drawString(48,105,'Editable UML, verified workflows, traceability and genuine local commits')
    canvas.setFont('ReportSans',8);canvas.drawString(48,67,'Academic scenario. No real mobile money or SMS. Not an official Ministry publication.')
    canvas.restoreState()


def inline(element):
    text=escape(element.text or '')
    for child in element:
        content=inline(child)
        if child.tag=='strong':text+='<b>'+content+'</b>'
        elif child.tag=='em':text+='<i>'+content+'</i>'
        elif child.tag=='code':text+='<font name="Courier">'+content+'</font>'
        elif child.tag=='a':text+='<a href="'+escape(child.get('href',''),quote=True)+'" color="#285b43">'+content+'</a>'
        elif child.tag=='br':text+='<br/>'
        else:text+=content
        text+=escape(child.tail or '')
    return text


def figure(story,node):
    relative=node.get('src');path=(DOCS/relative).resolve()
    assert path.is_relative_to(ROOT) and path.is_file(),f'Missing figure: {relative}'
    with PILImage.open(path) as source:width,height=source.size
    if relative.startswith('uml/previews/') or '-state.png' in relative:template='Poster'
    elif relative.startswith('uml/'):template='Diagram'
    else:template='ScreenTall' if height/width>1.1 else 'Diagram'
    switch(story,template)
    pagewidth,pageheight=SIZES[template];available_w=pagewidth-96;available_h=pageheight-205
    scale=min(available_w/width,available_h/height)
    caption=node.get('alt','Figure')
    story.append(Paragraph(escape(caption),styles['FigureTitle']))
    story.append(Spacer(1,8));story.append(Image(str(path),width=width*scale,height=height*scale))
    story.append(Spacer(1,12));story.append(Paragraph('Source: '+escape(relative)+' | Genuine generated model export or captured implementation evidence.',styles['Small']))


SIZES={'Body':A4,'Wide':landscape(A3),'Poster':landscape(A1),'Diagram':landscape(A2),'ScreenTall':A2}
layout='Body'


def switch(story,target,force=True):
    global layout
    if force or layout!=target:
        story.extend([NextPageTemplate(target),PageBreak()]);layout=target


def body(story):
    if layout!='Body':switch(story,'Body')


def table(story,node):
    raw=node.findall('./thead/tr')+node.findall('./tbody/tr')
    if not raw:raw=node.findall('./tr')
    cells=[list(row) for row in raw];columns=len(cells[0]);wide=len(cells)>25
    if wide:switch(story,'Wide')
    else:body(story)
    available=SIZES['Wide' if wide else 'Body'][0]-96
    header=[''.join(c.itertext()) for c in cells[0]]
    if wide and columns==5:weights=[34,175,270,305,310]
    elif columns==4 and header[:3]==['Module','IDs','Count']:weights=[105,75,50,270]
    else:
        weights=[]
        for col in range(columns):
            lengths=[len(''.join(row[col].itertext())) for row in cells]
            weights.append(max(8,min(70,sum(lengths)/len(lengths)+4)))
    widths=[available*w/sum(weights) for w in weights]
    data=[]
    for index,row in enumerate(cells):
        style=styles['TableHead'] if index==0 else styles['WideCell'] if wide else styles['Cell']
        data.append([Paragraph(inline(cell),style) for cell in row])
    result=LongTable(data,colWidths=widths,repeatRows=1,hAlign='LEFT',splitByRow=1)
    result.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),GREEN),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f4ec'),colors.white]),
        ('LINEBELOW',(0,0),(-1,0),.5,GREEN),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#dfe5d8')),
    ]));story.append(result);story.append(Spacer(1,13))


def blocks(story,node):
    for child in node:
        tag=child.tag
        if tag=='p':
            image=child.find('img')
            if image is not None:figure(story,image)
            else:body(story);story.append(Paragraph(inline(child),styles['Body']))
        elif tag in {'h1','h2','h3','h4'}:
            body(story);story.append(Paragraph(inline(child),styles['Section' if tag=='h2' else 'Subsection']))
        elif tag=='table':table(story,child)
        elif tag in {'ul','ol'}:
            body(story)
            for number,item in enumerate(child.findall('li'),1):
                label=f'{number}.' if tag=='ol' else '-'
                story.append(Paragraph(inline(item),styles['Body'],bulletText=label))
        elif tag=='pre':
            body(story);story.append(Preformatted(''.join(child.itertext()),styles['CodeBlock'],maxLineLength=95))
        elif tag=='blockquote':blocks(story,child)
        elif tag=='hr':body(story);story.append(Spacer(1,12))
        elif tag=='img':figure(story,child)


def build():
    global layout
    source=(DOCS/'TECHNICAL_PROPOSAL.md').read_text(encoding='utf-8')
    headings=[int(n) for n in re.findall(r'^## (\d+)\.',source,re.M)]
    assert headings==list(range(1,28)),f'Proposal sections are incomplete: {headings}'
    evidence=json.loads((DOCS/'evidence/acceptance-results.json').read_text(encoding='utf-8'))
    assert evidence['backend']['passed']==28 and evidence['frontend']['passed']==5
    assert evidence['functional_passed']==61 and evidence['functional_coverage_percent']==100
    source=source[source.index('## 1. Executive summary'):]
    matrix=(DOCS/'REQUIREMENTS_TRACEABILITY.md').read_text(encoding='utf-8').split('\n',2)[2]
    source=source.replace('<!-- INCLUDE_TRACEABILITY -->',matrix)
    source=source.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-')
    for path in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',source):assert (DOCS/path).is_file(),path
    root=ET.fromstring('<root>'+markdown.markdown(source,extensions=['tables','fenced_code'])+'</root>')
    target=DOCS/'TFPMDS_Technical_Proposal.pdf'
    doc=ProposalDoc(str(target),pagesize=A4,title='TFPMDS Technical Proposal and Implementation Report',
                    author='TFPMDS project owner - disclosed Codex assistance',subject='Academic software engineering project',
                    leftMargin=48,rightMargin=48,topMargin=56,bottomMargin=52)
    templates=[PageTemplate(id='Cover',frames=[Frame(48,52,A4[0]-96,A4[1]-108,id='cover-frame')],onPage=cover,pagesize=A4)]
    for name,size in SIZES.items():
        templates.append(PageTemplate(id=name,frames=[Frame(48,52,size[0]-96,size[1]-110,id=name+'-frame',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=page_header,pagesize=size))
    doc.addPageTemplates(templates)
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle('TOC',fontName='ReportSans',fontSize=10,leading=15,textColor=INK,leftIndent=0,firstLineIndent=0,spaceBefore=0,rightIndent=25)]
    layout='Body';story=[Spacer(1,1),NextPageTemplate('Body'),PageBreak(),Paragraph('Contents',styles['FigureTitle']),Spacer(1,12),toc,PageBreak()]
    blocks(story,root);doc.multiBuild(story)
    figure_count=len(re.findall(r"!\[",source))
    print(f'Created {target.name}: {doc.page} pages, {figure_count} genuine figure panels; 27 sections and full 61-row traceability appendix.')


if __name__=='__main__':build()
