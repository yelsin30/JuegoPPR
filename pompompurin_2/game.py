import pygame
from pygame.locals import *
import random
import math

# --- CONFIGURACIÓN ---
SCREEN_W, SCREEN_H = 1024, 576
FPS = 60
GRAVITY = 1
PLAYER_SPEED = 6
JUMP_STRENGTH = -18

# --- COLORES ---
SKY_COLOR = (135, 206, 235)
BLOCK_COLOR = (255, 204, 102)
BLOCK_USED_COLOR = (200, 180, 150)
ENEMY_COLOR = (160, 82, 45)

# ============================
# CLASE PERSONAJE PRINCIPAL
# ============================
class Player:
    def __init__(self, x, y):
        self.width = 50
        self.height = 60
        self.crouch_height = 45
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.is_crouching = False
        self.crouch_progress = 0.0

        self.blink_timer = random.uniform(2, 5)
        self.blink_duration = 0
        self.walk_timer = 0
        self.walk_speed = 10

        self.direction = 1
        self.prev_direction = 1
        self.turning = False
        self.turn_timer = 0.0
        self.turn_duration = 0.2

    def handle_input(self, keys):
        self.prev_direction = self.direction

        # Agacharse
        self.is_crouching = (keys[K_DOWN] or keys[K_s]) and self.on_ground

        # Movimiento horizontal
        self.vel_x = 0
        if keys[K_LEFT] or keys[K_a]:
            self.vel_x = -PLAYER_SPEED
            self.direction = -1
        if keys[K_RIGHT] or keys[K_d]:
            self.vel_x = PLAYER_SPEED
            self.direction = 1

        # Detectar cambio de dirección
        if self.direction != self.prev_direction:
            self.turning = True
            self.turn_timer = self.turn_duration

    def jump(self):
        if self.on_ground and not self.is_crouching:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False

    def apply_gravity(self):
        self.vel_y += GRAVITY
        if self.vel_y > 20:
            self.vel_y = 20

    def move(self, platforms, blocks):
        self.rect.x += self.vel_x
        for tile in platforms + [b.rect for b in blocks]:
            if self.rect.colliderect(tile):
                if self.vel_x > 0:
                    self.rect.right = tile.left
                elif self.vel_x < 0:
                    self.rect.left = tile.right

        self.rect.y += self.vel_y
        self.on_ground = False
        for tile in platforms + [b.rect for b in blocks]:
            if self.rect.colliderect(tile):
                if self.vel_y > 0:
                    self.rect.bottom = tile.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    # Golpe de bloque desde abajo
                    for b in blocks:
                        if b.rect == tile:
                            b.hit()
                    self.rect.top = tile.bottom
                    self.vel_y = 0

    def update_animation(self, dt):
        self.blink_timer -= dt
        if self.blink_timer <= 0:
            self.blink_duration = 0.15
            self.blink_timer = random.uniform(2, 5)
        if self.blink_duration > 0:
            self.blink_duration -= dt

        # Caminar solo si hay movimiento
        if self.vel_x != 0 and self.on_ground:
            self.walk_timer += dt * self.walk_speed
        else:
            self.walk_timer = 0

        # Giro
        if self.turning:
            self.turn_timer -= dt
            if self.turn_timer <= 0:
                self.turning = False

        # Suavizar agachado
        if self.is_crouching:
            self.crouch_progress = min(1.0, self.crouch_progress + dt * 8)
        else:
            self.crouch_progress = max(0.0, self.crouch_progress - dt * 8)

    def draw(self, surface, camera_x):
        temp = pygame.Surface((self.width + 60, self.height + 60), pygame.SRCALPHA)
        x, y, w, h = 30, 30, self.width, self.height
        body_color = (245, 222, 179)
        line_color = (90, 60, 40)
        shoe_color = (100, 50, 30)
        hat_color = (90, 60, 40)

        crouch_offset = int(10 * self.crouch_progress)
        crouch_scale = 1 - 0.15 * self.crouch_progress
        step_phase = math.sin(self.walk_timer) if self.walk_timer > 0 else 0
        swing_phase = math.sin(self.walk_timer) * 6 if self.walk_timer > 0 else 0

        # --- Piernas ---
        leg_length = 15
        leg_width = 10
        left_leg_x = x + 10
        right_leg_x = x + w - 20
        pygame.draw.rect(temp, shoe_color, (left_leg_x + swing_phase * self.direction, y + h - leg_length - crouch_offset, leg_width, leg_length))
        pygame.draw.rect(temp, shoe_color, (right_leg_x - swing_phase * self.direction, y + h - leg_length - crouch_offset, leg_width, leg_length))

        # --- Cuerpo ---
        body_rect = pygame.Rect(x + 5, y + 20 + crouch_offset, w - 10, (h - 25) * crouch_scale)
        pygame.draw.rect(temp, body_color, body_rect, border_radius=10)
        pygame.draw.rect(temp, line_color, body_rect, 2, border_radius=10)

        # --- Brazos ---
        arm_length = 15
        arm_width = 8
        arm_swing_left = math.sin(self.walk_timer) * 8 if self.walk_timer > 0 else 0
        arm_swing_right = -math.sin(self.walk_timer) * 8 if self.walk_timer > 0 else 0
        pygame.draw.rect(temp, body_color, (x - 5, y + 30 + arm_swing_left + crouch_offset, arm_width, arm_length), border_radius=5)
        pygame.draw.rect(temp, body_color, (x + w - 3, y + 30 + arm_swing_right + crouch_offset, arm_width, arm_length), border_radius=5)
        pygame.draw.rect(temp, line_color, (x - 5, y + 30 + arm_swing_left + crouch_offset, arm_width, arm_length), 2, border_radius=5)
        pygame.draw.rect(temp, line_color, (x + w - 3, y + 30 + arm_swing_right + crouch_offset, arm_width, arm_length), 2, border_radius=5)

        # --- Cabeza ---
        head_tilt = step_phase * 2 if self.walk_timer > 0 else 0
        head_rect = pygame.Rect(x - 5, y - 5 + crouch_offset + head_tilt, w + 10, 35 * crouch_scale)
        pygame.draw.ellipse(temp, body_color, head_rect)
        pygame.draw.ellipse(temp, line_color, head_rect, 2)

        # --- Gorro ---
        hat_rect = pygame.Rect(x + 5, y - 15 + crouch_offset + head_tilt, w, 20)
        pygame.draw.ellipse(temp, hat_color, hat_rect)
        pygame.draw.ellipse(temp, line_color, hat_rect, 2)

        # --- Orejas ---
        ear_y = y + 5 + crouch_offset + head_tilt
        pygame.draw.ellipse(temp, body_color, (x - 25, ear_y, 30, 20))
        pygame.draw.ellipse(temp, body_color, (x + w, ear_y, 30, 20))
        pygame.draw.ellipse(temp, line_color, (x - 25, ear_y, 30, 20), 2)
        pygame.draw.ellipse(temp, line_color, (x + w, ear_y, 30, 20), 2)

        # --- Ojos ---
        eye_open = (self.blink_duration <= 0)
        eye_w = 6
        eye_h = 8 if eye_open else 2
        left_eye = pygame.Rect(x + int(w * 0.35), y + 10 + crouch_offset + head_tilt, eye_w, eye_h)
        right_eye = pygame.Rect(x + int(w * 0.65), y + 10 + crouch_offset + head_tilt, eye_w, eye_h)
        pygame.draw.ellipse(temp, line_color, left_eye)
        pygame.draw.ellipse(temp, line_color, right_eye)
        if eye_open:
            pygame.draw.circle(temp, (255, 255, 255), (left_eye.centerx - 1, left_eye.centery - 1), 2)
            pygame.draw.circle(temp, (255, 255, 255), (right_eye.centerx - 1, right_eye.centery - 1), 2)

        # --- Boca ---
        pygame.draw.arc(temp, line_color,
                        (x + int(w * 0.4), y + 20 + crouch_offset + head_tilt, int(w * 0.2), 10),
                        math.radians(200), math.radians(340), 2)

        # --- Flip y giro ---
        if self.direction == -1:
            temp = pygame.transform.flip(temp, True, False)
        if self.turning:
            progress = 1 - (self.turn_timer / self.turn_duration)
            scale_factor = max(0.3, abs(math.cos(progress * math.pi)))
            temp = pygame.transform.scale(temp, (int(temp.get_width() * scale_factor), temp.get_height()))

        surface.blit(temp, (self.rect.x - camera_x - 30, self.rect.y - 30))

