# -*- coding: utf-8 -*-
"""
fruit-recognizer 桌面应用（PyQt6 原生 UI）

直接运行：python app/fruit_app.py
打包：pyinstaller --noconfirm --windowed -F --name fruit-recognizer app/fruit_app.py
"""
import sys, os, ctypes, ctypes.wintypes as wintypes

# 把项目根目录加入 import 路径，便于 `from core.recognizer import ...`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation,
                           QEasingCurve, QRectF)
from PyQt6.QtGui import (QImage, QPixmap, QColor, QPainter, QPainterPath,
                         QFont, QBrush)
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                             QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect,
                             QFrame, QSizePolicy)

from core.recognizer import recognize_frame

# ====== 配置区 ======
# 智谱 API Key：从环境变量 FRUIT_API_KEY 读取。
# 申请地址：https://open.bigmodel.cn/
# 设置方式（PowerShell）： setx FRUIT_API_KEY "你的Key"
API_KEY = os.environ.get("FRUIT_API_KEY", "")

THEMES = {
    "dark": {
        "bg": 0xCC14101F, "panel2": "rgba(255,255,255,0.09)",
        "txt": "#eef2f8", "faint": "#6b7891", "accent": "#34d399",
    },
    "light": {
        "bg": 0xCCF2F5FA, "panel2": "rgba(255,255,255,0.85)",
        "txt": "#18202e", "faint": "#8a98ab", "accent": "#10b981",
    },
}


class DWM:
    SetWindowCompositionAttribute = ctypes.windll.user32.SetWindowCompositionAttribute
    DwmSetWindowAttribute = ctypes.windll.dwmapi.DwmSetWindowAttribute

    class _ACCENT(ctypes.Structure):
        _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int),
                    ("GradientColor", ctypes.c_uint), ("AnimationId", ctypes.c_int)]

    class _DATA(ctypes.Structure):
        _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p),
                    ("SizeOfData", ctypes.c_int)]

    @staticmethod
    def acrylic(hwnd, color_argb=0xCC14101F):
        try:
            acc = DWM._ACCENT(4, 2, color_argb, 0)
            data = DWM._DATA(19, ctypes.cast(ctypes.byref(acc), ctypes.c_void_p),
                             ctypes.sizeof(acc))
            DWM.SetWindowCompositionAttribute(wintypes.HWND(int(hwnd)), ctypes.byref(data))
        except Exception:
            pass

    @staticmethod
    def round_corners(hwnd):
        try:
            pref = wintypes.DWORD(2)
            DWM.DwmSetWindowAttribute(wintypes.HWND(int(hwnd)), 33,
                                      ctypes.byref(pref), ctypes.sizeof(pref))
        except Exception:
            pass


class RecognizeThread(QThread):
    done = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, frame_bgr):
        super().__init__()
        self.frame = frame_bgr.copy()

    def run(self):
        try:
            result = recognize_frame(self.frame, API_KEY)
            self.done.emit(result)
        except Exception as e:
            self.failed.emit(str(e))


