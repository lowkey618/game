import pygame
import os

pygame.init()

# 窗口设置
WIDTH, HEIGHT = 540, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("中国象棋")
clock = pygame.time.Clock()

# 颜色
BG_COLOR = (230, 190, 140)
LINE_COLOR = (80, 40, 20)
RED = (200, 0, 0)
BLACK = (20, 20, 20)
WHITE = (255, 255, 255)
SELECT_COLOR = (255, 80, 80)

# 棋盘参数
GRID = 60
OFFSET_X, OFFSET_Y = 30, 30

# 棋子文字
piece_name = {
    "r": "车", "h": "马", "x": "象", "s": "士", "j": "将", "p": "炮", "z": "卒",
    "R": "車", "H": "馬", "X": "相", "S": "仕", "J": "帥", "P": "砲", "Z": "兵"
}

# 初始棋盘：小写黑方，大写红方
def reset_board():
    return [
        ["r","h","x","s","j","s","x","h","r"],
        ["","","","","","","","",""],
        ["","p","","","","","","p",""],
        ["z","","z","","z","","z","","z"],
        ["","","","","","","","",""],
        ["","","","","","","","",""],
        ["Z","","Z","","Z","","Z","","Z"],
        ["","P","","","","","","P",""],
        ["","","","","","","","",""],
        ["R","H","X","S","J","S","X","H","R"],
    ]

board = reset_board()
turn = "red"   # red红先行，black黑
selected = None # (row, col) 选中棋子
valid_moves = []

# ========== 【修复字体加载，避开win32 SysFont枚举bug】 ==========
font_piece = None
font_tip = None
try:
    # 方案1：尝试微软雅黑
    font_piece = pygame.font.SysFont("microsoftyahei", 40)
    font_tip = pygame.font.SysFont("microsoftyahei", 32)
except Exception:
    try:
        # 方案2：尝试simhei黑体
        font_piece = pygame.font.SysFont("simhei", 40)
        font_tip = pygame.font.SysFont("simhei", 32)
    except Exception:
        # 重点：上面SysFont全部炸了的时候，用内置默认字体！
        # 这个不会触发 initsysfonts_win32 报错，但是**内置字体不支持中文**
        # 棋子中文我们直接加载系统simhei字体文件路径
        try:
            # Windows黑体直接路径，绕开SysFont
            simhei_path = r"C:\Windows\Fonts\simhei.ttf"
            if os.path.exists(simhei_path):
                font_piece = pygame.font.Font(simhei_path, 40)
            else:
                font_piece = pygame.font.Font(None, 40)
            font_tip = pygame.font.Font(None, 32)
        except:
            font_piece = pygame.font.Font(None, 40)
            font_tip = pygame.font.Font(None, 32)

def draw_board():
    screen.fill(BG_COLOR)
    # 竖线
    for c in range(9):
        x = OFFSET_X + c * GRID
        pygame.draw.line(screen, LINE_COLOR, (x, OFFSET_Y), (x, OFFSET_Y + 9 * GRID), 2)
    # 横线
    for r in range(10):
        y = OFFSET_Y + r * GRID
        start_x = OFFSET_X
        end_x = OFFSET_X + 8 * GRID
        pygame.draw.line(screen, LINE_COLOR, (start_x, y), (end_x, y), 2)
    # 楚河汉界文字
    txt1 = font_tip.render("楚河", True, LINE_COLOR)
    txt2 = font_tip.render("漢界", True, LINE_COLOR)
    screen.blit(txt1, (80, OFFSET_Y + 4.4*GRID))
    screen.blit(txt2, (340, OFFSET_Y + 4.4*GRID))
    # 九宫斜线
    # 黑九宫
    pygame.draw.line(screen, LINE_COLOR,
        (OFFSET_X+3*GRID, OFFSET_Y),
        (OFFSET_X+5*GRID, OFFSET_Y+2*GRID), 2)
    pygame.draw.line(screen, LINE_COLOR,
        (OFFSET_X+5*GRID, OFFSET_Y),
        (OFFSET_X+3*GRID, OFFSET_Y+2*GRID), 2)
    # 红九宫
    pygame.draw.line(screen, LINE_COLOR,
        (OFFSET_X+3*GRID, OFFSET_Y+7*GRID),
        (OFFSET_X+5*GRID, OFFSET_Y+9*GRID), 2)
    pygame.draw.line(screen, LINE_COLOR,
        (OFFSET_X+5*GRID, OFFSET_Y+7*GRID),
        (OFFSET_X+3*GRID, OFFSET_Y+9*GRID), 2)

