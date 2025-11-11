import tkinter as tk
from tkinter import messagebox
import json

root = tk.Tk()
root.title("자동 블록코딩 + C# 변환 예제")
root.geometry("800x500")

# Canvas 생성
canvas = tk.Canvas(root, bg="white", width=750, height=300)
canvas.pack(padx=5, pady=5)

# 예시 블록 JSON
blocks_json = """
[
    {"라벨":"거리", "함수":"distance", "블럭타입":"만들기", "params":[5]},
    {"라벨":"속도", "함수":"speed", "블럭타입":"만들기", "params":[2]},
    {"라벨":"거리 더하기", "함수":"distanceAdd", "블럭타입":"붙이기", "target":"distance", "params":[3]},
    {"라벨":"속도 바꾸기", "함수":"speedSet", "블럭타입":"바꾸기", "target":"speed", "params":[7]}
]
"""
blocks_data = json.loads(blocks_json)
blocks = {}

# 블록 생성
for i, b in enumerate(blocks_data):
    x, y, w, h = 50, 50 + i*60, 150, 40
    rect = canvas.create_rectangle(x, y, x+w, y+h, fill="lightblue")
    text = canvas.create_text(x+w/2, y+h/2, text=b["라벨"])
    blocks[b["라벨"]] = {"json": b, "x": x, "y": y, "w": w, "h": h, "rect": rect, "text": text}

# 드래그 & 드롭
selected = None
offset_x = 0
offset_y = 0

def select_block(event):
    global selected, offset_x, offset_y
    for label, b in blocks.items():
        if b["x"] <= event.x <= b["x"]+b["w"] and b["y"] <= event.y <= b["y"]+b["h"]:
            selected = label
            offset_x = event.x - b["x"]
            offset_y = event.y - b["y"]
            break

def drag_block(event):
    global selected
    if selected:
        b = blocks[selected]
        b["x"] = event.x - offset_x
        b["y"] = event.y - offset_y
        canvas.coords(b["rect"], b["x"], b["y"], b["x"]+b["w"], b["y"]+b["h"])
        canvas.coords(b["text"], b["x"]+b["w"]/2, b["y"]+b["h"]/2)

def release_block(event):
    global selected
    selected = None

canvas.bind("<Button-1>", select_block)
canvas.bind("<B1-Motion>", drag_block)
canvas.bind("<ButtonRelease-1>", release_block)

# C# 코드 생성
def generate_csharp():
    lines = []
    lines.append("using UnityEngine;\npublic class BlockScript : MonoBehaviour {")
    for label, b in blocks.items():
        block = b["json"]
        fname = block["함수"]
        btype = block.get("블럭타입", "만들기")
        params = block.get("params", [])
        target = block.get("target", None)
        lines.append(f"    void {fname}() {{")
        if btype == "만들기":
            val = params[0] if params else 0
            lines.append(f"        float {fname} = {val};  // 자동 생성 변수 블록")
        elif btype == "붙이기":
            val = params[0] if params else 0
            lines.append(f"        {target} += {val};  // 붙이기 블록")
        elif btype == "바꾸기":
            val = params[0] if params else 0
            lines.append(f"        {target} = {val};  // 바꾸기 블록")
        lines.append("    }\n")
    lines.append("}")
    print("\n".join(lines))

# 버튼
btn_generate = tk.Button(root, text="C# 코드 생성", command=generate_csharp)
btn_generate.pack(pady=5)

root.mainloop()