class CameraView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cap = None
        self.current_frame = None
        self.pix = None
        self.scanning = False
        self.scan_y = 0
        self.setMinimumSize(720, 460)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.scan_timer = QTimer(self)
        self.scan_timer.setInterval(30)
        self.scan_timer.timeout.connect(self.advance_scan)
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                self.cap = None
        except Exception:
            self.cap = None
        if self.cap:
            self.timer.start(33)

    def poll(self):
        if not self.cap:
            return
        ok, frame = self.cap.read()
        if not ok or frame is None:
            return
        self.current_frame = frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
        self.pix = QPixmap.fromImage(img)
        self.update()

    def start_scan(self):
        self.scanning = True; self.scan_y = 0; self.scan_timer.start()

    def stop_scan(self):
        self.scanning = False; self.scan_timer.stop(); self.update()

    def advance_scan(self):
        self.scan_y += 7
        if self.scan_y > self.height():
            self.scan_y = 0
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath(); path.addRoundedRect(rect, 18, 18)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(18, 22, 34, 230)))
        p.drawPath(path)
        if self.pix is not None:
            scaled = self.pix.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled.width()) / 2
            y = (self.height() - scaled.height()) / 2
            p.setClipPath(path)
            p.drawPixmap(int(x), int(y), scaled)
            if self.scanning:
                p.fillRect(QRectF(0, self.scan_y - 2, self.width(), 4),
                           QColor(52, 211, 153, 200))
                p.fillRect(QRectF(0, self.scan_y + 2, self.width(), 14),
                           QColor(52, 211, 153, 40))
            p.setClipping(False)
        else:
            p.setPen(QColor(150, 160, 180))
            f = QFont(); f.setPointSize(13); p.setFont(f)
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter,
                       "未检测到摄像头\n请连接摄像头后重新打开")
        p.end()

    def release(self):
        self.timer.stop(); self.scan_timer.stop()
        if self.cap:
            try: self.cap.release()
            except Exception: pass
        self.cap = None


class ResultCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ResultCard")
        self.setFixedHeight(112)
        self.setVisible(False)
        self.theme = "dark"
        self.emo = QLabel("🍎")
        self.name = QLabel("—")
        self.desc = QLabel("")
        self.desc.setWordWrap(True)
        self.emo.setStyleSheet("font-size:42px;background:transparent;")
        right = QVBoxLayout(); right.setSpacing(4)
        right.addWidget(self.name); right.addWidget(self.desc)
        lay = QHBoxLayout(self); lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(18)
        lay.addWidget(self.emo); lay.addLayout(right, 1)

    def set_theme(self, theme):
        self.theme = theme

    def show_result(self, result):
        is_fruit = bool(result.get("is_fruit"))
        emo = result.get("emoji") or ("✅" if is_fruit else "⚠️")
        name = result.get("name") or ("识别完成" if is_fruit else "这不是水果")
        desc = result.get("desc") or ""
        self.emo.setText(emo); self.name.setText(str(name)); self.desc.setText(str(desc))
        if self.theme == "dark":
            bg = "rgba(24,40,34,0.96)" if is_fruit else "rgba(48,26,28,0.96)"
            bd = "rgba(52,211,153,0.55)" if is_fruit else "rgba(248,113,113,0.55)"
            txt, dim = "#eef2f8", "#9aa7bd"
        else:
            bg = "rgba(232,250,242,0.98)" if is_fruit else "rgba(254,238,238,0.98)"
            bd = "rgba(16,185,129,0.55)" if is_fruit else "rgba(239,68,68,0.55)"
            txt, dim = "#18202e", "#5b6a80"
        self.setStyleSheet(
            f"QFrame#ResultCard{{background:{bg};border:1px solid {bd};border-radius:16px;}}"
            f"QLabel{{background:transparent;}}")
        self.name.setStyleSheet(
            f"font-size:21px;font-weight:700;color:{txt};background:transparent;")
        self.desc.setStyleSheet(
            f"font-size:13px;color:{dim};background:transparent;")
        self.setVisible(True)
        eff = QGraphicsOpacityEffect(self); eff.setOpacity(0.0)
        self.setGraphicsEffect(eff)
        a = QPropertyAnimation(eff, b"opacity", self)
        a.setDuration(380); a.setStartValue(0.0); a.setEndValue(1.0)
        a.setEasingCurve(QEasingCurve.Type.OutBack); self._anim = a; a.start()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.theme = "dark"
        self.worker = None
        self.drag_pos = None
        self.setWindowTitle("水果识别")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(860, 680); self.setMinimumSize(760, 600)

        self.title = QLabel("🍉  水果识别")
        self.btn_theme = QPushButton("🌙"); self.btn_theme.setObjectName("IconBtn")
        self.btn_theme.setFixedSize(38, 38)
        self.btn_close = QPushButton("✕"); self.btn_close.setObjectName("IconBtn")
        self.btn_close.setFixedSize(38, 38)
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.btn_close.clicked.connect(self.close)
        bar = QHBoxLayout(); bar.setContentsMargins(18, 10, 10, 6)
        bar.addWidget(self.title); bar.addStretch(1)
        bar.addWidget(self.btn_theme); bar.addWidget(self.btn_close)

        self.cam = CameraView()
        self.card = ResultCard()
        self.btn_go = QPushButton("识别画面")
        self.btn_go.setObjectName("ActionBtn")
        self.btn_go.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_go.clicked.connect(self.do_recognize)
        self.status = QLabel("对准水果，点击「识别画面」")
        self.status.setStyleSheet("font-size:12px;")
        bottom = QHBoxLayout(); bottom.setContentsMargins(0, 0, 0, 0)
        bottom.addWidget(self.btn_go); bottom.addSpacing(14)
        bottom.addWidget(self.status, 1)

        content = QVBoxLayout(); content.setContentsMargins(20, 4, 20, 18)
        content.setSpacing(14)
        content.addWidget(self.cam, 1); content.addWidget(self.card); content.addLayout(bottom)

        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addLayout(bar); root.addLayout(content, 1)
        self.apply_theme()

    def apply_theme(self):
        t = THEMES[self.theme]
        self.setStyleSheet(f"""
            QWidget {{ color: {t['txt']}; }}
            QPushButton#IconBtn {{ background:transparent;border:none;border-radius:11px;font-size:15px; }}
            QPushButton#IconBtn:hover {{ background:rgba(150,160,180,0.18); }}
            QPushButton#ActionBtn {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {t['accent']}, stop:1 #0ea5e9);
                color:#fff;border:none;border-radius:14px;padding:12px 30px;
                font-size:15px;font-weight:700;
            }}
            QPushButton#ActionBtn:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #4ade80, stop:1 #38bdf8); }}
            QPushButton#ActionBtn:disabled {{ background:rgba(140,150,170,0.4); }}
        """)
        self.title.setStyleSheet(f"font-size:15px;font-weight:700;color:{t['txt']};")
        self.status.setStyleSheet(f"font-size:12px;color:{t['faint']};")
        self.card.set_theme(self.theme)
        DWM.acrylic(self.winId(), t["bg"])

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.drag_pos is not None and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, e):
        self.drag_pos = None

    def do_recognize(self):
        if self.worker and self.worker.isRunning():
            return
        frame = self.cam.current_frame
        if frame is None:
            self.status.setText("未获取到摄像头画面，请检查摄像头")
            return
        self.cam.start_scan(); self.btn_go.setEnabled(False)
        self.status.setText("识别中，请稍候…")
        self.worker = RecognizeThread(frame)
        self.worker.done.connect(self.on_result)
        self.worker.failed.connect(self.on_fail)
        self.worker.start()

    def on_result(self, result):
        self.cam.stop_scan(); self.btn_go.setEnabled(True)
        self.status.setText("识别完成 ✅" if result.get("is_fruit") else "提示：这不是水果")
        self.card.show_result(result)

    def on_fail(self, err):
        self.cam.stop_scan(); self.btn_go.setEnabled(True)
        self.status.setText(f"识别失败：{err[:60]}")

    def showEvent(self, e):
        super().showEvent(e)
        DWM.acrylic(self.winId(), THEMES[self.theme]["bg"])
        DWM.round_corners(self.winId())
        eff = QGraphicsOpacityEffect(self); eff.setOpacity(0.0)
        self.setGraphicsEffect(eff)
        a = QPropertyAnimation(eff, b"opacity", self)
        a.setDuration(420); a.setStartValue(0.0); a.setEndValue(1.0)
        a.setEasingCurve(QEasingCurve.Type.OutCubic); self._enter = a; a.start()

    def closeEvent(self, e):
        self.cam.release()
        if self.worker and self.worker.isRunning():
            self.worker.quit(); self.worker.wait(2000)
        super().closeEvent(e)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow(); w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
