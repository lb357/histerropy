import logging

VERSION = "v.19102025"
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(message)s')
logger.setLevel(logging.DEBUG)
logger.info(f"HisterroPy ({VERSION}) starting...")

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QScrollArea, QFileDialog, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QMouseEvent, QIcon
from ui_mainwindow import Ui_MainWindow
from ui_info import Ui_Info
from histerro_core import HisterroCore




class MainWindow(QMainWindow):
    def __init__(self):

        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        app_icon = QIcon("icon.ico")
        self.setWindowIcon(app_icon)

        self.zoom_coef = 1.0
        self.zoom_power = 1.5
        self.counter = 0

        self.tsx, self.tsy, self.sx, self.sy, self.fx, self.fy = 0, 0, 0, 0, 0, 0

        self.hcore = HisterroCore()
        self.hcore.load_image("initimg.jpg")

        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.ui.scrollArea.setWidget(self.imageLabel)
        self.ui.scrollArea.wheelEvent = self.scroll_area_wheel_event

        self.imageLabel.mousePressEvent = self.image_label_mouse_press_event
        self.imageLabel.mouseReleaseEvent = self.image_label_mouse_release_event
        self.imageLabel.mouseMoveEvent = self.image_label_mouse_move_event

        self.ui.actionOpen_Image.triggered.connect(self.action_open_image)
        self.ui.actionExit.triggered.connect(self.action_exit)
        self.ui.actionBleach.triggered.connect(self.action_bleach)
        self.ui.actionGrayscale.triggered.connect(self.action_graysacle)
        self.ui.actionBlur.triggered.connect(self.action_blur)
        self.ui.actionCompile.triggered.connect(self.action_compile)
        self.ui.actionRender.triggered.connect(self.action_render)
        self.ui.actionRemove_Line_Breaks.triggered.connect(self.action_remove_line_breaks)
        self.ui.actionSave_Text.triggered.connect(self.action_save_text)
        self.ui.actionInfo.triggered.connect(self.action_info)


        self.info_widget = QWidget()
        self.iui = Ui_Info()
        self.iui.setupUi(self.info_widget)



        self.image_update()
        self.text = []


    def scroll_area_wheel_event(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.image_update(event.angleDelta().y())
        else:
            QScrollArea.wheelEvent(self.ui.scrollArea, event)

    def image_label_mouse_press_event(self, event: QMouseEvent):
        if event.button() & Qt.MouseButton.LeftButton:
            self.tsx, self.tsy = int(event.position().x() * self.zoom_coef), int(event.position().y() * self.zoom_coef)
            self.hcore.temp_rect = (self.tsx, self.tsy, self.tsx, self.tsy)
            self.hcore.update_display()
            self.image_update()

    def image_label_mouse_release_event(self, event: QMouseEvent):
        if event.button() & Qt.MouseButton.LeftButton:
            self.update_rect_area(event)

            self.counter += 1
            self.hcore.add_rect(self.counter, (self.sx, self.sy, self.fx, self.fy))


            self.hcore.temp_rect = ()

        elif event.button() & Qt.MouseButton.RightButton:
            x, y = int(event.position().x() * self.zoom_coef), int(event.position().y() * self.zoom_coef)
            self.hcore.remove_point_rect(x, y)
            self.hcore.remove_point_rect(x, y)
            self.hcore.temp_rect = ()

        self.hcore.update_display()
        self.image_update()

    def image_label_mouse_move_event(self, event: QMouseEvent):
        if len(self.hcore.temp_rect) != 0:
            self.update_rect_area(event)

            self.hcore.temp_rect = (self.sx, self.sy, self.fx, self.fy)
            self.hcore.update_display()
            self.image_update()

    def update_rect_area(self, event: QMouseEvent):
        x, y = int(event.position().x() * self.zoom_coef), int(event.position().y() * self.zoom_coef)
        sx = min(self.tsx, x)
        sy = min(self.tsy, y)
        fx = max(self.tsx, x)
        fy = max(self.tsy, y)

        if (fx-sx)*(fy-sy) <=4:
            fx = sx + 2
            fy = sy + 2

        h, w, c = self.hcore.get_hwc()
        self.sx = max(sx, 0)
        self.sy = max(sy, 0)
        sfx = min(w, fx)
        sfy = min(h, fy)
        self.fx = min(self.sx + self.hcore.rect_size, sfx)
        self.fy = min(self.sy + self.hcore.rect_size, sfy)


    def image_update(self, zoom: float = 0):
        image = self.hcore.get_display()
        if zoom > 0:
            self.zoom_coef /= self.zoom_power
        elif zoom < 0:
            self.zoom_coef *= self.zoom_power

        image_pixmap = QPixmap.fromImage(image)
        image_size = image_pixmap.size()
        image_size.scale(int(image_size.width() / self.zoom_coef),
                         int(image_size.height() / self.zoom_coef), Qt.AspectRatioMode.KeepAspectRatio)
        image_pixmap = image_pixmap.scaled(image_size)
        self.imageLabel.setPixmap(image_pixmap)

    def action_exit(self, s):
        sys.exit(app.exec())

    def action_bleach(self, s):
        self.hcore.bleach()
        self.hcore.update_display()
        self.image_update()

    def action_graysacle(self, s):
        self.hcore.grayscale()
        self.hcore.update_display()
        self.image_update()

    def action_blur(self, s):
        self.hcore.blur()
        self.hcore.update_display()
        self.image_update()


    def action_open_image(self, s):
        imgpath = QFileDialog.getOpenFileName(self, "Open Image", "/", "Images (*.jpg;*.jpeg;*.jfif;*.jpe;*.png;*.bmp;*.tif;*.tiff;*.webp;)")
        if imgpath[0] != "":
            logger.info(f"Image from {imgpath[0]}")
            self.counter = 0
            self.tsx, self.tsy, self.sx, self.sy, self.fx, self.fy = 0, 0, 0, 0, 0, 0

            self.hcore.load_image(imgpath[0])
            self.image_update()


    def action_compile(self, s):
        self.text = self.hcore.compile()

        self.ui.textBrowser.setHtml(self.hcore.get_html(self.text))

        self.image_update()

    def action_render(self, s):
        self.hcore.update_display()
        self.image_update()

    def action_remove_line_breaks(self, s):
        self.text = self.hcore.rem_line_breaks(self.text)
        self.ui.textBrowser.setHtml(self.hcore.get_html(self.text))

    def action_info(self, s):
        self.info_widget.show()

    def action_save_text(self, s):
        txtpath = QFileDialog.getSaveFileName(self, "Save Text", "/",
                                              "Text (*.txt)")
        if txtpath[0] != "":
            logger.info(f"Text to {txtpath[0]}")
            with open(str(txtpath[0]), "w", encoding="UTF-16") as file:
                file.write(self.hcore.get_text(self.text))





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    logger.info(f"HisterroPy by Leonid Briskindov started!")
    window.show()
    sys.exit(app.exec())