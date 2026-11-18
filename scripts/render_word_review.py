"""Render native Word PDF exports with the packaged DOCX PNG rasterizer.

Windows has Microsoft Word but no LibreOffice in this workspace. Each input
DOCX must first be opened, its contents updated, saved and exported by Word.
This adapter reuses the skill's rendering implementation with those actual
Word exports, rather than substituting a layout made from source text.
"""
import argparse
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--renderer',type=Path,required=True)
args=parser.parse_args()
spec=importlib.util.spec_from_file_location('packaged_renderer',args.renderer)
renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)
work=ROOT.parent/'work/proposal-compatibility'
for part in [1,2,3]:
    native=work/(f'word-Part-{part}-final.pdf' if part>1 else 'word-Part-1.pdf')
    assert native.is_file(),f'Export the final Part {part} from Microsoft Word first.'
    def native_word_export(*positional,**keywords):
        return str(native.resolve()),'Reusing the actual Microsoft Word GUI export; LibreOffice is unavailable.'
    renderer.convert_to_pdf=native_word_export
    images=renderer.rasterize(str(ROOT/f'docs/submission/TFPMDS_Technical_Proposal_Part_{part}.docx'),
                              str(work/f'word-render-{part}'),100,verbose=True,emit_pdf=False)
    print(f'Part {part}: {len(images)} native Word pages rendered to PNG.')
