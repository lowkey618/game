import pygame
import random
import os

pygame.init()

WIDTH, HEIGHT = 800, 600
# 开启双缓冲，优化渲染
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
pygame.display.set_caption("贪吃蛇（低延迟版）")
clock = pygame.time.Clock()

# 颜色
BLACK = (15,15,20)
WHITE = (255,255,255)
GREEN = (0, 220, 80)
HEAD_COLOR = (0,255,160)
RED = (255, 40, 40)
GRAY = (100,100,100)

cell = 20

# ========== 修复字体，避开SysFont的bug ==========
font = None
big_font = None
try:
    simhei_path = r"C:\Windows\Fonts\simhei.ttf"
    if os.path.exists(simhei_path):
        font = pygame.font.Font(simhei_path, 28)
        big_font = pygame.font.Font(simhei_path, 55)
    else:
        # 找不到黑体，使用pygame内置字体（不崩溃，中文会方框）
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

MOVE_INTERVAL = 130  # 蛇移动间隔（毫秒，越小越快）
last_move_time = pygame.time.get_ticks()

def spawn_food():
    while True:
        fx = random.randrange(0, WIDTH-cell, cell)
        fy = random.randrange(0, HEIGHT-cell, cell)
        if [fx,fy] not in snake:
            return [fx, fy]

food = spawn_food()

running = True
while running:
    now = pygame.time.get_ticks()
    screen.fill(BLACK)

    # 事件只处理关闭、R重置
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

    # ========== 核心：实时读取按键，没有系统长按延迟 ==========
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

    # 定时移动蛇，和帧率解绑
    if not game_over and now - last_move_time > MOVE_INTERVAL:
        last_move_time = now
        head_x, head_y = snake[0]
        new_head = [head_x + dx, head_y + dy]

        # 撞墙
        if new_head[0]<0 or new_head[0]>=WIDTH or new_head[1]<0 or new_head[1]>=HEIGHT:
            game_over = True
        # 撞自己
        if new_head in snake:
            game_over = True

        snake.insert(0, new_head)
        if new_head == food:
            score += 10
            food = spawn_food()
        else:
            snake.pop()

    # 绘制食物
    pygame.draw.rect(screen, RED, (food[0], food[1], cell, cell), border_radius=4)
    # 绘制蛇
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

pygame.quit()