def draw_pieces():
    for r in range(10):
        for c in range(9):
            ch = board[r][c]
            if ch == "":
                continue
            cx = OFFSET_X + c * GRID
            cy = OFFSET_Y + r * GRID
            color = RED if ch.isupper() else BLACK
            # 棋子圆
            pygame.draw.circle(screen, WHITE, (cx, cy), 26)
            pygame.draw.circle(screen, color, (cx, cy), 26, 2)
            text = font_piece.render(piece_name[ch], True, color)
            rect = text.get_rect(center=(cx, cy))
            screen.blit(text, rect)
            # 选中标记
            if selected == (r,c):
                pygame.draw.circle(screen, SELECT_COLOR, (cx, cy), 30, 3)
    # 绘制可走点
    for (nr, nc) in valid_moves:
        nx = OFFSET_X + nc * GRID
        ny = OFFSET_Y + nr * GRID
        pygame.draw.circle(screen, (255,100,100), (nx, ny), 8)

def is_red(ch):
    return ch.isupper()
def is_black(ch):
    return ch.islower()

def get_moves(r, c):
    ch = board[r][c]
    if ch == "":
        return []
    moves = []
    piece = ch.lower()
    red = is_red(ch)

    def in_board(rr, cc):
        return 0 <= rr < 10 and 0 <= cc <9

    def can_move(tr, tc):
        if not in_board(tr,tc):
            return False
        target = board[tr][tc]
        if red:
            return target=="" or is_black(target)
        else:
            return target=="" or is_red(target)

    if piece == "j": # 将/帅
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        for dr,dc in dirs:
            nr, nc = r+dr, c+dc
            if not in_board(nr,nc):
                continue
            # 九宫范围
            if red:
                ok = 7<=nr<=9 and 3<=nc<=5
            else:
                ok = 0<=nr<=2 and 3<=nc<=5
            if ok and can_move(nr,nc):
                moves.append((nr,nc))
        # 将帅对面：中间不能有棋子
        if c == 4:
            if red:
                # 红帅向上看黑将
                check_r = r - 1
            else:
                # 黑将向下看红帅
                check_r = r + 1
            blocked = False
            while in_board(check_r,4):
                if board[check_r][4] != "":
                    if board[check_r][4].lower() == "j" and not blocked:
                        moves.append((check_r,4))
                    blocked = True
                    break
                check_r += -1 if red else 1

    elif piece == "s": # 士
        dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
        for dr,dc in dirs:
            nr, nc = r+dr, c+dc
            if not in_board(nr,nc): continue
            if red:
                ok = 7<=nr<=9 and 3<=nc<=5
            else:
                ok = 0<=nr<=2 and 3<=nc<=5
            if ok and can_move(nr,nc):
                moves.append((nr,nc))

    elif piece == "x": # 象/相
        # 象步，对应蹩腿点
        step_list = [
            (-2, -2, -1, -1),
            (-2,  2, -1,  1),
            ( 2, -2,  1, -1),
            ( 2,  2,  1,  1),
        ]
        for dr, dc, br, bc in step_list:
            nr, nc = r + dr, c + dc
            brr, bcc = r + br, c + bc
            if not in_board(nr, nc):
                continue
            # 象不能过河：红相只能下半盘，黑象上半盘
            if red and nr < 5:
                continue
            if not red and nr > 4:
                continue
            if board[brr][bcc] != "":
                continue
            if can_move(nr, nc):
                moves.append((nr, nc))

    elif piece == "h": # 马
        step_list = [
            (-2, -1, -1, 0),
            (-2,  1, -1, 0),
            (-1, -2, 0, -1),
            (-1,  2, 0,  1),
            ( 1, -2, 0, -1),
            ( 1,  2, 0,  1),
            ( 2, -1,  1, 0),
            ( 2,  1,  1, 0),
        ]
        for dr, dc, br, bc in step_list:
            nr, nc = r + dr, c + dc
            brr, bcc = r + br, c + bc
            if not in_board(nr, nc):
                continue
            if board[brr][bcc] != "":
                continue
            if can_move(nr, nc):
                moves.append((nr, nc))

    elif piece == "r": # 车
        # 上下
        for dr in (-1,1):
            nr = r+dr
            while in_board(nr,c):
                if board[nr][c] == "":
                    moves.append((nr,c))
                    nr += dr
                else:
                    if can_move(nr,c):
                        moves.append((nr,c))
                    break
        # 左右
        for dc in (-1,1):
            nc = c+dc
            while in_board(r,nc):
                if board[r][nc] == "":
                    moves.append((r,nc))
                    nc += dc
                else:
                    if can_move(r,nc):
                        moves.append((r,nc))
                    break

    elif piece == "p": # 炮
        # 上下
        for dr in (-1,1):
            nr = r+dr
            jump = False
            while in_board(nr,c):
                if board[nr][c] == "":
                    if not jump:
                        moves.append((nr,c))
                    nr += dr
                else:
                    if not jump:
                        jump = True
                        nr += dr
                    else:
                        if can_move(nr,c):
                            moves.append((nr,c))
                        break
        # 左右
        for dc in (-1,1):
            nc = c+dc
            jump = False
            while in_board(r,nc):
                if board[r][nc] == "":
                    if not jump:
                        moves.append((r,nc))
                    nc += dc
                else:
                    if not jump:
                        jump = True
                        nc += dc
                    else:
                        if can_move(r,nc):
                            moves.append((r,nc))
                        break

    elif piece == "z": # 卒/兵
        if red:
            dirs = [(-1,0)]
            if r <=4:
                dirs += [(0,-1),(0,1)]
        else:
            dirs = [(1,0)]
            if r >=5:
                dirs += [(0,-1),(0,1)]
        for dr,dc in dirs:
            nr, nc = r+dr, c+dc
            if in_board(nr,nc) and can_move(nr,nc):
                moves.append((nr,nc))
    return moves

