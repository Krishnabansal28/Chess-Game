import pygame

class Board:
    initial_grid = [
        ["br","bn","bb","bq","bk","bb","bn","br"],
        ["bp","bp","bp","bp","bp","bp","bp","bp"],
        ["--","--","--","--","--","--","--","--"],
        ["--","--","--","--","--","--","--","--"],
        ["--","--","--","--","--","--","--","--"],
        ["--","--","--","--","--","--","--","--"],
        ["wp","wp","wp","wp","wp","wp","wp","wp"],
        ["wr","wn","wb","wq","wk","wb","wn","wr"]
    ]

    def __init__(self):
        self.grid = [row[:] for row in self.initial_grid]
        self.last_move = None
        self.has_moved = {
            "wrl" : False, "wk" : False, "wrr" : False,
            "brl" : False, "bk" : False, "brr" : False
        }
        self.init_pos = None
        self.dest_pos = None

    def get_piece(self, row, col):
        return self.grid[row][col]
    
    def is_empty(self, row, col):
        return self.grid[row][col] == "--"
    
    def in_bounds(self, row, col):
        return 0 <= row < 8 and 0 <= col < 8
    
    def find_king(self, clr):
        target = f"{clr[0]}k"
        for r in range(8):
            for c in range(8):
                if self.grid[r][c] == target:
                    return (r, c)
        return None
    
    def simulate_move(self, from_row, from_col, to_row, to_col):
        piece = self.grid[from_row][from_col]
        captured = self.grid[to_row][to_col]

        en_passant = False
        ep_captured = None

        if piece[1] == "p" and from_col != to_col and captured == "--":
            en_passant = True
            ep_captured = self.grid[from_row][to_col]
            self.grid[from_row][to_col] = "--"
        
        self.grid[to_row][to_col] = piece
        self.grid[from_row][from_col] = "--"

        return captured, en_passant, ep_captured
    
    def revert_move(self, from_row, from_col, to_row, to_col, captured, en_passant, ep_captured):
        self.grid[from_row][from_col] = self.grid[to_row][to_col]
        self.grid[to_row][to_col] = captured

        if en_passant:
            self.grid[from_row][to_col] = ep_captured

    def move_piece(self, src, dst):
        from_row, from_col = src
        to_row, to_col = dst
        piece = self.grid[from_row][from_col]
        clr = piece[0]

        en_passant = False
        castling = False

        if piece[1] == "p" and abs(from_col - to_col) == 1 and self.is_empty(to_row, to_col):
            en_passant = True

        if piece[1] == "k" and abs(from_col - to_col) == 2:
            castling = True

        self.grid[to_row][to_col] = piece
        self.grid[from_row][from_col] = "--"

        if en_passant:
            self.grid[from_row][to_col] = "--"

        if castling:
            if to_col > from_col:
                self.grid[from_row][to_col-1] = self.grid[from_row][7]
                self.grid[from_row][7] = "--"
                self.has_moved[f"{clr}rr"] = True
            else:
                self.grid[from_row][to_col+1] = self.grid[from_row][0]
                self.grid[from_row][0] = "--"
                self.has_moved[f"{clr}rl"] = True

        if piece[1] == "k":
            self.has_moved[f"{clr}k"] = True
        elif piece[1] == "r":
            if from_row == 7 and from_col == 0:
                self.has_moved["wrl"] = True
            elif from_row == 7 and from_col == 7:
                self.has_moved["wrr"] = True
            elif from_row == 0 and from_col == 0:
                self.has_moved["brl"] = True
            elif from_row == 0 and from_col == 7:
                self.has_moved["brr"] = True

        self.last_move = (piece, from_row, from_col, to_row, to_col)
        self.init_pos = src
        self.dest_pos = dst

    def promote_pawn(self, row, col, clr, choice = "q"):
        self.grid[row][col] = f"{clr[0]}{choice}"
                
