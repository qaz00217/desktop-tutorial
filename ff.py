import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Blockly Python GUI (Local)")
window.resize(1000, 700)

# WebEngineView 생성
webview = QWebEngineView()

# HTML 경로
html_path = os.path.join(os.path.dirname(__file__), "blockly.html")
webview.load(QUrl.fromLocalFile(os.path.abspath(html_path)))

window.setCentralWidget(webview)
window.show()
sys.exit(app.exec())



# block.txt 전체 내용 읽기
with open("block.txt", "r", encoding="utf-8") as f:
    block_data = f.read()

# temp_main.py 줄 단위로 읽기
with open("temp_main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# "//블록" 있는 줄에 block_data 삽입
resultcount = ""
for line in lines:
    if "//블록" in line:
        resultcount += block_data + "\n"  # 삽입 후 줄바꿈 추가
    else:
        resultcount += line  # 원래 줄 그대로 추가

# 결과를 main.py에 저장
with open("main.py", "w", encoding="utf-8") as f:
    f.write(resultcount)