def click_pos(mx, my):
    c = round((mx - OFFSET_X)/GRID)
    r = round((my - OFFSET_Y)/GRID)
    if 0<=r<10 and 0<=c<9:
        return r,c
    return None

def is_check(side):
    """side: red / black 是否被将军"""
    king_ch = "J" if side=="red" else "j"
    kr, kc = -1,-1
    for rr in range(10):
        for cc in range(9):
            if board[rr][cc]==king_ch:
                kr,kc = rr,cc
                break
        if kr!=-1:break
    # 遍历对方所有棋子，看能不能吃到王
    for rr in range(10):
        for cc in range(9):
            p = board[rr][cc]
            if p=="":continue
            if side=="red" and is_red(p): continue
            if side=="black" and is_black(p): continue
            mv = get_moves(rr,cc)
            if (kr,kc) in mv:
                return True
    return False

def has_legal_move(side):
    """是否还有合法走法（解将/困毙判断）"""
    for r in range(10):
        for c in range(9):
            p = board[r][c]
            if p=="":continue
            if side=="red" and not is_red(p): continue
            if side=="black" and not is_black(p): continue
            mvs = get_moves(r,c)
            for (nr,nc) in mvs:
                # 模拟走子
                bak = board[nr][nc]
                board[nr][nc] = p
                board[r][c] = ""
                ok = not is_check(side)
                # 回滚
                board[r][c] = p
                board[nr][nc] = bak
                if ok:
                    return True
    return False

game_end = False
winner = ""

running = True
while running:
    draw_board()
    draw_pieces()

    # 提示文字
    if not game_end:
        tip = f"【红方走棋】" if turn=="red" else "【黑方走棋】"
    else:
        tip = f"{winner}获胜！按R重开"
    t = font_tip.render(tip, True, (20,20,20))
    screen.blit(t, (10, HEIGHT - 35))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # 重置棋盘
                board = reset_board()
                turn = "red"
                selected = None
                valid_moves = []
                game_end = False
                winner = ""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button==1 and not game_end:
            pos = click_pos(*event.pos)
            if pos is None:
                selected = None
                valid_moves = []
                continue
            r,c = pos
            piece = board[r][c]
            if selected is None:
                # 选中自己棋子
                if turn=="red" and piece.isupper():
                    selected = (r,c)
                    valid_moves = get_moves(r,c)
                elif turn=="black" and piece.islower():
                    selected = (r,c)
                    valid_moves = get_moves(r,c)
            else:
                sr, sc = selected
                # 点击同一个棋子：取消选中
                if (r,c) == (sr,sc):
                    selected = None
                    valid_moves = []
                    continue
                if (r,c) in valid_moves:
                    # 执行移动
                    bak = board[r][c]
                    board[r][c] = board[sr][sc]
                    board[sr][sc] = ""
                    # ✅ 走棋之后，自己不能处于被将军状态，违规撤销
                    if is_check(turn):
                        board[sr][sc] = board[r][c]
                        board[r][c] = bak
                    else:
                        # 切换对手回合
                        oppo = "black" if turn=="red" else "red"
                        # 判断对手：是否被将死 / 困毙
                        if not has_legal_move(oppo):
                            game_end = True
                            winner = "红方" if turn == "red" else "黑方"
                        turn = oppo
                # 直接点己方别的棋子，切换选中
                if (turn=="red" and board[r][c].isupper()) or (turn=="black" and board[r][c].islower()):
                    selected = (r,c)
                    valid_moves = get_moves(r,c)
                else:
                    selected = None
                    valid_moves = []

    pygame.display.flip()
    clock.tick(60)

pygame.quit()