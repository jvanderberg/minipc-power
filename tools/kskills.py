"""Put kicad-skills' kicad_sexpr package on sys.path (override the location with KICAD_SEXPR)."""
import os, sys

KICAD_SEXPR = os.environ.get('KICAD_SEXPR', os.path.expanduser('~/git/kicad-skills/skills/kicad-pcb-workflow/scripts'))
if KICAD_SEXPR not in sys.path:
    sys.path.insert(0, KICAD_SEXPR)
