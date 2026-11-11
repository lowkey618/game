import pygame
import random
import os
import numpy as np

pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
pygame.display.set_caption("贪吃蛇｜兰花草 MP3 版")
clock = pygame.time.Clock()

# 颜色
BLACK = (15,15,20)
WHITE = (255,255,255)
GREEN = (0, 220, 80)
HEAD_COLOR = (0,255,160)
RED = (255, 40, 40)
GRAY = (100,100,100)

cell = 20

# ---------------------- 音频工具：淡入淡出，消除咔哒爆音 ----------------------
def apply_fade(wave, fade_ms=6, sample_rate=44100):
    fade_samples = int(sample_rate * fade_ms / 1000)
    if len(wave) <= fade_samples * 2:
        return wave
    wave[:fade_samples] = wave[:fade_samples] * np.linspace(0, 1, fade_samples)
    wave[-fade_samples:] = wave[-fade_samples:] * np.linspace(1, 0, fade_samples)
    return wave

def pulse_wave(freq, duration, vol=0.3, duty=0.25):
    sample_rate = 44100
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, endpoint=False)
    phase = (t * freq) % 1.0
    wave = np.where(phase < duty, 1.0, -1.0)
    wave = wave * (32767 * vol)
    wave = wave.astype(np.int16)
    wave = apply_fade(wave)
    stereo = np.column_stack((wave, wave))
    return pygame.sndarray.make_sound(stereo)

def triangle_wave(freq, duration, vol=0.2):
    sample_rate = 44100
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, endpoint=False)
    wave = 2 * np.abs(2 * ((t * freq) % 1.0) - 1) - 1
    wave = wave * (32767 * vol)
    wave = wave.astype(np.int16)
    wave = apply_fade(wave)
    stereo = np.column_stack((wave, wave))
    return pygame.sndarray.make_sound(stereo)

# ---------------------- 预生成音效（吃、死亡） ----------------------
def make_eat_arp():
    notes = [660, 880, 1100]
    snds = []
    for n in notes:
        snds.append(pulse_wave(n, 0.07, vol=0.42, duty=0.3))
    return snds
eat_arp = make_eat_arp()

def make_gameover_sound():
    notes = [330, 262, 220, 196]
    snds = []
    for n in notes:
        snds.append(triangle_wave(n, 0.18, vol=0.32))
    return snds
gameover_arp = make_gameover_sound()

# ================= MP3 BGM 在这里 =================
# 把兰花草.mp3 和这个 py 文件放同一目录
bgm_path = R"D:/PyCharm test/game/音乐.mp3"
try:
    pygame.mixer.music.load(bgm_path)
    pygame.mixer.music.set_volume(0.25)
    pygame.mixer.music.play(-1)   # -1 = 无限循环
except Exception as e:
    print("警告：找不到 mp3 文件，没有背景音乐", e)

# ========== 字体 ==========
font = None
big_font = None
try:
    simhei_path = r"C:\Windows\Fonts\simhei.ttf"
    if os.path.exists(simhei_path):
        font = pygame.font.Font(simhei_path, 28)
        big_font = pygame.font.Font(simhei_path, 55)
    else:
        font = pygame.font.Font(None, 28)
        big_font = pygame.font.Font(None, 55)
except Exception:
    font = pygame.font.Font(None, 28)
    big_font = pygame.font.Font(None, 55)


snake = [ [WIDTH//2, HEIGHT//2] ]
dx, dy = cell, 0
food = [0,0]
score = 0
game_over = False

MOVE_INTERVAL = 130
last_move_time = pygame.time.get_ticks()

def spawn_food():
    while True:
        fx = random.randrange(0, WIDTH-cell, cell)
        fy = random.randrange(0, HEIGHT-cell, cell)
        if [fx,fy] not in snake:
            return [fx, fy]

food = spawn_food()
running = True

gameover_play_idx = 0
gameover_sound_start = 0
eat_play_idx = 0
eat_sound_start = 0
play_eat_sound = False
play_death_sound = False

while running:
    now = pygame.time.get_ticks()
    screen.fill(BLACK)

    # 如果游戏结束，把背景音乐压低；复活恢复音量
    if game_over:
        pygame.mixer.music.set_volume(0.08)
    else:
        pygame.mixer.music.set_volume(0.25)

    # 吃食物琶音
    if play_eat_sound:
        if now - eat_sound_start > eat_play_idx * 70:
            if eat_play_idx < len(eat_arp):
                eat_arp[eat_play_idx].play()
                eat_play_idx += 1
            else:
                play_eat_sound = False
                eat_play_idx = 0

    # 死亡音效
    if play_death_sound:
        if now - gameover_sound_start > gameover_play_idx * 160:
            if gameover_play_idx < len(gameover_arp):
                gameover_arp[gameover_play_idx].play()
                gameover_play_idx += 1
            else:
                play_death_sound = False
                gameover_play_idx = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if game_over and event.key == pygame.K_r:
                snake = [ [WIDTH//2, HEIGHT//2] ]
                dx, dy = cell, 0
                food = spawn_food()
                score = 0
                game_over = False
                play_death_sound = False
                gameover_play_idx = 0

    keys = pygame.key.get_pressed()
    if not game_over:
        if keys[pygame.K_UP] and dy != cell:
            dx, dy = 0, -cell
        elif keys[pygame.K_DOWN] and dy != -cell:
            dx, dy = 0, cell
        elif keys[pygame.K_LEFT] and dx != cell:
            dx, dy = -cell, 0
        elif keys[pygame.K_RIGHT] and dx != -cell:
            dx, dy = cell, 0

    if not game_over and now - last_move_time > MOVE_INTERVAL:
        last_move_time = now
        head_x, head_y = snake[0]
        new_head = [head_x + dx, head_y + dy]

        if new_head[0]<0 or new_head[0]>=WIDTH or new_head[1]<0 or new_head[1]>=HEIGHT or new_head in snake:
            game_over = True
            play_death_sound = True
            gameover_sound_start = now
        else:
            snake.insert(0, new_head)
            if new_head == food:
                score += 10
                food = spawn_food()
                play_eat_sound = True
                eat_sound_start = now
            else:
                snake.pop()

    pygame.draw.rect(screen, RED, (food[0], food[1], cell, cell), border_radius=4)
    for i, seg in enumerate(snake):
        if i == 0:
            pygame.draw.rect(screen, HEAD_COLOR, (seg[0], seg[1], cell, cell), border_radius=5)
        else:
            pygame.draw.rect(screen, GREEN, (seg[0], seg[1], cell, cell), border_radius=3)

    score_txt = font.render(f"分数：{score}", True, WHITE)
    screen.blit(score_txt, (10, 10))

    if game_over:
        over_text = big_font.render("游戏结束！", True, RED)
        tip_text = font.render("按 R 重新开始", True, GRAY)
        r1 = over_text.get_rect(center=(WIDTH//2, HEIGHT//2 -40))
        r2 = tip_text.get_rect(center=(WIDTH//2, HEIGHT//2 +20))
        screen.blit(over_text, r1)
        screen.blit(tip_text, r2)

    pygame.display.flip()
    clock.tick(60)

pygame.mixer.music.stop()
pygame.quit()