# ============================
# CLASE BLOQUES INTERACTIVOS
# ============================
class Block:
    def __init__(self, x, y, w=40, h=40):
        self.rect = pygame.Rect(x, y, w, h)
        self.used = False
        self.bounce_offset = 0
        self.bounce_velocity = 0
        self.coins = []

    def hit(self):
        if not self.used:
            self.bounce_velocity = -5
            self.used = True
            # Crear moneda animada
            self.coins.append({"y": self.rect.y - 10, "vy": -6, "time": 0})

    def update(self, dt):
        # Rebote
        self.bounce_offset += self.bounce_velocity
        self.bounce_velocity += 0.8
        if self.bounce_offset > 0:
            self.bounce_offset = 0
            self.bounce_velocity = 0

        # Monedas animadas
        for coin in self.coins:
            coin["y"] += coin["vy"]
            coin["vy"] += 0.5
            coin["time"] += dt
        self.coins = [c for c in self.coins if c["time"] < 0.8]

    def draw(self, surface, camera_x):
        color = BLOCK_USED_COLOR if self.used else BLOCK_COLOR
        pygame.draw.rect(surface, color, (self.rect.x - camera_x, self.rect.y + self.bounce_offset, self.rect.width, self.rect.height))
        pygame.draw.rect(surface, (120, 80, 40), (self.rect.x - camera_x, self.rect.y + self.bounce_offset, self.rect.width, self.rect.height), 3)

        # Dibujar monedas animadas
        for coin in self.coins:
            pygame.draw.circle(surface, (255, 215, 0), (int(self.rect.centerx - camera_x), int(coin["y"])), 8)
            pygame.draw.circle(surface, (180, 140, 0), (int(self.rect.centerx - camera_x), int(coin["y"])), 8, 2)

