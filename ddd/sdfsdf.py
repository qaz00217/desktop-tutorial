import re

# ===== 기존 C# 코드 =====
cscode = """
void DistanceAdd()
{
    distance = 5;
}

void SpeedSet()
{
    speed = 2;
}
"""

# ===== 블록 매핑 정보 (함수별 순서대로 적용) =====
block_mappings = [
    {"함수이름":"함수1","변수이름":"변수1","값":10,"블럭타입":"바꾸기"},
    {"함수이름":"함수1","변수이름":"변수1","값":3,"블럭타입":"붙이기"},
    {"함수이름":"함수2","변수이름":"변수2","값":7,"블럭타입":"바꾸기"},
    {"함수이름":"함수2","변수이름":"변수2","값":5,"블럭타입":"붙이기"}
]

lines = cscode.splitlines()
new_lines = []
current_func = None
mappings_per_func = {}

# 블록 매핑을 함수별로 그룹화
for mapping in block_mappings:
    func = mapping["함수이름"]
    mappings_per_func.setdefault(func, []).append(mapping)

i = 0
while i < len(lines):
    line = lines[i]
    func_match = re.match(r'\s*void (\w+)\(\)', line)
    if func_match:
        orig_func = func_match.group(1)
        # 현재 함수에 대응되는 매핑 있는지 확인
        func_mappings = mappings_per_func.get(orig_func, [])
        if func_mappings:
            # 함수 이름 치환 (첫 매핑 기준)
            first_map = func_mappings[0]
            line = line.replace(orig_func, first_map["함수이름"])
            current_func = first_map["함수이름"]
        new_lines.append(line)
        i += 1
        # 함수 바디 처리
        while i < len(lines):
            body_line = lines[i]
            if body_line.strip() == "}":
                # 붙이기 블록 추가: 함수 끝 직전에 append
                for mapping in func_mappings:
                    if mapping["블럭타입"] == "붙이기":
                        new_lines.append(f"    {mapping['변수이름']} += {mapping['값']};  // 붙이기 블록")
                new_lines.append(body_line)
                break
            # 바꾸기 블록: 기존 라인 덮어쓰기
            if func_mappings:
                # 첫 번째 매핑 중 바꾸기 블록이면 적용
                for mapping in func_mappings:
                    if mapping["블럭타입"] == "바꾸기":
                        new_lines.append(f"    {mapping['변수이름']} = {mapping['값']};  // 바꾸기 블록")
                        break
                else:
                    new_lines.append(body_line)
            else:
                new_lines.append(body_line)
            i += 1
    else:
        new_lines.append(line)
    i += 1

new_cscode = "\n".join(new_lines)
print(new_cscode)
