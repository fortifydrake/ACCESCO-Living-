import pygame
import random
import sys
import cv2
import numpy as np
import os
import json 

# --- Constants ---
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

# Colors (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MAROON = (128, 0, 0)
OFF_WHITE = (250, 250, 250)
PIPE_BODY_COLOR = (60, 60, 70)
PIPE_HIGHLIGHT = (80, 80, 90)
ACCENT_MAROON = (100, 0, 0)
GOLD = (255, 215, 0)
BUTTON_COLOR = (128, 0, 0)
BUTTON_HOVER = (150, 20, 20)

# --- Bird Definitions ---
# Each bird has a type and specific colors/features
BIRD_SHOP_DATA = [
    {"id": "classic", "name": "Goldfinch", "price": 0, "color": (255, 215, 0)},
    {"id": "eagle",   "name": "Bald Eagle","price": 15, "color": (139, 69, 19)}, 
    {"id": "dragon",  "name": "Wyvern",    "price": 30, "color": (34, 139, 34)}, 
    {"id": "phoenix", "name": "Phoenix",   "price": 50, "color": (255, 69, 0)},
]

# Game Physics
GRAVITY = 0.25
BIRD_JUMP = -6
PIPE_SPEED = 3
PIPE_FREQUENCY = 1500

# --- Data Management ---
SAVE_FILE = "accesco_save.json"

def load_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"coins": 0, "unlocked": [0], "current": 0}

def save_data(data):
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)
    except:
        print("Could not save game data.")

# --- Helper Functions ---
def load_sound(name):
    if os.path.exists(name):
        return pygame.mixer.Sound(name)
    return None

def load_coin_image(image_path, size):
    """Loads a coin image and scales it."""
    if not os.path.exists(image_path):
        return None
    try:
        img = pygame.image.load(image_path).convert_alpha()
        img = pygame.transform.smoothscale(img, (size, size))
        return img
    except Exception as e:
        print(f"Error loading coin image: {e}")
        return None

