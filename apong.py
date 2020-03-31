import math
import time
import pygame
import os
import sys
import random

SERVE_DELAY = 1.5
HEIGHT = 262-16
V = 1./HEIGHT
WIDTH = 455-80
H = 1./WIDTH
BAT_HEIGHT = 16*V
BAT_WIDTH = 4*H
BALL_HEIGHT = 4*V
BALL_WIDTH = 4*H
NET_WIDTH = H 
HSPEEDS = ( (0,0.26), (4,0.39), (12,0.53) ) # screen widths per second
VLOADS = ( 0,1,2,3,3,4,5,6 )
VSPEEDS = (0.680,0.455,0.228,0,-0.226,-0.462,-0.695)
TOP_GAP = 6*V
BOTTOM_GAP = 4*V
BAT_1_X_START = 48*H
NET_X_START   = 176*H
NET_STRIPE_HEIGHT = 4*V
BAT_2_X_START = 304*H
BALL_X_START = NET_X_START + 6*H
SCORE_1_X_START = 48*H
SCORE_2_X_START = 192*H
SCORE_Y_START = 16*V
DIGIT_PIXEL_V = 4*V
DIGIT_PIXEL_H = 4*H

SEGMENTS = ((0,0,3,0),(3,0,3,3),(3,3,3,7),(0,7,3,7),(0,3,0,7),(0,0,0,3),(0,3,3,3))
DIGITS = ("ABCDEF", "BC", "ABGED", "ABGCD", "FGBC", "AFGCD", "ACDEFG", "ABC", "ABCDEFG", "ABCDFG")

FPS = 60.
WINDOW_SIZE = (800,int(800*HEIGHT/WIDTH))
BLACK = (0,0,0)
WHITE = (200,200,200)

JOY_RANGE = 0.8

hits = 0

def clamp(x,m,M):
    return max(min(x,M),m)

def getHSpeed():
    prev = 0
    for hs in HSPEEDS:
        if hs[0] > hits:
            return prev
        prev = hs[1]
    return HSPEEDS[-1][1]
    
def getVSpeedLoad(y):
    i = int((y+0.5)*len(VLOADS)+0.5)
    if i<0:
        return VLOADS[0]
    elif i>=len(VLOADS):
        return VLOADS[-1]
    else:
        return VLOADS[i]

def toScreen(xy):
    return ( int(0.5+WINDOW_SIZE[0]*xy[0]), int(0.5+WINDOW_SIZE[1]*xy[1]) )
        
class RectSprite(object):
    def __init__(self,wh,xy=[0.5,0.5],vxvy=[0.,0.]):
        self.xy = list(xy)
        self.wh = list(wh)
        self.vxvy = list(vxvy)
        
    def updateXY(self, dt):
        for i in range(2):
            self.xy[i] += dt * self.vxvy[i]
        
    # returns y position of hit normalized over self, or None if no impact
    def hit(self,target):
        for i in range(2):
            if abs(self.xy[i]-target.xy[i]) >= (self.wh[i]+target.wh[i]) * 0.5:
                return None
        return (target.xy[1]-self.xy[1]) / target.wh[1]
        
    def draw(self):
        x,y = toScreen((self.xy[0]-self.wh[0]*0.5, self.xy[1]-self.wh[1]*0.5))
        w,h = toScreen(self.wh)
        pygame.draw.rect(surface, WHITE, (x,y,w,h))
        
class Bat(RectSprite):
    def __init__(self,index):
        super().__init__((BAT_WIDTH,BAT_HEIGHT))
        self.index = index
        self.direction = (1,-1)[index]
        self.xy[0] = (BAT_1_X_START,BAT_2_X_START)[index] + self.wh[0]*0.5
        
    def setPosition(self,offset):
        self.xy[1] = (1.-TOP_GAP-BOTTOM_GAP-self.wh[1])*0.5*(offset+1) + TOP_GAP + 0.5*self.wh[1]

