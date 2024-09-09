import pygame
import sys
from pygame.locals import *

pygame.init()

CELL_SIZE = 40
FONT = pygame.font.SysFont("Arial", 24)

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 171, 28)
YELLOW = (220, 235, 113)
GRAY = (40, 40, 40)
BLUE = (0, 0, 255)

# Cargar imágenes
WALL_IMAGE = pygame.transform.scale(pygame.image.load("wall.png"), (CELL_SIZE, CELL_SIZE))
GOAL_IMAGE = pygame.transform.scale(pygame.image.load("goal.png"), (CELL_SIZE, CELL_SIZE))
PLAYER_IMAGE = pygame.transform.scale(pygame.image.load("player.png"), (CELL_SIZE, CELL_SIZE))

class Button:
    def __init__(self, text, x, y, width, height, callback):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = GRAY
        self.callback = callback

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)
        text_surf = FONT.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Node:
    def __init__(self, state, parent, action):
        self.state = state
        self.parent = parent
        self.action = action

class StackFrontier:
    def __init__(self):
        self.frontier = []

    def add(self, node):
        self.frontier.append(node)

    def contains_state(self, state):
        return any(node.state == state for node in self.frontier)

    def empty(self):
        return len(self.frontier) == 0

    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        else:
            node = self.frontier.pop()
            return node

class QueueFrontier(StackFrontier):
    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        else:
            node = self.frontier.pop(0)
            return node

class Maze:
    def __init__(self, filename):
        with open(filename) as f:
            contents = f.read()

        if contents.count("A") != 1 or contents.count("B") != 1:
            raise Exception("El laberinto debe tener exactamente un inicio (A) y un final (B)")

        contents = contents.splitlines()
        self.height = len(contents)
        self.width = max(len(line) for line in contents)

        self.walls = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                try:
                    if contents[i][j] == "A":
                        self.start = (i, j)
                        row.append(False)
                    elif contents[i][j] == "B":
                        self.goal = (i, j)
                        row.append(False)
                    elif contents[i][j] == " ":
                        row.append(False)
                    else:
                        row.append(True)
                except IndexError:
                    row.append(False)
            self.walls.append(row)
        self.solution = None

    def neighbors(self, state):
        row, col = state
        candidates = [
            ("up", (row - 1, col)),
            ("down", (row + 1, col)),
            ("left", (row, col - 1)),
            ("right", (row, col + 1))
        ]
        result = []
        for action, (r, c) in candidates:
            if 0 <= r < self.height and 0 <= c < self.width and not self.walls[r][c]:
                result.append((action, (r, c)))
        return result

    def solve(self, algorithm="DFS"):
        start = Node(state=self.start, parent=None, action=None)
        if algorithm == "DFS":
            frontier = StackFrontier()  # Usamos una pila para DFS
        else:
            frontier = QueueFrontier()  # Usamos una cola para BFS
        
        frontier.add(start)
        self.explored = set()
        self.num_explored = 0

        while True:
            if frontier.empty():
                raise Exception("No se encontró solución")
            
            node = frontier.remove()  # DFS usa pop (último), BFS usa pop(0) (primero)
            self.num_explored += 1

            if node.state == self.goal:
                actions = []
                cells = []
                while node.parent is not None:
                    actions.append(node.action)
                    cells.append(node.state)
                    node = node.parent
                actions.reverse()
                cells.reverse()
                self.solution = (actions, cells)
                return
            
            self.explored.add(node.state)
            for action, state in self.neighbors(node.state):
                if not frontier.contains_state(state) and state not in self.explored:
                    child = Node(state=state, parent=node, action=action)
                    frontier.add(child)

