import math
import os
import sys

from PIL import Image
from PyQt5.QtCore import QRect, Qt, QThread, QStandardPaths, QPoint, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QPen, QIcon, QFont, QColor, QCursor, \
    QBrush, QPainterPath
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QTextEdit, QFileDialog, QGroupBox, QSlider, QWidget, \
    QColorDialog
import jamresourse  # 导入资源文件


class MaskLayer(QLabel):  # 遮罩层
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # 设置透明背景
        self.setMouseTracking(True)  # 鼠标追踪 设置为True时时刻监听鼠标位置

    def paintEvent(self, e):
        super().paintEvent(e)

        painter = QPainter(self)
        rect = QRect(min(self.parent.x0, self.parent.x1), min(self.parent.y0, self.parent.y1),
                     abs(self.parent.x1 - self.parent.x0), abs(self.parent.y1 - self.parent.y0))

        painter.setPen(QPen(Qt.red, 3, Qt.SolidLine))
        painter.drawRect(rect)  # 画框选区
        painter.drawRect(0, 0, self.width(), self.height())  # 画边界框
        painter.setPen(QPen(Qt.red, 10, Qt.SolidLine))
        # 画选框上的八个点移动点
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
        # 画分辨率
        painter.drawText(x, y,
                         '{}x{}'.format(abs(self.parent.x1 - self.parent.x0), abs(self.parent.y1 - self.parent.y0)))

        painter.setPen(Qt.NoPen)
        # 填充阴影遮罩
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

        # 画放大镜区
        if not (self.parent.painter_tools['drawcircle_on'] or self.parent.painter_tools['drawrect_bs_on'] or
                self.parent.painter_tools['pen_on'] or self.parent.painter_tools['eraser_on'] or
                self.parent.painter_tools['drawtext_on'] or self.parent.painter_tools['backgrounderaser_on']
                or self.parent.painter_tools['drawpix_bs_on'] or self.parent.move_rect):

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
                painter.setPen(QPen(Qt.white, 1, Qt.SolidLine))
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
        self.setMouseTracking(True)
        self.px = self.py = -50
        self.pixpng = ":/msk.jpg"
        self.startpaint = 0
        self.pixPainter = None

    def paintEvent(self, e):
        super().paintEvent(e)
        # 画鼠标位置处的圆
        if 1 in self.parent.painter_tools.values():
            painter = QPainter(self)
            painter.setPen(QPen(self.parent.pencolor, 1, Qt.SolidLine))
            rect = QRectF(self.px - self.parent.tool_width // 2, self.py - self.parent.tool_width // 2,
                          self.parent.tool_width, self.parent.tool_width)
            painter.drawEllipse(rect)
            painter.end()
        if self.startpaint:

            while len(self.parent.eraser_pointlist):  # 画橡皮擦
                self.pixPainter = QPainter(self.pixmap())
                self.pixPainter.setRenderHint(QPainter.Antialiasing)
                self.pixPainter.setBrush(QColor(0, 0, 0, 0))
                self.pixPainter.setPen(Qt.NoPen)
                self.pixPainter.setCompositionMode(QPainter.CompositionMode_Clear)
                new_pen_point = self.parent.eraser_pointlist.pop(0)
                if self.parent.old_pen[0] != -2 and new_pen_point[0] != -2:
                    self.pixPainter.drawEllipse(new_pen_point[0] - self.parent.tool_width / 2,
                                                new_pen_point[1] - self.parent.tool_width / 2,
                                                self.parent.tool_width, self.parent.tool_width)

                self.parent.old_pen = new_pen_point
                self.pixPainter.end()

            while len(self.parent.pen_pointlist):  # 画笔功能
                self.pixPainter = QPainter(self.pixmap())
                self.pixPainter.setRenderHint(QPainter.Antialiasing)
                self.pixPainter.setBrush(self.parent.pencolor)
                self.pixPainter.setPen(QPen(self.parent.pencolor, self.parent.tool_width, Qt.SolidLine))
                new_pen_point = self.parent.pen_pointlist.pop(0)
                if self.parent.old_pen[0] != -2 and new_pen_point[0] != -2:
                    path = QPainterPath(QPoint(self.parent.old_pen[0], self.parent.old_pen[1]))
                    path.quadTo(QPoint((new_pen_point[0] + self.parent.old_pen[0]) / 2,
                                       (new_pen_point[1] + self.parent.old_pen[1]) / 2),
                                QPoint(new_pen_point[0], new_pen_point[1]))
                    self.pixPainter.drawPath(path)
                self.parent.old_pen = new_pen_point
                self.pixPainter.end()

            while len(self.parent.drawpix_pointlist):  # 画马赛克/材质贴图功能
                self.pixPainter = QPainter(self.pixmap())
                self.pixPainter.setRenderHint(QPainter.Antialiasing)
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
                self.pixPainter.end()

            if self.parent.drawrect_pointlist[0][0] != -2 and self.parent.drawrect_pointlist[1][0] != -2:  # 画方形
                self.pixPainter = QPainter(self.pixmap())
                self.pixPainter.setRenderHint(QPainter.Antialiasing)
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
                self.pixPainter.end()

            if self.parent.drawcircle_pointlist[0][0] != -2 and self.parent.drawcircle_pointlist[1][0] != -2:  # 画圆
                self.pixPainter = QPainter(self.pixmap())
                self.pixPainter.setRenderHint(QPainter.Antialiasing)
                temppainter = QPainter(self)
                temppainter.setPen(QPen(self.parent.pencolor, 3, Qt.SolidLine))
                poitlist = self.parent.drawcircle_pointlist
                temppainter.drawEllipse(min(poitlist[0][0], poitlist[1][0]), min(poitlist[0][1], poitlist[1][1]),
                                        abs(poitlist[0][0] - poitlist[1][0]), abs(poitlist[0][1] - poitlist[1][1]))
                temppainter.end()
                if self.parent.drawcircle_pointlist[2] == 1:
                    self.pixPainter.setPen(QPen(self.parent.pencolor, 3, Qt.SolidLine))
                    self.pixPainter.drawEllipse(min(poitlist[0][0], poitlist[1][0]),
                                                min(poitlist[0][1], poitlist[1][1]),
                                                abs(poitlist[0][0] - poitlist[1][0]),
                                                abs(poitlist[0][1] - poitlist[1][1]))
                    self.parent.drawcircle_pointlist = [[-2, -2], [-2, -2], 0]
                self.pixPainter.end()

            if self.parent.drawarrow_pointlist[0][0] != -2 and self.parent.drawarrow_pointlist[1][0] != -2:  # 画箭头
                self.pixPainter = QPainter(self.pixmap())
                self.pixPainter.setRenderHint(QPainter.Antialiasing)
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
                self.pixPainter.end()

            if len(self.parent.drawtext_pointlist) > 1 or self.parent.text_box.paint:  # 画文字
                self.pixPainter = QPainter(self.pixmap())
                self.pixPainter.setRenderHint(QPainter.Antialiasing)
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

                self.pixPainter.end()
        else:
            self.startpaint = 1
        # print('end')