class Ball(RectSprite):
    def __init__(self,xy=[0.5,0.5],load=VLOADS[-1]//2,direction=1):
        super().__init__((BALL_WIDTH,BALL_HEIGHT),xy=xy)
        self.load = load
        self.minY = self.wh[1]*0.5
        self.maxY = 1-self.wh[1]*0.5
        self.minX = self.wh[0]*0.5
        self.maxX = 1-self.wh[0]*0.5
        self.serve(direction)
        
    def draw(self):
        if self.wait <= 0:
            super().draw()
        
    def serve(self,direction):
        global hits
        
        hits = 0
        self.xy[0] = BALL_X_START - 0.5*self.wh[0]
        self.xy[1] = random.uniform(BOTTOM_GAP+self.wh[1]*0.5,1-TOP_GAP-self.wh[1]*0.5)
        self.vxvy[0] = direction*getHSpeed()
        self.vxvy[1] = VSPEEDS[self.load]
        self.wait = SERVE_DELAY
        
    def reverseVertical(self):
        self.load = VLOADS[-1]-self.load
        self.vxvy[1] = VSPEEDS[self.load]
        
    def updateXY(self, dt):
        global hits
        
        if self.wait > 0:
            self.wait -= dt
            if self.wait > 0:
                return
        
        super().updateXY(dt)
        
        if self.xy[1]>self.maxY:
            self.xy[1]=clamp(self.maxY*2-self.xy[1],self.minY,self.maxY)
            self.reverseVertical()
        elif self.xy[1]<self.minY:
            self.xy[1]=clamp(self.minY*2-self.xy[1],self.minY,self.maxY)
            self.reverseVertical()
            
        for bat in bats:
            y = bat.hit(self)
            if y is not None:
                hits += 1
                self.vxvy[0] = bat.direction * getHSpeed()
                self.load = getVSpeedLoad(y)
                self.vxvy[1] = VSPEEDS[self.load]
                
        if self.xy[0] < self.minX:
            # right scores
            self.load = VLOADS[-1] - self.load
            self.serve(-1 if bats else 1)
            return 1
        elif self.xy[0] > self.maxX:
            # left scores
            self.load = VLOADS[-1] - self.load
            self.serve(1 if bats else -1)
            return 0
            
        return None

def drawDigit(xy,n):
    for segmentLetter in DIGITS[n]:
        segment = SEGMENTS[ord(segmentLetter)-ord("A")]
        sx,sy=toScreen((xy[0]+segment[0]*DIGIT_PIXEL_H,xy[1]+segment[1]*DIGIT_PIXEL_V))
        w,h=toScreen(((segment[2]-segment[0]+1)*DIGIT_PIXEL_H,(segment[3]-segment[1]+1)*DIGIT_PIXEL_V))
        pygame.draw.rect(surface, WHITE, (sx,sy,w,h))
        
def drawScore(xy,score):
    x = xy[0]+DIGIT_PIXEL_H*4*3
    while True:
        drawDigit((x,xy[1]),score%10)
        score = score // 10
        if score == 0:
            break
        x -= DIGIT_PIXEL_H*8
        
def adjustJoystick(y):
    y /= JOY_RANGE
    return clamp(y,-1,1)

scores = None
hits = None
ball = None
bats = None        
        
def initGame():
    global scores, hits, ball, bats
    
    bats = ( Bat(0), Bat(1) )
    scores = [0 for bat in bats]
    hits = 0
    
    ball = Ball(xy=(NET_X_START,0.5),load=random.randint(0,VLOADS[-1]))
    
def noGame():
    global scores, hits, ball, bats
    
    bats = tuple()
    hits = 0   
    ball = Ball(xy=(NET_X_START,0.5),load=random.randint(0,VLOADS[-1]))
    
def net():
    y = 0
    w,h = toScreen((NET_WIDTH,NET_STRIPE_HEIGHT))
    while y < 1.:
        sx,sy=toScreen((NET_X_START,y))
        pygame.draw.rect(surface, WHITE, (sx,sy,w,h))
        y += 2*NET_STRIPE_HEIGHT
    
def drawBoard():
    surface.fill(BLACK)
    net()

joy = None    
    
def initJoystick():    
    global joy

    joy = None
    
    while joy is None:
        clock.tick(FPS)
        for event in pygame.event.get():        
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit(0)
        pygame.joystick.init()
        count = pygame.joystick.get_count()
        if count:
            joy = pygame.joystick.Joystick(0)
            for i in range(1,count):
                j = pygame.joystick.Joystick(i)
                n = j.get_name().lower()
                if 'paddle' in n or 'stelladaptor' in n:
                    joy = j
                    break
            joy.init()
        else:
            pygame.event.pump()
            surface.fill(BLACK)
            text = myfont.render("Insert paddles", True, WHITE)
            textRect = text.get_rect()
            textRect.center = (WINDOW_SIZE[0]//2,WINDOW_SIZE[1]//2)
            surface.blit(text, textRect)
            pygame.joystick.quit()
            pygame.display.flip()

pygame.init()
pygame.font.init()
myfont = pygame.font.SysFont(pygame.font.get_default_font(),int(WINDOW_SIZE[1]/10.))
pygame.key.set_repeat(300,100)
os.environ['SDL_VIDEO_CENTERED'] = '1'

# Create pygame screen and objects
surface = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("apong")
clock = pygame.time.Clock()

initJoystick()

scores = [0,0]
noGame()

running = True
playing = False

while running:
    pygame.event.pump()
    for event in pygame.event.get():        
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        if not bats and event.type == pygame.JOYBUTTONDOWN:
            initGame()

    dt = clock.tick(FPS) / 1000.
    drawBoard()
    drawScore((SCORE_1_X_START,SCORE_Y_START),scores[0])
    drawScore((SCORE_2_X_START,SCORE_Y_START),scores[1])
    for bat in bats:
        bat.setPosition(adjustJoystick(joy.get_axis(bat.index)))
    edge = ball.updateXY(dt) 
    ball.draw()
    for bat in bats:
        bat.draw()
    pygame.display.flip()
    if edge is not None and bats:
        scores[edge] += 1
        if scores[edge] == 10:
            noGame()

pygame.quit()