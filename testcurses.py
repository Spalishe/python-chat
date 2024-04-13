import curses
import math
X = 0
def main(stdscr):
    global X
    while True:
        X = X + 0.005
        stdscr.clear()
        stdscr.addstr(10,10,str(math.floor(math.sin(X)*1000)/1000))
        stdscr.refresh()

curses.wrapper(main)