# --- UI Classes ---
class Button:
    def __init__(self, x, y, width, height, text, action_code):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action_code
        self.font = pygame.font.SysFont('Arial', 18, bold=True)
        self.is_hovered = False

    def draw(self, screen):
        color = BUTTON_HOVER if self.is_hovered else BUTTON_COLOR
        # Shadow
        pygame.draw.rect(screen, (50, 0, 0), self.rect.move(0, 3), border_radius=8)
        # Body
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        # Border
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=8)
        
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# --- Drawing Helpers ---
def draw_realistic_bird(screen, bird_type, rect, color, angle=0):
    """Draws realistic bird silhouettes using polygons."""
    x, y = rect.x, rect.y
    w, h = rect.width, rect.height
    
    # 1. CLASSIC (Goldfinch shape)
    if bird_type == "classic":
        # Body & Tail
        points = [
            (x + w*0.2, y + h*0.4), # Back neck
            (x + w*0.8, y + h*0.6), # Rump
            (x + w*0.9, y + h*0.5), # Tail tip top
            (x + w*0.85, y + h*0.7),# Tail tip bottom
            (x + w*0.5, y + h*0.9), # Belly
            (x + w*0.1, y + h*0.6), # Breast
        ]
        pygame.draw.polygon(screen, color, points)
        # Head
        pygame.draw.circle(screen, color, (int(x + w*0.25), int(y + h*0.4)), int(w*0.22))
        # Beak (Black tip)
        pygame.draw.polygon(screen, BLACK, [(x + w*0.4, y + h*0.3), (x + w*0.6, y + h*0.4), (x + w*0.4, y + h*0.45)])
        # Wing (Black)
        pygame.draw.ellipse(screen, BLACK, (x + w*0.3, y + h*0.5, w*0.4, h*0.25))
        # Eye
        pygame.draw.circle(screen, BLACK, (int(x + w*0.3), int(y + h*0.35)), 2)

    # 2. EAGLE
    elif bird_type == "eagle":
        # Body (Brown)
        body_pts = [(x, y+h*0.3), (x+w*0.6, y+h*0.3), (x+w*0.4, y+h*0.9), (x+w*0.1, y+h*0.8)]
        pygame.draw.polygon(screen, color, body_pts)
        # White Head
        pygame.draw.circle(screen, WHITE, (int(x + w*0.65), int(y + h*0.35)), int(w*0.25))
        # Beak (Yellow Hook)
        pygame.draw.polygon(screen, (255, 215, 0), [(x+w*0.8, y+h*0.25), (x+w, y+h*0.4), (x+w*0.75, y+h*0.45)])
        # Eye (Fierce)
        pygame.draw.circle(screen, BLACK, (int(x + w*0.7), int(y + h*0.3)), 3)
        # Wing (Large spread)
        pygame.draw.polygon(screen, (80, 40, 10), [(x+w*0.2, y+h*0.4), (x+w*0.5, y+h*0.4), (x+w*0.1, y+h*0.1)])

    # 3. DRAGON
    elif bird_type == "dragon":
        # Tail
        pygame.draw.line(screen, color, (x, y+h*0.5), (x-10, y+h*0.7), 3)
        # Body
        body_rect = pygame.Rect(x, y+h*0.3, w*0.8, h*0.5)
        pygame.draw.ellipse(screen, color, body_rect)
        # Neck & Head
        pygame.draw.polygon(screen, color, [(x+w*0.6, y+h*0.4), (x+w*0.9, y+h*0.2), (x+w*0.8, y+h*0.5)])
        # Wing (Bat-like webbed)
        wing_pts = [(x+w*0.3, y+h*0.4), (x+w*0.1, y), (x+w*0.6, y), (x+w*0.5, y+h*0.4)]
        pygame.draw.polygon(screen, (20, 80, 20), wing_pts)
        # Eye (Red)
        pygame.draw.circle(screen, (255, 0, 0), (int(x + w*0.85), int(y + h*0.3)), 2)

    # 4. PHOENIX
    elif bird_type == "phoenix":
        # Long flowing tail
        pygame.draw.polygon(screen, (255, 140, 0), [(x+w*0.2, y+h*0.6), (x-10, y+h*0.4), (x-10, y+h*0.8)])
        # Body
        pygame.draw.ellipse(screen, color, (x, y+h*0.2, w*0.8, h*0.6))
        # Head crest
        pygame.draw.polygon(screen, GOLD, [(x+w*0.6, y+h*0.3), (x+w*0.7, y), (x+w*0.8, y+h*0.3)])
        # Eye (White hot)
        pygame.draw.circle(screen, WHITE, (int(x + w*0.7), int(y + h*0.35)), 3)
        # Wing (Flame)
        pygame.draw.polygon(screen, (255, 200, 0), [(x+w*0.3, y+h*0.4), (x+w*0.6, y+h*0.1), (x+w*0.5, y+h*0.5)])

# --- Classes ---

class Coin:
    def __init__(self, x, y, image=None):
        self.x = x
        self.y = y
        self.radius = 15
        self.diameter = self.radius * 2
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.diameter, self.diameter)
        self.collected = False
        self.animation_offset = 0
        self.image = image

    def move(self):
        self.x -= PIPE_SPEED
        self.rect.x = int(self.x - self.radius)
        self.animation_offset += 0.1
        self.rect.y = int(self.y - self.radius + np.sin(self.animation_offset) * 5)

    def draw(self, screen):
        if not self.collected:
            if self.image:
                screen.blit(self.image, self.rect)
            else:
                # Fallback to drawn circles if image fails to load
                pygame.draw.circle(screen, (218, 165, 32), self.rect.center, self.radius)
                pygame.draw.circle(screen, GOLD, self.rect.center, self.radius - 2)
                pygame.draw.circle(screen, WHITE, (self.rect.centerx - 5, self.rect.centery - 5), 3)
                pygame.draw.circle(screen, MAROON, self.rect.center, self.radius, 1)