class AutotextEdit(QTextEdit):  # 文字框
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = self.document()
        self.document.contentsChanged.connect(self.textAreaChanged)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.paint = False
        self.parent = parent

    def textAreaChanged(self):  # 文本框边界自适应
        self.document.adjustSize()
        newWidth = self.document.size().width() + 25
        newHeight = self.document.size().height() + 15
        if newWidth != self.width():
            self.setFixedWidth(newWidth)
        if newHeight != self.height():
            self.setFixedHeight(newHeight)

    def keyPressEvent(self, e):  # 回车隐藏
        if e.key() == Qt.Key_Return:
            self.paint = True
            self.hide()
        super().keyPressEvent(e)

    def keyReleaseEvent(self, e):  # 回车释放绘图
        if e.key() == Qt.Key_Return:
            self.parent.update()
        super().keyReleaseEvent(e)


class Slabel(QLabel):  # 区域截图功能主图层/背景图层
    def __init__(self, parent=None):
        super().__init__()
        # self.pixmap()=QPixmap()
        self.paintlayer = PaintLayer(self)  # 实例化绘图层
        self.mask = MaskLayer(self)  # 实例化遮罩层

        self.text_box = AutotextEdit(self)  # 实例化文本框

        # 初始化位置、控制变量等
        self.flag = self.choicing = self.move_rect = self.move_y0 = self.move_x0 = self.move_x1 = self.move_y1 = False
        self.x0 = self.y0 = self.rx0 = self.ry0 = self.x1 = self.y1 = self.mouse_posx = self.mouse_posy = -50
        self.image = None
        self.setMouseTracking(True)  # 鼠标实时追踪
        self.parent = parent
        self.setWindowFlags(Qt.WindowStaysOnTopHint)  # 窗口置顶
        self.screen = QApplication.primaryScreen()  # 抓屏初始化
        self.tool_width = 5

        self.setToolTip("左键框选，右键返回")
        self.id = QApplication.desktop().winId()

        self.botton_box = QGroupBox(self)  # 按钮容器框

        def save_as():
            self.cutpic(save_as=True)

        save_botton = QPushButton(QIcon(":/saveicon.png"), '', self.botton_box)
        save_botton.setGeometry(0, 0, 30, 30)
        save_botton.setToolTip('另存为文件')
        save_botton.clicked.connect(save_as)
        # self.btn2 = QPushButton("滚动截屏", self.botton_box)
        # self.btn2.setGeometry(save_botton.x() + save_botton.width(), 0, 80, 30)
        # self.btn2.clicked.connect(self.roll_shot)
        self.btn1 = QPushButton("确定", self.botton_box)  # 确定按钮
        self.btn1.setGeometry(save_botton.x() + save_botton.width(), 0, 80, 30)
        self.btn1.clicked.connect(self.cutpic)

        self.botton_box.resize(self.btn1.width() + save_botton.width(), self.btn1.height())
        self.botton_box.hide()

        self.pencolor = Qt.red
        # self.backgrounderaser_pointlist = self.eraser_pointlist = self.drawrect_pointlist \
        #     = self.pen_pointlist = self.drawpix_pointlist = self.drawcircle_pointlist = \
        #     self.drawarrow_pointlist = self.drawtext_pointlist = []
        # 存储绘图数据的列表
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

        def get_color():
            self.pencolor = QColorDialog.getColor(Qt.red, self, '选择颜色')
            self.text_box.setTextColor(self.pencolor)
            self.choice_clor.setStyleSheet('background-color:{0};'.format(self.pencolor.name()))

        self.painter_box = QGroupBox(self)#左侧画笔工具栏
        self.painter_box.setGeometry(0, self.height() // 2,100,400)
        self.painter_box.setStyleSheet("QGroupBox{border:none}")
        self.choice_clor = QPushButton('', self.painter_box)  # 颜色选择按钮
        self.choice_clor.setToolTip('选择画笔颜色')
        icon4 = QIcon()
        icon4.addPixmap(QPixmap(":/yst.png"), QIcon.Normal, QIcon.Off)
        self.choice_clor.setIcon(icon4)
        self.choice_clor.move(0, 25)
        self.choice_clor.clicked.connect(get_color)

        self.slider_width = QSlider(Qt.Horizontal, self.painter_box)  # 大小调节滑动条
        label = QLabel(self.painter_box)
        label.setStyleSheet('background-color:rgba(200,180,180,200)')
        label.resize(20, 20)

        def change_size():
            label.setText(str(self.slider_width.value()))
            self.tool_width = self.slider_width.value()

        def resize_width():
            self.slider_width.resize(100, 20)
            label.move(self.slider_width.width(), self.slider_width.y())
            label.show()

        def re_resize():
            self.slider_width.resize(35, 20)
            # label.hide()
            label.move(self.slider_width.width(), self.slider_width.y())

        self.slider_width.setGeometry(0, self.choice_clor.y() - 20, 35, 20)
        self.slider_width.setToolTip('设置画笔大小,也可用鼠标滚轮调节')
        self.slider_width.valueChanged.connect(change_size)
        self.slider_width.sliderPressed.connect(resize_width)
        self.slider_width.sliderReleased.connect(re_resize)
        self.slider_width.setMaximum(99)
        self.slider_width.setMinimum(1)
        self.slider_width.setValue(10)
        label.move(self.slider_width.width(), self.slider_width.y())
        self.slider_width.show()

        def change_tools(r):
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
            choise_pix.hide()
            for tool in self.painter_tools:
                if tool == r:
                    self.painter_tools[tool] = 1
                else:
                    self.painter_tools[tool] = 0

        def change_msk():
            if self.painter_tools['drawpix_bs_on']:
                self.painter_tools['drawpix_bs_on'] = 0
                self.msk.setStyleSheet('')
                choise_pix.hide()
            else:
                change_tools('drawpix_bs_on')
                self.msk.setStyleSheet('background-color:rgb(239,50,50)')
                choise_pix.show()

        def change_bs():
            if self.painter_tools['drawrect_bs_on']:
                self.painter_tools['drawrect_bs_on'] = 0
                self.bs.setStyleSheet('')
            else:
                change_tools('drawrect_bs_on')
                self.bs.setStyleSheet('background-color:rgb(239,50,50)')

        def change_pen():
            if self.painter_tools['pen_on']:
                self.painter_tools['pen_on'] = 0
                self.pen.setStyleSheet('')
            else:
                change_tools('pen_on')
                self.pen.setStyleSheet('background-color:rgb(239,50,50)')

        def choise_drawpix():
            pic, l = QFileDialog.getOpenFileName(self, "选择图片", QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation), "img Files (*.PNG *.jpg *.JPG *.JPEG *.BMP *.ICO)"
                                                  ";;all files(*.*)")
            if pic:
                self.paintlayer.pixpng = pic
                icon4 = QIcon()
                icon4.addPixmap(QPixmap(pic), QIcon.Normal, QIcon.Off)
                choise_pix.setIcon(icon4)
                # print(pic)

        self.msk = QPushButton('', self.painter_box)  # 材质画笔按钮
        self.msk.setToolTip('材质贴图工具,可以充当马赛克')
        icon4 = QIcon()
        icon4.addPixmap(QPixmap(":/mskicon.png"), QIcon.Normal, QIcon.Off)
        self.msk.setIcon(icon4)
        self.msk.move(0, self.choice_clor.y() + self.choice_clor.height())
        self.msk.clicked.connect(change_msk)
        choise_pix = QPushButton('', self.painter_box)  # 选择贴图按钮
        choise_pix.setToolTip('选择笔刷材质贴图')
        icon4 = QIcon()
        icon4.addPixmap(QPixmap(":/msk.jpg"), QIcon.Normal, QIcon.Off)
        choise_pix.setIcon(icon4)
        choise_pix.move(30, self.msk.y())
        choise_pix.clicked.connect(choise_drawpix)
        choise_pix.hide()

        def draw_arrow():
            if self.painter_tools['drawarrow_on']:
                self.painter_tools['drawarrow_on'] = 0
                self.drawarrow.setStyleSheet('')
            else:
                change_tools('drawarrow_on')
                self.drawarrow.setStyleSheet('background-color:rgb(239,50,50)')

        self.drawarrow = QPushButton('', self.painter_box)  # 画箭头按钮
        self.drawarrow.setToolTip('绘制箭头')
        icon4 = QIcon()
        icon4.addPixmap(QPixmap(":/arrowicon.png").scaled(50, 50), QIcon.Normal, QIcon.Off)
        self.drawarrow.setIcon(icon4)
        self.drawarrow.move(0, self.msk.y() + self.msk.height())
        self.drawarrow.clicked.connect(draw_arrow)

        def drawcircle():
            if self.painter_tools['drawcircle_on']:
                self.painter_tools['drawcircle_on'] = 0
                self.drawcircle.setStyleSheet('')
            else:
                change_tools('drawcircle_on')
                self.drawcircle.setStyleSheet('background-color:rgb(239,50,50)')

        self.drawcircle = QPushButton('', self.painter_box)  # 画圆按钮
        self.drawcircle.setToolTip('绘制圆')
        icon4 = QIcon()
        icon4.addPixmap(QPixmap(":/circle.png").scaled(50, 50), QIcon.Normal, QIcon.Off)
        self.drawcircle.setIcon(icon4)
        self.drawcircle.move(0, self.drawarrow.y() + self.drawarrow.height())
        self.drawcircle.clicked.connect(drawcircle)

        self.bs = QPushButton('', self.painter_box)  # 画矩形按钮
        self.bs.setToolTip('绘制矩形')
        icon4 = QIcon()
        icon4.addPixmap(QPixmap(":/rect.png"), QIcon.Normal, QIcon.Off)
        self.bs.setIcon(icon4)
        self.bs.move(0, self.drawcircle.y() + self.drawcircle.height())
        self.bs.clicked.connect(change_bs)

        def drawtext():
            if self.painter_tools['drawtext_on']:
                self.painter_tools['drawtext_on'] = 0
                self.drawtext.setStyleSheet('')
            else:
                change_tools('drawtext_on')
                self.drawtext.setStyleSheet('background-color:rgb(239,50,50)')

        self.drawtext = QPushButton('', self.painter_box)  # 画文字按钮
        self.drawtext.setToolTip('绘制文字')
        icon4 = QIcon()
        icon4.addPixmap(QPixmap(":/texticon.png"), QIcon.Normal, QIcon.Off)
        self.drawtext.setIcon(icon4)
        self.drawtext.move(0, self.bs.y() + self.bs.height())
        self.drawtext.clicked.connect(drawtext)

        self.pen = QPushButton('', self.painter_box)  # 画笔工具按钮
        self.pen.setToolTip('画笔工具')
        icon4 = QIcon()
        icon4.addPixmap(QPixmap(":/pen.png"), QIcon.Normal, QIcon.Off)
        self.pen.setIcon(icon4)
        self.pen.move(0, self.drawtext.y() + self.drawtext.height())
        self.pen.clicked.connect(change_pen)

        def clear_paint():
            if self.painter_tools['eraser_on']:
                self.painter_tools['eraser_on'] = 0
                self.eraser.setStyleSheet('')
            else:
                change_tools('eraser_on')
                self.eraser.setStyleSheet('background-color:rgb(239,50,50)')

        def clear_background():
            if self.painter_tools['backgrounderaser_on']:
                self.painter_tools['backgrounderaser_on'] = 0
                self.backgrounderaser.setStyleSheet('')
            else:
                change_tools('backgrounderaser_on')
                self.backgrounderaser.setStyleSheet('background-color:rgb(239,50,50)')

        self.eraser = QPushButton('', self.painter_box)  # 橡皮擦工具按钮
        self.eraser.setToolTip('橡皮擦')
        icon4 = QIcon()
        icon4.addPixmap(QPixmap(":/eraser.png"), QIcon.Normal, QIcon.Off)
        self.eraser.setIcon(icon4)
        self.eraser.move(0, self.pen.y() + self.pen.height())
        self.eraser.clicked.connect(clear_paint)
        self.backgrounderaser = QPushButton('', self.painter_box)  # 背景橡皮擦工具按钮
        icon4 = QIcon()
        icon4.addPixmap(QPixmap(":/backgrounderaser.png"), QIcon.Normal, QIcon.Off)
        self.backgrounderaser.setIcon(icon4)
        self.backgrounderaser.setToolTip('背景橡皮擦')
        self.backgrounderaser.move(0, self.eraser.y() + self.eraser.height())
        self.backgrounderaser.clicked.connect(clear_background)
        self.showFullScreen()
        self.hide()
        if not os.path.exists("jamtools截屏"):
            os.mkdir("jamtools截屏")

    def screen_shot(self):  # 截图启动函数
        window.hide()  # 隐藏窗口
        pix = self.screen.grabWindow(self.id)  # 截图
        self.showFullScreen()
        self.setPixmap(pix)  # 把截图放在全屏窗口中
        self.painter_box.raise_()
        self.show()
        # 设置遮罩层
        self.mask.setGeometry(0, 0, self.width(), self.height())
        self.mask.show()
        # 设置绘画层
        # try:
        #     self.paintlayer.pixmap().fill(QColor(0,0,0,0))
        # except:
        #     print("initpainter")
        self.paintlayer.startpaint = 0
        self.paintlayer.pixpng = ":/msk.jpg"
        self.paintlayer.setGeometry(0, 0, self.width(), self.height())
        self.paintlayer.show()
        self.paintlayer.setPixmap(QPixmap(self.width(), self.height()))
        self.paintlayer.pixmap().fill(Qt.transparent)  # 重点,不然不透明
        # 初始化绘图数据和控制变量
        self.backgrounderaser_pointlist = []
        self.eraser_pointlist = []
        self.pen_pointlist = []
        self.drawpix_pointlist = []
        self.drawrect_pointlist = [[-2, -2], [-2, -2], 0]
        self.drawarrow_pointlist = [[-2, -2], [-2, -2], 0]
        self.drawcircle_pointlist = [[-2, -2], [-2, -2], 0]
        self.old_pen = self.old_eraser = self.old_brush = self.old_backgrounderaser = [-2, -2]
        # 初始化文本框
        self.text_box.resize(100, 30)
        self.text_box.setTextColor(self.pencolor)
        self.text_box.setStyleSheet("background-color: rgba(0, 0, 0, 10);")
        self.text_box.hide()
        self.choice_clor.setStyleSheet('background-color:rgb(255,0,0);')
        # 先保存原图
        pix.save("jamtools截屏/get.png")
        # print('save_the_primary_png')

    def choice(self):  # 显示选择界面的函数
        self.choicing = True

        btn1w = self.x1
        btn1h = self.y1
        if self.x1 > self.x0:
            btn1w = self.x1 - self.botton_box.width()

        if self.y1 > self.y0:
            btn1h = self.y1 - self.botton_box.height()
        self.botton_box.move(btn1w, btn1h)
        self.botton_box.show()

    # def roll_shot(self):
    #     x0 = min(self.x0, self.x1)
    #     y0 = min(self.y0, self.y1)
    #     x1 = max(self.x0, self.x1)
    #     y1 = max(self.y0, self.y1)
    #
    #     area = (x0, y0, x1 - x0, y1 - y0)
    #     if (x1 - x0) < 50 or (y1 - y0) < 50:
    #         Trayicon.showM('过小!')
    #         return
    #     self.hide()
    #     roller.setup()
    #     if not self.parent.ssview:
    #         self.parent.init_ssview()
    #     roller.auto_roll(area)
    #     print('end')

    def cutpic(self, save_as=False):  # 图片裁剪函数
        # img = cv2.imread("jamtools截屏/get.png")
        pix = self.pixmap()
        # pix.save('jamtools截屏/background.png')
        paintlayer = self.paintlayer.pixmap()
        paintlayer.save('jamtools截屏/getpainter.png')
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, paintlayer)
        painter.end()  # 一定要end
        pix.save('jamtools截屏/get.png')

        x0 = min(self.x0, self.x1)
        y0 = min(self.y0, self.y1)
        x1 = max(self.x0, self.x1)
        y1 = max(self.y0, self.y1)

        if (x1 - x0) < 1 or (y1 - y0) < 1:
            return
        cropped = (x0, y0, x1, y1)  # 裁剪
        img = Image.open("jamtools截屏/get.png")
        img = img.crop(cropped)
        img.save("jamtools截屏/jam_outputfile.png")
        if save_as:
            path, l = QFileDialog.getSaveFileName(self, "选择图片", QStandardPaths.writableLocation(
                QStandardPaths.PicturesLocation), "img Files (*.PNG *.jpg *.JPG *.JPEG *.BMP *.ICO)"
                                                  ";;all files(*.*)")
            if path:
                print(path)
                img.save(path)

        # self.hide()
        self.manage_data()

    def manage_data(self):  # 图片处理函数
        # 复制图像数据到剪切板
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(QPixmap("jamtools截屏/jam_outputfile.png"))

        # 复制文件到剪切板,而不是图像数据
        # data = QMimeData()
        # url = QUrl.fromLocalFile('/jamtools截屏/jam_outputfile.png')
        # data.setUrls([url])
        # clipboard.setMimeData(data)
        window.show()
        self.clear()
        self.hide()

    # 鼠标点击事件
    def mousePressEvent(self, event):
        self.botton_box.hide()
        if event.button() == Qt.LeftButton:
            self.left_button_push = True
            if 1 in self.painter_tools.values():#如果有绘画按钮按下就收集鼠标数据
                if self.painter_tools['drawrect_bs_on']:
                    self.drawrect_pointlist = [[event.x(), event.y()], [-2, -2], 0]
                    # self.drawrect_pointlist[0] = [event.x(), event.y()]
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
                # 以下检测选框拖拽
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
                        min(self.y0, self.y1) + 10 < event.y() < max(self.y0, self.y1) - 10):
                    self.move_rect = True
                    self.bx = abs(max(self.x1, self.x0) - event.x())
                    self.by = abs(max(self.y1, self.y0) - event.y())
                else:

                    self.flag = True# 这个是检测是否拖拽中
                    self.x0 = self.rx0 = event.x()  # rx0用于边界修正
                    self.y0 = self.ry0 = event.y()
                    if self.x1 == -50:
                        self.x1 = event.x()
                        self.y1 = event.y()

                    # print('re')
                if r:#检查是否拖动的是四个角
                    if (self.y0 - 8 < event.y() < self.y0 + 8) and (
                            min(self.x0, self.x1) - 10 < event.x() < max(self.x0, self.x1) + 10):
                        self.move_y0 = True
                        # print('y0')
                    elif self.y1 - 8 < event.y() < self.y1 + 8 and (
                            min(self.x0, self.x1) - 10 < event.x() < max(self.x0, self.x1) + 10):
                        self.move_y1 = True
                        # print('y1')
            self.update()
        elif event.button() == Qt.RightButton:#右键动作
            if 1 in self.painter_tools.values():#有绘图按钮按下则退出绘图按钮
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
            elif self.choicing:#退出选择框
                self.choicing = False
                # print('init')
                # self.painter.eraseRect()
                self.x0 = self.y0 = self.x1 = self.y1 = -50
                # self.btn1.hide()
                # self.btn2.hide()
                self.update()
            else:#最后退出截屏
                window.show()
                self.hide()

    # 鼠标释放事件
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.left_button_push = False
            # 画笔数据收集
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
            # 检测滑轮,以调整画笔或放大镜大小
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
            # 移动数据收集
            self.mouse_posx = event.x()
            self.mouse_posy = event.y()
            if 1 in self.painter_tools.values():
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
                # 以下为鼠标图标改变
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
                    # 拖拽数据收集
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
                    # 边界和选框拖拽功能
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
            self.hide()

    # 绘制事件
    def paintEvent(self, event):
        super().paintEvent(event)

        while len(self.backgrounderaser_pointlist):#背景橡皮擦
            # print(self.backgrounderaser_pointlist)
            pixPainter = QPainter(self.pixmap())
            pixPainter.setRenderHint(QPainter.Antialiasing)
            pixPainter.setBrush(QColor(0, 0, 0, 0))
            pixPainter.setPen(Qt.NoPen)
            pixPainter.setCompositionMode(QPainter.CompositionMode_Clear)
            new_pen_point = self.backgrounderaser_pointlist.pop(0)
            if self.old_pen[0] != -2 and new_pen_point[0] != -2:
                pixPainter.drawEllipse(new_pen_point[0] - self.tool_width / 2,
                                       new_pen_point[1] - self.tool_width / 2,
                                       self.tool_width, self.tool_width)
            self.old_pen = new_pen_point
            pixPainter.end()


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(500, 500, 300, 80)
        self.setWindowTitle('酱截屏')
        self.botton = QPushButton('截屏', self)
        self.botton.setToolTip('截屏功能,也可以使用快捷键ALT+Z')
        self.botton.setStatusTip('截屏功能,可以使用快捷键ALT+Z')
        self.botton.move(100, 30)
        self.botton.clicked.connect(screenshots.screen_shot)
        self.botton.setShortcut("Alt+Z")
        self.show()


app = QApplication(sys.argv)
screenshots = Slabel()
window = Window()
print('按下Alt+z键进行截屏!')
sys.exit(app.exec_())
