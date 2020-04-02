import math
import time
import pygame
import os
import sys
import random
import struct

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
BLACK = (0,0,0)
WHITE = (220,220,220)
GRAY = (180,180,180)
SAMPLE_RATE = 22050
HIT_SOUND = (491,0.016)
SCORE_SOUND = (246,0.220)
BOUNCE_SOUND = (246,0.016)
JOY_RANGE = 0.7

SILENT = False

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
        
def sign(x):
    if x < 0:
        return -1
    elif x > 0:
        return 1
    else:
        return 0

def getScale():        
    if WINDOW_SIZE[0] * HEIGHT > WINDOW_SIZE[1] * WIDTH:
        # wider than we need, match height
        return float(WINDOW_SIZE[1]) * WIDTH / HEIGHT, float(WINDOW_SIZE[1])
    else:
        # match width
        return float(WINDOW_SIZE[0]), float(WINDOW_SIZE[0]) * HEIGHT / WIDTH
        
def toScreenXY(xy):
    return ( int(0.5+SCALE[0]*(xy[0]-0.5)+CENTER[0]), int(0.5+SCALE[1]*(xy[1]-0.5)+CENTER[1]) )
        
def toScreenWH(xy):
    return ( int(0.5+SCALE[0]*xy[0]), int(0.5+SCALE[1]*xy[1]) )
        
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
        return (self.xy[1]-target.xy[1]) / self.wh[1]
        
    def draw(self,color=WHITE):
        x,y = toScreenXY((self.xy[0]-self.wh[0]*0.5, self.xy[1]-self.wh[1]*0.5))
        w,h = toScreenWH(self.wh)
        pygame.draw.rect(surface, color, (x,y,w,h))
        
class Bat(RectSprite):
    def __init__(self,index):
        super().__init__((BAT_WIDTH,BAT_HEIGHT))
        self.index = index
        self.direction = (1,-1)[index]
        self.xy[0] = (BAT_1_X_START,BAT_2_X_START)[index] + self.wh[0]*0.5
        
    def setPosition(self,offset):
        self.xy[1] = (1.-TOP_GAP-BOTTOM_GAP-self.wh[1])*0.5*(offset+1) + TOP_GAP + 0.5*self.wh[1]

class Ball(RectSprite):
    def __init__(self,xy=[0.4,0],load=0,direction=1):
        super().__init__((BALL_WIDTH,BALL_HEIGHT),xy=xy)
        self.hits = 0
        self.vxvy[0] = direction*getHSpeed()
        self.serve_direction = 1
        self.minY = self.wh[1]*0.5
        self.maxY = 1-self.wh[1]*0.5
        self.minX = self.wh[0]*0.5
        self.maxX = 1-self.wh[0]*0.5
        self.serve_direction = None
        self.wait = 0
        self.setLoad(load)
        
    def setLoad(self,load):
        self.load = load
        self.vxvy[1] = VSPEEDS[load]        
        
    def draw(self):
        if self.wait <= 0:
            super().draw()
            
    def serve(self):
        self.wait = SERVE_DELAY
        
    def reverseVertical(self):
        self.setLoad(VLOADS[-1]-self.load)
        
    def updateXY(self, dt):
        if self.wait > 0:
            self.wait -= dt
            if self.wait <= 0:
                self.xy[0] = BALL_X_START - 0.5*self.wh[0]
                if self.serve_direction is None:
                    self.serve_direction = sign(self.vxvy[0])
                self.vxvy[0] = self.serve_direction*getHSpeed()
                self.hits = 0
        
        super().updateXY(dt)
        
        if self.xy[1]>self.maxY:
            self.xy[1]=clamp(self.maxY*2-self.xy[1],self.minY,self.maxY)
            self.reverseVertical()
            sound(bounceSound)
        elif self.xy[1]<self.minY:
            self.xy[1]=clamp(self.minY*2-self.xy[1],self.minY,self.maxY)
            self.reverseVertical()
            sound(bounceSound)
            
        if self.wait <= 0:
            for bat in bats:
                y = bat.hit(self)
                if y is not None:
                    sound(hitSound)
                    self.hits += 1
                    self.vxvy[0] = bat.direction * getHSpeed()
                    self.setLoad(getVSpeedLoad(y))
                
        if self.xy[0] < self.minX:
            self.vxvy[0] = abs(self.vxvy[0])
            self.xy[0] = self.minX
            if bats and self.wait <= 0:
                # right scores
                self.serve_direction = -1
                self.wait = SERVE_DELAY
                return 1
                
        elif self.xy[0] > self.maxX:
            self.vxvy[0] = -abs(self.vxvy[0])
            self.xy[0] = self.maxX
            
            if bats and self.wait <= 0:
                # left scores
                self.serve_direction = 1
                self.wait = SERVE_DELAY
                return 0
            
        return None

