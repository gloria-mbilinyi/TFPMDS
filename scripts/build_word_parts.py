"""Build three native editable Word parts from the corrected report blocks.

Run with the Codex bundled Python (python-docx/Pillow). Run build_proposal.py
first to expand Markdown and preserve the original PDF split boundaries.
"""
import json
import argparse
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from docx import Document
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from PIL import Image

from proposal_layout import ROOT, WORK, FRAGMENTS, plates

TARGET=ROOT/'docs'/'submission'
TARGET.mkdir(exist_ok=True)
RECORDS=json.loads((WORK/'content.json').read_text(encoding='utf-8'))


def field(paragraph,instruction,result=''):
    run=paragraph.add_run()
    for tag,text in [('begin',None),('instruction',instruction),('separate',None)]:
        node=OxmlElement('w:instrText' if tag=='instruction' else 'w:fldChar')
        if text:node.set(qn('xml:space'),'preserve');node.text=text
        else:node.set(qn('w:fldCharType'),tag)
        run._r.append(node)
    if result:paragraph.add_run(result)
    end=OxmlElement('w:fldChar');end.set(qn('w:fldCharType'),'end');paragraph.add_run()._r.append(end)


def bookmark(paragraph,index):
    start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),str(1000+index));start.set(qn('w:name'),f'source_block_{index}')
    end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),str(1000+index))
    paragraph._p.insert(0,start);paragraph._p.append(end)


def inline(paragraph,node,bold=False,italic=False,code=False):
    if node.text:
        run=paragraph.add_run(node.text);run.bold=bold;run.italic=italic
        if code:run.font.name='Courier New';run.font.size=Pt(10)
    for child in node:
        if child.tag=='br':paragraph.add_run().add_break()
        elif child.tag=='a':
            hyperlink=OxmlElement('w:hyperlink')
            hyperlink.set(qn('r:id'),paragraph.part.relate_to(child.get('href'),RT.HYPERLINK,is_external=True))
            run=OxmlElement('w:r');text=OxmlElement('w:t');text.text=''.join(child.itertext());run.append(text);hyperlink.append(run);paragraph._p.append(hyperlink)
        else:inline(paragraph,child,bold or child.tag=='strong',italic or child.tag=='em',code or child.tag=='code')
        if child.tail:paragraph.add_run(child.tail)


def section_format(section,landscape=False):
    section.orientation=WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    section.page_width=Mm(297 if landscape else 210);section.page_height=Mm(210 if landscape else 297)
    section.top_margin=section.bottom_margin=Mm(18 if landscape else 22)
    section.left_margin=section.right_margin=Mm(18 if landscape else 22)
    section.header_distance=section.footer_distance=Mm(9)


def native_table(doc,node):
    rows=node.findall('./thead/tr')+node.findall('./tbody/tr')
    if not rows:rows=node.findall('./tr')
    cells=[list(row) for row in rows];cols=len(cells[0])
    width=261 if len(rows)>25 else 166
    weights=[12,44,63,75,67] if len(rows)>25 else [max(12,min(65,sum(len(''.join(r[c].itertext())) for r in cells)/len(cells))) for c in range(cols)]
    table=doc.add_table(rows=len(rows),cols=cols);table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
    for col,weight in zip(table.columns,weights):col.width=Mm(width*weight/sum(weights))
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        b=OxmlElement('w:'+edge);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
    table._tbl.tblPr.append(borders)
    for row_number,(row,values) in enumerate(zip(table.rows,cells)):
        trpr=row._tr.get_or_add_trPr();keep=OxmlElement('w:cantSplit');trpr.append(keep)
        if row_number==0:trpr.append(OxmlElement('w:tblHeader'))
        for col_number,(cell,value) in enumerate(zip(row.cells,values)):
            cell.width=Mm(width*weights[col_number]/sum(weights));cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr=cell._tc.get_or_add_tcPr();margins=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                item=OxmlElement('w:'+side);item.set(qn('w:w'),'85');item.set(qn('w:type'),'dxa');margins.append(item)
            pr.append(margins)
            shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'263B4A' if row_number==0 else 'F2F4F6' if row_number%2 else 'FFFFFF');pr.append(shade)
            p=cell.paragraphs[0];inline(p,value);p.paragraph_format.line_spacing=1.05;p.paragraph_format.space_after=Pt(2)
            if col_number==0 and cols>3:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.size=Pt(9 if len(rows)>25 else 10);run.bold=row_number==0
                if row_number==0:run.font.color.rgb=RGBColor(255,255,255)
    return table


