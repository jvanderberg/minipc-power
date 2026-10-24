"""Put kicad-skills' kicad_sexpr package on sys.path (override the location with KICAD_SEXPR)."""
import os, sys

KICAD_SEXPR = os.environ.get('KICAD_SEXPR', os.path.expanduser('~/git/kicad-skills/skills/kicad-pcb-workflow/scripts'))
# appended, not prepended: the scripts folder also holds generic module names (schgen, netspec, board_setup, ...)
# and the project's own tools/ (sys.path[0]) must win; only kicad_sexpr is meant to come from here
if KICAD_SEXPR not in sys.path:
    sys.path.append(KICAD_SEXPR)