# ============================
# ENEMIGOS SIMPLES
# ============================
class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.vel_x = -2

    def update(self, platforms):
        self.rect.x += self.vel_x
        # Cambiar dirección si llega a un borde
        on_platform = False
        for p in platforms:
            if self.rect.colliderect(p):
                on_platform = True
        if not on_platform:
            self.vel_x *= -1

    def draw(self, surface, camera_x):
        pygame.draw.ellipse(surface, ENEMY_COLOR, (self.rect.x - camera_x, self.rect.y, self.rect.width, self.rect.height))

# ============================
# DECORACIÓN DE FONDO
# ============================
def draw_background(surface, camera_x):
    # Parallax suave
    parallax = camera_x * 0.5

    # Montañas
    for i in range(0, 3000, 300):
        pygame.draw.polygon(surface, (180, 220, 180),
                            [(i - parallax, SCREEN_H - 40),
                             (i + 150 - parallax, SCREEN_H - 200),
                             (i + 300 - parallax, SCREEN_H - 40)])

    # Nubes kawaii ☁️
    for i in range(0, 3000, 400):
        pygame.draw.ellipse(surface, (255, 255, 255), (i - parallax, 100, 100, 50))
        pygame.draw.ellipse(surface, (255, 255, 255), (i + 30 - parallax, 80, 120, 60))
        pygame.draw.ellipse(surface, (255, 255, 255), (i + 60 - parallax, 100, 100, 50))

    # Árboles kawaii 🌳
    for i in range(100, 3000, 500):
        pygame.draw.rect(surface, (139, 69, 19), (i - parallax, SCREEN_H - 140, 20, 100))
        pygame.draw.circle(surface, (34, 139, 34), (i + 10 - parallax, SCREEN_H - 150), 50)

# ============================
# PLATAFORMAS BASE
# ============================
def draw_platform(surface, rect, camera_x):
    x, y, w, h = rect
    base_color = (205, 133, 63)
    line_color = (90, 60, 40)
    pygame.draw.rect(surface, base_color, (x - camera_x, y, w, h), border_radius=10)
    pygame.draw.rect(surface, line_color, (x - camera_x, y, w, h), 3, border_radius=10)

# ============================
# MAIN GAME
# ============================
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Pom Pom Purin - Fondo + Bloques + Enemigos 👾✨")
clock = pygame.time.Clock()

player = Player(100, 100)

platforms = [
    pygame.Rect(0, SCREEN_H - 40, 3000, 40),
    pygame.Rect(400, SCREEN_H - 150, 200, 30),
    pygame.Rect(800, SCREEN_H - 250, 200, 30),
    pygame.Rect(1400, SCREEN_H - 200, 200, 30),
    pygame.Rect(2000, SCREEN_H - 300, 200, 30)
]

# Bloques interactivos 🧱
blocks = [
    Block(600, SCREEN_H - 300),
    Block(620, SCREEN_H - 300),
    Block(640, SCREEN_H - 300),
]

# Enemigos 👾
enemies = [
    Enemy(500, SCREEN_H - 80),
    Enemy(1000, SCREEN_H - 290),
    Enemy(1800, SCREEN_H - 240),
]

camera_x = 0

# ============================
# BUCLE PRINCIPAL
# ============================
running = True
while running:
    dt = clock.tick(FPS) / 1000
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            if event.key in (K_SPACE, K_w, K_UP):
                player.jump()

    player.handle_input(keys)
    player.apply_gravity()
    player.move(platforms, blocks)
    player.update_animation(dt)

    # --- Actualizar bloques y enemigos ---
    for b in blocks:
        b.update(dt)
    for e in enemies:
        e.update(platforms)

    # --- Colisión con enemigos ---
    for e in enemies[:]:
        if player.rect.colliderect(e.rect):
            if player.vel_y > 0:
                enemies.remove(e)  # saltó encima
                player.vel_y = JUMP_STRENGTH // 2  # rebote
            else:
                player.rect.x -= player.vel_x * 2  # empujón simple

    # --- Scroll lateral ---
    target_camera_x = player.rect.centerx - SCREEN_W // 2
    camera_x += (target_camera_x - camera_x) * 0.1

    # --- Dibujar ---
    screen.fill(SKY_COLOR)
    draw_background(screen, camera_x)

    for p in platforms:
        draw_platform(screen, p, camera_x)
    for b in blocks:
        b.draw(screen, camera_x)
    for e in enemies:
        e.draw(screen, camera_x)

    player.draw(screen, camera_x)

    pygame.display.flip()

pygame.quit()