def cover(doc):
    for text,style in [('Dar es Salaam Institute of Technology','Subtitle'),
                       ('Bachelor of Engineering in Computer Engineering','Subtitle'),
                       ("Tanzania Farmers' Produce Marketing and Distribution System (TFPMDS)",'Title'),
                       ('Technical Proposal and Implementation Report','Subtitle'),
                       ('Gloria Beneth Mbilinyi','Subtitle')]:
        p=doc.add_paragraph(text,style);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after=Pt(18)
    for text in ['Registration number: [To be completed]','Course or module name: [To be completed]',
                 'Lecturer or supervisor: [To be completed]','Submission date: [To be completed]']:
        p=doc.add_paragraph(text);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(10)
    for text in ['Software engineering project. Academic prototype version 1.0.0.',
                 'Prepared under the direction of gloria-mbilinyi with disclosed Codex assistance.',
                 'Implementation evidence recorded on 18 November 2026.',
                 'React / TypeScript / Tailwind CSS + FastAPI / SQLAlchemy / SQLite.',
                 'Editable UML, verified workflows, traceability and genuine Git history.',
                 'Academic scenario. Simulated mobile money and SMS. Not an official Ministry publication.']:
        p=doc.add_paragraph(text);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(6)
        for r in p.runs:r.font.size=Pt(10)
    doc.add_page_break()