class Bird:
    def __init__(self, image=None, bird_data=None):
        self.x = 50
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.width = 50 # Slightly larger for detail
        self.height = 40
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        self.image = image # For Face capture
        self.bird_data = bird_data if bird_data else BIRD_SHOP_DATA[0]
        self.color = self.bird_data['color']
        self.type = self.bird_data['id']

    def jump(self):
        self.velocity = BIRD_JUMP

    def move(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.y = int(self.y)

    def draw(self, screen):
        if self.image:
            # Face Mode
            screen.blit(self.image, self.rect)
            pygame.draw.circle(screen, WHITE, self.rect.center, self.width//2, 2)
        else:
            # Procedural Realistic Bird Mode
            draw_realistic_bird(screen, self.type, self.rect, self.color)

class Pipe:
    def __init__(self, coin_image=None):
        self.gap = 170 # Bigger gap for bigger birds
        self.width = 70
        self.cap_height = 25 
        self.cap_overhang = 6 
        self.x = SCREEN_WIDTH
        self.height = random.randint(100, SCREEN_HEIGHT - self.gap - 100)
        
        self.top_rect = pygame.Rect(self.x, 0, self.width, self.height)
        self.bottom_rect = pygame.Rect(self.x, self.height + self.gap, self.width, SCREEN_HEIGHT - (self.height + self.gap))
        
        self.passed = False
        self.has_coin = random.choice([True, False])
        self.coin = None
        if self.has_coin:
            coin_y = self.height + (self.gap // 2)
            self.coin = Coin(self.x + self.width//2, coin_y, coin_image)

    def move(self):
        self.x -= PIPE_SPEED
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x
        if self.coin:
            self.coin.move()

    def draw_pillar(self, screen, rect, is_top_pipe):
        pygame.draw.rect(screen, PIPE_BODY_COLOR, rect)
        highlight_rect = pygame.Rect(rect.x + 5, rect.y, 10, rect.height)
        pygame.draw.rect(screen, PIPE_HIGHLIGHT, highlight_rect)
        pygame.draw.rect(screen, MAROON, rect, 2)
        
        cap_width = self.width + (self.cap_overhang * 2)
        cap_x = rect.x - self.cap_overhang
        cap_y = rect.bottom - self.cap_height if is_top_pipe else rect.top
        cap_rect = pygame.Rect(cap_x, cap_y, cap_width, self.cap_height)
        
        pygame.draw.rect(screen, MAROON, cap_rect)
        pygame.draw.line(screen, (180, 50, 50), (cap_rect.left, cap_rect.top), (cap_rect.right, cap_rect.top), 2)
        pygame.draw.rect(screen, BLACK, cap_rect, 1)

    def draw(self, screen):
        self.draw_pillar(screen, self.top_rect, is_top_pipe=True)
        self.draw_pillar(screen, self.bottom_rect, is_top_pipe=False)
        if self.coin and not self.coin.collected:
            self.coin.draw(screen)

# --- Video & Background ---
def get_video_frame(cap):
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
        if not ret: return None 

    frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.transpose(frame, (1, 0, 2))
    return pygame.surfarray.make_surface(frame)

def draw_background(screen, font_large, font_small, video_surface=None):
    if video_surface:
        screen.blit(video_surface, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 30)) 
        screen.blit(overlay, (0,0))
    else:
        screen.fill(OFF_WHITE)
        for i in range(-SCREEN_HEIGHT, SCREEN_WIDTH + SCREEN_HEIGHT, 40):
            pygame.draw.line(screen, (240, 230, 230), (i, 0), (i + SCREEN_HEIGHT, SCREEN_HEIGHT), 2)
        
        watermark_text = font_large.render("ACCESCO", True, (245, 220, 220))
        wm_rect = watermark_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        screen.blit(watermark_text, wm_rect)

    header_height = 60
    header_surface = pygame.Surface((SCREEN_WIDTH, header_height), pygame.SRCALPHA)
    header_surface.fill((*MAROON, 220))
    screen.blit(header_surface, (0,0))
    pygame.draw.line(screen, ACCENT_MAROON, (0, header_height), (SCREEN_WIDTH, header_height), 3)
    
    brand_text = font_small.render("ACCESCO", True, WHITE)
    sub_text = pygame.font.SysFont('Arial', 14).render("Fashion | Food | Grocery", True, (220, 220, 220))
    screen.blit(brand_text, (20, 10))
    screen.blit(sub_text, (20, 35))

def capture_face(screen):
    cap = cv2.VideoCapture(0)
    font = pygame.font.SysFont('Arial', 20)
    clock = pygame.time.Clock()
    box_size = 200
    box_x = (SCREEN_WIDTH - box_size) // 2
    box_y = (SCREEN_HEIGHT - box_size) // 2
    center_point = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    radius = box_size // 2
    
    # Capture Button
    btn_capture = Button(SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT - 100, 120, 50, "CAPTURE", "CAPTURE")

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1) 
        frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
        frame_display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_transposed = np.transpose(frame_display, (1, 0, 2))
        cam_surface = pygame.surfarray.make_surface(frame_transposed)
        
        screen.blit(cam_surface, (0,0))
        pygame.draw.circle(screen, WHITE, center_point, radius, 3)
        
        msg = font.render("Align Face", True, WHITE)
        msg_bg = pygame.Rect(SCREEN_WIDTH//2 - 80, 30, 160, 40)
        pygame.draw.rect(screen, MAROON, msg_bg) 
        msg_rect = msg.get_rect(center=(SCREEN_WIDTH//2, 50))
        screen.blit(msg, msg_rect)
        
        # Draw Capture Button
        mouse_pos = pygame.mouse.get_pos()
        btn_capture.check_hover(mouse_pos)
        btn_capture.draw(screen)
        
        pygame.display.update()
        clock.tick(30)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release(); pygame.quit(); sys.exit()
            
            # Click or Key
            clicked = False
            if event.type == pygame.MOUSEBUTTONDOWN and btn_capture.is_clicked(event.pos):
                clicked = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                clicked = True
                
            if clicked:
                face_roi = frame[box_y:box_y+box_size, box_x:box_x+box_size]
                face_rgba = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGBA)
                mask = np.zeros((box_size, box_size), dtype=np.uint8)
                cv2.circle(mask, (box_size//2, box_size//2), box_size//2, 255, -1)
                face_rgba[:, :, 3] = mask
                face_rgba = np.ascontiguousarray(face_rgba)
                final_bird_surface = pygame.image.frombuffer(face_rgba, (box_size, box_size), 'RGBA')
                final_bird_surface = pygame.transform.smoothscale(final_bird_surface, (40, 40))
                cap.release()
                return final_bird_surface
    cap.release()
    return None

def shop_menu(screen, game_data):
    """Handles the Shop UI with Buttons."""
    font_ui = pygame.font.SysFont('Arial', 30, bold=True)
    font_small = pygame.font.SysFont('Arial', 20)
    
    selected_idx = game_data['current']
    
    # Buttons
    btn_prev = Button(20, SCREEN_HEIGHT//2, 60, 50, "<", "PREV")
    btn_next = Button(SCREEN_WIDTH - 80, SCREEN_HEIGHT//2, 60, 50, ">", "NEXT")
    btn_action = Button(SCREEN_WIDTH//2 - 75, SCREEN_HEIGHT//2 + 100, 150, 50, "ACTION", "ACTION")
    btn_back = Button(20, SCREEN_HEIGHT - 70, 100, 40, "BACK", "BACK")
    
    while True:
        screen.fill(OFF_WHITE)
        pygame.draw.rect(screen, MAROON, (0, 0, SCREEN_WIDTH, 80))
        title = font_ui.render("BIRD SHOP", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 25))
        
        coin_text = font_small.render(f"Coins: {game_data['coins']}", True, GOLD)
        screen.blit(coin_text, (20, 85))
        
        bird_info = BIRD_SHOP_DATA[selected_idx]
        is_unlocked = selected_idx in game_data['unlocked']
        
        # Preview Area
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50
        preview_rect = pygame.Rect(cx-30, cy-30, 60, 60)
        draw_realistic_bird(screen, bird_info['id'], preview_rect, bird_info['color'])
        
        name_text = font_ui.render(bird_info['name'], True, BLACK)
        screen.blit(name_text, (cx - name_text.get_width()//2, cy + 50))
        
        # Update Action Button Text
        if is_unlocked:
            if selected_idx == game_data['current']:
                btn_action.text = "EQUIPPED"
                btn_action.color = (100, 100, 100) # Greyed out
            else:
                btn_action.text = "EQUIP"
                btn_action.color = (0, 150, 0) # Green
        else:
            btn_action.text = f"BUY ({bird_info['price']})"
            if game_data['coins'] >= bird_info['price']:
                btn_action.color = MAROON
            else:
                btn_action.color = (100, 100, 100)

        # Draw Buttons
        mouse_pos = pygame.mouse.get_pos()
        for btn in [btn_prev, btn_next, btn_action, btn_back]:
            btn.check_hover(mouse_pos)
            btn.draw(screen)
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_prev.is_clicked(event.pos):
                    selected_idx = (selected_idx - 1) % len(BIRD_SHOP_DATA)
                elif btn_next.is_clicked(event.pos):
                    selected_idx = (selected_idx + 1) % len(BIRD_SHOP_DATA)
                elif btn_back.is_clicked(event.pos):
                    return game_data
                elif btn_action.is_clicked(event.pos):
                    if is_unlocked:
                        game_data['current'] = selected_idx
                        save_data(game_data)
                    elif game_data['coins'] >= bird_info['price']:
                        game_data['coins'] -= bird_info['price']
                        game_data['unlocked'].append(selected_idx)
                        game_data['current'] = selected_idx
                        save_data(game_data)

# --- State Machine Functions ---

def show_main_menu(screen, bg_cap, game_data):
    font_ui = pygame.font.SysFont('Arial', 30, bold=True)
    font_large = pygame.font.SysFont('Arial', 50, bold=True)
    
    # Menu Buttons
    cx = SCREEN_WIDTH // 2
    btn_start = Button(cx - 100, 260, 200, 60, "START GAME", "START")
    btn_capture = Button(cx - 100, 340, 200, 60, "CAPTURE FACE", "CAPTURE")
    btn_shop = Button(cx - 100, 420, 200, 60, "BIRD SHOP", "SHOP")
    
    while True:
        video_surf = get_video_frame(bg_cap) if bg_cap else None
        draw_background(screen, font_large, font_ui, video_surf)
        
        menu_bg_rect = pygame.Rect(40, 150, 320, 380)
        menu_surface = pygame.Surface((320, 380), pygame.SRCALPHA)
        menu_surface.fill((255, 255, 255, 230))
        screen.blit(menu_surface, (40, 150))
        pygame.draw.rect(screen, MAROON, menu_bg_rect, 4)
        
        title = font_ui.render("Welcome to", True, BLACK)
        title2 = font_ui.render("ACCESCO GAME", True, MAROON)
        
        screen.blit(title, (cx - title.get_width()//2, 170))
        screen.blit(title2, (cx - title2.get_width()//2, 210))
        
        # Draw Buttons
        mouse_pos = pygame.mouse.get_pos()
        for btn in [btn_start, btn_capture, btn_shop]:
            btn.check_hover(mouse_pos)
            btn.draw(screen)
        
        coins_hud = pygame.font.SysFont('Arial', 18).render(f"Coins: {game_data['coins']}", True, GOLD)
        screen.blit(coins_hud, (cx - coins_hud.get_width()//2, 500))
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_start.is_clicked(event.pos): return "START"
                if btn_capture.is_clicked(event.pos): return "CAPTURE"
                if btn_shop.is_clicked(event.pos): return "SHOP"

def run_game_loop(screen, bg_cap, game_data, bird_image, sounds, coin_image):
    current_bird_data = BIRD_SHOP_DATA[game_data['current']]
    bird = Bird(bird_image, current_bird_data)
    pipes = []
    score = 0
    collected_in_run = 0
    
    clock = pygame.time.Clock()
    SPAWNPIPE = pygame.USEREVENT
    pygame.time.set_timer(SPAWNPIPE, PIPE_FREQUENCY)
    
    font_large = pygame.font.SysFont('Arial', 50, bold=True)
    font_ui = pygame.font.SysFont('Arial', 30, bold=True)
    
    game_active = True
    
    # Game Over Buttons
    btn_restart = Button(SCREEN_WIDTH//2 - 120, 320, 110, 50, "RESTART", "RESTART")
    btn_menu = Button(SCREEN_WIDTH//2 + 10, 320, 110, 50, "MENU", "MENU")
    
    while True:
        # Event Handling
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_active:
                    # Tap anywhere to jump
                    bird.jump()
                    if sounds['jump']: sounds['jump'].play()
                else:
                    # Game Over Logic
                    if btn_restart.is_clicked(event.pos):
                        return "RESTART"
                    if btn_menu.is_clicked(event.pos):
                        return "MENU"
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_active:
                        bird.jump()
                        if sounds['jump']: sounds['jump'].play()
                    else:
                        return "RESTART"

            if event.type == SPAWNPIPE and game_active:
                pipes.append(Pipe(coin_image))

        # Update Logic
        video_surf = get_video_frame(bg_cap) if bg_cap else None
        draw_background(screen, font_large, font_ui, video_surf)

        if game_active:
            bird.move()
            bird.draw(screen)

            if bird.y >= SCREEN_HEIGHT or bird.y <= 0:
                game_active = False
                if sounds['crash']: sounds['crash'].play()

            for pipe in pipes:
                pipe.move()
                pipe.draw(screen)

                collision_rect = bird.rect.inflate(-10, -10)
                if collision_rect.colliderect(pipe.top_rect) or collision_rect.colliderect(pipe.bottom_rect):
                    game_active = False
                    if sounds['crash']: sounds['crash'].play()

                if not pipe.passed and bird.x > pipe.x + pipe.width:
                    score += 1
                    pipe.passed = True
                    if sounds['score']: sounds['score'].play()
                
                if pipe.coin and not pipe.coin.collected:
                    if collision_rect.colliderect(pipe.coin.rect):
                        pipe.coin.collected = True
                        game_data['coins'] += 1
                        collected_in_run += 1
                        if sounds['collect']: sounds['collect'].play()
                        save_data(game_data)
            
            if len(pipes) > 0 and pipes[0].x < -pipes[0].width:
                pipes.pop(0)
            
            # HUD - Moved down to avoid header overlap
            score_surface = font_ui.render(f"Score: {int(score)}", True, MAROON)
            coins_surface = font_ui.render(f"Coins: {game_data['coins']}", True, GOLD)
            screen.blit(score_surface, (SCREEN_WIDTH - 140, 70))
            screen.blit(coins_surface, (20, 70))

        else:
            # GAME OVER SCREEN
            go_bg_rect = pygame.Rect(50, 180, 300, 220)
            go_surface = pygame.Surface((300, 220), pygame.SRCALPHA)
            go_surface.fill((255, 255, 255, 230))
            screen.blit(go_surface, (50, 180))
            pygame.draw.rect(screen, MAROON, go_bg_rect, 4)

            game_over_surface = font_ui.render("Game Over", True, MAROON)
            score_txt = pygame.font.SysFont('Arial', 22).render(f"Score: {score}", True, BLACK)
            coin_txt = pygame.font.SysFont('Arial', 22).render(f"Collected: {collected_in_run}", True, GOLD)
            
            cx = go_bg_rect.centerx
            screen.blit(game_over_surface, (cx - game_over_surface.get_width()//2, 200))
            screen.blit(score_txt, (cx - score_txt.get_width()//2, 240))
            screen.blit(coin_txt, (cx - coin_txt.get_width()//2, 270))
            
            # Draw Buttons
            btn_restart.check_hover(mouse_pos)
            btn_menu.check_hover(mouse_pos)
            btn_restart.draw(screen)
            btn_menu.draw(screen)

        pygame.display.update()
        clock.tick(FPS)

def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ACCESCO Flappy Game")
    
    # Load assets
    game_data = load_data()
    sounds = {
        'jump': load_sound("jump.wav"),
        'score': load_sound("score.wav"),
        'crash': load_sound("crash.wav"),
        'collect': load_sound("collect.wav")
    }
    
    video_path = 'background.mp4'
    bg_cap = cv2.VideoCapture(video_path) if os.path.exists(video_path) else None
    
    bird_image = None
    
    # NEW: Load coin image (diameter = 2 * radius = 30)
    coin_image = load_coin_image("coin.jpg", 30)
        
    # --- MAIN APP LOOP ---
    app_state = "MENU" # MENU, GAME, SHOP, CAPTURE
    
    while True:
        if app_state == "MENU":
            action = show_main_menu(screen, bg_cap, game_data)
            if action == "QUIT": break
            elif action == "START": app_state = "GAME"
            elif action == "SHOP": app_state = "SHOP"
            elif action == "CAPTURE": app_state = "CAPTURE"
            
        elif app_state == "SHOP":
            game_data = shop_menu(screen, game_data)
            app_state = "MENU" # Return to menu after shop
            
        elif app_state == "CAPTURE":
            if bg_cap: bg_cap.release()
            bird_image = capture_face(screen)
            if os.path.exists(video_path): bg_cap = cv2.VideoCapture(video_path)
            app_state = "MENU"
            
        elif app_state == "GAME":
            result = run_game_loop(screen, bg_cap, game_data, bird_image, sounds, coin_image)
            if result == "QUIT": break
            elif result == "MENU": app_state = "MENU"
            elif result == "RESTART": pass # Loop continues in GAME state

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()