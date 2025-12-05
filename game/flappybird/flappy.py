import pygame
import random
import sys
import cv2
import numpy as np
import os
import json 

# --- Constants & Swiggy-like Theme ---
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

# Brand Colors (Swiggy Style)
# Using Tuples (R, G, B) to prevent "Invalid Color" errors
THEME_BRAND = (112, 4, 88)    # #6C5CE7 (New Brand Color - Purple/Blue)
THEME_BG = (242, 242, 242)      # #F2F2F2 (Light Gray Background)
THEME_CARD_BG = (255, 255, 255) # #FFFFFF (White Cards)
TEXT_DARK = (61, 65, 82)        # #3D4152 (Dark Text)
TEXT_GRAY = (104, 107, 120)     # #686B78 (Subtext)
THEME_GREEN = (96, 178, 70)     # #60B246 (Success/Veg Green)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)

# Colors for Pipes/Game
PIPE_BODY_COLOR = (60, 60, 70)
PIPE_HIGHLIGHT = (80, 80, 90)

# --- Bird Definitions & Assets ---
BIRD_IMAGES = {} # Will store loaded pygame images

BIRD_SHOP_DATA = [
    {"id": "classic", "name": "Goldfinch", "price": 0, "color": (255, 215, 0), "image": "bird_classic.png"},
    {"id": "eagle",   "name": "Bald Eagle","price": 15, "color": (139, 69, 19), "image": "bird_eagle.jpg"},
    {"id": "dragon",  "name": "Wyvern",    "price": 30, "color": (34, 139, 34), "image": "bird_dragon.png"},
    {"id": "phoenix", "name": "Phoenix",   "price": 50, "color": (255, 69, 0), "image": "bird_phoenix.png"},
    {"id": "owl",     "name": "Snowy Owl", "price": 75, "color": (240, 240, 240), "image": "bird_owl.png"},
    {"id": "penguin", "name": "Penguin",   "price": 100,"color": (30, 30, 30), "image": "bird_penguin.png"},
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
    if not os.path.exists(image_path):
        return None
    try:
        img = pygame.image.load(image_path).convert_alpha()
        img = pygame.transform.smoothscale(img, (size, size))
        return img
    except Exception as e:
        return None

def load_bird_images():
    """Loads all bird images from disk."""
    for bird_data in BIRD_SHOP_DATA:
        bird_id = bird_data["id"]
        image_path = bird_data["image"]
        if os.path.exists(image_path):
            try:
                img = pygame.image.load(image_path).convert_alpha()
                # Scale images to a standard size
                BIRD_IMAGES[bird_id] = pygame.transform.smoothscale(img, (50, 40))
            except Exception as e:
                print(f"Error loading image for {bird_id}: {e}")
                BIRD_IMAGES[bird_id] = None # Fallback
        else:
            BIRD_IMAGES[bird_id] = None

def draw_rounded_rect(surface, color, rect, radius=10):
    """Helper to draw rounded rectangles."""
    pygame.draw.rect(surface, color, rect, border_radius=radius)

# --- UI Classes ---
class Button:
    def __init__(self, x, y, width, height, text, action_code, color=THEME_BRAND, text_color=WHITE, font_size=16):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action_code
        self.color = color
        self.text_color = text_color
        self.font = pygame.font.SysFont('Verdana', font_size, bold=True)
        self.is_hovered = False

    def draw(self, screen):
        # Hover effect: darken slightly
        draw_color = list(self.color)
        if self.is_hovered:
            draw_color = [max(0, c - 30) for c in draw_color]
        
        # Shadow
        shadow_rect = self.rect.move(0, 2)
        draw_rounded_rect(screen, (200, 200, 200), shadow_rect, radius=8)
        
        # Body
        draw_rounded_rect(screen, draw_color, self.rect, radius=8)
        
        # Text
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class ProductCard:
    """A Swiggy-style item card for the shop."""
    def __init__(self, x, y, width, height, bird_data, is_unlocked, is_equipped):
        self.rect = pygame.Rect(x, y, width, height)
        self.data = bird_data
        self.is_unlocked = is_unlocked
        self.is_equipped = is_equipped
        self.font_name = pygame.font.SysFont('Verdana', 14, bold=True)
        self.font_price = pygame.font.SysFont('Verdana', 12)
        
        # Action Button (Buy or Equip)
        btn_w, btn_h = 80, 30
        btn_x = x + width - btn_w - 10
        btn_y = y + (height - btn_h) // 2
        
        if self.is_equipped:
            self.btn = Button(btn_x, btn_y, btn_w, btn_h, "EQUIPPED", "NONE", color=THEME_BG, text_color=TEXT_GRAY, font_size=10)
        elif self.is_unlocked:
            self.btn = Button(btn_x, btn_y, btn_w, btn_h, "EQUIP", "EQUIP", color=THEME_GREEN, font_size=12)
        else:
            self.btn = Button(btn_x, btn_y, btn_w, btn_h, "ADD", "BUY", color=WHITE, text_color=THEME_GREEN, font_size=14)

    def draw(self, screen):
        # Card Background
        draw_rounded_rect(screen, THEME_CARD_BG, self.rect, radius=12)
        
        # Preview Icon
        cx, cy = self.rect.x + 40, self.rect.centery
        bird_id = self.data['id']
        bird_img = BIRD_IMAGES.get(bird_id)
        
        if bird_img:
            # Scale down for preview
            preview_img = pygame.transform.smoothscale(bird_img, (40, 32))
            preview_rect = preview_img.get_rect(center=(cx, cy))
            screen.blit(preview_img, preview_rect)
        else:
            # Fallback preview
            pygame.draw.circle(screen, self.data['color'], (cx, cy), 20)
        
        # Text Info
        text_x = self.rect.x + 80
        name_surf = self.font_name.render(self.data['name'], True, TEXT_DARK)
        screen.blit(name_surf, (text_x, self.rect.y + 15))
        
        if not self.is_unlocked:
            price_surf = self.font_price.render(f"₹{self.data['price']} Coins", True, TEXT_GRAY)
            screen.blit(price_surf, (text_x, self.rect.y + 35))
        else:
            status = "Owned"
            status_surf = self.font_price.render(status, True, TEXT_GRAY)
            screen.blit(status_surf, (text_x, self.rect.y + 35))

        # Button Border if "ADD" style
        if self.btn.text == "ADD":
            pygame.draw.rect(screen, THEME_GREEN, self.btn.rect, 1, border_radius=8)
            
        self.btn.draw(screen)

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
                pygame.draw.circle(screen, (218, 165, 32), self.rect.center, self.radius)
                pygame.draw.circle(screen, GOLD, self.rect.center, self.radius - 2)
                pygame.draw.circle(screen, WHITE, (self.rect.centerx - 5, self.rect.centery - 5), 3)
                pygame.draw.circle(screen, THEME_BRAND, self.rect.center, self.radius, 1)

class Bird:
    def __init__(self, face_image=None, bird_data=None):
        self.x = 50
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.width = 50 
        self.height = 40
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        self.face_image = face_image 
        self.bird_data = bird_data if bird_data else BIRD_SHOP_DATA[0]
        self.type = self.bird_data['id']
        self.image = BIRD_IMAGES.get(self.type)

    def jump(self):
        self.velocity = BIRD_JUMP

    def move(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.y = int(self.y)

    def draw(self, screen):
        if self.face_image:
            # Face Mode
            screen.blit(self.face_image, self.rect)
            pygame.draw.circle(screen, WHITE, self.rect.center, self.width//2, 2)
        elif self.image:
            # Image Mode
            screen.blit(self.image, self.rect)
        else:
            # Fallback if image failed to load (simple rect)
            pygame.draw.rect(screen, self.bird_data['color'], self.rect)

class Pipe:
    def __init__(self, coin_image=None):
        self.gap = 170 
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
        pygame.draw.rect(screen, THEME_BRAND, rect, 2)
        
        cap_width = self.width + (self.cap_overhang * 2)
        cap_x = rect.x - self.cap_overhang
        cap_y = rect.bottom - self.cap_height if is_top_pipe else rect.top
        cap_rect = pygame.Rect(cap_x, cap_y, cap_width, self.cap_height)
        
        pygame.draw.rect(screen, THEME_BRAND, cap_rect)
        pygame.draw.line(screen, (255, 160, 80), (cap_rect.left, cap_rect.top), (cap_rect.right, cap_rect.top), 2)
        pygame.draw.rect(screen, BLACK, cap_rect, 1)

    def draw(self, screen):
        self.draw_pillar(screen, self.top_rect, is_top_pipe=True)
        self.draw_pillar(screen, self.bottom_rect, is_top_pipe=False)
        if self.coin and not self.coin.collected:
            self.coin.draw(screen)

# --- Video & Background ---
BACKGROUND_IMAGE = None

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

def load_background_image():
    global BACKGROUND_IMAGE
    if os.path.exists("background.png"):
        try:
            img = pygame.image.load("background.png").convert()
            BACKGROUND_IMAGE = pygame.transform.smoothscale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception as e:
            print(f"Error loading background image: {e}")

def draw_header(screen):
    """Draws the clean white Swiggy-like header."""
    header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 60)
    pygame.draw.rect(screen, WHITE, header_rect)
    # Bottom Shadow
    pygame.draw.line(screen, (220, 220, 220), (0, 60), (SCREEN_WIDTH, 60), 2)
    
    font_brand = pygame.font.SysFont('Verdana', 22, bold=True)
    brand_text = font_brand.render("ACCESCO", True, THEME_BRAND)
    
    font_sub = pygame.font.SysFont('Arial', 12)
    sub_text = font_sub.render("FOOD | FASHION", True, TEXT_GRAY)
    
    screen.blit(brand_text, (20, 10))
    screen.blit(sub_text, (20, 38))

def draw_background(screen, video_surface=None):
    if video_surface:
        screen.blit(video_surface, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 30)) 
        screen.blit(overlay, (0,0))
    elif BACKGROUND_IMAGE:
        screen.blit(BACKGROUND_IMAGE, (0, 0))
    else:
        screen.fill(THEME_BG)

    draw_header(screen)

def capture_face(screen):
    cap = cv2.VideoCapture(0)
    font = pygame.font.SysFont('Verdana', 16)
    clock = pygame.time.Clock()
    box_size = 200
    box_x = (SCREEN_WIDTH - box_size) // 2
    box_y = (SCREEN_HEIGHT - box_size) // 2
    center_point = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    radius = box_size // 2
    
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
        
        # Header Overlay
        header_bg = pygame.Rect(0, 0, SCREEN_WIDTH, 60)
        pygame.draw.rect(screen, THEME_BRAND, header_bg)
        msg = font.render("Align Face inside Circle", True, WHITE)
        msg_rect = msg.get_rect(center=(SCREEN_WIDTH//2, 30))
        screen.blit(msg, msg_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        btn_capture.check_hover(mouse_pos)
        btn_capture.draw(screen)
        
        pygame.display.update()
        clock.tick(30)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release(); pygame.quit(); sys.exit()
            
            clicked = False
            if event.type == pygame.MOUSEBUTTONDOWN and btn_capture.is_clicked(event.pos): clicked = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: clicked = True
                
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
    """Handles the Shop UI with Swiggy-style vertical list."""
    clock = pygame.time.Clock()
    font_coins = pygame.font.SysFont('Verdana', 14, bold=True)
    
    # Create Cards
    cards = []
    card_height = 70
    start_y = 110
    for i, bird_info in enumerate(BIRD_SHOP_DATA):
        is_unlocked = i in game_data['unlocked']
        is_equipped = (i == game_data['current'])
        cards.append(ProductCard(20, start_y + (i * (card_height + 15)), SCREEN_WIDTH - 40, card_height, bird_info, is_unlocked, is_equipped))
    
    btn_back = Button(20, SCREEN_HEIGHT - 60, SCREEN_WIDTH - 40, 45, "BACK TO MENU", "BACK")

    while True:
        screen.fill(THEME_BG)
        draw_header(screen)
        
        # Sub-header
        sub_head_rect = pygame.Rect(0, 60, SCREEN_WIDTH, 40)
        pygame.draw.rect(screen, WHITE, sub_head_rect)
        coin_text = font_coins.render(f"WALLET: ₹{game_data['coins']}", True, THEME_BRAND)
        screen.blit(coin_text, (20, 70))
        
        shop_title = font_coins.render("BIRD SHOP", True, TEXT_DARK)
        screen.blit(shop_title, (SCREEN_WIDTH - 120, 70))

        # Draw Cards
        mouse_pos = pygame.mouse.get_pos()
        for card in cards:
            card.btn.check_hover(mouse_pos)
            card.draw(screen)
            
        btn_back.check_hover(mouse_pos)
        btn_back.draw(screen)
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.is_clicked(event.pos):
                    return game_data
                
                for i, card in enumerate(cards):
                    if card.btn.is_clicked(event.pos):
                        bird_info = card.data
                        if card.is_unlocked:
                            # Equip
                            game_data['current'] = i
                            save_data(game_data)
                            # Update UI
                            for c in cards: c.is_equipped = False
                            card.is_equipped = True
                            card.btn.text = "EQUIPPED"
                            card.btn.color = THEME_BG
                            card.btn.text_color = TEXT_GRAY
                        elif game_data['coins'] >= bird_info['price']:
                            # Buy
                            game_data['coins'] -= bird_info['price']
                            game_data['unlocked'].append(i)
                            game_data['current'] = i
                            save_data(game_data)
                            # Update UI logic to unlocked state
                            card.is_unlocked = True
                            card.is_equipped = True
                            # Reset others
                            for c in cards: 
                                if c != card: c.is_equipped = False
                            card.btn.text = "EQUIPPED"
                            card.btn.color = THEME_BG
                            card.btn.text_color = TEXT_GRAY

# --- State Machine Functions ---

def show_main_menu(screen, bg_cap, game_data):
    font_hero = pygame.font.SysFont('Verdana', 24, bold=True)
    font_sub = pygame.font.SysFont('Verdana', 14)
    
    # Menu Cards (Like Swiggy Categories)
    cx = SCREEN_WIDTH // 2
    
    # Hero Section
    btn_start = Button(20, 200, SCREEN_WIDTH - 40, 100, "PLAY GAME", "START", color=THEME_BRAND, font_size=24)
    
    # Secondary Options row
    btn_shop = Button(20, 320, (SCREEN_WIDTH - 50)//2, 80, "SHOP", "SHOP", color=WHITE, text_color=TEXT_DARK)
    btn_capture = Button(20 + (SCREEN_WIDTH - 50)//2 + 10, 320, (SCREEN_WIDTH - 50)//2, 80, "FACE CAM", "CAPTURE", color=WHITE, text_color=TEXT_DARK)
    
    while True:
        video_surf = get_video_frame(bg_cap) if bg_cap else None
        draw_background(screen, video_surf)
        
        # Welcome Text overlay
        if not video_surf:
            welcome = font_hero.render("Hungry for Game?", True, TEXT_DARK)
            sub = font_sub.render("Order up some fun!", True, TEXT_GRAY)
            screen.blit(welcome, (20, 100))
            screen.blit(sub, (20, 135))
        
        # Draw Buttons
        mouse_pos = pygame.mouse.get_pos()
        for btn in [btn_start, btn_shop, btn_capture]:
            btn.check_hover(mouse_pos)
            btn.draw(screen)
        
        # Floating Coin Balance
        coin_pill_rect = pygame.Rect(20, SCREEN_HEIGHT - 60, 120, 40)
        draw_rounded_rect(screen, WHITE, coin_pill_rect, radius=20)
        coin_txt = font_sub.render(f"₹ {game_data['coins']}", True, THEME_BRAND)
        screen.blit(coin_txt, (40, SCREEN_HEIGHT - 50))
        
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
    
    font_ui = pygame.font.SysFont('Verdana', 16, bold=True)
    
    game_active = True
    
    # Game Over Buttons
    btn_restart = Button(20, 360, SCREEN_WIDTH - 40, 50, "TRY AGAIN", "RESTART")
    btn_menu = Button(20, 420, SCREEN_WIDTH - 40, 50, "MAIN MENU", "MENU", color=WHITE, text_color=THEME_BRAND)
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_active:
                    bird.jump()
                    if sounds['jump']: sounds['jump'].play()
                else:
                    if btn_restart.is_clicked(event.pos): return "RESTART"
                    if btn_menu.is_clicked(event.pos): return "MENU"
            
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
        draw_background(screen, video_surf)

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
            
            # HUD - Swiggy style Pill
            hud_rect = pygame.Rect(SCREEN_WIDTH - 120, 70, 100, 30)
            draw_rounded_rect(screen, WHITE, hud_rect, 15)
            score_surface = font_ui.render(f"Score: {int(score)}", True, THEME_BRAND)
            screen.blit(score_surface, (SCREEN_WIDTH - 110, 75))

        else:
            # GAME OVER CARD
            card_rect = pygame.Rect(20, 150, SCREEN_WIDTH - 40, 340)
            draw_rounded_rect(screen, WHITE, card_rect, 15)
            
            go_font = pygame.font.SysFont('Verdana', 24, bold=True)
            txt_font = pygame.font.SysFont('Verdana', 16)
            
            go_surf = go_font.render("Game Over", True, TEXT_DARK)
            screen.blit(go_surf, (card_rect.centerx - go_surf.get_width()//2, 180))
            
            score_txt = txt_font.render(f"Score: {score}", True, TEXT_GRAY)
            coin_txt = txt_font.render(f"Earned: ₹{collected_in_run}", True, THEME_BRAND)
            
            screen.blit(score_txt, (card_rect.centerx - score_txt.get_width()//2, 230))
            screen.blit(coin_txt, (card_rect.centerx - coin_txt.get_width()//2, 260))
            
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
    
    # Load initial assets
    game_data = load_data()
    load_bird_images() # Load all bird images at start
    load_background_image() # Load background image at start

    sounds = {
        'jump': load_sound("jump.wav"),
        'score': load_sound("score.wav"),
        'crash': load_sound("crash.wav"),
        'collect': load_sound("collect.wav")
    }

    # --- Background Music ---
    music_path = 'music.mp3'
    if os.path.exists(music_path):
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.5) 
        pygame.mixer.music.play(-1) 
    else:
        print(f"Warning: {music_path} not found.")
    
    video_path = 'backgroud.mp4'
    bg_cap = cv2.VideoCapture(video_path) if os.path.exists(video_path) else None
    
    bird_image = None
    coin_image = load_coin_image("coin.jpg", 30)
    
    app_state = "MENU"
    
    while True:
        if app_state == "MENU":
            action = show_main_menu(screen, bg_cap, game_data)
            if action == "QUIT": break
            elif action == "START": app_state = "GAME"
            elif action == "SHOP": app_state = "SHOP"
            elif action == "CAPTURE": app_state = "CAPTURE"
            
        elif app_state == "SHOP":
            game_data = shop_menu(screen, game_data)
            app_state = "MENU" 
            
        elif app_state == "CAPTURE":
            if bg_cap: bg_cap.release()
            bird_image = capture_face(screen)
            if os.path.exists(video_path): bg_cap = cv2.VideoCapture(video_path)
            app_state = "MENU"
            
        elif app_state == "GAME":
            result = run_game_loop(screen, bg_cap, game_data, bird_image, sounds, coin_image)
            if result == "QUIT": break
            elif result == "MENU": app_state = "MENU"
            elif result == "RESTART": pass 

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
