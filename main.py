import random
from moves import ChessBoard

try:
    import numpy as np
    from PIL import Image, ImageDraw
    import chess
except ImportError:
    raise Exception("Missing Modules: Install Numpy, Chess and Pillow before proceeding")

try:
    import torch
    from torch.utils.data import Dataset, DataLoader
    import torch.nn as nn
    import torch.optim as optim
    from torchvision.models import resnet18, ResNet18_Weights

    import albumentations as Alb
    from albumentations.pytorch import ToTensorV2
except ImportError:
    raise Exception("Missing Modules: Install Torch, TorchVision, Albumentations before proceeding")

try:
    from helperModule import compressIconSVG
except ImportError:
    raise Exception("Missing Module: Missing Helper Module")

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
        im = Image.open(f"{spritePathPrefix}{v}").convert("RGBA")
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

def generateRandomSample(sprites = None, lightSqCol = (240,217,181), darkSqCol = (181, 136, 99), showImg : bool = False):
    board = generateBoardPosCustom(15)

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

    if showImg:
        canvas.show()
    return np.array(canvas.convert('RGB')), arr

class SyntheticChessDataset(Dataset):
    def __init__(self, sprites : dict, epochSize : int = 10000):
        self.sprites = sprites
        self.epochSize = epochSize

        self.transform = Alb.Compose([
            Alb.ImageCompression(quality_range=(60, 100), p = 0.5),
            Alb.GaussianBlur(blur_limit=(3,5), p=0.3),
            Alb.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
            Alb.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=10, p=0.3),
            
            # Convert to [0.0, 1.0] float and apply ImageNet Z-score normalization
            Alb.Normalize(),
            
            # Convert NumPy (H, W, C) to PyTorch Tensor (C, H, W)
            ToTensorV2()
        ])
    def __len__(self):
        return self.epochSize
    
    def __getitem__(self, idx):
        image, label = generateRandomSample(self.sprites)

        augmented = self.transform(image=image)
        tensorImage = augmented['image']

        tensorLabel = torch.tensor(label, dtype=torch.long)

        return tensorImage, tensorLabel

class ChessBoardCNN(nn.Module):
    def __init__(self, num_classes: int = 13):
        super().__init__()

        base_model = resnet18(weights=ResNet18_Weights.DEFAULT)

        self.backbone = nn.Sequential(*list(base_model.children()[::-2]))

        self.head = torch.conv2d(in_channels = 512, out_channels=num_classes, kernel_size=1)
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        logits = self.head(features)
        return logits

def trainModel():
    if torch.cuda.is_available():
        device = torch.device('cuda')
    elif torch.mps.is_available():
        device = torch.device('mps')
    else:
        device = torch.device('cpu')
    print(f"Model is training on device: {device}")

    model = ChessBoardCNN(13).to(device)

    sprites = loadImg()
    dataset = SyntheticChessDataset(sprites, epochSize=5000)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

    weights = torch.tensor([0.2] + [1.0] * 12, dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights)
    
    optimizer = optim.AdamW(model.parameters(), lr=0.001)

    num_epochs = 10
    
    for epoch in range(num_epochs):
        model.train() 
        running_loss = 0.0
        
        # 5. The Batch Loop
        for batch_idx, (images, labels) in enumerate(dataloader):

            # Move data to GPU
            images = images.to(device)
            labels = labels.to(device)

            # OPTIMIZATION
            
            #Zero out old gradients from the previous batch
            optimizer.zero_grad()
            
            # Forward Pass (Make a guess)
            # images shape: (32, 3, 256, 256) -> logits shape: (32, 13, 8, 8)
            logits = model(images)
            
            # Calculate Loss (Grade the guess)
            # Compares the (32, 13, 8, 8) logits against the (32, 8, 8) true integer labels
            loss = criterion(logits, labels)
            
            # Backward Pass & Optimize (Tweak the weights)
            loss.backward()  # Computes the gradient of the loss w.r.t every weight
            optimizer.step() # Updates the weights based on the gradients
            
            running_loss += loss.item()

            if batch_idx % 50 == 0:
                print(f"Epoch [{epoch+1}/{num_epochs}] Batch {batch_idx} | Loss: {loss.item():.4f}")
        
        avg_loss = running_loss / len(dataloader)
        print(f"--- Epoch {epoch+1} Completed | Average Loss: {avg_loss:.4f} ---")
        
        # Save the model weights after each epoch
        torch.save(model.state_dict(), f"chessboard_cnn_epoch_{epoch+1}.pth")

if __name__ == '__main__':
    spritesList = loadImg()
    generateRandomSample(spritesList, showImg=True)

    # Make sure that the sprites are loaded
    svgDir = "Resources/piece/alpha"
    outDir = "Resources/processedPieceIcon"
    try:
        compressModule = compressIconSVG(svgDir, outDir, 32)
        compressModule.compress()
    except Exception as e:
        print(f"Error: {e}")


    trainDataset = SyntheticChessDataset(spritesList, epochSize=10000)

    trainLoader = DataLoader(
        trainDataset,
        batch_size=64,
        shuffle=True,
        num_workers=4,
        pin_memory=True
    )

    for image, label in trainLoader:
        print(f"Image batch shape: {image.shape}")
        print(f"Label batch shape: {label.shape}")
        break