def drawDigit(xy,n):
    xy = toScreenXY(xy)
    w,h = toScreenWH((DIGIT_PIXEL_H,DIGIT_PIXEL_V))
    for segmentLetter in DIGITS[n]:
        segment = SEGMENTS[ord(segmentLetter)-ord("A")]
        sw,sh=(segment[2]-segment[0]+1)*w,(segment[3]-segment[1]+1)*h
        sx,sy=xy[0]+segment[0]*w,xy[1]+segment[1]*h
        pygame.draw.rect(surface, WHITE, (sx,sy,sw,sh))
        
def drawScore(xy,score):
    x = xy[0]+DIGIT_PIXEL_H*4*3
    while True:
        drawDigit((x,xy[1]),score%10)
        score = score // 10
        if score == 0:
            break
        x -= DIGIT_PIXEL_H*8

def getDisplaySize():
    info = pygame.display.Info()
    return info.current_w, info.current_h
        
joy = None    
scores = None
ball = None
bats = None        
        
def adjustJoystick(y):
    y /= JOY_RANGE
    return clamp(y,-1,1)

def attract():
    global bats

    bats = []
    ball.setLoad(0)
    
def initGame():
    global scores, ball
    
    bats = []
    scores = [0,0]
    
    ball = Ball()
    attract()
    
def start():
    global bats
    
    bats = ( Bat(0), Bat(1) )
    
    scores = [0,0]
    
    ball.serve()
    
def net():
    y = 0
    w,h = toScreenWH((NET_WIDTH,NET_STRIPE_HEIGHT))
    while y < 1.:
        sx,sy=toScreenXY((NET_X_START,y))
        pygame.draw.rect(surface, WHITE, (sx,sy,w,h))
        y += 2*NET_STRIPE_HEIGHT
    
def drawBoard():
    surface.fill(BLACK)
    net()
    
def sound(s):
    if not SILENT:
        pygame.mixer.Sound.play(s)
    
def wavHeader(sampleRate,size,channels,dataSize):
    return struct.pack("<4sL4s4sHHLLHH4sL", b"RIFF", 36+8+dataSize, b"WAVE", b"fmt ", 1, channels,
            sampleRate, sampleRate*channels*size//8, channels*size//8, size, b"data", dataSize)
    
def makeSound(frequency,duration):
    numSamples = int(0.5 + duration*SAMPLE_RATE)
    halfPeriod = int(0.5 + 0.5 * SAMPLE_RATE / frequency)
    
    data = bytearray()
    value = 0
    for i in range(int(0.5+float(numSamples)/halfPeriod)):
        data += bytearray([value]*halfPeriod)
        value ^= 0xFF
        
    return pygame.mixer.Sound(bytearray(wavHeader(SAMPLE_RATE,8,1,len(data))) + data)

def getDimensions():
    global WINDOW_SIZE, SCALE, CENTER, myfont
    WINDOW_SIZE = surface.get_size()
    SCALE = getScale()
    CENTER = WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2
    myfont = pygame.font.SysFont(pygame.font.get_default_font(),int(WINDOW_SIZE[1]/10.))

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
            for i in range(0,count):
                j = pygame.joystick.Joystick(i)
                n = j.get_name().lower()
                if 'paddle' in n or 'stelladaptor' in n:
                    joy = j
                    break
            if joy is not None: 
                joy.init()
        if joy is None:
            pygame.event.pump()
            surface.fill(BLACK)
            text = myfont.render("Insert paddles", True, WHITE)
            textRect = text.get_rect()
            textRect.center = (WINDOW_SIZE[0]//2,WINDOW_SIZE[1]//2)
            surface.blit(text, textRect)
            pygame.joystick.quit()
            pygame.display.flip()
            sound(hitSound)
            time.sleep(1)

pygame.init()
if not SILENT:
    pygame.mixer.init(SAMPLE_RATE,8,1)
hitSound = makeSound(*HIT_SOUND)
scoreSound = makeSound(*SCORE_SOUND)
bounceSound = makeSound(*BOUNCE_SOUND)

pygame.font.init()
pygame.key.set_repeat(300,100)
os.environ['SDL_VIDEO_CENTERED'] = '1'

# Create pygame screen and objects
if len(sys.argv)>1 and "w" in sys.argv[1]:
    surface = pygame.display.set_mode((800,600), pygame.RESIZABLE)
else:
    surface = pygame.display.set_mode(getDisplaySize(), pygame.FULLSCREEN)
if len(sys.argv)>1 and "q" in sys.argv[1]:
    SILENT = True
pygame.mouse.set_visible(False)
getDimensions()
pygame.display.set_caption("pypaddle")
clock = pygame.time.Clock()

initJoystick()

scores = [0,0]
initGame()

running = True
playing = False

while running:
    pygame.event.pump()
    for event in pygame.event.get():        
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif not bats and event.type == pygame.JOYBUTTONDOWN:
            start()
        elif event.type == pygame.VIDEORESIZE:
            surface = pygame.display.set_mode((event.w, event.h),pygame.RESIZABLE)
            getDimensions()
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
    if edge is not None and bats:
        sound(scoreSound)
        scores[edge] += 1
        if scores[edge] == 11:
            attract()
    pygame.display.flip()

pygame.quit()
