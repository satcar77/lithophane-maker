
import sys
import ctypes,struct
from PySide2.QtCore import QCoreApplication, Signal, SIGNAL, SLOT, Qt, QSize, QPoint
from PySide2.QtWidgets import (QFormLayout,QLineEdit,QLabel,QFileDialog,QApplication, QWidget, QMessageBox,QAction,QVBoxLayout, QHBoxLayout, QSlider,QPushButton,QMainWindow,
    QOpenGLWidget)
from PySide2.QtGui import QSurfaceFormat, QPixmap, QDoubleValidator
import numpy as np
from PIL import Image
from glwidget import GLWidget


class Window(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.glWidget = GLWidget()
        self.glWidget.setMinimumWidth(600)
        self.xSlider = self.createSlider(SIGNAL("xRotationChanged(int)"),
                                         self.glWidget.setXRotation)
        self.ySlider = self.createSlider(SIGNAL("yRotationChanged(int)"),
                                         self.glWidget.setYRotation)
        self.zSlider = self.createSlider(SIGNAL("zRotationChanged(int)"),
                                         self.glWidget.setZRotation)
        self.zoomSlider = self.createZoomSlider(SIGNAL("zoomChanged(int)"),self.glWidget.setZoom)
        
        self.button = QPushButton('Generate STL')
        self.applyButton = QPushButton('Apply')
        self.button.clicked.connect(self.showSaveDialog)
        self.applyButton.clicked.connect(self.applySettings)
        self.imageView = QLabel("Preview unavailable")
        self.minThicknessTextBox= QLineEdit()
        self.maxThicknessTextBox= QLineEdit()
        self.stepSizeTextBox= QLineEdit()
        self.minThicknessTextBox.setValidator(QDoubleValidator(0.99,99.99,2))
        self.maxThicknessTextBox.setValidator(QDoubleValidator(0.99,99.99,2))
        self.stepSizeTextBox.setValidator(QDoubleValidator(0.99,99.99,2))
        self.setFormDefaults()
        rightSide = QFormLayout()
        rightSide.addRow("Preview",self.imageView)
        rightSide.addRow("Min Thickness", self.minThicknessTextBox)
        rightSide.addRow("Max Thickness", self.maxThicknessTextBox)
        rightSide.addRow("Step Size", self.stepSizeTextBox)
        rightSide.addRow(self.applyButton)
        rightSide.addRow(self.button)
        
        mainLayout = QHBoxLayout()
        leftSide = QVBoxLayout()
        leftSide.addWidget(self.glWidget)
        leftSide.addWidget(QLabel("Zoom"))
        leftSide.addWidget(self.zoomSlider)
        leftSide.addWidget(QLabel("X Rotation"))
        leftSide.addWidget(self.xSlider)
        leftSide.addWidget(QLabel("Y Rotation"))
        leftSide.addWidget(self.ySlider)
        leftSide.addWidget(QLabel("Z Rotation"))
        leftSide.addWidget(self.zSlider)
        
        leftWidget = QWidget()
        leftWidget.setLayout(leftSide)
        
        mainLayout.addWidget(leftWidget)
        
        rightWidget=QWidget()
        rightWidget.setLayout(rightSide)
        mainLayout.addWidget(rightWidget)
        
        widget= QWidget()
        widget.setLayout(mainLayout)

        openAction = QAction("&Open Image File", self)
        openAction.setShortcut("Ctrl+O")
        openAction.setStatusTip('Open an Image')
        openAction.triggered.connect(self.showImagePicker)
        
        saveAction = QAction("&Save as STL", self)
        saveAction.setShortcut("Ctrl+S")
        saveAction.setStatusTip('Save lithophane in .STL format')
        saveAction.triggered.connect(self.showSaveDialog)
        
        aboutAction = QAction("&About", self)
        aboutAction.setStatusTip('About the program')
        aboutAction.triggered.connect(self.showAboutDialog)

        self.statusBar()

        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)

        aboutMenu = mainMenu.addMenu('&Help')
        aboutMenu.addAction(aboutAction)

        self.setCentralWidget(widget)
        self.xSlider.setValue(15 * 16)
        self.ySlider.setValue(345 * 16)
        self.zSlider.setValue(0 * 16)
        self.zoomSlider.setValue(90)
        self.setWindowTitle(self.tr("Lithophane Maker"))
        self.setGeometry(50,50,1200,800) 
        self.connect(self.glWidget, SIGNAL("fileSaved()"), self.showFileSaved)

    def showAboutDialog(self):
        messageBox = QMessageBox(QMessageBox.Information, "About",
                                         "This program was made for Incessant Rain Studios",
                                         QMessageBox.Close)
        messageBox.setDetailedText("Developer : Satkar Dhakal")
        messageBox.exec_()
    
    def showFileSaved(self):
        QMessageBox.about(self, "Success", "Export success")

    def setFormDefaults(self):
        self.minThicknessTextBox.setText("0.4")
        self.maxThicknessTextBox.setText("2")
        self.stepSizeTextBox.setText("0.2")

    def applySettings(self):
        self.glWidget.applyParams(float(self.minThicknessTextBox.text()),float(self.maxThicknessTextBox.text()),float(self.stepSizeTextBox.text()))
    def createSlider(self, changedSignal, setterSlot):
        slider = QSlider(Qt.Horizontal)

        slider.setRange(0, 360 * 16)
        slider.setSingleStep(16)
        slider.setPageStep(15 * 16)
        slider.setTickInterval(15 * 16)
        slider.setTickPosition(QSlider.TicksBelow)
        self.glWidget.connect(slider, SIGNAL("valueChanged(int)"), setterSlot)
        self.connect(self.glWidget, changedSignal, slider, SLOT("setValue(int)"))
        return slider

    def createZoomSlider(self, changedSignal, setterSlot):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(10, 400)
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TicksBelow)
        self.glWidget.connect(slider, SIGNAL("valueChanged(int)"), setterSlot)
        self.connect(self.glWidget, changedSignal, slider, SLOT("setValue(int)"))
        return slider
     
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super(Window, self).keyPressEvent(event)
    
    def showImagePicker(self):
        qimage = QFileDialog.getOpenFileName(None,'OpenFile','C:\\',"Image file(*.jpeg *.jpg)")
        self.imageView.setVisible(1)
        self.imageView.setPixmap(QPixmap(qimage[0]).scaledToWidth(400))
        self.glWidget.updateImage(qimage[0])
   
        
    def showSaveDialog(self):
        filename = QFileDialog.getSaveFileName(self, "Save file", "", ".STL")
        print(filename[0])
        self.glWidget.generateSTL(filename[0]+filename[1])

if __name__ == '__main__':
    app = QApplication(sys.argv)

    fmt = QSurfaceFormat()
    if "--multisample" in QCoreApplication.arguments():
        fmt.setSamples(4)
    if "--coreprofile" in QCoreApplication.arguments():
        fmt.setVersion(3, 2)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    mainWindow = Window()
    if "--transparent" in QCoreApplication.arguments():
        mainWindow.setAttribute(Qt.WA_TranslucentBackground)
        mainWindow.setAttribute(Qt.WA_NoSystemBackground, False)

    mainWindow.resize(mainWindow.sizeHint())
    mainWindow.show()

    res = app.exec_()
    sys.exit(res)
