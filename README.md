# Jamscreenshot
一个用python实现的类似微信QQ截屏的工具源码，
来自本人自制工具集[Jamtools](https://github.com/fandesfyf/JamTools)里面的截屏部分整合，代码完全原创，分享出来
转载请标明出处！

如果你还需要滚动截屏功能,可以看看[这个](https://github.com/fandesfyf/roll_screenshot)
----20210206更新------
新增了透视裁剪工具(类似于PS里的用法)、多边形截图工具、取色器工具、油漆桶工具、背景还原画笔(配合背景橡皮擦使用)、支持回退10步操作历史记录、新增一键还原按钮、新增智能选框的开关。画笔等增加透明度支持，在画笔/标记时可以通过按住ctrl键+滚轮快速调整画笔透明度，新增常用颜色到取色按钮(鼠标划过即可显示)、固定截屏在屏幕上时可以通过按住ctrl+滚轮快速调节截屏的透明度

# 效果图
加了一个简陋的主界面

![image](https://github.com/fandesfyf/Jamscreenshot/blob/master/image/60430e4e61d28d0e79da9d58e46037f.png)

截图效果：
![image](https://github.com/fandesfyf/Jamscreenshot/blob/master/image/jp00.png)

![image](https://github.com/fandesfyf/Jamscreenshot/blob/master/image/jp2.png)

![image](https://github.com/fandesfyf/Jamscreenshot/blob/master/image/58e820362dd287f6668e011e20a1020.png)

![image](https://github.com/fandesfyf/Jamscreenshot/blob/master/image/0180a5748681abe7254ce6734aa64de.png)
可以看到，几乎实现了微信截图的所有功能，还有一些微信截图没有的功能，像材质图片画笔、背景橡皮擦、所有颜色自选、画笔大小/放大镜倍数可通过滑轮调节等；
代码总长999+行，直接运行即可！

-----------------2020.4.9更新--------------
更新：
支持把多个图片固定在屏幕上
支持窗口控件识别(基于opencv的轮廓识别功能)，需要opencv库！
直接pip install opencv-python即可

# 模块安装
主要使用的是PyQt5模块
直接 pip install PyQt5 即可
还需要PIL
直接pip install Pillow 即可

附带的jamresourse.py文件是图片资源文件(鼠标样式等)

# 提交环境为python3.7   pyqt5==5.13.2  win10 一切正常!
其他环境自行测试
