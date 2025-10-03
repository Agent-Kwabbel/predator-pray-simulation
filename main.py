import pygame
import random
import math
import matplotlib.pyplot as plt
from pygame.math import Vector2

# Constanten: kun je veranderen om het leuker te maken
WIDTH, HEIGHT = 1800, 1200
MOB_SIZE = 5
NUM_MOBS = 500
BASE_SPEED = 2
SPEED_DEVIATION = 1/2
TURN_ANGLE = 0.5
SIGHT_RANGE = 125
INTERACTION_RADIUS = SIGHT_RANGE
GRID_FACTOR = 5
GRID_SIZE = SIGHT_RANGE / GRID_FACTOR
MIN_AGE = 3000
MAX_AGE = 9000
BASE_HUNGER = 3000
HUNGER_DEVIATION = 0.20
FONT_SIZE = 12

team_counts = {1: [], 2: [], 3: []}
time_steps = []

# De kleurtjes
COLORS = {1: (255, 0, 0), 2: (0, 255, 0), 3: (0, 0, 255)}
RELATIONS = {1: 2, 2: 3, 3: 1}
RELATION_COLORS = {
    (1, 2): (100, 255, 100), (2, 3): (100, 255, 100), (3, 1): (100, 255, 100),  # Predator colors
    (2, 1): (255, 0, 0), (3, 2): (255, 0, 0), (1, 3): (255, 0, 0)  # Prey colors
}

# Init van de PyGame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, FONT_SIZE)

show_grid = False
def draw_grid():
    for x in range(0, WIDTH, int(GRID_SIZE)):
        pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, int(GRID_SIZE)):
        pygame.draw.line(screen, (50, 50, 50), (0, y), (WIDTH, y))

