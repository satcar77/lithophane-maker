import numpy as np
from PIL import Image
import ctypes,struct
from PySide2.QtGui import QVector3D
class Lithophane():
    def __init__(self):
        self.m_count = 0
        self.i = 0
        self.m_data = np.empty(3000000 * 6, dtype = ctypes.c_float)               
        self.min_thickness = 0.2
        self.max_thickness = 1.4
        self.step_size = 0.2
        self.width = 0 
        self.height = 0
    
    def setParams(self, minT,maxT,step_size):
        self.__init__()
        self.min_thickness = minT
        self.max_thickness = maxT
        self.step_size  = step_size

    def generateVertex(self,img_scr):
        self.i = 0 
        self.m_count = 0
        self.m_data = np.empty(3000000 * 6, dtype = ctypes.c_float)            
        image = Image.open(img_scr)
        basewidth = 300
        wpercent = (basewidth/float(image.size[0]))
        hsize = int((float(image.size[1])*float(wpercent)))
        image = image.resize((basewidth,hsize), Image.ANTIALIAS)
        ary = np.array(image)
        r,g,b = np.split(ary,3,axis=2)
        r=r.reshape(-1)
        g=r.reshape(-1)
        b=r.reshape(-1)
        self.width = ary.shape[0]
        self.height = ary.shape[1]
        bitmap = list(map(lambda x: 255-(0.299*x[0]+0.587*x[1]+0.114*x[2]),zip(r,g,b)))
        max_grey = np.amax(bitmap)
        min_grey = np.amin(bitmap)
        bitmap_mapped = list(map(lambda x: (self.max_thickness - self.min_thickness)/(max_grey - min_grey)*x + self.min_thickness,bitmap))
        bitmap1 = np.array(bitmap_mapped).reshape([self.width,self.height])
        for x in range(0,self.width-1):
            for y in range(0,self.height-1):
                x1=x*self.step_size
                y1=y*self.step_size
                z1=bitmap1[x,y]
                x2=(x+1)*self.step_size
                y2=y*self.step_size
                z2=bitmap1[x+1,y]
                x3=(x+1)*self.step_size
                y3=(y+1)*self.step_size
                z3=bitmap1[x+1,y+1]
                x4=x*self.step_size
                y4=(y+1)*self.step_size
                z4=bitmap1[x,y+1]
                n = QVector3D(QVector3D.normal(QVector3D(x1,y1,z1),QVector3D(x2,y2,z2),QVector3D(x3,y3,z3)))
                self.add(QVector3D(x1,y1,z1),n)
                self.add(QVector3D(x2,y2,z2),n)
                self.add(QVector3D(x3,y3,z3),n)
                self.add(QVector3D(x4,y4,z4),n)
        self.generateBackFace()
        self.generateBorders()
        print("Vertices were added to vbo")

    def generateBackFace(self):
        n= QVector3D(0,0,1)
        self.add(QVector3D(0,0,0),n)
        self.add(QVector3D(0,self.height*self.step_size,0),n)
        self.add(QVector3D(self.width*self.step_size,self.height*self.step_size,0),n)
        self.add(QVector3D(self.width*self.step_size,0,0),n)

    def generateBorders(self):
        #top frame
        n= QVector3D(0,1,0)
        self.add(QVector3D(0,self.height*self.step_size,0),n)
        self.add(QVector3D(self.width*self.step_size,self.height*self.step_size,0),n)
        self.add(QVector3D(self.width*self.step_size,self.height*self.step_size,self.max_thickness),n)
        self.add(QVector3D(0,self.height*self.step_size,self.max_thickness),n)    
        
        #bottom
        n= QVector3D(0,-1,0)
        self.add(QVector3D(0,0,0),n)
        self.add(QVector3D(self.width*self.step_size,0,0),n)
        self.add(QVector3D(self.width*self.step_size,0,self.max_thickness),n)
        self.add(QVector3D(0,0,self.max_thickness),n)    
        
        #sides
        n= QVector3D(1,0,0)
        self.add(QVector3D(0,0,0),n)
        self.add(QVector3D(0,0,self.max_thickness),n)
        self.add(QVector3D(0,self.height*self.step_size,self.max_thickness),n)
        self.add(QVector3D(0,self.height*self.step_size,0),n)  
        
        n= QVector3D(-1,0,0)
        self.add(QVector3D(self.width*self.step_size,0,0),n)
        self.add(QVector3D(self.width*self.step_size,0,self.max_thickness),n)
        self.add(QVector3D(self.width*self.step_size,self.height*self.step_size,self.max_thickness),n)
        self.add(QVector3D(self.width*self.step_size,self.height*self.step_size,0),n)
        
    def constData(self):
        return self.m_data.tobytes()

    def count(self):
        return self.m_count

    def vertexCount(self):
        return self.m_count / 6

    def quad(self, x1, y1, x2, y2, x3, y3, x4, y4):
        n = QVector3D.normal(QVector3D(x4 - x1, y4 - y1, 0), QVector3D(x2 - x1, y2 - y1, 0))

        self.add(QVector3D(x1, y1, -0.05), n)
        self.add(QVector3D(x4, y4, -0.05), n)
        self.add(QVector3D(x2, y2, -0.05), n)

        self.add(QVector3D(x3, y3, -0.05), n)
        self.add(QVector3D(x2, y2, -0.05), n)
        self.add(QVector3D(x4, y4, -0.05), n)

        n = QVector3D.normal(QVector3D(x1 - x4, y1 - y4, 0), QVector3D(x2 - x4, y2 - y4, 0))

        self.add(QVector3D(x4, y4, 0.05), n)
        self.add(QVector3D(x1, y1, 0.05), n)
        self.add(QVector3D(x2, y2, 0.05), n)

        self.add(QVector3D(x2, y2, 0.05), n)
        self.add(QVector3D(x3, y3, 0.05), n)
        self.add(QVector3D(x4, y4, 0.05), n)

    def extrude(self, x1, y1, x2, y2):
        n = QVector3D.normal(QVector3D(0, 0, -0.1), QVector3D(x2 - x1, y2 - y1, 0))

        self.add(QVector3D(x1, y1, 0.05), n)
        self.add(QVector3D(x1, y1, -0.05), n)
        self.add(QVector3D(x2, y2, 0.05), n)

        self.add(QVector3D(x2, y2, -0.05), n)
        self.add(QVector3D(x2, y2, 0.05), n)
        self.add(QVector3D(x1, y1, -0.05), n)

    def add(self, v, n):
        self.m_data[self.i] = v.x()
        self.i += 1
        self.m_data[self.i] = v.y()
        self.i += 1
        self.m_data[self.i] = v.z()
        self.i += 1
        self.m_data[self.i] = n.x()
        self.i += 1
        self.m_data[self.i] = n.y()
        self.i += 1
        self.m_data[self.i] = n.z()
        self.i += 1
        self.m_count += 6