class MoveGenerator:
    def __init__(self, board):
        self.board = board

    def get_legal_moves(self, row, col):
        b = self.board
        piece = b.get_piece(row, col)
        if piece == "--":
            return []
        raw = self._get_raw_moves(piece[1], row, col)
        legal = []
        clr = "white" if piece[0] == "w" else "black"
        for move in raw:
            captured, en_passant, ep_captured = b.simulate_move(row, col, move[0], move[1])
            if not self.is_in_check(clr):
                legal.append(move)
            b.revert_move(row, col, move[0], move[1], captured, en_passant, ep_captured)

        return legal
    
    def has_legal_moves(self, clr):
        b = self.board

        for r in range(8):
            for c in range(8):
                if b.get_piece(r, c) != "--" and b.get_piece(r, c)[0] == clr[0]:
                    if self.get_legal_moves(r, c):
                        return True
        
        return False
    
    def is_in_check(self, clr):
        king_pos = self.board.find_king(clr)
        if not king_pos:
            return False
        attacking = "black" if clr == "white" else "white"
        return self._is_square_attacked(king_pos[0], king_pos[1], attacking)
    
    def is_checkmate(self, clr):
        return self.is_in_check(clr) and not self.has_legal_moves(clr)
    
    def is_stalemate(self, clr):
        return not self.is_in_check(clr) and not self.has_legal_moves(clr)
    
    def _get_raw_moves(self, piece_type, row, col):
        dispatch = {
            "p" : self._pawn_moves,
            "r" : self._rook_moves,
            "n" : self._knight_moves,
            "b" : self._bishop_moves,
            "q" : self._queen_moves,
            "k" : self._king_moves
        }

        return dispatch[piece_type](row, col)
    
    def _get_attack_squares(self, piece_type, row, col):
        dispatch = {
            "p" : self._pawn_attacks,
            "r" : self._rook_moves,
            "n" : self._knight_moves,
            "b" : self._bishop_moves,
            "q" : self._queen_moves,
            "k" : self._king_attacks
        }

        return dispatch[piece_type](row, col)
    
    def _pawn_moves(self, row, col):
        b = self.board
        piece = b.get_piece(row, col)
        clr = "white" if piece[0] == "w" else "black"
        direction = 1 if clr == "black" else -1
        moves = []

        # forward
        if b.in_bounds(row + direction, col) and b.is_empty(row + direction, col):
            moves.append((row + direction, col))
            start_row = 6 if clr == "white" else 1
            if row == start_row and b.is_empty(row + 2 * direction, col):
                moves.append((row + 2 * direction, col))

        # diagonal captures
        for dc in [-1, 1]:
            nr, nc = row + direction, col + dc
            if b.in_bounds(nr, nc) and not b.is_empty(nr, nc) and b.get_piece(nr, nc)[0] != piece[0]:
                moves.append((nr, nc))

        # en passant
        lm = b.last_move
        ep_row = 3 if clr == "white" else 4
        if row == ep_row and lm and lm[0][1] == "p" and lm[0][0] != piece[0]:
            if abs(lm[1] - lm[3]) == 2 and lm[3] == row and abs(lm[4] - col) == 1:
                moves.append((row + direction, lm[4]))

        return moves
    
    def _pawn_attacks(self, row, col):
        b = self.board
        piece = b.get_piece(row, col)
        direction = -1 if piece[0] == "w" else 1
        attacks = []

        for dc in [-1, 1]:
            r, c = row + direction, col + dc
            if b.in_bounds(r, c):
                attacks.append((r, c))

        return attacks
    
    def _sliding_moves(self, row, col, directions):
        b = self.board
        piece = b.get_piece(row, col)
        moves = []

        for dr, dc in directions:
            for i in range(1, 8):
                r, c = row + dr * i, col + dc * i
                if not b.in_bounds(r, c):
                    break
                target = b.get_piece(r, c)
                if target == "--":
                    moves.append((r, c))
                elif target[0] != piece[0]:
                    moves.append((r, c))
                    break
                else:
                    break

        return moves
    
    def _rook_moves(self, row, col):
        return self._sliding_moves(row, col, [(-1, 0), (1, 0), (0, -1), (0, 1)])
    
    def _bishop_moves(self, row, col):
        return self._sliding_moves(row, col, [(-1, -1), (-1, 1), (1, -1), (1, 1)])
    
    def _queen_moves(self, row, col):
        return self._rook_moves(row, col) + self._bishop_moves(row, col)
    
    def _knight_moves(self, row, col):
        b = self.board
        piece = b.get_piece(row, col)
        moves = []

        for dr, dc in [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (1, -2), (-1, 2), (1, 2)]:
            r, c = row + dr, col + dc
            if b.in_bounds(r, c) and (b.is_empty(r, c) or b.get_piece(r, c)[0] != piece[0]):
                moves.append((r, c))

        return moves

    def _king_moves(self, row, col):
        b = self.board
        piece = b.get_piece(row, col)
        clr = "white" if piece[0] == "w" else "black"
        moves = []

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            r, c = row + dr, col + dc
            if b.in_bounds(r, c) and (b.is_empty(r, c) or b.get_piece(r, c)[0] != piece[0]):
                moves.append((r, c))

        # castling
        for side in ["l", "r"]:
            dest = self._can_castle(clr, row, col, side)
            if dest is not None:
                moves.append((row, dest))

        return moves
    
    def _king_attacks(self, row, col):
        b = self.board
        attacks = []

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            r, c = row + dr, col + dc
            if b.in_bounds(r, c):
                attacks.append((r, c))
        return attacks
            
    def _can_castle(self, clr, king_row, king_col, side):
        b = self.board

        if b.has_moved[f"{clr[0]}k"] or b.has_moved[f"{clr[0]}r{side}"]:
            return None
        
        # check if rook actually exists on it starting square
        rook_col = 0 if side == "l" else 7
        expected_rook = f"{clr[0]}r"
        if b.get_piece(king_row, rook_col) != expected_rook:
            return None
        
        # squares between king and rook must be empty
        step = 1 if rook_col > king_col else -1
        if any(not b.is_empty(king_row, c) for c in range(king_col + step, rook_col, step)):
            return None
        
        attacking = "black" if clr == "white" else "white"

        # king cannot be in check currently
        if self._is_square_attacked(king_row, king_col, attacking):
            return None
        
        # king cannot pass through or land on an attacked square
        dest_col = king_col + 2 * step
        if any(self._is_square_attacked(king_row, c, attacking) for c in range(king_col + step, dest_col + step, step)):
            return None
        
        return dest_col
        
    def _is_square_attacked(self, row, col, by_clr):
        b = self.board
        for r in range(8):
            for c in range(8):
                p = b.get_piece(r, c)
                if p == "--" or p[0] != by_clr[0]:
                    continue
                attacks = self._get_attack_squares(p[1], r, c)
                if(row, col) in attacks:
                    return True        
        return False
    
