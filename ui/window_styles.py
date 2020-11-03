import numpy as np
from ui import get_term

term = get_term()

def draw_border(pos, dim, title=None):
    pos = np.array(pos)
    dim = np.array(dim)
    width, height = dim

    # draw border
    border  = term.move_xy(pos) + "┌" + "─" * (width-2) + "┐"
    for i in range(height-2):
        border += term.move_xy(pos+(0,i+1)) + "│ "
        border += term.move_xy(pos+(width-2,i+1)) + " │"
    border += term.move_xy(pos+(0,height-1)) + "└" + "─" * (width-2) + "┘"
    print(border, flush=False)

    # set title
    if title is not None:
        print(term.move_xy(pos+(1+0,0)) + " %s " % term.bold(term.white(title)), flush=False)

def draw_border2(pos, dim, title=None):
    pos = np.array(pos)
    dim = np.array(dim)
    width, height = dim

    # draw border
    border  = term.move_xy(pos) + " " + " " * (width-2) + "│"
    for i in range(height-2):
        border += term.move_xy(pos+(0,i+1)) + "  "
        border += term.move_xy(pos+(width-2,i+1)) + " │"
    border += term.move_xy(pos+(0,height-1)) + " " + " " * (width-2) + "│"
    print(border, flush=False)

    # set title
    if title is not None:
        print(term.move_xy(pos+(1+0,0)) + " %s " % term.bold(term.white(title)), flush=False)
