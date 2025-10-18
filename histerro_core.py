import cv2
import numpy as np
from PySide6.QtGui import QImage
import easyocr
import easyocr.utils
from paddleocr import PaddleOCR
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(message)s')
logger.setLevel(logging.DEBUG)

WORD_PROPABLY = 0
WORD_PERHAPS = 1
WORD_HARDLY = 2

OCR_EASY = "easyocr"
OCR_PADDLE = "paddleocr"

#OCR = OCR_EASY
with open("settings.ini", "r") as file:
    OCR=eval(file.readline())



class HisterroCore:
    def __init__(self):
        self.image = np.zeros((128, 128, 3), dtype=np.uint8)
        self.rect_size = 2560
        self.alpha, self.beta = 1.2, 0
        self.display = self.image.copy()
        self.temp_rect = ()
        self.rects = {}
        if OCR == OCR_EASY:
            self.ocr = easyocr.Reader(["ru"])
        elif OCR == OCR_PADDLE:
            self.ocr = PaddleOCR(
                                            use_doc_orientation_classify=False,
                                            use_doc_unwarping=False,
                                            use_textline_orientation=False,
                lang="ru"

            )
        else:
            self.ocr = None
            raise Exception(f"Unknown OCR: {OCR}")



    def load_image(self, path):
        self.rects = {}
        self.temp_rect = ()
        self.image = cv2.imread(path, flags=cv2.IMREAD_COLOR)
        self.update_display()

    def update_display(self):
        self.display = self.image.copy()
        for rect in self.rects:
            temp_rect_pts = ((self.rects[rect][0], self.rects[rect][1]), (self.rects[rect][2], self.rects[rect][3]))
            self.display = cv2.rectangle(self.display, *temp_rect_pts, (255, 0, 0), 3)
            self.display = cv2.putText(self.display, str(rect), temp_rect_pts[0], cv2.FONT_HERSHEY_SIMPLEX,
                                1, (255, 0, 0), 1, cv2.LINE_AA)

        if len(self.temp_rect) == 4:
            temp_rect_pts = ((self.temp_rect[0], self.temp_rect[1]), (self.temp_rect[2], self.temp_rect[3]))
            self.display = cv2.rectangle(self.display, *temp_rect_pts, (0, 0, 255), 2)
        #print(self.start_point)

    def add_rect(self, name, rect):
        self.rects[name] = rect

    def remove_rect(self, name):
        del self.rects[name]

    def remove_point_rect(self, x, y):
        rrect = None
        for rect in self.rects:
            sx, sy, fx, fy = self.rects[rect]
            if sx < x < fx and sy < y < fy:
                rrect = rect
                break
        if rrect is not None:
            self.remove_rect(rrect)

    def get_display(self):
        h, w, c = self.get_hwc()
        return QImage(self.display.data, w, h, c*w, QImage.Format.Format_BGR888)

    def get_hwc(self):
        h, w, c = self.image.shape
        return h, w, c

    def compile(self, display_words: bool = True, paragraphs: bool = True):
        logger.info(f"Сompiling an image into text... | display_words: {display_words}, paragraphs: {paragraphs}, OCR: {OCR}, rects: {len(self.rects)}")
        txt = []
        for rect in sorted(self.rects.keys()):
            sx, sy, fx, fy = self.rects[rect]
            rimg = self.image[sy:fy, sx:fx]
            #horizontal_list, free_list = self.ocr.detect(rimg)
            #rtxt = self.ocr.recognize(img_cv_grey=np.array(cv2.cvtColor(rimg, cv2.COLOR_BGR2GRAY)),
            #                          horizontal_list=horizontal_list[0],
            #                          free_list=free_list[0])

            if OCR == OCR_EASY:
                rtxt = self.ocr.readtext(rimg)
            elif OCR==OCR_PADDLE:
                rtxt = self.convert_paddle_to_easy(self.ocr.predict(rimg))
            else:
                rtxt = []
                raise Exception(f"Unknown OCR: {OCR}")


            #print(rtxt)


            if paragraphs:
                mx = min([word[0][p][0] for p in range(4) for word in rtxt])
                offset = 0
                for word in rtxt:
                    if any(word[0][p][0] == mx for p in range(4)):
                        offset = int((max([word[0][p][0] for p in range(4)]) - mx) / len(word[1])*1.25)
                        break

                for i in range(len(rtxt)-1):
                    cwx = max([rtxt[i][0][p][0] for p in range(4)])
                    nwx = min([rtxt[i+1][0][p][0] for p in range(4)])
                    nwys = min([rtxt[i+1][0][p][1] for p in range(4)])
                    nwyf = max([rtxt[i + 1][0][p][1] for p in range(4)])

                    if ((nwx - mx) > offset and nwx < cwx) :
                        rtxt.insert(i+1, [[[mx, nwys], [nwx, nwys], [nwx, nwyf], [mx, nwyf]], "\n\t", 1])
                    elif (cwx - mx) > offset and i == 0:
                        rtxt.insert(0, [[[mx, nwys], [nwx, nwys], [nwx, nwyf], [mx, nwyf]], "\n\t", 1])



            for word in rtxt:


                word_area = [np.array(word[0], dtype=np.int32)+np.array([sx, sy])]
                #print(word)
                if float(word[2]) > 0.90:
                    txt.append([word[1], WORD_PROPABLY])
                    if display_words:
                        self.display = cv2.polylines(self.display, word_area, True,
                                                     (0, 255, 0), 2)

                elif float(word[2]) > 0.80:
                    txt.append([word[1], WORD_PERHAPS])
                    if display_words:
                        self.display = cv2.polylines(self.display, word_area, True,
                                                     (0, 255, 255), 2)

                else:
                    txt.append([word[1], WORD_HARDLY])
                    if display_words:
                        #print(np.array(word[0], dtype=np.int32))
                        self.display = cv2.polylines(self.display,word_area, True,
                                                     (0, 0, 255), 2)
            txt.append(["\n", WORD_PROPABLY])
        logger.info("Image compiled!")
        return txt

    @staticmethod
    def rem_line_breaks(txt):
        for wi in range(len(txt)-1):
            if len(txt[wi][0]) >= 2:
                if txt[wi][0][-1] == "-" or txt[wi][0][-1] == "–":
                    txt[wi][0] = txt[wi][0][:-1] + txt[wi+1][0]
                    txt[wi+1][0] = ""
                    txt[wi][1] = WORD_HARDLY
                    txt[wi+1][1] = WORD_HARDLY
                if txt[wi][0][-2:] == "- " or txt[wi][0][-2:] == "– ":
                    txt[wi][0] = txt[wi][0][:-2] + txt[wi+1][0]
                    txt[wi + 1][0] = ""
                    txt[wi][1] = WORD_HARDLY
                    txt[wi+1][1] = WORD_HARDLY
        return txt

    @staticmethod
    def get_text(txt):
        out = ""
        for word in txt:
            out += f"{word[0]} "
        return out

    @staticmethod
    def get_html(txt):
        out = ""
        for word in txt:
            if word[0] == "\n":
                out += f"<br>"
            elif word[0] == "\n\t":
                out += f"<br><p>&emsp;</p>"
            elif word[0] == "":
                out += ""
            else:
                if word[1] == WORD_PROPABLY:
                    out += f"<span style=\" font-family:'Times New Roman'; font-size:12pt; color:#008800;\" >{word[0]} </span>"
                elif word[1] == WORD_PERHAPS:
                    out += f"<span style=\" font-family:'Times New Roman'; font-size:12pt; color:#888800;\" >{word[0]} </span>"
                else:
                    out += f"<span style=\" font-family:'Times New Roman'; font-size:12pt; color:#880000;\" >{word[0]} </span>"
        return out


    def blur(self):
        self.image = cv2.blur(self.image, (4, 4))

    def bleach(self):
        self.image = cv2.convertScaleAbs(self.image, alpha=self.alpha, beta=self.beta)

    def grayscale(self):
        self.image = cv2.cvtColor(cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)

    def convert_paddle_to_easy(self, data):
        out = []
        for word in data:
            texts = word["rec_texts"]
            scores = word["rec_scores"]
            rec_polys = [arr.tolist() for arr in word["rec_polys"]]
            for i in range(len(texts)):
                out.append([rec_polys[i], texts[i], scores[i]])
        return out