class Renderer:
    # colors
    WHITE = (255,255,255)
    BLACK = (0,0,0)
    LIGHT_SQ = (235,236,208)
    DARK_SQ = (115,149,82)
    BACKGROUND = (48,46,43)
    MENU_CLR = (38,37,34)
    HIGHLIGHT_MOVES_DARK = (99,128,70,128)
    HIGHLIGHT_MOVES_LIGHT = (202,203,179,128)
    HIGHLIGHT_SELECTED_DARK = (185,202,67)
    HIGHLIGHT_SELECTED_LIGHT = (245,246,130)
    CAPTURE_DARK = (159,173,58,128)
    CAPTURE_LIGHT = (202,203,179,128)
    LAST_MOVE_CLR = [(185,202,67),(245,246,130)]

    SQUARE_SIZE = 75
    MARGIN_X = 20
    MARGIN_Y = 40
    MENU_SIZE = 50

    def __init__(self, screen):
        self.screen = screen
        self.piece_images = {}
        self.font = pygame.font.SysFont("Algerian", 20)
        self.coord_font = pygame.font.SysFont("arial", 15, "bold")
        self.image_folder = "assets"
        self.load_images(self.image_folder)

    def load_images(self, folder):
        pieces = ["wp", "bp", "wr", "br", "wn", "bn", "wb", "bb", "wq", "bq", "wk", "bk"]
        sz = self.SQUARE_SIZE
        for p in pieces:
            raw = pygame.image.load(f"{folder}/{p}.png")
            self.piece_images[p] = pygame.transform.smoothscale(raw, (sz - sz // 8, sz - sz // 8))

    def draw(self, board, selected_square, valid_moves, chance):
        s = self.screen
        s.fill(self.BACKGROUND)
        s.fill(self.MENU_CLR, (0, 0, s.get_width(), self.MENU_SIZE))

        self._draw_squares(board, selected_square)
        self._draw_last_move(board)
        self._draw_coordinates()
        self._draw_highlights(board, valid_moves)
        self._draw_pieces(board)
        self._draw_turn(chance)

    def _sqr_rect(self, row, col):
        x = col * self.SQUARE_SIZE + self.MARGIN_X
        y = row * self.SQUARE_SIZE + self.MARGIN_Y + self.MENU_SIZE
        return (x, y, self.SQUARE_SIZE, self.SQUARE_SIZE)
    
    def _is_light(self, row, col):
        return (row + col) % 2 == 0

    def _draw_squares(self, board, selected_square):
        for r in range(8):
            for c in range(8):
                clr = self.LIGHT_SQ if self._is_light(r, c) else self.DARK_SQ
                self.screen.fill(clr, self._sqr_rect(r, c))

        if selected_square:
            r, c = selected_square
            clr = self.HIGHLIGHT_SELECTED_LIGHT if self._is_light(r, c) else self.HIGHLIGHT_SELECTED_DARK
            self.screen.fill(clr, self._sqr_rect(r, c))

    def _draw_coordinates(self):
        # draw files (a - h)
        files = "abcdefgh"
        for col in range(8):
            file_clr = self.DARK_SQ if self._is_light(7, col) else self.LIGHT_SQ
            file_surf = self.coord_font.render(files[col], True, file_clr)
            fx = self.MARGIN_X + col * self.SQUARE_SIZE + self.SQUARE_SIZE - file_surf.get_width() - 3
            fy = self.MENU_SIZE + self.MARGIN_Y + 8 * self.SQUARE_SIZE - file_surf.get_height() - 3
            self.screen.blit(file_surf, (fx, fy))

        # draw ranks (1 - 8)
        for row in range(8):
            rank_num = str(8 - row)
            rank_clr = self.DARK_SQ if self._is_light(row, 0) else self.LIGHT_SQ
            rank_surf = self.coord_font.render(rank_num, True, rank_clr)
            rx = self.MARGIN_X + 3
            ry = self.MENU_SIZE + self.MARGIN_Y + row * self.SQUARE_SIZE + 4
            self.screen.blit(rank_surf, (rx, ry))

    def _draw_last_move(self, board):
        if not board.init_pos or not board.dest_pos:
            return
        for pos in [board.init_pos, board.dest_pos]:
            r, c = pos
            clr = self.LAST_MOVE_CLR[1] if self._is_light(r, c) else self.LAST_MOVE_CLR[0]
            self.screen.fill(clr, self._sqr_rect(r, c))

    def _draw_highlights(self, board, valid_moves):
        for r, c in valid_moves:
            rect = self._sqr_rect(r, c)
            cx = rect[0] + self.SQUARE_SIZE // 2
            cy = rect[1] + self.SQUARE_SIZE // 2
            if board.is_empty(r, c):
                clr = self.HIGHLIGHT_MOVES_LIGHT if self._is_light(r, c) else self.HIGHLIGHT_MOVES_DARK
                pygame.draw.circle(self.screen, clr, (cx, cy), self.SQUARE_SIZE // 6)
            else:
                clr = self.CAPTURE_LIGHT if self._is_light(r, c) else self.CAPTURE_DARK
                pygame.draw.circle(self.screen, clr, (cx, cy), self.SQUARE_SIZE // 2, 8)

    def _draw_pieces(self, board):
        for r in range(8):
            for c in range(8):
                piece = board.get_piece(r, c)
                if piece != "--":
                    img = self.piece_images[piece]
                    rect = pygame.Rect(self._sqr_rect(r, c))
                    self.screen.blit(img, img.get_rect(center = rect.center))

    def _draw_turn(self, chance):
        text = self.font.render(f"Chance : {chance.capitalize()}", True, self.WHITE)
        rect = text.get_rect(center = pygame.Rect(0, 0, self.screen.get_width(), self.MENU_SIZE).center)
        self.screen.blit(text, rect)

    def show_promotion_menu(self, clr):
        options = [("q", "Queen"), ("r", "Rook"), ("b", "Bishop"), ("n", "Knight")]
        box_w, box_h = 160, 60
        start_x = (self.screen.get_width() - box_w) // 2
        start_y = (self.screen.get_height() - box_h * 4) // 2
        
        surf = pygame.Surface((box_w, box_h * 4))
        surf.fill(self.WHITE)
        font = pygame.font.SysFont("Algerian", 22)

        for i, (code, name) in enumerate(options):
            img = pygame.transform.smoothscale(pygame.image.load(f"{self.image_folder}/{clr[0]}{code}.png"), (50, 50))
            surf.blit(img, (5, i * box_h + 5))
            label = font.render(name, True, (30,30,30))
            surf.blit(label, (65, i * box_h + 18))

        self.screen.blit(surf, (start_x, start_y))
        pygame.display.flip()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "q"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if start_x <= mx < start_x + box_w:
                        idx = (my - start_y) // box_h
                        if 0 <= idx < 4:
                            return options[idx][0]

    def show_game_over(self, message):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        font_big = pygame.font.SysFont("Algerian", 42)
        font_sub = pygame.font.SysFont("Algerian", 22)
        text = font_big.render(message, True, (255, 220, 80))
        sub = font_sub.render("Press R to restart or ESC to quit", True, (200, 200, 200))
        cx, cy = self.screen.get_width() // 2, self.screen.get_height() // 2
        self.screen.blit(text, text.get_rect(center = (cx, cy - 30)))
        self.screen.blit(sub, sub.get_rect(center = (cx, cy + 30)))
        
class Game:
    SQUARE_SIZE = Renderer.SQUARE_SIZE
    MARGIN_X = Renderer.MARGIN_X
    MARGIN_Y = Renderer.MARGIN_Y
    MENU_SIZE = Renderer.MENU_SIZE

    def __init__(self):
        pygame.init()
        screen_w = 8 * self.SQUARE_SIZE + 2 * self.MARGIN_X
        screen_h = 8 * self.SQUARE_SIZE + 2 * self.MARGIN_Y + self.MENU_SIZE
        screen = pygame.display.set_mode((screen_w, screen_h))
        pygame.display.set_caption("CHESS")

        self.board = Board()
        self.move_gen = MoveGenerator(self.board)
        self.renderer = Renderer(screen)

        self.chance = "white"
        self.selected_square = None
        self.valid_moves = []
        self.game_over = False
        self.game_over_msg = ""
        self.running = True
    
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.key == pygame.K_r and self.game_over:
                        self._reset()
                    if event.key == pygame.K_q and not self.game_over:
                        self.game_over = True
                        self.game_over_msg = "Game Abort!"
                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    self._handle_click(event.pos)

            self.renderer.draw(self.board, self.selected_square, self.valid_moves, self.chance)

            if self.game_over:
                self.renderer.show_game_over(self.game_over_msg)

            pygame.display.update()
            clock.tick(60)

        pygame.quit()

    def _reset(self):
        self.board = Board()
        self.move_gen = MoveGenerator(self.board)
        self.chance = "white"
        self.selected_square = None
        self.valid_moves = []
        self.game_over = False
        self.game_over_msg = ""
        self.running = True

    def _handle_click(self, pos):
        col = (pos[0] - self.MARGIN_X) // self.SQUARE_SIZE
        row = (pos[1] - self.MARGIN_Y - self.MENU_SIZE) // self.SQUARE_SIZE

        if not (0 <= row < 8 and 0 <= col < 8):
            return
        
        if self.selected_square:
            if (row, col) in self.valid_moves:
                self._execute_move(self.selected_square, (row, col))
                self.selected_square = None
                self.valid_moves = []
            elif self._is_own_piece(row, col):
                self._select(row, col)
            else:
                self.selected_square = None
                self.valid_moves = []

        else:
            if self._is_own_piece(row, col):
                self._select(row, col)

    def _select(self, row, col):
        self.selected_square = (row, col)
        self.valid_moves = self.move_gen.get_legal_moves(row, col)

    def _is_own_piece(self, row, col):
        piece = self.board.get_piece(row, col)
        return piece != "--" and piece[0] == self.chance[0]
    
    def _execute_move(self, src, dst):
        self.board.move_piece(src, dst)
        to_row, to_col = dst
        piece = self.board.get_piece(to_row, to_col)

        # pawn promotion
        if piece[1] == "p":
            promote_row = 0 if self.chance == "white" else 7
            if to_row == promote_row:
                choice = self.renderer.show_promotion_menu(self.chance)
                if choice is None:
                    self.running = False
                    return
                self.board.promote_pawn(to_row, to_col, self.chance, choice)

        # switch turn
        self.chance = "black" if self.chance == "white" else "white"

        # check win / draw conditions
        if self.move_gen.is_checkmate(self.chance):
            winner = "White" if self.chance == "black" else "Black"
            self.game_over = True
            self.game_over_msg = f"{winner} wins by checkmate!"
        elif self.move_gen.is_stalemate(self.chance):
            self.game_over = True
            self.game_over_msg = f"Draw by stalemate"

if __name__ == "__main__":
    Game().run()