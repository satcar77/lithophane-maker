from shiboken2 import VoidPtr
import numpy as np
import ctypes,struct
from PySide2.QtCore import QCoreApplication, Signal, SIGNAL, SLOT, Qt, QSize, QPoint
from PySide2.QtGui import (QDoubleValidator,QVector3D, QOpenGLFunctions, QOpenGLVertexArrayObject, QOpenGLBuffer,
    QOpenGLShaderProgram, QMatrix4x4, QOpenGLShader,QPixmap, QOpenGLContext, QSurfaceFormat)
from PySide2.QtWidgets import (QOpenGLWidget,QMessageBox)
from lithophane import Lithophane
try:
    from OpenGL import GL
except ImportError:
    app = QApplication(sys.argv)
    messageBox = QMessageBox(QMessageBox.Critical, "OpenGL hellogl",
                                         "PyOpenGL must be installed to run this program.",
                                         QMessageBox.Close)
    messageBox.setDetailedText("Run:\npip install PyOpenGL PyOpenGL_accelerate")
    messageBox.exec_()
    sys.exit(1)


class GLWidget(QOpenGLWidget, QOpenGLFunctions):
    xRotationChanged = Signal(int)
    yRotationChanged = Signal(int)
    zRotationChanged = Signal(int)
    zoomChanged = Signal(int)
    fileSaved = Signal()

    def __init__(self, parent=None):
        QOpenGLWidget.__init__(self, parent)
        QOpenGLFunctions.__init__(self)

        self.core = "--coreprofile" in QCoreApplication.arguments()
        self.xRot = 0
        self.yRot = 0
        self.zRot = 4327
        self.zoom = 0
        self.lastPos = 0
        self.lithophane = Lithophane()
        self.vao = QOpenGLVertexArrayObject()
        self.lithophaneVbo = QOpenGLBuffer()
        self.program = QOpenGLShaderProgram()
        self.projMatrixLoc = 0
        self.mvMatrixLoc = 0
        self.normalMatrixLoc = 0
        self.lightPosLoc = 0
        self.proj = QMatrix4x4()
        self.camera = QMatrix4x4()
        self.world = QMatrix4x4()
        self.transparent = "--transparent" in QCoreApplication.arguments()
        if self.transparent:
            fmt = self.format()
            fmt.setAlphaBufferSize(8)
            self.setFormat(fmt)

    def updateImage(self, img_scr):
        self.fileDir = img_scr
        self.lithophane.generateVertex(img_scr)
        self.initializeGL()

    def generateSTL(self,file_name):
        file=open(file_name, "w")
        file.write("solid lithophane\n")  
        i=0
        v_data=[]
        while(i <= self.lithophane.m_count):
           n1=self.lithophane.m_data[i]
           i+=1
           n2=self.lithophane.m_data[i]
           i+=1
           n3=self.lithophane.m_data[i]
           i+=1
           v1=self.lithophane.m_data[i]
           i+=1
           v2=self.lithophane.m_data[i]
           i+=1
           v3=self.lithophane.m_data[i]
           i+=1
           v_data.append([n1,n2,n3])
        triangle_count = 0
        for i in range(0,len(v_data)-1,4):
            q1 = v_data[i]
            q2 = v_data[i+1]
            q3 = v_data[i+2]
            q4 = v_data[i+3]
            file.write("facet normal 0.0 0.0 0.0\n")
            file.write("    outer loop\n")
            file.write("            vertex {} {} {}\n".format(np.float32(q1[0]),np.float32(q1[1]),np.float32(q1[2])))
            file.write("            vertex {} {} {}\n".format(np.float32(q2[0]),np.float32(q2[1]),np.float32(q2[2])))
            file.write("            vertex {} {} {}\n".format(np.float32(q4[0]),np.float32(q4[1]),np.float32(q4[2])))
            file.write("    end loop\n")
            file.write("endfacet\n") 
            
            file.write("facet normal 0.0 0.0 0.0\n")
            file.write("    outer loop\n")
            file.write("            vertex {} {} {}\n".format(np.float32(q2[0]),np.float32(q2[1]),np.float32(q2[2])))
            file.write("            vertex {} {} {}\n".format(np.float32(q3[0]),np.float32(q3[1]),np.float32(q3[2])))
            file.write("            vertex {} {} {}\n".format(np.float32(q4[0]),np.float32(q4[1]),np.float32(q4[2])))
            file.write("    end loop\n")
            file.write("endfacet\n") 
            triangle_count+=2
        print("Written {} triangles".format(triangle_count))
        file.close()
        self.fileSaved.emit()

    def xRotation(self):    
        return self.xRot

    def yRotation(self):
        return self.yRot

    def zRotation(self):
        return self.zRot

    def minimumSizeHint(self):
        return QSize(50, 50)

    def sizeHint(self):
        return QSize(400, 400)

    def normalizeAngle(self, angle):
        while angle < 0:
            angle += 360 * 16
        while angle > 360 * 16:
            angle -= 360 * 16
        return angle

    def setXRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.xRot:
            self.xRot = angle
            self.emit(SIGNAL("xRotationChanged(int)"), angle)
            self.update()

    def setYRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.yRot:
            self.yRot = angle
            self.emit(SIGNAL("yRotationChanged(int)"), angle)
            self.update()

    def setZRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.zRot:
            self.zRot = angle
            self.emit(SIGNAL("zRotationChanged(int)"), angle)
            print(angle)
            self.update()
    
    def setZoom(self, val):
        if val != self.zoom:
            self.zoom = -val
            self.emit(SIGNAL("zoomChanged(int)"), val)
            self.update()

    def applyParams(self, minT, maxT, step_size):
        if not self.fileDir:
            return 
        self.lithophane.setParams(minT,maxT,step_size)
        self.updateImage(self.fileDir)

    def cleanup(self):
        self.makeCurrent()
        self.lithophaneVbo.destroy()
        del self.program
        self.program = None
        self.doneCurrent()

    def vertexShaderSourceCore(self):
        return """#version 150
                in vec4 vertex;
                in vec3 normal;
                out vec3 vert;
                out vec3 vertNormal;
                uniform mat4 projMatrix;
                uniform mat4 mvMatrix;
                uniform mat3 normalMatrix;
                void main() {
                   vert = vertex.xyz;
                   vertNormal = normalMatrix * normal;
                   gl_Position = projMatrix * mvMatrix * vertex;
                }"""

    def fragmentShaderSourceCore(self):
        return """#version 150
                in highp vec3 vert;
                in highp vec3 vertNormal;
                out highp vec4 fragColor;
                uniform highp vec3 lightPos;
                void main() {
                   highp vec3 L = normalize(lightPos - vert);
                   highp float NL = max(dot(normalize(vertNormal), L), 0.0);
                   highp vec3 color = vec3(0.39, 1.0, 0.0);
                   highp vec3 col = clamp(color * 0.2 + color * 0.8 * NL, 0.0, 1.0);
                   fragColor = vec4(col, 1.0);
                }"""


    def vertexShaderSource(self):
        return """attribute vec4 vertex;
                attribute vec3 normal;
                varying vec3 vert;
                varying vec3 vertNormal;
                uniform mat4 projMatrix;
                uniform mat4 mvMatrix;
                uniform mat3 normalMatrix;
                void main() {
                   vert = vertex.xyz;
                   vertNormal = normalMatrix * normal;
                   gl_Position = projMatrix * mvMatrix * vertex;
                }"""

    def fragmentShaderSource(self):
        return """varying highp vec3 vert;
                varying highp vec3 vertNormal;
                uniform highp vec3 lightPos;
                void main() {
                   highp vec3 L = normalize(lightPos - vert);
                   highp float NL = max(dot(normalize(vertNormal), L), 0.0);
                   highp vec3 color = vec3(0.39, 1.0, 0.0);
                   highp vec3 col = clamp(color * 0.2 + color * 0.8 * NL, 0.0, 1.0);
                   gl_FragColor = vec4(col, 1);
                }"""

    def initializeGL(self):
        self.context().aboutToBeDestroyed.connect(self.cleanup)
        self.initializeOpenGLFunctions()
        self.glClearColor(0, 0, 0, 1)

        self.program = QOpenGLShaderProgram()

        if self.core:
            self.vertexShader = self.vertexShaderSourceCore()
            self.fragmentShader = self.fragmentShaderSourceCore()
        else:
            self.vertexShader = self.vertexShaderSource()
            self.fragmentShader = self.fragmentShaderSource()

        self.program.addShaderFromSourceCode(QOpenGLShader.Vertex, self.vertexShader)
        self.program.addShaderFromSourceCode(QOpenGLShader.Fragment, self.fragmentShader)
        self.program.bindAttributeLocation("vertex", 0)
        self.program.bindAttributeLocation("normal", 1)
        self.program.link()

        self.program.bind()
        self.projMatrixLoc = self.program.uniformLocation("projMatrix")
        self.mvMatrixLoc = self.program.uniformLocation("mvMatrix")
        self.normalMatrixLoc = self.program.uniformLocation("normalMatrix")
        self.lightPosLoc = self.program.uniformLocation("lightPos")

        self.vao.create()
        vaoBinder = QOpenGLVertexArrayObject.Binder(self.vao)

        self.lithophaneVbo.create()
        self.lithophaneVbo.bind()
        float_size = ctypes.sizeof(ctypes.c_float)
        self.lithophaneVbo.allocate(self.lithophane.constData(), 300000 *6 * float_size)
        self.setupVertexAttribs()
        self.camera.setToIdentity()
        self.camera.translate(0, 0, -90)

        self.program.setUniformValue(self.lightPosLoc, QVector3D(10, 0, 20))
        self.program.release()
        vaoBinder = None

    def setupVertexAttribs(self):
        self.lithophaneVbo.bind()
        f = QOpenGLContext.currentContext().functions()
        f.glEnableVertexAttribArray(0)
        f.glEnableVertexAttribArray(1)
        float_size = ctypes.sizeof(ctypes.c_float)

        null = VoidPtr(0)
        pointer = VoidPtr(3 * float_size)
        f.glVertexAttribPointer(0, 3, int(GL.GL_FLOAT), int(GL.GL_FALSE), 6 * float_size, null)
        f.glVertexAttribPointer(1, 3, int(GL.GL_FLOAT), int(GL.GL_FALSE), 6 * float_size, pointer)
        self.lithophaneVbo.release()
    
    def paintGL(self):
        self.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self.glEnable(GL.GL_DEPTH_TEST)
        self.glEnable(GL.GL_CULL_FACE)

        self.world.setToIdentity()
        self.world.rotate(self.xRot / 16, 1, 0, 0)
        self.world.rotate(self.yRot / 16, 0, 1, 0)
        self.world.rotate(self.zRot / 16, 0, 0, 1)
        self.camera.setToIdentity()
        self.camera.translate(0,0,self.zoom)
        self.world.translate(-self.lithophane.width*0.5*0.2,-self.lithophane.height*0.5*0.2 , 0)
        vaoBinder = QOpenGLVertexArrayObject.Binder(self.vao)
        self.program.bind()
        self.program.setUniformValue(self.projMatrixLoc, self.proj)
        self.program.setUniformValue(self.mvMatrixLoc, self.camera * self.world)
        normalMatrix = self.world.normalMatrix()
        self.program.setUniformValue(self.normalMatrixLoc, normalMatrix)

        self.glDrawArrays(GL.GL_QUADS, 0, self.lithophane.vertexCount())
        self.program.release()
        vaoBinder = None

    def resizeGL(self, width, height):
        self.proj.setToIdentity()
        self.proj.perspective(45, width / height, 0.01, 1000)

    def mousePressEvent(self, event):
        self.lastPos = QPoint(event.pos())

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() & Qt.LeftButton:
            self.setXRotation(self.xRot + 8 * dy)
            self.setYRotation(self.yRot + 8 * dx)
        elif event.buttons() & Qt.RightButton:
            self.setXRotation(self.xRot + 8 * dy)
            self.setZRotation(self.zRot + 8 * dx)

        self.lastPos = QPoint(event.pos())