def build(part):
    doc=Document();section_format(doc.sections[0])
    for name in ['Normal','Body Text','List Bullet','List Number']:
        style=doc.styles[name];style.font.name='Times New Roman';style.font.size=Pt(12)
        style.paragraph_format.line_spacing=1.5;style.paragraph_format.space_after=Pt(7)
    for name,size in [('Title',22),('Subtitle',13),('Heading 1',16),('Heading 2',13),('Caption',11),('TOC Heading',14)]:
        style=doc.styles[name];style.font.name='Times New Roman';style.font.size=Pt(size);style.font.color.rgb=RGBColor(0,0,0)
        style.paragraph_format.line_spacing=1.15;style.paragraph_format.space_before=Pt(10);style.paragraph_format.space_after=Pt(7)
    doc.styles['Title'].font.bold=True
    doc.styles['Subtitle'].font.italic=False
    # Theme attributes override explicit font names in Word. The stock template
    # also carries a blue Title border; remove both rather than trusting preview.
    for name in ['Normal','Body Text','List Bullet','List Number','Title','Subtitle','Heading 1','Heading 2','Caption','TOC Heading']:
        style=doc.styles[name]
        for node in style.element.xpath('.//w:rFonts'):
            for attribute in list(node.attrib):
                if 'theme' in attribute.lower():del node.attrib[attribute]
        for node in style.element.xpath('./w:pPr/w:pBdr | ./w:rPr/w:spacing'):
            node.getparent().remove(node)
    # Older Word-compatible native layout: inline images, no text boxes, macros,
    # embedded OLE objects, custom fonts, or external image relationships.
    settings=doc.settings.element
    update=OxmlElement('w:updateFields');update.set(qn('w:val'),'true');settings.append(update)
    doc.core_properties.title=f'TFPMDS Technical Proposal Part {part}'
    doc.core_properties.author='Gloria Beneth Mbilinyi'
    doc.core_properties.subject='Academic report with disclosed Codex assistance'
    p=doc.sections[0].header.paragraphs[0];p.text=f'TFPMDS Technical Proposal | Part {part}'
    p.style='Normal';p.paragraph_format.line_spacing=1
    for run in p.runs:run.font.size=Pt(9)
    p=doc.sections[0].footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.line_spacing=1;p.add_run(f'Part {part} | Page ');field(p,' PAGE ')
    for run in p.runs:run.font.size=Pt(9)
    if part==1:cover(doc)
    else:doc.add_paragraph(f'TFPMDS Technical Proposal Part {part}','Title')
    bounds={1:'1-10',2:'11-20',3:'21-45'}[part]
    doc.add_paragraph(f'Content from original PDF pages {bounds}. New Word pagination differs. This part opens independently; read Parts 1, 2 and 3 in order.')
    doc.add_paragraph('Contents','TOC Heading')
    toc=doc.add_paragraph();field(toc,' TOC \\o "1-2" \\h \\z \\u ')
    # Seed the field with local headings; Word replaces this result on F9.
    separate=toc._p.xpath('.//w:fldChar[@w:fldCharType="separate"]')[0]
    end=toc._p.xpath('.//w:fldChar[@w:fldCharType="end"]')[0]
    for record in [r for r in RECORDS if r['part']==part and r['tag']=='h2']:
        run=OxmlElement('w:r');text=OxmlElement('w:t');text.text=record['text']+'\n';run.append(text)
        toc._p.insert(toc._p.index(end.getparent()),run)
    doc.add_page_break()
    mode='body';images=[];block_ids=[]
    def switch(target,force=False):
        nonlocal mode
        if target!=mode:
            section_format(doc.add_section(WD_SECTION_START.NEW_PAGE),target=='landscape');mode=target
        elif force:doc.add_page_break()
    for record in [r for r in RECORDS if r['part']==part]:
        node=ET.fromstring(record['xml']);tag=node.tag;image=node.find('img') if tag=='p' else None
        first=None
        if image is not None:
            relative=image.get('src');panel_list=plates(relative)
            for panel_index,plate in enumerate(panel_list):
                switch('landscape',True)
                p=doc.add_paragraph(image.get('data-caption',image.get('alt')),'Caption');p.paragraph_format.keep_with_next=True
                if first is None:first=p
                note=plate.get('caption',f"Row {plate['row']}/{plate['rows']} | Column {plate['col']}/{plate['cols']} | Edges overlap; read left to right, then top to bottom.")
                p=doc.add_paragraph(note);p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(3);p.paragraph_format.keep_with_next=True
                for r in p.runs:r.font.size=Pt(9)
                if 'sequence-process-' in relative:
                    p=doc.add_paragraph(FRAGMENTS[int(Path(relative).stem.rsplit('-',1)[1])]);p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(3);p.paragraph_format.keep_with_next=True
                    for r in p.runs:r.font.size=Pt(9)
                with Image.open(plate['path']) as im:w,h=im.size
                factor=min(735/w,365/h)
                p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(2)
                picture=p.add_run().add_picture(plate['path'],width=Pt(w*factor),height=Pt(h*factor))
                picture._inline.docPr.set('descr',image.get('alt')+'; '+note)
                p=doc.add_paragraph('Source: '+relative+' | Editable draw.io source and complete export are included in the submission package.')
                p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(0)
                for r in p.runs:r.font.size=Pt(8)
                images.append({'block':record['index'],**plate})
        elif tag=='table':
            switch('landscape' if len(node.findall('./tbody/tr'))>25 else 'body')
            t=native_table(doc,node);first=t.cell(0,0).paragraphs[0]
            doc.add_paragraph().paragraph_format.space_after=Pt(4)
        else:
            switch('body')
            if tag in {'h2','h3','h4'}:
                first=doc.add_paragraph(style='Heading 1' if tag=='h2' else 'Heading 2');inline(first,node)
            elif tag=='p':first=doc.add_paragraph();inline(first,node)
            elif tag in {'ul','ol'}:
                for number,item in enumerate(node.findall('li'),1):
                    p=doc.add_paragraph(style='List Bullet' if tag=='ul' else 'Normal')
                    if tag=='ol':p.add_run(f'{number}. ')
                    inline(p,item)
                    if first is None:first=p
            elif tag=='pre':
                first=doc.add_paragraph(''.join(node.itertext()));first.paragraph_format.line_spacing=1
                for r in first.runs:r.font.name='Courier New';r.font.size=Pt(9)
            elif tag=='hr':first=doc.add_paragraph()
            else:raise ValueError(f'Unhandled source block: {tag}')
        bookmark(first,record['index']);block_ids.append(record['index'])
    path=TARGET/f'TFPMDS_Technical_Proposal_Part_{part}.docx'
    pending=WORK/f'part-{part}-pending.docx';doc.save(pending);pending.replace(path)
    return {'part':part,'file':str(path),'original_pdf_pages':bounds,'source_blocks':block_ids,
            'figure_panels':len(images),'figures':images,'native_tables':len(doc.tables),
            'bytes':path.stat().st_size}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parts',type=int,nargs='+',choices=[1,2,3],default=[1,2,3])
    args=parser.parse_args()
    prior=json.loads((WORK/'word-build.json').read_text(encoding='utf-8')) if (WORK/'word-build.json').exists() else []
    result=[r for r in prior if r['part'] not in args.parts]+[build(part) for part in args.parts]
    result.sort(key=lambda r:r['part'])
    (WORK/'word-build.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k not in {'figures','source_blocks'}} for r in result]))
