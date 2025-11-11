import numpy as np
import math

# ------------------------------
# 1. 점/선/평면/삼각형 교점
# ------------------------------

def point_plane_distance(p, plane_point, plane_normal):
    """점 p와 평면(plane_point, plane_normal) 사이 거리"""
    p, plane_point, plane_normal = map(np.array, (p, plane_point, plane_normal))
    plane_normal = plane_normal / np.linalg.norm(plane_normal)
    return np.dot(p - plane_point, plane_normal)

def line_plane_intersection(p0, p1, plane_point, plane_normal):
    """선분 p0->p1과 평면 교점, 없으면 None"""
    p0, p1, plane_point, plane_normal = map(np.array, (p0, p1, plane_point, plane_normal))
    plane_normal = plane_normal / np.linalg.norm(plane_normal)
    u = p1 - p0
    denom = np.dot(plane_normal, u)
    if abs(denom) < 1e-6:  # 평행
        return None
    t = np.dot(plane_normal, plane_point - p0) / denom
    if 0 <= t <= 1:
        return p0 + t * u
    return None

def ray_triangle_intersection(ray_origin, ray_dir, tri):
    """Möller–Trumbore 알고리즘"""
    epsilon = 1e-6
    vertex0, vertex1, vertex2 = map(np.array, tri)
    edge1 = vertex1 - vertex0
    edge2 = vertex2 - vertex0
    h = np.cross(ray_dir, edge2)
    a = np.dot(edge1, h)
    if abs(a) < epsilon:
        return None
    f = 1.0 / a
    s = ray_origin - vertex0
    u = f * np.dot(s, h)
    if u < 0.0 or u > 1.0:
        return None
    q = np.cross(s, edge1)
    v = f * np.dot(ray_dir, q)
    if v < 0.0 or u + v > 1.0:
        return None
    t = f * np.dot(edge2, q)
    if t > epsilon:
        return ray_origin + ray_dir * t
    return None

# ------------------------------
# 2. 벡터 각도 계산
# ------------------------------

def angle_between_vectors(a, b):
    a, b = map(np.array, (a, b))
    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b)
    dot_product = np.clip(np.dot(a_norm, b_norm), -1.0, 1.0)
    return math.acos(dot_product)  # 라디안

def vector_to_angles(v):
    """방향 벡터를 yaw(pan), pitch(tilt) 각도로 변환"""
    x, y, z = v
    yaw = math.atan2(z, x)
    pitch = math.atan2(y, math.sqrt(x**2 + z**2))
    return yaw, pitch

# ------------------------------
# 3. 회전 (행렬, 쿼터니언)
# ------------------------------

def rotation_matrix(axis, theta):
    """axis='x','y','z', theta in radians"""
    c, s = math.cos(theta), math.sin(theta)
    if axis == 'x':
        return np.array([[1,0,0],[0,c,-s],[0,s,c]])
    elif axis == 'y':
        return np.array([[c,0,s],[0,1,0],[-s,0,c]])
    elif axis == 'z':
        return np.array([[c,-s,0],[s,c,0],[0,0,1]])
    else:
        raise ValueError("Axis must be 'x','y','z'")

def quaternion_multiply(q1, q2):
    """q = [w, x, y, z]"""
    w1,x1,y1,z1 = q1
    w2,x2,y2,z2 = q2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 - x1*z2 + y1*w2 + z1*x2
    z = w1*z2 + x1*y2 - y1*x2 + z1*w2
    return np.array([w,x,y,z])

def quaternion_rotate_vector(q, v):
    """벡터 v를 쿼터니언 q로 회전"""
    q_conj = np.array([q[0], -q[1], -q[2], -q[3]])
    v_quat = np.array([0]+list(v))
    return quaternion_multiply(quaternion_multiply(q, v_quat), q_conj)[1:]

# ------------------------------
# 4. 투영 행렬 (카메라)
# ------------------------------

def perspective(fov, aspect, near, far):
    """원근 투영 행렬"""
    f = 1.0 / math.tan(fov/2)
    mat = np.zeros((4,4))
    mat[0,0] = f / aspect
    mat[1,1] = f
    mat[2,2] = (far+near)/(near-far)
    mat[2,3] = (2*far*near)/(near-far)
    mat[3,2] = -1
    return mat

def orthographic(left, right, bottom, top, near, far):
    """정투영 행렬"""
    mat = np.zeros((4,4))
    mat[0,0] = 2/(right-left)
    mat[1,1] = 2/(top-bottom)
    mat[2,2] = -2/(far-near)
    mat[0,3] = -(right+left)/(right-left)
    mat[1,3] = -(top+bottom)/(top-bottom)
    mat[2,3] = -(far+near)/(far-near)
    mat[3,3] = 1
    return mat

# ------------------------------
# 5. 충돌 박스 (AABB, OBB)
# ------------------------------

def aabb_intersect(min1, max1, min2, max2):
    """AABB 충돌 체크"""
    for i in range(3):
        if max1[i] < min2[i] or min1[i] > max2[i]:
            return False
    return True

def point_in_aabb(p, min_corner, max_corner):
    p = np.array(p)
    return np.all(p >= min_corner) and np.all(p <= max_corner)

# OBB 충돌은 회전 행렬 포함해야 하므로 조금 복잡
def point_in_obb(p, center, axes, half_sizes):
    """
    p: 점
    center: OBB 중심
    axes: 3x3 직교 행렬 (local x,y,z axes)
    half_sizes: 각 축 절반 길이
    """
    d = p - center
    for i in range(3):
        if abs(np.dot(d, axes[:,i])) > half_sizes[i]:
            return False
    return True
