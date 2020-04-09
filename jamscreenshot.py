import math
import os
import sys
import time

import cv2
from PIL import Image
from PyQt5.QtCore import QRect, Qt, QThread, QStandardPaths, QPoint, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QPen, QIcon, QFont, QColor, QCursor, \
    QBrush, QPainterPath
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QTextEdit, QFileDialog, QGroupBox, QSlider, QWidget, \
    QColorDialog, QMenu
import jamresourse  # 导入资源文件


class Finder():  # 自动选区类
    def __init__(self, parent):
        self.h = self.w = 0
        self.rect_list = self.contours = []
        self.area_threshold = 500
        self.parent = parent
        self.img = None

    def find_contours_setup(self):
        # t = time.process_time()
        self.setup()
        # print('ffindt0', time.process_time() - t)
        self.find_contours()
        # print('ffindt', time.process_time() - t)

    def setup(self):
        t1 = time.process_time()
        self.img = cv2.imread('j_temp/get.png')
        t2 = time.process_time()
        self.h, self.w, _ = self.img.shape
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)  # 灰度化
        t3 = time.process_time()
        # ret, th = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        # th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)  # 自动阈值
        th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)  # 自动阈值
        t4 = time.process_time()
        self.contours, hierarchy = cv2.findContours(th, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        print('setuptime', t2 - t1, t3 - t2, t4 - t3)

    def find_contours(self):
        self.rect_list = [[0, 0, self.w, self.h]]
        for i in self.contours:
            x, y, w, h = cv2.boundingRect(i)
            area = cv2.contourArea(i)
            if area > self.area_threshold and w > 10 and h > 10:
                # cv2.rectangle(self.img, (x, y), (x + w, y + h), (0, 0, 255), 1)
                # newcontours.append(i)
                self.rect_list.append([x, y, x + w, y + h])
        print('contours:', len(self.contours), 'left', len(self.rect_list))

    def find_targetrect(self, point):
        # print(len(self.rect_list))
        # point = (1000, 600)
        target_rect = [0, 0, self.w, self.h]
        target_area = 1920 * 1080
        for rect in self.rect_list:
            if point[0] in range(rect[0], rect[2]):
                # print('xin',rect)
                if point[1] in range(rect[1], rect[3]):
                    # print('yin', rect)
                    area = (rect[3] - rect[1]) * (rect[2] - rect[0])
                    # print(area,target_area)
                    if area < target_area:
                        target_rect = rect
                        target_area = area
                        # print('target', target_area, target_rect)
                        # x,y,w,h=target_rect[0],target_rect[1],target_rect[2]-target_rect[0],target_rect[3]-target_rect[1]
                        # cv2.rectangle(self.img, (x, y), (x + w, y + h), (0, 0, 255), 1)
        # cv2.imwrite("img.png", self.img)
        return target_rect

    def clear_setup(self):
        self.h = self.w = 0
        self.rect_list = self.contours = []
        self.img = None


class MaskLayer(QLabel):  # 遮罩层
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.parent.on_init:
            print('oninit return')
            return
        painter = QPainter(self)

        rect = QRect(min(self.parent.x0, self.parent.x1), min(self.parent.y0, self.parent.y1),
                     abs(self.parent.x1 - self.parent.x0), abs(self.parent.y1 - self.parent.y0))

        painter.setPen(QPen(Qt.green, 3, Qt.SolidLine))
        painter.drawRect(rect)
        painter.drawRect(0, 0, self.width(), self.height())
        painter.setPen(QPen(Qt.green, 7, Qt.SolidLine))
        painter.drawPoint(
            QPoint(self.parent.x0, min(self.parent.y1, self.parent.y0) + abs(self.parent.y1 - self.parent.y0) // 2))
        painter.drawPoint(
            QPoint(min(self.parent.x1, self.parent.x0) + abs(self.parent.x1 - self.parent.x0) // 2, self.parent.y0))
        painter.drawPoint(
            QPoint(self.parent.x1, min(self.parent.y1, self.parent.y0) + abs(self.parent.y1 - self.parent.y0) // 2))
        painter.drawPoint(
            QPoint(min(self.parent.x1, self.parent.x0) + abs(self.parent.x1 - self.parent.x0) // 2, self.parent.y1))
        painter.drawPoint(QPoint(self.parent.x0, self.parent.y0))
        painter.drawPoint(QPoint(self.parent.x0, self.parent.y1))
        painter.drawPoint(QPoint(self.parent.x1, self.parent.y0))
        painter.drawPoint(QPoint(self.parent.x1, self.parent.y1))

        x = y = 100
        if self.parent.x1 > self.parent.x0:
            x = self.parent.x0 + 5
        else:
            x = self.parent.x0 - 72
        if self.parent.y1 > self.parent.y0:
            y = self.parent.y0 + 15
        else:
            y = self.parent.y0 - 5

        painter.drawText(x, y,
                         '{}x{}'.format(abs(self.parent.x1 - self.parent.x0), abs(self.parent.y1 - self.parent.y0)))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 120))
        painter.drawRect(0, 0, self.width(), min(self.parent.y1, self.parent.y0))
        painter.drawRect(0, min(self.parent.y1, self.parent.y0), min(self.parent.x1, self.parent.x0),
                         self.height() - min(self.parent.y1, self.parent.y0))
        painter.drawRect(max(self.parent.x1, self.parent.x0), min(self.parent.y1, self.parent.y0),
                         self.width() - max(self.parent.x1, self.parent.x0),
                         self.height() - min(self.parent.y1, self.parent.y0))
        painter.drawRect(min(self.parent.x1, self.parent.x0), max(self.parent.y1, self.parent.y0),
                         max(self.parent.x1, self.parent.x0) - min(self.parent.x1, self.parent.x0),
                         self.height() - max(self.parent.y1, self.parent.y0))
        if not (self.parent.painter_tools['drawcircle_on'] or self.parent.painter_tools['drawrect_bs_on'] or
                self.parent.painter_tools['pen_on'] or self.parent.painter_tools['eraser_on'] or
                self.parent.painter_tools['drawtext_on'] or self.parent.painter_tools['backgrounderaser_on']
                or self.parent.painter_tools['drawpix_bs_on'] or self.parent.move_rect):
            # 'drawpix_bs_on': 0, 'drawarrow_on': 0, 'drawcircle_on': 0, 'drawrect_bs_on': 0,
            #                               'pen_on': 0, 'eraser_on': 0, 'drawtext_on': 0,
            #                               'backgrounderaser_on': 0
            # painter.setBrush(QColor(0, 0, 0, 0))
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            if self.parent.mouse_posx > self.width() - 140:
                enlarge_box_x = self.parent.mouse_posx - 140
            else:
                enlarge_box_x = self.parent.mouse_posx + 20
            if self.parent.mouse_posy > self.height() - 140:
                enlarge_box_y = self.parent.mouse_posy - 120
            else:
                enlarge_box_y = self.parent.mouse_posy + 20
            enlarge_rect = QRect(enlarge_box_x, enlarge_box_y, 120, 120)
            painter.drawRect(enlarge_rect)
            painter.drawText(enlarge_box_x, enlarge_box_y - 8,
                             '({0}x{1})'.format(self.parent.mouse_posx, self.parent.mouse_posy))
            try:
                painter.setCompositionMode(QPainter.CompositionMode_Source)
                p = self.parent.pixmap()
                larger_pix = p.copy(self.parent.mouse_posx - 60, self.parent.mouse_posy - 60, 120, 120).scaled(
                    120 + self.parent.tool_width * 10, 120 + self.parent.tool_width * 10)
                pix = larger_pix.copy(larger_pix.width() / 2 - 60, larger_pix.height() / 2 - 60, 120, 120)
                painter.drawPixmap(enlarge_box_x, enlarge_box_y, pix)
                painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))
                painter.drawLine(enlarge_box_x, enlarge_box_y + 60, enlarge_box_x + 120, enlarge_box_y + 60)
                painter.drawLine(enlarge_box_x + 60, enlarge_box_y, enlarge_box_x + 60, enlarge_box_y + 120)

            except:
                print('draw_enlarge_box fail')

        painter.end()


class PaintLayer(QLabel):  # 绘画层
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # self.setAutoFillBackground(False)
        # self.setPixmap(QPixmap())
        self.setMouseTracking(True)
        self.px = self.py = -50
        self.pixpng = ":/msk.jpg"

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.parent.on_init:
            print('oninit return')
            return
        if 1 in self.parent.painter_tools.values():
            painter = QPainter(self)
            painter.setPen(QPen(self.parent.pencolor, 1, Qt.SolidLine))
            rect = QRectF(self.px - self.parent.tool_width // 2, self.py - self.parent.tool_width // 2,
                          self.parent.tool_width, self.parent.tool_width)
            painter.drawEllipse(rect)
            painter.end()
        try:
            self.pixPainter = QPainter(self.pixmap())
            self.pixPainter.setRenderHint(QPainter.Antialiasing)
        except:
            print('pixpainter fail!')
        while len(self.parent.eraser_pointlist):

            self.pixPainter.setBrush(QColor(0, 0, 0, 0))
            self.pixPainter.setPen(Qt.NoPen)
            self.pixPainter.setCompositionMode(QPainter.CompositionMode_Clear)
            new_pen_point = self.parent.eraser_pointlist.pop(0)
            # for i in range(len(self.parent.eraser_pointlist )- 1):
            if self.parent.old_pen[0] != -2 and new_pen_point[0] != -2:
                self.pixPainter.drawEllipse(new_pen_point[0] - self.parent.tool_width / 2,
                                            new_pen_point[1] - self.parent.tool_width / 2,
                                            self.parent.tool_width, self.parent.tool_width)

            self.parent.old_pen = new_pen_point
            # self.pixPainter.end()
        while len(self.parent.pen_pointlist):
            # self.pixPainter = QPainter(self.pixmap())
            # self.pixPainter.setRenderHint(QPainter.Antialiasing)
            self.pixPainter.setBrush(self.parent.pencolor)
            self.pixPainter.setPen(QPen(self.parent.pencolor, self.parent.tool_width, Qt.SolidLine))
            new_pen_point = self.parent.pen_pointlist.pop(0)
            # for i in range(len(self.parent.pen_pointlist )- 1):
            if self.parent.old_pen[0] != -2 and new_pen_point[0] != -2:
                # self.pixPainter.drawEllipse(new_pen_point[0] - self.parent.tool_width / 4,
                #                             new_pen_point[1] - self.parent.tool_width / 4,
                #                             self.parent.tool_width/2, self.parent.tool_width/2)
                path = QPainterPath(QPoint(self.parent.old_pen[0], self.parent.old_pen[1]))
                path.quadTo(QPoint((new_pen_point[0] + self.parent.old_pen[0]) / 2,
                                   (new_pen_point[1] + self.parent.old_pen[1]) / 2),
                            QPoint(new_pen_point[0], new_pen_point[1]))
                self.pixPainter.drawPath(path)
            self.parent.old_pen = new_pen_point
        while len(self.parent.drawpix_pointlist):
            brush = QBrush(self.parent.pencolor)
            brush.setTexture(QPixmap(self.pixpng))
            self.pixPainter.setBrush(brush)
            self.pixPainter.setPen(Qt.NoPen)
            new_pen_point = self.parent.drawpix_pointlist.pop(0)
            if self.parent.old_pen[0] != -2 and new_pen_point[0] != -2:
                self.pixPainter.drawEllipse(new_pen_point[0] - self.parent.tool_width / 2,
                                            new_pen_point[1] - self.parent.tool_width / 2,
                                            self.parent.tool_width, self.parent.tool_width)

            self.parent.old_pen = new_pen_point
        if self.parent.drawrect_pointlist[0][0] != -2 and self.parent.drawrect_pointlist[1][0] != -2:
            # print(self.parent.drawrect_pointlist)
            temppainter = QPainter(self)
            temppainter.setPen(QPen(self.parent.pencolor, 3, Qt.SolidLine))

            poitlist = self.parent.drawrect_pointlist
            temppainter.drawRect(min(poitlist[0][0], poitlist[1][0]), min(poitlist[0][1], poitlist[1][1]),
                                 abs(poitlist[0][0] - poitlist[1][0]), abs(poitlist[0][1] - poitlist[1][1]))
            temppainter.end()
            if self.parent.drawrect_pointlist[2] == 1:
                self.pixPainter.setPen(QPen(self.parent.pencolor, 3, Qt.SolidLine))
                self.pixPainter.drawRect(min(poitlist[0][0], poitlist[1][0]), min(poitlist[0][1], poitlist[1][1]),
                                         abs(poitlist[0][0] - poitlist[1][0]), abs(poitlist[0][1] - poitlist[1][1]))

                self.parent.drawrect_pointlist = [[-2, -2], [-2, -2], 0]

        if self.parent.drawcircle_pointlist[0][0] != -2 and self.parent.drawcircle_pointlist[1][0] != -2:  # 画圆
            temppainter = QPainter(self)
            temppainter.setPen(QPen(self.parent.pencolor, 3, Qt.SolidLine))
            poitlist = self.parent.drawcircle_pointlist
            temppainter.drawEllipse(min(poitlist[0][0], poitlist[1][0]), min(poitlist[0][1], poitlist[1][1]),
                                    abs(poitlist[0][0] - poitlist[1][0]), abs(poitlist[0][1] - poitlist[1][1]))
            temppainter.end()
            if self.parent.drawcircle_pointlist[2] == 1:
                self.pixPainter.setPen(QPen(self.parent.pencolor, 3, Qt.SolidLine))
                self.pixPainter.drawEllipse(min(poitlist[0][0], poitlist[1][0]), min(poitlist[0][1], poitlist[1][1]),
                                            abs(poitlist[0][0] - poitlist[1][0]), abs(poitlist[0][1] - poitlist[1][1]))
                self.parent.drawcircle_pointlist = [[-2, -2], [-2, -2], 0]

        if self.parent.drawarrow_pointlist[0][0] != -2 and self.parent.drawarrow_pointlist[1][0] != -2:  # 画箭头
            temppainter = QPainter(self)

            poitlist = self.parent.drawarrow_pointlist
            temppainter.translate(poitlist[0][0], poitlist[0][1])
            degree = math.degrees(math.atan2(poitlist[1][1] - poitlist[0][1], poitlist[1][0] - poitlist[0][0]))
            temppainter.rotate(degree)
            dx = math.sqrt((poitlist[1][1] - poitlist[0][1]) ** 2 + (poitlist[1][0] - poitlist[0][0]) ** 2)
            dy = 30
            temppainter.drawPixmap(0, -dy / 2, QPixmap(':/arrow.png').scaled(dx, dy))
            temppainter.end()
            if self.parent.drawarrow_pointlist[2] == 1:
                self.pixPainter.translate(poitlist[0][0], poitlist[0][1])
                degree = math.degrees(math.atan2(poitlist[1][1] - poitlist[0][1], poitlist[1][0] - poitlist[0][0]))
                self.pixPainter.rotate(degree)
                dx = math.sqrt((poitlist[1][1] - poitlist[0][1]) ** 2 + (poitlist[1][0] - poitlist[0][0]) ** 2)
                dy = 30
                self.pixPainter.drawPixmap(0, -dy / 2, QPixmap(':/arrow.png').scaled(dx, dy))
                self.parent.drawarrow_pointlist = [[-2, -2], [-2, -2], 0]
                # self.parent.drawarrow_pointlist[0] = [-2, -2]

        if len(self.parent.drawtext_pointlist) > 1 or self.parent.text_box.paint:
            self.parent.text_box.paint = False
            # print(self.parent.drawtext_pointlist)
            text = self.parent.text_box.toPlainText()
            self.parent.text_box.clear()
            pos = self.parent.drawtext_pointlist.pop(0)
            if text:
                self.pixPainter.setFont(QFont('微软雅黑', self.parent.tool_width))
                self.pixPainter.setPen(QPen(self.parent.pencolor, 3, Qt.SolidLine))
                self.pixPainter.drawText(pos[0] + self.parent.text_box.document.size().height() / 8,
                                         pos[1] + self.parent.text_box.document.size().height() * 32 / 41, text)
        try:
            self.pixPainter.end()
        except:
            print("pixpainter end fail!")


class AutotextEdit(QTextEdit):  # 文字框
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = self.document()
        self.document.contentsChanged.connect(self.textAreaChanged)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.paint = False
        self.parent = parent

    def textAreaChanged(self, minsize=0):
        self.document.adjustSize()
        newWidth = self.document.size().width() + 25
        newHeight = self.document.size().height() + 15
        if newWidth != self.width():
            if newWidth < minsize:
                self.setFixedWidth(minsize)
            else:
                self.setFixedWidth(newWidth)
        if newHeight != self.height():
            if newHeight < minsize:
                self.setFixedHeight(minsize)
            else:
                self.setFixedHeight(newHeight)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return:
            self.paint = True
            self.hide()
        super().keyPressEvent(e)

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Return:
            self.parent.update()
        super().keyReleaseEvent(e)


class Freezer(QLabel):  # 固定图片类
    def __init__(self, parent=None, img=None, x=0, y=0, listpot=0):
        super().__init__(parent)
        self.drag = False
        self.on_top = True
        imgpix = QPixmap(img)
        self.listpot = listpot
        self.setPixmap(imgpix)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setGeometry(x, y, imgpix.width(), imgpix.height())
        self.show()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        quitAction = menu.addAction("退出")
        topaction = menu.addAction('(取消)置顶')
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == quitAction:
            self.clear()
        elif action == topaction:
            if self.on_top:
                self.on_top = False
                self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
                self.setWindowFlag(Qt.Tool, False)
                self.show()
            else:
                self.on_top = True
                self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                self.setWindowFlag(Qt.Tool, True)
                self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = True
            self.p_x, self.p_y = event.x(), event.y()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = False

    def mouseMoveEvent(self, event):
        if self.isVisible():
            self.setCursor(Qt.SizeAllCursor)
            if self.drag:
                self.move(event.x() + self.x() - self.p_x, event.y() + self.y() - self.p_y)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            # self.resize(self.width()/2,self.height()/2)
            # time.sleep(5)
            self.clear()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def clear(self):
        self.clearMask()
        self.hide()
        super().clear()
        window.freeze_imgs[self.listpot] = None

    def closeEvent(self, e):
        self.clear()
        e.ignore()


class Slabel(QLabel):  # 截图功能主界面
    def __init__(self, parent=None):
        super().__init__()
        # self.ready_flag = False
        # self.pixmap()=QPixmap()
        self.on_init = True
        self.paintlayer = PaintLayer(self)
        self.mask = MaskLayer(self)
        self.text_box = AutotextEdit(self)
        self.setMouseTracking(True)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.botton_box = QGroupBox(self)
        self.save_botton = QPushButton(QIcon(":/saveicon.png"), '', self.botton_box)
        self.save_botton.clicked.connect(lambda: self.cutpic(1))
        self.btn1 = QPushButton("确定", self.botton_box)
        self.freeze_img_botton = QPushButton(self.botton_box)

        self.pencolor = Qt.red
        self.painter_box = QGroupBox(self)
        self.choice_clor = QPushButton('', self.painter_box)

        self.slider_width = QSlider(Qt.Horizontal, self.painter_box)
        self.slider_label = QLabel(self.painter_box)
        self.msk = QPushButton('', self.painter_box)
        self.choise_pix = QPushButton('', self.painter_box)
        self.drawarrow = QPushButton('', self.painter_box)
        self.drawcircle = QPushButton('', self.painter_box)
        self.bs = QPushButton('', self.painter_box)
        self.drawtext = QPushButton('', self.painter_box)
        self.pen = QPushButton('', self.painter_box)
        self.eraser = QPushButton('', self.painter_box)
        self.backgrounderaser = QPushButton('', self.painter_box)

        # self.init_slabel()
        self.init_slabel_thread = Commen_Thread(self.init_slabel)
        self.init_slabel_thread.start()  # 后台初始化线程

        self.setVisible(False)
        self.showFullScreen()
        self.hide()
        self.on_init = False

    def init_slabel(self):  # 后台初始化部分
        self.flag = self.readyflag = self.choicing = self.move_rect = self.move_y0 = self.move_x0 = self.move_x1 = self.move_y1 = False
        self.x0 = self.y0 = self.rx0 = self.ry0 = self.x1 = self.y1 = self.mouse_posx = self.mouse_posy = -50
        self.image = None
        self.finding_rect = True
        self.finder = Finder(self)
        self.setToolTip("左键框选，右键返回")
        self.id = QApplication.desktop().winId()
        self.screen = QApplication.primaryScreen()
        self.tool_width = 5

        self.save_botton.setGeometry(0, 0, 30, 30)
        self.save_botton.setToolTip('另存为文件')
        self.freeze_img_botton.setGeometry(self.save_botton.x() + self.save_botton.width(), 0, 30, 30)
        self.freeze_img_botton.setIcon(QIcon(":/freeze.png"))
        self.freeze_img_botton.setToolTip('固定图片于屏幕上')
        self.freeze_img_botton.clicked.connect(self.freeze_img)

        self.btn1.setGeometry(self.freeze_img_botton.x() + self.freeze_img_botton.width(), 0, 50, 30)
        self.btn1.clicked.connect(self.cutpic)
        self.botton_box.resize(self.btn1.width() + self.save_botton.width() + self.freeze_img_botton.width(),
                               self.btn1.height())
        self.botton_box.hide()
        self.backgrounderaser_pointlist = []
        self.eraser_pointlist = []
        self.pen_pointlist = []
        self.drawpix_pointlist = []
        self.drawtext_pointlist = []
        self.drawrect_pointlist = [[-2, -2], [-2, -2], 0]
        self.drawarrow_pointlist = [[-2, -2], [-2, -2], 0]
        self.drawcircle_pointlist = [[-2, -2], [-2, -2], 0]
        self.painter_tools = {'drawpix_bs_on': 0, 'drawarrow_on': 0, 'drawcircle_on': 0, 'drawrect_bs_on': 0,
                              'pen_on': 0, 'eraser_on': 0, 'drawtext_on': 0,
                              'backgrounderaser_on': 0}

        self.old_pen = self.old_eraser = self.old_brush = self.old_backgrounderaser = None
        self.left_button_push = False

        self.painter_box.setGeometry(0, self.height() // 2 - 200, 100, 400)
        self.choice_clor.setToolTip('选择画笔颜色')
        self.choice_clor.clicked.connect(self.get_color)
        self.choice_clor.setIcon(QIcon(":/yst.png"))
        self.choice_clor.move(0, 25)

        self.slider_label.setStyleSheet('background-color:rgba(200,180,180,200)')
        self.slider_label.resize(20, 20)
        self.slider_width.setGeometry(0, self.choice_clor.y() - 20, 35, 20)
        self.slider_width.setToolTip('设置画笔大小,也可用鼠标滚轮调节')
        self.slider_width.valueChanged.connect(self.change_size_fun)
        self.slider_width.sliderPressed.connect(self.resize_width_fun)
        self.slider_width.sliderReleased.connect(self.re_resize_fun)
        self.slider_width.setMaximum(99)
        self.slider_width.setMinimum(1)
        self.slider_width.setValue(5)
        self.slider_label.move(self.slider_width.width(), self.slider_width.y())
        self.slider_width.show()

        # print(pic)

        self.msk.setToolTip('材质贴图工具,可以充当马赛克')
        self.msk.setIcon(QIcon(":/mskicon.png"))
        self.msk.move(0, self.choice_clor.y() + self.choice_clor.height())
        self.msk.clicked.connect(self.change_msk_fun)
        self.choise_pix.setToolTip('选择笔刷材质贴图')

        self.choise_pix.setIcon(QIcon(":/msk.jpg"))
        self.choise_pix.move(30, self.msk.y())
        self.choise_pix.clicked.connect(self.choise_drawpix_fun)
        self.choise_pix.hide()

        self.drawarrow.setToolTip('绘制箭头')
        self.drawarrow.setIcon(QIcon(":/arrowicon.png"))
        self.drawarrow.move(0, self.msk.y() + self.msk.height())
        self.drawarrow.clicked.connect(self.draw_arrow_fun)

        self.drawcircle.setToolTip('绘制圆')
        self.drawcircle.setIcon(QIcon(":/circle.png"))
        self.drawcircle.move(0, self.drawarrow.y() + self.drawarrow.height())
        self.drawcircle.clicked.connect(self.drawcircle_fun)

        self.bs.setToolTip('绘制矩形')
        self.bs.setIcon(QIcon(":/rect.png"))
        self.bs.move(0, self.drawcircle.y() + self.drawcircle.height())
        self.bs.clicked.connect(self.change_bs_fun)

        self.drawtext.setToolTip('绘制文字')
        self.drawtext.setIcon(QIcon(":/texticon.png"))
        self.drawtext.move(0, self.bs.y() + self.bs.height())
        self.drawtext.clicked.connect(self.drawtext_fun)

        self.pen.setToolTip('画笔工具')
        self.pen.setIcon(QIcon(":/pen.png"))
        self.pen.move(0, self.drawtext.y() + self.drawtext.height())

        self.pen.clicked.connect(self.change_pen_fun)

        self.eraser.setToolTip('橡皮擦')
        self.eraser.setIcon(QIcon(":/eraser.png"))
        self.eraser.move(0, self.pen.y() + self.pen.height())
        self.eraser.clicked.connect(self.clear_paint_fun)
        self.backgrounderaser.setIcon(QIcon(":/backgrounderaser.png"))
        self.backgrounderaser.setToolTip('背景橡皮擦')
        self.backgrounderaser.move(0, self.eraser.y() + self.eraser.height())
        self.backgrounderaser.clicked.connect(self.clear_background_fun)

        if not os.path.exists("j_temp"):
            os.mkdir("j_temp")

    def get_color(self):
        self.pencolor = QColorDialog.getColor(Qt.red, self, '选择颜色')
        self.text_box.setTextColor(self.pencolor)
        self.choice_clor.setStyleSheet('background-color:{0};'.format(self.pencolor.name()))

    def drawcircle_fun(self):
        if self.painter_tools['drawcircle_on']:
            self.painter_tools['drawcircle_on'] = 0
            self.drawcircle.setStyleSheet('')
        else:
            self.change_tools_fun('drawcircle_on')
            self.drawcircle.setStyleSheet('background-color:rgb(239,50,50)')

    def draw_arrow_fun(self):
        if self.painter_tools['drawarrow_on']:
            self.painter_tools['drawarrow_on'] = 0
            self.drawarrow.setStyleSheet('')
        else:
            self.change_tools_fun('drawarrow_on')
            self.drawarrow.setStyleSheet('background-color:rgb(239,50,50)')

    def drawtext_fun(self):
        if self.painter_tools['drawtext_on']:
            self.painter_tools['drawtext_on'] = 0
            self.drawtext.setStyleSheet('')
        else:
            self.change_tools_fun('drawtext_on')
            self.drawtext.setStyleSheet('background-color:rgb(239,50,50)')

    def change_pen_fun(self):
        if self.painter_tools['pen_on']:
            self.painter_tools['pen_on'] = 0
            self.pen.setStyleSheet('')
        else:
            self.change_tools_fun('pen_on')
            self.pen.setStyleSheet('background-color:rgb(239,50,50)')

    def clear_paint_fun(self):
        if self.painter_tools['eraser_on']:
            self.painter_tools['eraser_on'] = 0
            self.eraser.setStyleSheet('')
        else:
            self.change_tools_fun('eraser_on')
            self.eraser.setStyleSheet('background-color:rgb(239,50,50)')

    def clear_background_fun(self):
        if self.painter_tools['backgrounderaser_on']:
            self.painter_tools['backgrounderaser_on'] = 0
            self.backgrounderaser.setStyleSheet('')
        else:
            self.change_tools_fun('backgrounderaser_on')
            self.backgrounderaser.setStyleSheet('background-color:rgb(239,50,50)')

    def change_size_fun(self):
        self.slider_label.setText(str(self.slider_width.value()))
        self.tool_width = self.slider_width.value()

    def resize_width_fun(self):
        self.slider_width.resize(100, 20)
        self.slider_label.move(self.slider_width.width(), self.slider_width.y())
        self.slider_label.show()

    def re_resize_fun(self):
        self.slider_width.resize(35, 20)
        # self.slider_label.hide()
        self.slider_label.move(self.slider_width.width(), self.slider_width.y())

    def change_tools_fun(self, r):
        self.pen.setStyleSheet('')
        self.bs.setStyleSheet('')
        self.eraser.setStyleSheet('')
        self.backgrounderaser.setStyleSheet('')
        self.msk.setStyleSheet('')
        self.drawarrow.setStyleSheet('')
        self.drawcircle.setStyleSheet('')
        self.drawtext.setStyleSheet('')
        self.text_box.clear()
        self.text_box.hide()
        self.choise_pix.hide()
        for tool in self.painter_tools:
            if tool == r:
                self.painter_tools[tool] = 1
            else:
                self.painter_tools[tool] = 0

    def change_msk_fun(self):
        if self.painter_tools['drawpix_bs_on']:
            self.painter_tools['drawpix_bs_on'] = 0
            self.msk.setStyleSheet('')
            self.choise_pix.hide()
        else:
            self.change_tools_fun('drawpix_bs_on')
            self.msk.setStyleSheet('background-color:rgb(239,50,50)')
            self.choise_pix.show()

    def change_bs_fun(self):
        # print('cahngegbs')
        if self.painter_tools['drawrect_bs_on']:
            self.painter_tools['drawrect_bs_on'] = 0
            self.bs.setStyleSheet('')
        else:
            self.change_tools_fun('drawrect_bs_on')
            self.bs.setStyleSheet('background-color:rgb(239,50,50)')

    def choise_drawpix_fun(self):
        pic, l = QFileDialog.getOpenFileName(self, "选择图片", QStandardPaths.writableLocation(
            QStandardPaths.PicturesLocation), "img Files (*.PNG *.jpg *.JPG *.JPEG *.BMP *.ICO)"
                                              ";;all files(*.*)")
        if pic:
            self.paintlayer.pixpng = pic
            icon4 = QIcon()
            icon4.addPixmap(QPixmap(pic), QIcon.Normal, QIcon.Off)
            self.choise_pix.setIcon(icon4)

    def screen_shot(self):
        window.hide()
        pix = self.screen.grabWindow(self.id)
        self.setPixmap(pix)
        self.mask.setGeometry(0, 0, self.width(), self.height())
        self.mask.show()
        # self.paintlayer.__init__(self)
        # self.paintlayer.pixpng = ":/msk.jpg"
        self.paintlayer.setGeometry(0, 0, self.width(), self.height())
        self.paintlayer.show()
        self.paintlayer.setPixmap(QPixmap(self.width(), self.height()))
        self.paintlayer.pixmap().fill(Qt.transparent)  # 重点,不然不透明
        self.showFullScreen()  # 全屏必须在所有控件画完再进行

        self.backgrounderaser_pointlist = []
        self.eraser_pointlist = []
        self.drawrect_pointlist = [[-2, -2], [-2, -2], 0]
        self.pen_pointlist = []
        self.drawpix_pointlist = []
        self.drawarrow_pointlist = [[-2, -2], [-2, -2], 0]
        self.drawcircle_pointlist = [[-2, -2], [-2, -2], 0]
        self.old_pen = self.old_eraser = self.old_brush = self.old_backgrounderaser = [-2, -2]
        self.finding_rect = True

        # self.text_box.setGeometry(0, 0, 50, 50)

        self.painter_box.setStyleSheet("QGroupBox{border:none}")
        self.init_ss_thread = Commen_Thread(self.init_ss_thread_fun)

        # self.old_backgrounderaser=[-2, -2]
        # self.old_pen = [-2, -2]
        # self.old_brush = [-2, -2]
        # self.drawrect_bs_on = self.pen_on = False
        pix.save("j_temp/get.png")
        self.init_ss_thread.start()

    def init_ss_thread_fun(self):
        self.finder.find_contours_setup()
        self.paintlayer.pixpng = ":/msk.jpg"
        # self.text_box.resize(100, 30)
        self.text_box.setTextColor(self.pencolor)
        self.text_box.setStyleSheet("background-color: rgba(0, 0, 0, 10);")
        self.text_box.hide()
        self.choice_clor.setStyleSheet('background-color:rgb(255,0,0);')

    def freeze_img(self):
        self.cutpic(2)
        window.freeze_imgs.append(Freezer(None, "j_temp/jam_outputfile.png",
                                          min(self.x0, self.x1), min(self.y0, self.y1),
                                          len(window.freeze_imgs)))
        window.show()
        self.clear_and_hide()

    def choice(self):
        self.choicing = True
        # self.btn2.show()
        btn1w = self.x1
        # btn2w = btn1w + self.botton_box.width()
        btn1h = self.y1
        # btn2h = btn1h
        if self.x1 > self.x0:
            btn1w = self.x1 - self.botton_box.width()
            # btn2w = btn1w - self.btn2.width()

        if self.y1 > self.y0:
            btn1h = self.y1 - self.botton_box.height()
            # btn2h = btn1h
        self.botton_box.move(btn1w, btn1h)
        # self.btn1.move(btn1w, btn1h)
        # self.btn2.move(btn2w, btn2h)
        self.botton_box.show()
        # self.btn1.show()
        # self.btn2.show()
        # self.btn2.move(self.x1 + 100, self.y1)
        # self.show()

    def cutpic(self, save_as=0):
        # img = cv2.imread("j_temp/get.png")
        pix = self.pixmap()
        # pix.save('j_temp/background.png')
        paintlayer = self.paintlayer.pixmap()
        paintlayer.save('j_temp/getpainter.png')
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, paintlayer)
        painter.end()  # 一定要end
        pix.save('j_temp/get.png')

        # pix = self.mask.pixmap()
        # pix.save('j_temp/getmask.png')

        x0 = min(self.x0, self.x1)
        y0 = min(self.y0, self.y1)
        x1 = max(self.x0, self.x1)
        y1 = max(self.y0, self.y1)

        # print(x0, y0, x1, y1)
        if (x1 - x0) < 1 or (y1 - y0) < 1:
            # Trayicon.showM('选择范围过小，请重新选择！')
            # print(00)
            return
        cropped = (x0, y0, x1, y1)  # 裁剪
        img = Image.open("j_temp/get.png")
        img = img.crop(cropped)
        img.save("j_temp/jam_outputfile.png")
        if save_as:
            if save_as == 1:
                path, l = QFileDialog.getSaveFileName(self, "选择图片", QStandardPaths.writableLocation(
                    QStandardPaths.PicturesLocation), "img Files (*.PNG *.jpg *.JPG *.JPEG *.BMP *.ICO)"
                                                      ";;all files(*.*)")
                if path:
                    print(path)
                    img.save(path)
                    self.clear_and_hide()
                else:
                    return
            elif save_as == 2:
                return

        self.manage_data()

    def manage_data(self):  # 图片处理函数
        # 复制图像数据到剪切板
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(QPixmap("j_temp/jam_outputfile.png"))

        # 复制文件到剪切板,而不是图像数据
        # data = QMimeData()
        # url = QUrl.fromLocalFile('/jamtools截屏/jam_outputfile.png')
        # data.setUrls([url])
        # clipboard.setMimeData(data)
        window.show()
        self.clear()
        self.hide()
        self.clear_and_hide()

        # self.close()

    # 鼠标点击事件
    def mousePressEvent(self, event):
        self.botton_box.hide()
        # self.btn1.hide()
        # self.btn2.hide()

        if event.button() == Qt.LeftButton:

            self.left_button_push = True
            if 1 in self.painter_tools.values():
                if self.painter_tools['drawrect_bs_on']:
                    # print("ch",self.drawrect_pointlist)
                    self.drawrect_pointlist = [[event.x(), event.y()], [-2, -2], 0]
                elif self.painter_tools['drawarrow_on']:
                    self.drawarrow_pointlist = [[event.x(), event.y()], [-2, -2], 0]
                    # self.drawarrow_pointlist[0] = [event.x(), event.y()]
                elif self.painter_tools['drawcircle_on']:
                    self.drawcircle_pointlist = [[event.x(), event.y()], [-2, -2], 0]
                    # self.drawcircle_pointlist[0] = [event.x(), event.y()]
                elif self.painter_tools['drawtext_on']:
                    self.text_box.move(event.x(), event.y())
                    self.drawtext_pointlist.append([event.x(), event.y()])
                    self.text_box.setFont(QFont('微软雅黑', self.tool_width))
                    self.text_box.setTextColor(self.pencolor)
                    self.text_box.textAreaChanged()
                    self.text_box.show()
                    self.text_box.setFocus()
                    # self.update()
                    # self.old_brush = [event.x(), event.y()]
                # elif (not self.painter_tools['drawrect_bs_on']) and (not self.painter_tools['pen_on']):
            else:
                r = 0
                if (self.x0 - 8 < event.x() < self.x0 + 8) and (
                        min(self.y0, self.y1) - 10 < event.y() < max(self.y0, self.y1) + 10):
                    self.move_x0 = True
                    r = 1
                    # print('x0')

                elif (self.x1 - 8 < event.x() < self.x1 + 8) and (
                        min(self.y0, self.y1) - 10 < event.y() < max(self.y0, self.y1) + 10):
                    self.move_x1 = True
                    r = 1
                    # print('x1')

                elif (self.y0 - 8 < event.y() < self.y0 + 8) and (
                        min(self.x0, self.x1) - 10 < event.x() < max(self.x0, self.x1) + 10):
                    self.move_y0 = True
                    # print('y0')
                elif self.y1 - 8 < event.y() < self.y1 + 8 and (
                        min(self.x0, self.x1) - 10 < event.x() < max(self.x0, self.x1) + 10):
                    self.move_y1 = True
                    # print('y1')

                    # print('getrect')
                    # self.flag=False
                    # self.move_rect=True
                elif (min(self.x0, self.x1) + 10 < event.x() < max(self.x0, self.x1) - 10) and (
                        min(self.y0, self.y1) + 10 < event.y() < max(self.y0, self.y1) - 10) and not self.finding_rect:
                    # if not self.finding_rect:
                    self.move_rect = True
                    self.bx = abs(max(self.x1, self.x0) - event.x())
                    self.by = abs(max(self.y1, self.y0) - event.y())
                else:
                    self.flag = True
                    if self.finding_rect:
                        self.readyflag = True
                        self.rx0 = event.x()
                        self.ry0 = event.y()
                    else:
                        self.x0 = self.rx0 = event.x()  # rx0用于边界修正
                        self.y0 = self.ry0 = event.y()
                        if self.x1 == -50:
                            self.x1 = event.x()
                            self.y1 = event.y()

                    # print('re')
                if r:
                    if (self.y0 - 8 < event.y() < self.y0 + 8) and (
                            min(self.x0, self.x1) - 10 < event.x() < max(self.x0, self.x1) + 10):
                        self.move_y0 = True
                        # print('y0')
                    elif self.y1 - 8 < event.y() < self.y1 + 8 and (
                            min(self.x0, self.x1) - 10 < event.x() < max(self.x0, self.x1) + 10):
                        self.move_y1 = True
                        # print('y1')
            if self.finding_rect:
                self.finding_rect = False
                # self.finding_rectde = True
            self.update()
        elif event.button() == Qt.RightButton:
            if 1 in self.painter_tools.values():
                self.pen.setStyleSheet('')
                self.bs.setStyleSheet('')
                self.eraser.setStyleSheet('')
                self.backgrounderaser.setStyleSheet('')
                self.msk.setStyleSheet('')
                self.drawarrow.setStyleSheet('')
                self.drawcircle.setStyleSheet('')
                self.drawtext.setStyleSheet('')
                self.text_box.hide()
                for key in self.painter_tools.keys():
                    self.painter_tools[key] = 0
            elif self.choicing:
                self.choicing = False
                self.finding_rect = True
                print('init')
                self.x0 = self.y0 = self.x1 = self.y1 = -50
                # self.btn1.hide()
                # self.btn2.hide()
                self.update()
            else:
                window.show()
                self.clear_and_hide()

    # 鼠标释放事件
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.left_button_push = False

            if self.painter_tools['pen_on']:
                self.pen_pointlist.append([-2, -2])
            elif self.painter_tools['drawpix_bs_on']:
                self.drawpix_pointlist.append([-2, -2])
            elif self.painter_tools['drawrect_bs_on']:
                self.drawrect_pointlist[1] = [event.x(), event.y()]
                self.drawrect_pointlist[2] = 1
            elif self.painter_tools['drawarrow_on']:
                self.drawarrow_pointlist[1] = [event.x(), event.y()]
                self.drawarrow_pointlist[2] = 1
            elif self.painter_tools['drawcircle_on']:
                self.drawcircle_pointlist[1] = [event.x(), event.y()]
                self.drawcircle_pointlist[2] = 1
            elif self.painter_tools['eraser_on']:
                self.eraser_pointlist.append([-2, -2])
            elif self.painter_tools['backgrounderaser_on']:
                self.backgrounderaser_pointlist.append([-2, -2])
            self.flag = False
            self.move_rect = self.move_y0 = self.move_x0 = self.move_x1 = self.move_y1 = False
            self.choice()
            # self.btn1.show()
            self.update()

    # 鼠标滑轮事件
    def wheelEvent(self, event):
        if self.isVisible():
            angleDelta = event.angleDelta() / 8
            dy = angleDelta.y()
            # print(dy)
            if dy > 0:
                self.tool_width += 1
            elif self.tool_width > 1:
                self.tool_width -= 1
            self.slider_width.setValue(self.tool_width)
            # if 1 in self.painter_tools.values():

            if self.painter_tools['drawtext_on']:
                # self.text_box.move(event.x(), event.y())
                # self.drawtext_pointlist.append([event.x(), event.y()])
                self.text_box.setFont(QFont('微软雅黑', self.tool_width))
                # self.text_box.setTextColor(self.pencolor)
                self.text_box.textAreaChanged()
            self.update()

    # 鼠标移动事件
    def mouseMoveEvent(self, event):
        if self.isVisible():
            # print(self.painter_tools)
            self.mouse_posx = event.x()
            self.mouse_posy = event.y()

            if self.finding_rect:
                self.x0, self.y0, self.x1, self.y1 = self.finder.find_targetrect((self.mouse_posx, self.mouse_posy))
                # print(rect)
            elif 1 in self.painter_tools.values():
                self.paintlayer.px = event.x()
                self.paintlayer.py = event.y()
                if self.left_button_push:
                    if self.painter_tools['pen_on']:
                        self.pen_pointlist.append([event.x(), event.y()])
                    elif self.painter_tools['drawpix_bs_on']:
                        self.drawpix_pointlist.append([event.x(), event.y()])
                    elif self.painter_tools['drawrect_bs_on']:
                        self.drawrect_pointlist[1] = [event.x(), event.y()]
                    elif self.painter_tools['drawarrow_on']:
                        self.drawarrow_pointlist[1] = [event.x(), event.y()]
                    elif self.painter_tools['drawcircle_on']:
                        self.drawcircle_pointlist[1] = [event.x(), event.y()]
                    elif self.painter_tools['eraser_on']:
                        self.eraser_pointlist.append([event.x(), event.y()])
                    elif self.painter_tools['backgrounderaser_on']:
                        # print('bakpoint')
                        self.backgrounderaser_pointlist.append([event.x(), event.y()])
                # self.update()
                if self.painter_tools['pen_on']:
                    self.setCursor(QCursor(QPixmap(":/pen.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                elif self.painter_tools['drawpix_bs_on']:
                    self.setCursor(QCursor(QPixmap(self.paintlayer.pixpng).scaled(32, 32, Qt.KeepAspectRatio), 0, 25))
                elif self.painter_tools['drawrect_bs_on']:
                    self.setCursor(QCursor(QPixmap(":/rect.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 30))
                elif self.painter_tools['drawarrow_on']:
                    self.setCursor(QCursor(QPixmap(":/arrowicon.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                elif self.painter_tools['drawcircle_on']:
                    self.setCursor(QCursor(QPixmap(":/circle.png").scaled(32, 32, Qt.KeepAspectRatio), 8, 20))
                elif self.painter_tools['drawtext_on']:
                    self.setCursor(QCursor(QPixmap(":/texticon.png").scaled(16, 16, Qt.KeepAspectRatio), 0, 0))
                elif self.painter_tools['eraser_on']:
                    self.setCursor(QCursor(QPixmap(":/eraser.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
                elif self.painter_tools['backgrounderaser_on']:
                    self.setCursor(QCursor(QPixmap(":/backgrounderaser.png").scaled(32, 32, Qt.KeepAspectRatio), 0, 32))
            else:  # 不在绘画
                minx = min(self.x0, self.x1)
                maxx = max(self.x0, self.x1)
                miny = min(self.y0, self.y1)
                maxy = max(self.y0, self.y1)
                if ((minx - 8 < event.x() < minx + 8) and (miny - 8 < event.y() < miny + 8)) or \
                        ((maxx - 8 < event.x() < maxx + 8) and (maxy - 8 < event.y() < maxy + 8)):
                    self.setCursor(Qt.SizeFDiagCursor)
                elif ((minx - 8 < event.x() < minx + 8) and (maxy - 8 < event.y() < maxy + 8)) or \
                        ((maxx - 8 < event.x() < maxx + 8) and (miny - 8 < event.y() < miny + 8)):
                    self.setCursor(Qt.SizeBDiagCursor)
                elif (self.x0 - 8 < event.x() < self.x0 + 8) and (
                        miny - 10 < event.y() < maxy + 10):
                    self.setCursor(Qt.SizeHorCursor)
                elif (self.x1 - 8 < event.x() < self.x1 + 8) and (
                        miny - 10 < event.y() < maxy + 10):
                    self.setCursor(Qt.SizeHorCursor)
                elif (self.y0 - 8 < event.y() < self.y0 + 8) and (
                        minx - 10 < event.x() < maxx + 10):
                    self.setCursor(Qt.SizeVerCursor)

                elif (self.y1 - 8 < event.y() < self.y1 + 8) and (
                        minx - 10 < event.x() < maxx + 10):
                    self.setCursor(Qt.SizeVerCursor)

                elif (minx + 10 < event.x() < maxx - 10) and (
                        miny + 10 < event.y() < maxy - 10):
                    self.setCursor(Qt.SizeAllCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
                    # print(11)
                QApplication.processEvents()
                if self.flag:
                    # self.btn1.hide()
                    # self.btn2.hide()
                    if self.readyflag:
                        self.readyflag = False
                    else:
                        self.x1 = event.x()
                        self.y1 = event.y()
                        self.x0 = self.rx0
                        self.y0 = self.ry0
                        if self.y1 > self.y0:  # 边界修正
                            self.y1 += 1
                        else:
                            self.y0 += 1
                        if self.x1 > self.x0:
                            self.x1 += 1
                        else:
                            self.x0 += 1
                else:
                    if self.move_x0:
                        self.x0 = event.x()
                    elif self.move_x1:
                        self.x1 = event.x()
                    if self.move_y0:
                        self.y0 = event.y()
                    elif self.move_y1:
                        self.y1 = event.y()
                    elif self.move_rect:
                        dx = abs(self.x1 - self.x0)
                        dy = abs(self.y1 - self.y0)
                        if self.x1 > self.x0:
                            self.x1 = event.x() + self.bx
                            self.x0 = self.x1 - dx
                        else:
                            self.x0 = event.x() + self.bx
                            self.x1 = self.x0 - dx

                        if self.y1 > self.y0:
                            self.y1 = event.y() + self.by
                            self.y0 = self.y1 - dy
                        else:
                            self.y0 = event.y() + self.by
                            self.y1 = self.y0 - dy

            self.update()

    def keyPressEvent(self, e):
        # self.pixmap().save(temp_path + '/aslfdhds.png')
        if e.key() == Qt.Key_Escape:
            self.clear_and_hide()

    def clear_and_hide(self):
        self.clear()
        self.hide()
        self.finder.clear_setup()
        self.botton_box.hide()
        self.flag = self.readyflag = self.choicing = self.move_rect = self.move_y0 = self.move_x0 = self.move_x1 = self.move_y1 = False
        self.x0 = self.y0 = self.rx0 = self.ry0 = self.x1 = self.y1 = self.mouse_posx = self.mouse_posy = -50
        self.image = None
        self.finding_rect = True
        self.backgrounderaser_pointlist = []
        self.eraser_pointlist = []
        self.pen_pointlist = []
        self.drawpix_pointlist = []
        self.drawtext_pointlist = []
        self.drawrect_pointlist = [[-2, -2], [-2, -2], 0]
        self.drawarrow_pointlist = [[-2, -2], [-2, -2], 0]
        self.drawcircle_pointlist = [[-2, -2], [-2, -2], 0]
        self.painter_tools = {'drawpix_bs_on': 0, 'drawarrow_on': 0, 'drawcircle_on': 0, 'drawrect_bs_on': 0,
                              'pen_on': 0, 'eraser_on': 0, 'drawtext_on': 0,
                              'backgrounderaser_on': 0}
        self.old_pen = self.old_eraser = self.old_brush = self.old_backgrounderaser = None
        self.left_button_push = False
        self.init_ss_thread = self.ocrthread = None
        self.paintlayer.clear()
        self.paintlayer.clearMask()
        self.mask.clear()
        self.mask.clearMask()
        self.clearMask()
        self.clear()
        print('cleard')

    # 绘制事件
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.on_init:  # 因为一些参数是在另外的线程初始化,所以判断当截屏线程初始化时不继续绘制(否则会有xxx no attribute报错)
            print('oninit return')
            return
        while len(self.backgrounderaser_pointlist):
            # print(self.backgrounderaser_pointlist)
            pixPainter = QPainter(self.pixmap())
            pixPainter.setRenderHint(QPainter.Antialiasing)
            pixPainter.setBrush(QColor(0, 0, 0, 0))
            pixPainter.setPen(Qt.NoPen)
            # pixPainter.setPen(Qt.NoPen)
            pixPainter.setCompositionMode(QPainter.CompositionMode_Clear)
            new_pen_point = self.backgrounderaser_pointlist.pop(0)
            # for i in range(len(self.backgrounderaser_pointlist )- 1):
            if self.old_pen[0] != -2 and new_pen_point[0] != -2:
                pixPainter.drawEllipse(new_pen_point[0] - self.tool_width / 2,
                                       new_pen_point[1] - self.tool_width / 2,
                                       self.tool_width, self.tool_width)
            self.old_pen = new_pen_point
            pixPainter.end()


class Commen_Thread(QThread):
    def __init__(self, action, *args):
        super(QThread, self).__init__()
        self.action = action
        self.args = args
        # print(self.args)

    def run(self):
        print('start_thread')
        if self.args:
            if len(self.args) == 1:
                self.action(self.args[0])
            elif len(self.args) == 2:
                self.action(self.args[0], self.args[1])
        else:
            self.action()


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.freeze_imgs = []
        self.setGeometry(500, 500, 300, 80)
        self.setWindowTitle('酱截屏')
        self.botton = QPushButton('截屏', self)
        self.botton.setToolTip('截屏功能,也可以使用快捷键ALT+Z')
        self.botton.setStatusTip('截屏功能,可以使用快捷键ALT+Z')
        self.botton.move(100, 30)
        self.botton.clicked.connect(screenshots.screen_shot)
        self.botton.setShortcut("Alt+Z")
        self.show()

    def hide(self):
        self.setWindowOpacity(0)
        super().hide()
        self.setWindowOpacity(1)


app = QApplication(sys.argv)
screenshots = Slabel()
window = Window()
print('''激活窗口后,按下Alt+z键进行截屏!\n如需全局快捷键方法可参考:https://blog.csdn.net/Fandes_F/article/details/103226341\n
本项目地址:https://github.com/fandesfyf/Jamscreenshot\n源码重构自本人项目Jamtools的截屏部分功能,如需滚动截屏、截屏文字识别、
图像主体识别功能可直接下载Beta版Jamtools安装文件(目前最新版为0.7.5Beta)，链接：https://download.csdn.net/download/Fandes_F/12318081''')
sys.exit(app.exec_())
