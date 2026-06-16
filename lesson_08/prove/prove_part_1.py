"""
Course: CSE 251 
Assignment: 08 Prove Part 1
File:   prove_part_1.py
Author: <Add name here>

Purpose: Part 1 of assignment 8, finding the path to the end of a maze using recursion.

Instructions:

- Do not create classes for this assignment, just functions.
- Do not use any other Python modules other than the ones included.
- Complete any TODO comments.
"""

import math
from screen import Screen
from maze import Maze
import cv2
import sys

# Include cse 351 files
from cse351 import *

SCREEN_SIZE = 800
COLOR = (0, 0, 255)
SLOW_SPEED = 100
FAST_SPEED = 1
speed = FAST_SPEED

def solve(maze, current_path, x, y):
    current_path.append((x,y))
    maze.move(x, y, COLOR)

    if maze.at_end(x,y):
        return current_path
    
    open_moves = maze.get_possible_moves(x,y)

    for move in open_moves:
        next_x = move[0]
        next_y = move[1]
        
        paths = solve(maze,current_path,next_x, next_y)

        if paths is not None:
            return paths

    current_path.pop()
    maze.restore(x,y)
    return None

def solve_path(maze):

    path = []
    
    start_position = maze.get_start_pos()
    
    
    solve(maze, path, start_position[0], start_position[1])

    return path


def get_path(log, filename):
    """ Do not change this function """
    # 'Maze: Press "q" to quit, "1" slow drawing, "2" faster drawing, "p" to play again'
    global speed

    # create a Screen Object that will contain all of the drawing commands
    screen = Screen(SCREEN_SIZE, SCREEN_SIZE)
    screen.background((255, 255, 0))

    maze = Maze(screen, SCREEN_SIZE, SCREEN_SIZE, filename)

    path = solve_path(maze)

    log.write(f'Drawing commands to solve = {screen.get_command_count()}')

    done = False
    while not done:
        if screen.play_commands(speed): 
            key = cv2.waitKey(0)
            if key == ord('1'):
                speed = SLOW_SPEED
            elif key == ord('2'):
                speed = FAST_SPEED
            elif key == ord('q'):
                exit()
            elif key != ord('p'):
                done = True
        else:
            done = True

    return path


def find_paths(log):
    """ Do not change this function """

    files = (
        'very-small.bmp',
        'very-small-loops.bmp',
        'small.bmp',
        'small-loops.bmp',
        'small-odd.bmp',
        'small-open.bmp',
        'large.bmp',
        'large-loops.bmp',
        'large-squares.bmp',
        'large-open.bmp'
    )

    log.write('*' * 40)
    log.write('Part 1')
    for filename in files:
        filename = f'./mazes/{filename}'
        log.write()
        log.write(f'File: {filename}')
        path = get_path(log, filename)
        log.write(f'Found path has length     = {len(path)}')
    log.write('*' * 40)


def main():
    """ Do not change this function """
    sys.setrecursionlimit(5000)
    log = Log(show_terminal=True)
    find_paths(log)


if __name__ == "__main__":
    main()