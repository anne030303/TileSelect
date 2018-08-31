import glob
import os
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from shutil import move
import seaborn as sns
import sys
from TileSelect_frame import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QGraphicsScene
from PyQt5.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

#展圖
def tile_plt(tiles_exist):
    tile1_max,tile2_max = np.array(list(tiles_exist.keys())).max(axis = 0)
    tile1_min,tile2_min = np.array(list(tiles_exist.keys())).min(axis = 0)
    tile_mat = np.zeros(shape=(tile1_max+1,tile2_max+1))
    for key,value in tiles_exist.items():
        tile_mat[key] = value
    
    sns.set(style="white",font_scale=1)
    cmap = sns.color_palette(['#C3C3C3','#ffffb2','#fdae61','#1a9641'])
    fig, ax = plt.subplots(figsize=(9,4))
    
    ax = sns.heatmap(tile_mat[tile1_min:,tile2_min:], ax=ax, 
                     cmap=ListedColormap(cmap), 
                     vmax=3,
                     square=True, linewidths=.1,cbar=True)
    ax.invert_yaxis()
    colorbar = ax.collections[0].colorbar
    colorbar.set_ticks(np.arange(0+3/8,3+3/8,3/4))
    colorbar.set_ticklabels(['No Data', 'All_Pending', 'Tiles_Pending', 'Tiles_Complete'])
    figure = plt.gcf()
    return figure

#比對Tile狀態
def tile_compare(pending_dir, tile_txt, mode = 0):
    filename = glob.glob(pending_dir+'\*.xml')
    tiles_line = open(tile_txt).readlines()
    tiles_exist = {}
    tiles_to_file = {}
    
    for i in filename:
        match = tile_match(i,mode)
        tiles_to_file[match] = i
        tiles_exist[match] = 1
    
    for i in tiles_line:
        i = i.replace('\n','')
        match = tile_match(i,mode)
        if match in tiles_exist:
            tiles_exist[match] = 2
        else:
            tiles_exist[match] = 3
    return tiles_exist,tiles_to_file

#匹配Tile編號
def tile_match(filename,mode):
    if mode == 0:
        pat_Tile = re.compile(r'Tile_\+(\d+)_\+(\d+)')
        Tilename = re.search(pat_Tile,filename)
        return tuple(map(int,Tilename.groups()))
    elif mode == 1:
        pat_Tile = re.compile(r'Tile_(\d+)')
        Tilename = re.search(pat_Tile,filename)
        return Tilename.group()

#移動不需要的Tile
def move_tile(path,tiles_exist,tiles_to_file):
    path_temp = os.path.join(path,'temp')
    path_pending = os.path.join(path,'pending')
    if not os.path.exists(path_temp):
        os.makedirs(path_temp)
    if not os.path.exists(path_pending):
        os.makedirs(path_pending)
    for key,value in tiles_exist.items():
        if value == 1:
            move(tiles_to_file[key],path_temp)
        elif value == 2:
            move(tiles_to_file[key],path_pending)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(QIcon('RW.ico'))
        
        self.dname = None
        self.fname = None
        self.tilemode = 0
        self.tiles_exist = None
        self.tiles_to_file = None
        self.status = 0
        
        self.toolButton_PendingPath.clicked.connect(self.showDir)
        self.toolButton_TilePath.clicked.connect(self.showFile)
        self.comboBox_TileMode.currentIndexChanged.connect(self.comboBox)
        self.pushButton_Import.clicked.connect(self.tileimport)
        self.pushButton_TileMove.clicked.connect(self.movetile)
        self.lineEdit_PendingPath.textChanged.connect(self.linecheck)
        self.lineEdit_TilePath.textChanged.connect(self.linecheck)

    def showDir(self):
        self.dname= QFileDialog.getExistingDirectory(self, '開啟Pending資料夾',"",QFileDialog.ShowDirsOnly)
        if self.dname:
            self.lineEdit_PendingPath.setText(self.dname)
        self.hint()

    def showFile(self):
        self.fname, _ = QFileDialog.getOpenFileNames(self,"開啟tile文字檔", "","TXT Files (*.txt)")
        if self.fname:
            self.lineEdit_TilePath.setText(self.fname[0])
        self.hint()
            
    def comboBox(self):
        tile_mode = {'Regular planar grid':0,'Adaptive tiling':1}
        self.tilemode = tile_mode[self.comboBox_TileMode.currentText()]
        self.hint()
        
    def tileimport(self):
        try:
            self.dname = self.lineEdit_PendingPath.text()
            self.fname = self.lineEdit_TilePath.text()
            self.tiles_exist,self.tiles_to_file = tile_compare(self.dname,self.fname,self.tilemode)
            self.status = 1
            if self.tilemode == 0:
                self.draw = FigureCanvas(tile_plt(self.tiles_exist))
                graphicscene = QGraphicsScene()
                graphicscene.addWidget(self.draw)
                self.graphicsView.setScene(graphicscene)
                self.graphicsView.show()
            self.hint()
        except:
            self.label.setText('匯入檔案發生錯誤!')
            
        
        
    def movetile(self):
        try:
            move_tile(self.dname,self.tiles_exist,self.tiles_to_file)
            self.status = 2
            self.hint()
        except:
            self.label.setText('整理檔案發生錯誤!')
        
    
    def hint(self):
        if os.path.isdir(self.dname) == False and self.status == 0:
            self.label.setText('小提示：匯入資料夾路徑')
        elif os.path.isfile(self.fname) == False and self.status == 0:
            self.label.setText('小提示：匯入tile路徑')
        elif self.status == 1:
            self.label.setText('小提示：匯入成功，點選整理資料夾')
        elif self.status == 2:
            self.label.setText('小提示：整理完成')
        else:
            self.label.setText('小提示：檢查資料是否正確')
            
    def linecheck(self):
        self.dname = self.lineEdit_PendingPath.text()
        self.fname = self.lineEdit_TilePath.text()
        self.status = 0
        self.hint()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