def highlight_grid_box(mob):
    cell_x = int(mob.pos.x // GRID_SIZE) * GRID_SIZE
    cell_y = int(mob.pos.y // GRID_SIZE) * GRID_SIZE
    pygame.draw.rect(screen, (255, 255, 0), (cell_x, cell_y, GRID_SIZE, GRID_SIZE), 2)

def highlight_checked_grid_boxes(mob):
    mob_cell_x, mob_cell_y = int(mob.pos.x // GRID_SIZE), int(mob.pos.y // GRID_SIZE)
    min_x = (mob_cell_x - GRID_FACTOR - 1) * GRID_SIZE
    min_y = (mob_cell_y - GRID_FACTOR - 1) * GRID_SIZE
    max_x = (mob_cell_x + GRID_FACTOR + 2) * GRID_SIZE
    max_y = (mob_cell_y + GRID_FACTOR + 2) * GRID_SIZE

    min_x = max(0, min_x // GRID_SIZE * GRID_SIZE)
    min_y = max(0, min_y // GRID_SIZE * GRID_SIZE)
    max_x = min(WIDTH, (max_x // GRID_SIZE) * GRID_SIZE)
    max_y = min(HEIGHT, (max_y // GRID_SIZE) * GRID_SIZE)

    pygame.draw.rect(screen, (0, 255, 255), (min_x, min_y, max_x - min_x, max_y - min_y), 2)


class Mob:
    def __init__(self, x=None, y=None):
        self.pos = Vector2(
            x if x is not None else random.randint(0, WIDTH),
            y if y is not None else random.randint(0, HEIGHT)
        )
        self.type = random.choice([1, 2, 3])
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = BASE_SPEED * random.uniform(1 - SPEED_DEVIATION, 1 + SPEED_DEVIATION)
        self.alive = True
        self.age = random.randint(MIN_AGE, MAX_AGE)
        self.hunger = round(BASE_HUNGER * random.uniform(1 - HUNGER_DEVIATION, 1 + HUNGER_DEVIATION))

    def move(self, mobs_in_range):
        attackers = []
        closest_prey = None
        closest_prey_dist = float('inf')

        # Kijkt naar andere mobs in de buurt
        for other in mobs_in_range:
            if other is self or not other.alive:
                continue
            afstand = self.toroidal_distance_squared(other)
            if afstand < SIGHT_RANGE ** 2:
                if RELATIONS[self.type] == other.type and afstand < closest_prey_dist:
                    closest_prey = other
                    closest_prey_dist = afstand
                elif RELATIONS[other.type] == self.type:
                    attackers.append((afstand, other))

        if attackers:
            flee_vector = Vector2(0, 0)
            if len(attackers) == 1:
                afstand, attacker = attackers[0]
                flee_vector = -self.toroidal_vector(attacker).normalize()
            else:
                for afstand, attacker in attackers:
                    vec_from_attacker = self.toroidal_vector(attacker)
                    if afstand > 0:
                        flee_vector -= vec_from_attacker / afstand

            if flee_vector.length_squared() > 0:
                self.angle = math.atan2(flee_vector.y, flee_vector.x)
        elif closest_prey:
            vec_to_prey = self.toroidal_vector(closest_prey)
            self.angle = math.atan2(vec_to_prey.y, vec_to_prey.x)
        else:
            self.angle += random.uniform(-TURN_ANGLE, TURN_ANGLE)

        # Positie updaten
        self.pos.x = (self.pos.x + math.cos(self.angle) * self.speed) % WIDTH
        self.pos.y = (self.pos.y + math.sin(self.angle) * self.speed) % HEIGHT

    # Toroidal is dus blijkbaar een "soort 2D wereld met wrapping om de randen".
    def toroidal_distance_squared(self, other): # Dit is sneller, anders moet je wortelberekeningen gebruiken :)
        dx = min(abs(self.pos.x - other.pos.x), WIDTH - abs(self.pos.x - other.pos.x))
        dy = min(abs(self.pos.y - other.pos.y), HEIGHT - abs(self.pos.y - other.pos.y))
        return dx * dx + dy * dy

    def toroidal_vector(self, other):
        dx = other.pos.x - self.pos.x
        dy = other.pos.y - self.pos.y
        if abs(dx) > WIDTH / 2:
            dx -= math.copysign(WIDTH, dx)
        if abs(dy) > HEIGHT / 2:
            dy -= math.copysign(HEIGHT, dy)
        return Vector2(dx, dy)

    def draw(self):
        if self.alive:
            pygame.draw.circle(screen, COLORS[self.type], (int(self.pos.x), int(self.pos.y)), MOB_SIZE)

    def draw_info(self):
        text = font.render(f'Age: {self.age}, Hunger: {self.hunger}', True, (255, 255, 255))
        screen.blit(text, (self.pos.x + 10, self.pos.y - 10))

class SpatialHash:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.grid = {}

    def insert(self, mob):
        key = self.get_cell(mob.pos)
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(mob)

    def get_nearby(self, mob):
        x, y = self.get_cell(mob.pos)
        nearby = []
        for dx in range(-GRID_FACTOR - 1, GRID_FACTOR + 1):
            for dy in range(-GRID_FACTOR - 1, GRID_FACTOR + 1):
                nearby.extend(self.grid.get((x + dx, y + dy), []))
        return nearby

    def clear(self):
        self.grid.clear()

    def get_cell(self, pos):
        return int(pos.x // self.cell_size), int(pos.y // self.cell_size)

# Initialize mobs
mobs = [Mob() for _ in range(NUM_MOBS)]
selected_mob = None
spatial_hash = SpatialHash(GRID_SIZE)

time_step = 0

running = True
while running:
    screen.fill((0, 0, 0))
    mouse_x, mouse_y = pygame.mouse.get_pos()

    spatial_hash.clear()
    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check voor mob selectie
            for mob in mobs:
                if mob.toroidal_distance_squared(Mob(mouse_x, mouse_y)) < (MOB_SIZE * 2) ** 2:
                    selected_mob = mob
                    break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                show_grid = not show_grid

    alive_counts = {1: 0, 2: 0, 3: 0}

    # Update mobs
    for mob in mobs:
        if mob.alive:
            spatial_hash.insert(mob)
            mob.move(spatial_hash.get_nearby(mob))
            mob.age -= 1
            mob.hunger -= 1
            if mob.age <= 0 or mob.hunger <= 0:
                mob.alive = False
            else:
                mob.draw()
                alive_counts[mob.type] += 1

    alive_mobs = [mob for mob in mobs if mob.alive]
    n = len(alive_mobs)
    for i in range(n):
        for j in range(i + 1, n):
            mob_i = alive_mobs[i]
            mob_j = alive_mobs[j]
            if mob_i.toroidal_distance_squared(mob_j) < (MOB_SIZE * 2) ** 2:
                if RELATIONS[mob_i.type] == mob_j.type:
                    mob_j.type = mob_i.type
                    new_mob = Mob(mob_i.pos.x + random.random(), mob_i.pos.y + random.random())
                    new_mob.type = mob_i.type
                    mob_i.hunger = round(BASE_HUNGER * random.uniform(1 - HUNGER_DEVIATION, 1 + HUNGER_DEVIATION))
                elif RELATIONS[mob_j.type] == mob_i.type:
                    mob_i.type = mob_j.type
                    new_mob = Mob(mob_j.pos.x + random.random(), mob_j.pos.y + random.random())
                    new_mob.type = mob_j.type
                    mob_j.hunger = round(BASE_HUNGER * random.uniform(1 - HUNGER_DEVIATION, 1 + HUNGER_DEVIATION))

    if show_grid:
        draw_grid()

    # Mob selectie etc.
    if selected_mob and selected_mob.alive:
        selected_mob.draw_info()
        for other in mobs:
            if other.alive and selected_mob != other:
                dist = selected_mob.toroidal_distance_squared(other)
                if dist < INTERACTION_RADIUS ** 2:
                    relation_color = RELATION_COLORS.get((selected_mob.type, other.type), (200, 200, 200))
                    vec = selected_mob.toroidal_vector(other)
                    pygame.draw.line(screen, relation_color,
                                     (selected_mob.pos.x, selected_mob.pos.y),
                                     (selected_mob.pos.x + vec.x, selected_mob.pos.y + vec.y), 2)
        if show_grid:
            highlight_grid_box(selected_mob)
            highlight_checked_grid_boxes(selected_mob)

    y_offset = 10
    for mob_type, count in alive_counts.items():
        text = font.render(f'Team {mob_type}: {count}', True, COLORS[mob_type])
        screen.blit(text, (10, y_offset))
        y_offset += 20

    time_steps.append(time_step)
    for key in alive_counts:
        team_counts[key].append(alive_counts[key])
    time_step += 1

    # Remove dode mobs
    mobs = [mob for mob in mobs if mob.alive]

    fps = int(clock.get_fps())
    fps_text = font.render(f'FPS: {fps}', True, (255, 255, 255))
    screen.blit(fps_text, (10, HEIGHT - 15))

    if len(mobs) == 0:
        pygame.display.quit()
        pygame.quit()
        break

    pygame.display.flip()
    clock.tick(30)

pygame.quit()

plt.figure(figsize=(10, 5))
plt.plot(time_steps, team_counts[1], label='Team 1 (Red)', color='red')
plt.plot(time_steps, team_counts[2], label='Team 2 (Green)', color='green')
plt.plot(time_steps, team_counts[3], label='Team 3 (Blue)', color='blue')
plt.xlabel('Time Steps')
plt.ylabel('Population Count')
plt.title('Population of Each Team Over Time')
plt.legend()
plt.show()