def draw_maze(maze, player_pos, solution=None, show_solution=False, show_explored=False, offset_x=0, offset_y=0):
    for i, row in enumerate(maze.walls):
        for j, col in enumerate(row):
            if col:
                SCREEN.blit(WALL_IMAGE, (offset_x + j * CELL_SIZE, offset_y + i * CELL_SIZE))
            elif (i, j) == maze.start:
                pygame.draw.rect(SCREEN, RED, pygame.Rect(offset_x + j * CELL_SIZE, offset_y + i * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            elif (i, j) == maze.goal:
                SCREEN.blit(GOAL_IMAGE, (offset_x + j * CELL_SIZE, offset_y + i * CELL_SIZE))
            elif solution and show_solution and (i, j) in solution:
                pygame.draw.rect(SCREEN, YELLOW, pygame.Rect(offset_x + j * CELL_SIZE, offset_y + i * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            elif solution and show_explored and (i, j) in maze.explored:
                pygame.draw.rect(SCREEN, BLUE, pygame.Rect(offset_x + j * CELL_SIZE, offset_y + i * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            else:
                pygame.draw.rect(SCREEN, WHITE, pygame.Rect(offset_x + j * CELL_SIZE, offset_y + i * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    SCREEN.blit(PLAYER_IMAGE, (offset_x + player_pos[1] * CELL_SIZE, offset_y + player_pos[0] * CELL_SIZE))

def menu(mazes, select_maze_callback):
    global SCREEN
    SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_width, screen_height = SCREEN.get_size()

    background_image = pygame.image.load("fondo.jpg")
    background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

    buttons = []
    button_width = 200
    button_height = 50
    margin = 20
    start_y = (screen_height - (button_height + margin) * len(mazes)) // 2

    for idx, maze_file in enumerate(mazes):
        btn = Button(f"Laberinto {idx + 1}", (screen_width - button_width) // 2, start_y + idx * (button_height + margin), button_width, button_height, lambda m=idx: select_maze_callback(m))
        buttons.append(btn)

    while True:
        SCREEN.blit(background_image, (0, 0))

        title_surf = FONT.render("Selecciona un Laberinto", True, WHITE)
        title_rect = title_surf.get_rect(center=(screen_width // 2, start_y - 60))
        SCREEN.blit(title_surf, title_rect)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for btn in buttons:
                    if btn.is_clicked(pos):
                        return btn.callback()

        for btn in buttons:
            btn.draw(SCREEN)

        pygame.display.flip()

def game(mazes, maze_idx):
    global SCREEN
    if maze_idx >= len(mazes):
        print("¡Has completado todos los laberintos!")
        pygame.quit()
        sys.exit()

    maze_file = mazes[maze_idx]
    maze = Maze(maze_file)
    player_pos = maze.start
    solution = None
    show_solution = False
    show_explored = False

    maze_width = len(maze.walls[0]) * CELL_SIZE
    maze_height = len(maze.walls) * CELL_SIZE

    SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_width, screen_height = SCREEN.get_size()

    offset_x = (screen_width - maze_width) // 2
    offset_y = (screen_height - maze_height) // 2

    solve_buttons = []
    button_width = 150
    button_height = 40
    margin = 10
    solve_buttons.append(Button("Solucionar DFS", 10, screen_height - button_height - margin, button_width, button_height, lambda: solve_maze(maze, "DFS")))
    solve_buttons.append(Button("Solucionar BFS", 170, screen_height - button_height - margin, button_width, button_height, lambda: solve_maze(maze, "BFS")))

    def solve_maze(maze_instance, algorithm):
        nonlocal solution, show_solution, show_explored
        try:
            maze_instance.solve(algorithm)
            solution = maze_instance.solution[1]
            show_solution = True
            show_explored = True
        except Exception as e:
            print(e)

    running = True
    while running:
        SCREEN.fill(BLACK)
        draw_maze(maze, player_pos, solution, show_solution, show_explored, offset_x, offset_y)

        for btn in solve_buttons:
            btn.draw(SCREEN)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            if event.type == MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for btn in solve_buttons:
                    if btn.is_clicked(pos):
                        btn.callback()

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                row, col = player_pos
                new_pos = player_pos
                if event.key == K_UP:
                    new_pos = (row - 1, col)
                elif event.key == K_DOWN:
                    new_pos = (row + 1, col)
                elif event.key == K_LEFT:
                    new_pos = (row, col - 1)
                elif event.key == K_RIGHT:
                    new_pos = (row, col + 1)
                else:
                    continue

                if 0 <= new_pos[0] < maze.height and 0 <= new_pos[1] < maze.width and not maze.walls[new_pos[0]][new_pos[1]]:
                    player_pos = new_pos

                if player_pos == maze.goal:
                    print("¡Has llegado al final!")
                    running = False
                    game(mazes, maze_idx + 1)

    return

def main():
    mazes = ["laberinto.txt", "laberinto2.txt", "laberinto3.txt", "laberinto4.txt", "laberinto5.txt"]
    menu(mazes, lambda maze_idx: game(mazes, maze_idx))

if __name__ == "__main__":
    main()
    pygame.quit()
