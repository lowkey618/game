import pygame
import math
import random

# -------------------------- 初始化配置 --------------------------
pygame.init()
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("美式黑八台球")
clock = pygame.time.Clock()
FPS = 60

# 颜色
GREEN = (34, 139, 34)
BROWN = (101, 67, 33)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 200, 0)
RED = (220, 20, 20)

BALL_RADIUS = 14
HOLE_RADIUS = 22
FRICTION = 0.98  # 摩擦力
SPEED_LIMIT = 0.3

# 袋口位置 6个袋
holes = [
    (40, 40),
    (WIDTH//2, 30),
    (WIDTH-40, 40),
    (40, HEIGHT-40),
    (WIDTH//2, HEIGHT-30),
    (WIDTH-40, HEIGHT-40)
]

# ========== 【修复重点】全局预加载字体，不再在draw函数里面反复创建 ==========
try:
    ball_font = pygame.font.SysFont("simhei", 12)
    ui_font = pygame.font.SysFont("simhei", 22)
    over_font = pygame.font.SysFont("simhei", 40)
except:
    # 找不到黑体，改用pygame默认字体兜底
    ball_font = pygame.font.Font(None, 12)
    ui_font = pygame.font.Font(None, 22)
    over_font = pygame.font.Font(None, 40)


class Ball:
    def __init__(self, x, y, color, number, is_solid=False):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.color = color
        self.number = number
        self.radius = BALL_RADIUS
        self.is_solid = is_solid  # True实球(1‑7), False花球(9‑15), 8号黑八

    def update(self):
        # 摩擦力减速
        self.vx *= FRICTION
        self.vy *= FRICTION
        self.x += self.vx
        self.y += self.vy

        # 桌壁反弹
        left, right = 50, WIDTH-50
        top, bot = 50, HEIGHT-50
        if self.x - self.radius < left:
            self.x = left + self.radius
            self.vx *= -0.9
        if self.x + self.radius > right:
            self.x = right - self.radius
            self.vx *= -0.9
        if self.y - self.radius < top:
            self.y = top + self.radius
            self.vy *= -0.9
        if self.y + self.radius > bot:
            self.y = bot - self.radius
            self.vy *= -0.9

        # 极小速度置零
        if abs(self.vx) < SPEED_LIMIT:
            self.vx = 0
        if abs(self.vy) < SPEED_LIMIT:
            self.vy = 0

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
        if self.number != 0:
            text = ball_font.render(str(self.number), True, WHITE if self.number == 8 else BLACK)
            surf.blit(text, (self.x-6, self.y-7))

    def is_in_hole(self):
        for (hx, hy) in holes:
            dist = math.hypot(self.x - hx, self.y - hy)
            if dist < HOLE_RADIUS:
                return True
        return False

# 球体碰撞
def ball_collide(b1: Ball, b2: Ball):
    dx = b2.x - b1.x
    dy = b2.y - b1.y
    dist = math.hypot(dx, dy)
    min_dist = b1.radius + b2.radius
    if dist >= min_dist:
        return
    # 分离重叠
    overlap = min_dist - dist
    nx = dx / dist
    ny = dy / dist
    b1.x -= overlap * nx * 0.5
    b2.x += overlap * nx * 0.5
    b1.y -= overlap * ny * 0.5
    b2.y += overlap * ny * 0.5

    # 弹性碰撞
    v1n = b1.vx * nx + b1.vy * ny
    v2n = b2.vx * nx + b2.vy * ny
    v1t_x = b1.vx - v1n * nx
    v1t_y = b1.vy - v1n * ny
    v2t_x = b2.vx - v2n * nx
    v2t_y = b2.vy - v2n * ny
    # 交换法向速度
    b1.vx = v2n * nx + v1t_x
    b1.vy = v2n * ny + v1t_y
    b2.vx = v1n * nx + v2t_x
    b2.vy = v1n * ny + v2t_y


def create_rack():
    """摆球：黑八在中间，实球花球交错"""
    balls = []
    # 白球 0号
    white = Ball(180, HEIGHT//2, WHITE, 0)
    balls.append(white)

    # 三角摆球位置
    start_x = 650
    start_y = HEIGHT//2
    offset_y = BALL_RADIUS * 2 * 0.866
    offset_x = BALL_RADIUS * 2

    ball_nums = [
        [1],
        [2, 3],
        [4, 8, 5],
        [6, 7, 9, 10],
        [11,12,13,14,15]
    ]
    solid_list = set(range(1,8))
    for row_idx, row in enumerate(ball_nums):
        row_len = len(row)
        y0 = start_y - (row_len-1)*offset_y*0.5
        for col_idx, num in enumerate(row):
            bx = start_x + row_idx * offset_x
            by = y0 + col_idx * offset_y
            is_solid = num in solid_list
            col = RED if is_solid else YELLOW
            if num ==8:
                col = BLACK
            b = Ball(bx, by, col, num, is_solid)
            balls.append(b)
    return balls


def main():
    balls = create_rack()
    cue_aim = False
    aim_start = (0,0)
    game_over = False
    win_msg = ""
    my_type = None  # "solid" / "stripe" / None
    solid_potted = 0
    stripe_potted = 0
    eight_potted = False

    while True:
        screen.fill(BROWN)
        # 画台呢
        pygame.draw.rect(screen, GREEN, (50,50,WIDTH-100,HEIGHT-100))
        # 画袋口
        for hx, hy in holes:
            pygame.draw.circle(screen, BLACK, (hx, hy), HOLE_RADIUS)

        # 事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if game_over:
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 鼠标按下开始瞄准
                cue_aim = True
                aim_start = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONUP and event.button ==1 and cue_aim:
                # 出杆
                mx, my = pygame.mouse.get_pos()
                white = balls[0]
                dx = aim_start[0] - mx
                dy = aim_start[1] - my
                power = math.hypot(dx, dy)
                power = min(power,120)
                angle = math.atan2(dy, dx)
                white.vx = math.cos(angle) * power * 0.12
                white.vy = math.sin(angle) * power * 0.12
                cue_aim = False

        # 更新球
        moving = False
        for b in balls:
            b.update()
            if abs(b.vx) > 0.01 or abs(b.vy) >0.01:
                moving = True

        # 球体两两碰撞
        for i in range(len(balls)):
            for j in range(i+1, len(balls)):
                ball_collide(balls[i], balls[j])

        # 检测进袋
        new_balls = []
        for b in balls:
            if b.is_in_hole():
                if b.number == 0:
                    # 白球落袋
                    game_over = True
                    win_msg = "白球进袋！游戏失败！"
                elif b.number ==8:
                    eight_potted = True
                    if my_type is None:
                        game_over = True
                        win_msg = "黑八过早进袋，你输了！"
                    else:
                        if (my_type=="solid" and solid_potted>=7) or (my_type=="stripe" and stripe_potted>=7):
                            game_over = True
                            win_msg = "恭喜！打进黑八，胜利！"
                        else:
                            game_over = True
                            win_msg = "黑八提前进袋，失败！"
                else:
                    if b.is_solid:
                        solid_potted +=1
                    else:
                        stripe_potted +=1
                    # 首次进球确定自己的花色
                    if my_type is None:
                        my_type = "solid" if b.is_solid else "stripe"
            else:
                new_balls.append(b)
        balls = new_balls

        # 绘制球
        for b in balls:
            b.draw(screen)

        # 瞄准线
        if cue_aim and not moving:
            mx, my = pygame.mouse.get_pos()
            wx, wy = balls[0].x, balls[0].y
            pygame.draw.line(screen, (255,255,0), (wx,wy), (mx,my),2)

        # UI文字
        t1 = ui_font.render(f"实球进袋:{solid_potted}/7 | 花球进袋:{stripe_potted}/7", True, WHITE)
        if my_type is None:
            t2 = ui_font.render("尚未确定花色，击球落袋来选定", True, WHITE)
        else:
            tname = "实球(1‑7)" if my_type=="solid" else "花球(9‑15)"
            t2 = ui_font.render(f"你的花色：{tname}，打完后打黑八", True, WHITE)
        screen.blit(t1, (60,10))
        screen.blit(t2, (60,35))

        if game_over:
            over_text = over_font.render(win_msg, True, (255,80,80))
            screen.blit(over_text, (WIDTH//2-220, HEIGHT//2))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()