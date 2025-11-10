import math
import numpy as np

# ✅ 벡터를 단위 벡터로 변환 (Normalize)
def normalize(v):
    v = np.array(v, dtype=float)
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

# ✅ 벡터 내적 (Dot product)
def dot(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    return float(np.dot(a, b))

# ✅ 벡터 외적 (Cross product)
def cross(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    return np.cross(a, b)

# ✅ 두 점 사이 거리
def distance(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    return float(np.linalg.norm(a - b))

# ✅ 행렬 곱
def matmul(A, B):
    A = np.array(A, dtype=float)
    B = np.array(B, dtype=float)
    return A @ B

# ✅ 올림, 내림, 제곱근
def ceil(x): return math.ceil(x)
def floor(x): return math.floor(x)
def sqrt(x): return math.sqrt(x)

# ✅ min, max (리스트나 튜플 입력)
def minimum(values): return min(values)
def maximum(values): return max(values)
