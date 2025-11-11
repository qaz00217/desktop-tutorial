from PIL import Image

# PNG 열기
img = Image.open("skin.png").convert("RGB")
width, height = img.size

print(f"Image size: {width}x{height}")

# 모든 픽셀 RGB 출력
for y in range(height):
    for x in range(width):
        r, g, b = img.getpixel((x, y))
        print(f"{r} {g} {b}")
