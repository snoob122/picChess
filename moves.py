class ChessBoard:

    # ======================= Information =======================

    def __init__(self):
        # Trắng ('P', 'N', 'B', 'R', 'Q', 'K')
        # Đen ('p', 'n', 'b', 'r', 'q', 'k')
        self.board = [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ]

        self.castlingPossible = {
            "White": {'L': True, 'R': True},
            "Black": {'l': True, 'r': True}
        }

        self.enPassantPos = None

    def isValidPosition(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8
    
    def getColor(self, point):
        if point == '.':
            return None
        elif point.isupper():
            return "White"
        else:
            return "Black"

    # ======================= Basic moves =======================

    # Use for Bishop, Rook and Queen
    
    def straightAndDiagonalMoves(self, r, c, color, dir):
        moves = []
        
        for dr, dc in dir:
            nr = r + dr
            nc = c + dc
            while self.isValidPosition(nr, nc):  # Check in the board 
                target = self.board[nr][nc]
                if target == '.':               # Empty
                    moves.append((nr, nc))
                else:
                    if self.getColor(target) != color:   # Opponent
                        moves.append((nr, nc))
                    break
                nr += dr
                nc += dc
        return moves
        
    # === Knight (N) ===

    def knightMoves(self, r, c, color):
        moves = []
 
        dir = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]

        for dr, dc in dir:
            nr = r + dr
            nc = c + dc
            if self.isValidPosition(nr, nc):  # Check in the board 
                target = self.board[nr][nc]
                if target == '.' or self.getColor(target) != color: # Empty or opponent
                    moves.append((nr, nc))

        return moves

    # === Bishop (B) ===

    def bishopMoves(self, r, c, color):
        dirBishop = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        return self.straightAndDiagonalMoves(r, c, color, dirBishop)

    # === Rook (R) ===

    def rookMoves(self, r, c, color):
        dirRook = [(0, -1), (0, 1), (1, 0), (-1, 0)]
        return self.straightAndDiagonalMoves(r, c, color, dirRook)

    # === Queen (Q) ===

    def queenMoves(self, r, c, color):
        dirQueen = [
            (-1, -1), (1, -1), (-1, 1), (1, 1),
            (0, -1), (0, 1), (1, 0), (-1, 0)  
        ]
        return self.straightAndDiagonalMoves(r, c, color, dirQueen)

    # === Pawn (P) ===

    def pawnMoves(self, r, c, color):
        moves = []

        dir = -1 if color == "White" else 1
        startRow = 6 if color == "White" else 1

        # Move forward
        nr = r + dir    # 1 step
        if self.isValidPosition(nr, c) and self.board[nr][c] == '.':
            moves.append((nr, c))

            nr2 = r + (2 * dir)     # 2 steps
            if r == startRow and self.board[nr2][c] == '.':
                moves.append((nr2, c))

        # Fight diagonal
        for dc in [-1, 1]:
            nr, nc = r + dir, c + dc
            if self.isValidPosition(nr, nc):
                target = self.board[nr][nc]

                if target != '.' and self.getColor(target) != color:
                    moves.append((nr, nc))

                if (nr, nc) == self.enPassantPos:  # En Passant
                    moves.append((nr, nc))

        return moves

    # === King (K) ===

    def kingMoves(self, r, c, color):
        moves = []

        dir = [
            (-1, -1), (-1, 0), (-1, 1), (0, -1), 
            (0, 1), (1, -1), (1, 0), (1, 1)
        ]

        # Basic moves
        for dr, dc in dir:
            nr = r + dr
            nc = c + dc
            if self.isValidPosition(nr, nc):
                target = self.board[nr][nc]
                if target == '.' or self.getColor(target) != color:  # Empty or opponent
                    moves.append((nr, nc))

        # Castling
        opponentColor = "Black" if color == "White" else "White"
        if self.isKingAttacked(r, c, opponentColor):  # Can not castle when being attacked
            return moves

        rowCastling = 7 if color == "White" else 0
        if r == rowCastling and c == 4: 

            left = self.castlingPossible[color]['L'] if color == "White" else self.castlingPossible[color]['l']
            right = self.castlingPossible[color]['R'] if color == "White" else self.castlingPossible[color]['r']

            if left:   # Castling on the left
                if self.board[r][1] == '.' and self.board[r][2] == '.' and self.board[r][3] == '.':
                    if not self.isKingAttacked(r, 2, opponentColor) and not self.isKingAttacked(r, 3, opponentColor):
                        moves.append((r, 2))

            if right:   # Castling on the right
                if self.board[r][5] == '.' and self.board[r][6] == '.':
                    if not self.isKingAttacked(r, 5, opponentColor) and not self.isKingAttacked(r, 6, opponentColor):
                        moves.append((r, 6))

        return moves

    # ======================= Check King =======================

    def findKing(self, color):
        king = 'K' if color == "White" else 'k'
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == king:
                    return (r, c)
        return None

    def isKingAttacked(self, cur_r, cur_c, opponentColor):
        for r in range(8):
            for c in range(8):
                pos = self.board[r][c]
                if pos != '.' and self.getColor(pos) == opponentColor:

                    p_upper = pos.upper()
                    if p_upper == 'N': moves = self.knightMoves(r, c, opponentColor)
                    elif p_upper == 'B': moves = self.bishopMoves(r, c, opponentColor)
                    elif p_upper == 'R': moves = self.rookMoves(r, c, opponentColor)
                    elif p_upper == 'Q': moves = self.queenMoves(r, c, opponentColor)
                    elif p_upper == 'P': 
                        dir = -1 if opponentColor == "White" else 1
                        moves = [(r + dir, c - 1), (r + dir, c + 1)]
                    elif p_upper == 'K':
                        dirKing = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                        moves = [
                            (r + dr, c + dc)
                            for dr, dc in dirKing
                            if self.isValidPosition(r + dr, c + dc)
                        ]
                    
                    if (cur_r, cur_c) in moves:
                        return True
                    
        return False

    def safeMoves(self, r, c):
        cur = self.board[r][c]
        if cur == '.':
            return []
        
        color = self.getColor(cur)
        opponentColor = "Black" if color == "White" else "White"

        # Take next moves of all chess-pieces
        p_upper = cur.upper()
        if p_upper == 'N': nextMoves = self.knightMoves(r, c, color)
        elif p_upper == 'B': nextMoves = self.bishopMoves(r, c, color)
        elif p_upper == 'R': nextMoves = self.rookMoves(r, c, color)
        elif p_upper == 'Q': nextMoves = self.queenMoves(r, c, color)
        elif p_upper == 'P': nextMoves = self.pawnMoves(r, c, color)
        elif p_upper == 'K': nextMoves = self.kingMoves(r, c, color)
        else: return []

        safeMoves = []

        for nr, nc in nextMoves:
            # Fake moves for checking
            self.board[nr][nc] = cur
            self.board[r][c] = '.'

            kingPos = self.findKing(color)
            isKingChecked = self.isKingAttacked(kingPos[0], kingPos[1], opponentColor)

            # Return back
            self.board[r][c] = cur
            self.board[nr][nc] = '.'

            if not isKingChecked:
                safeMoves.append((nr, nc))

        return safeMoves

    # ======================= Move and update =======================

    def makeMove(self, r, c, nr, nc, promotionPiece):
        piece = self.board[r][c]
        color = self.getColor(piece)
        p_upper = piece.upper()

        # Castling (move K and R)
        if p_upper == 'K' and abs(nc - c) == 2:
            if nc == 6:             # On the right
                rook = self.board[r][7]
                self.board[r][7] = '.'
                self.board[r][5] = rook
            elif nc == 2:           # On the left
                rook = self.board[r][0]
                self.board[r][0] = '.'
                self.board[r][3] = rook
        # ------------------------

        # En passant
        if p_upper == 'P' and (nr, nc) == self.enPassantPos:
            self.board[r][nc] = '.'   # Dead pawn position

        if p_upper == 'P' and abs(nr - r) == 2:
            self.enPassantPos = ((r + nr) // 2, c)
        else:
            self.enPassantPos = None  # No second chance for en passant
        # ------------------------

        self.board[nr][nc] = piece
        self.board[r][c] = '.'

        # Promotion
        if p_upper == 'P':
            lastRow = 0 if color == "White" else 7
            if nr == lastRow:
                self.board[nr][nc] = promotionPiece.upper() if color == "White" else promotionPiece.lower()

        # Castling is impossible when moving K or R
        if p_upper == 'K':
            if color == "White":
                self.castlingPossible["White"]['L'] = False
                self.castlingPossible["White"]['R'] = False
            else:
                self.castlingPossible["Black"]['l'] = False
                self.castlingPossible["Black"]['r'] = False

        if p_upper == 'R':
            if color == "White":
                if r == 7 and c == 0: self.castlingPossible["White"]['L'] = False
                if r == 7 and c == 7: self.castlingPossible["White"]['R'] = False
            else:
                if r == 0 and c == 0: self.castlingPossible["Black"]['l'] = False
                if r == 0 and c == 7: self.castlingPossible["Black"]['r'] = False
