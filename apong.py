import math

HEIGHT = 262-16
V = 1./HEIGHT
WIDTH = 455-80
H = 1./455.
BAT_HEIGHT = 16*V
BAT_WIDTH = 4*H
BALL_HEIGHT = 4*V
BALL_WIDTH = 4*H
HSPEEDS = ( (0,0.26), (4,0.39), (12,0.53) ) # screen widths per second
VSPEED_LOADS = ( 7,8,9,10,10,11,12,13 )
VSPEEDS = (0.680,0.455,0.228,0,-0.226,-0.462,-0.695)
TOP_GAP = 2*V
BOTTOM_GAP = 2*V

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
    
class getVSpeedLoad(y):
    i = int((y+0.5)*len(VSPEED_LOADS)+0.5)
    if i<0:
        return VSPEED_LOADS[0]
    elif i>=len(VSPEED_LOADS):
        return VSPEED_LOADS[-1]
    else:
        return VSPEED_LOADS[i]
    
class RectSprite(object):
    def __init__(self,wh,xy=[0.5,0.5],vxvy=[0.,0.]):
        self.xy = xy
        self.wh = wh
        self.vxvy = vxvy
        
    def updateXY(self, dt):
        for i in range(2):
            self.xy[i] += dt * vxvy[i]
        
    # returns y position of hit normalized over self, or None if no impact
    def hit(self,target):
        for i in range(2):
            if math.abs(self.xy[i]-target.xy[i]) >= (self.wh[i]+target.wh[i]) * 0.5:
                return None
        return (target.xy[1]-self.xy[1]) / target.wh[1]
        
class Bat(object):
    def __init__(self,index):
        super().__init__((BAT_WIDTH,BAT_HEIGHT))
        self.index = index
        self.direction = (-1,0)[index]
        
    def setPosition(self,offset):
        self.xy[1] = (1.-TOP_GAP-BOTTOM_GAP-self.wh[1])*0.5*(offset+1) + TOP_GAP + 0.5*self.wh[1]

bats = ( Bat(0), Bat(1) )
scores = [0 for b in bats]

class Ball(RectSprite):
    def __init__(self,xy=[0.5,0.5],load=len(VSPEED_LOADS)//2,direction=1):
        super().__init__((BALL_WIDTH,BALL_HEIGHT),xy=xy,vxvy=vxvy)
        self.load = load
        self.vxvy[0] = direction*getHSpeed()
        self.vxvy[1] = VSPEEDS[load]
        self.minY = self.wh[1]*0.5
        self.maxY = 1-self.wh[1]*0.5
        self.minX = self.wh[0]*0.5
        self.maxX = 1-self.wh[0]*0.5
        
    def updateXY(self, dt):
        global hit
        
        super().updateXY(dt)
        
        if self.xy[1]>self.maxY:
            self.xy[1]=clamp(self.maxY*2-self.xy[1],self.minY,self.maxY)
            self.load = VSPEED_LOADS[-1]-self.load+VSPEED_LOADS[0]            
            self.vxvy[1] = VSPEEDS[self.load]
        elif self.xy[1]<self.minY:
            self.xy[1]=clamp(self.minY*2-self.xy[1],self.minY,self.maxY)
            self.load = VSPEED_LOADS[-1]-self.load+VSPEED_LOADS[0]            
            self.vxvy[1] = VSPEEDS[self.load]
            
        for bat in bats:
            y = bat.hit(self)
            if y is not None:
                hits += 1
                self.vxvy[0] = bat.direction * getHSpeed()
                self.load = getVSpeedLoad(y)
                self.vxvy[1] = VSPEEDS[self.load]
                
        if self.xy[0] < self.minX:
            # right scores
            return 1
        elif self.xy[1] > self.maxX:
            # left scores
            return 0
            
        return None
        