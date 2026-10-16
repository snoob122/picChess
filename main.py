import numpy as np
import os
import random
from PIL import Image, ImageDraw
from Moves import ChessBoard  # <-- Thêm dòng này

CLASS_MAP = {
    'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6,
    'p': 7, 'n': 8, 'b': 9, 'r': 10, 'q': 11, 'k': 12
}

DEFAULT_SPRITE_PREFIX = "Resources/processedPieceIcon/"
DEFAULT_PIECE_NAME_LIST = {
    'P': "wP.png", 'N': "wN.png", 'B': "wB.png",
    'R': "wR.png", 'Q': "wQ.png", 'K': "wK.png",
    'p': "bP.png", 'n': "bN.png", 'b': "bB.png",
    'r': "bR.png", 'q': "bQ.png", 'k': "bK.png"
}

def loadImg(spriteNameArr : dict[str, str] = DEFAULT_PIECE_NAME_LIST, spritePathPrefix : str = DEFAULT_SPRITE_PREFIX) -> dict:
    returnDict = {}
    for k, v in spriteNameArr.items():
        im = Image.open(f"{spritePathPrefix}{v}")
        returnDict[k] = im
    return returnDict

def generateBoardPosCustom(depth=15) -> ChessBoard:
    board = ChessBoard()
    current_color = "White"

    for _ in range(depth):
        all_legal_moves = []
        for r in range(8):
            for c in range(8):
                piece = board.board[r][c]
                if piece != '.' and board.getColor(piece) == current_color:
                    moves = board.safeMoves(r, c)
                    for nr, nc in moves:
                        all_legal_moves.append((r, c, nr, nc))
        
        if not all_legal_moves:
            break
            
        r, c, nr, nc = random.choice(all_legal_moves)
        board.makeMove(r, c, nr, nc, promotionPiece='Q')
        current_color = "Black" if current_color == "White" else "White"
        
    return board

def generateRandomSample(sprites = None, lightSqCol = (240,217,181), darkSqCol = (181, 136, 99)):
    board = generateBoardPosCustom(30)

    canvas = Image.new("RGBA", (256, 256))
    draw = ImageDraw.Draw(canvas)

    for i in range(8):
        for j in range(8):
            color = lightSqCol
            if ((i + j) % 2 != 0):
                color = darkSqCol
            draw.rectangle([(j * 32, i * 32), (32 + j * 32, 32 + i * 32)], fill=color, width=32)

    arr = np.zeros((8, 8), dtype=np.int64)
    for r in range(8):
        for c in range(8):
            piece = board.board[r][c]
            if piece != '.':
                arr[r, c] = CLASS_MAP[piece]
                canvas.alpha_composite(sprites[piece], dest=(c * 32, r * 32))

    canvas.show()
    return np.array(canvas.convert('RGB')), arr

spritesList = loadImg()
generateRandomSample(spritesList)
