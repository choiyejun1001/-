import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# -------------------------------------------------------------------
# 1. 페이지 헤더
# -------------------------------------------------------------------
st.set_page_config(
    page_title="스마트 UAM 3D 도심 드론 관제기",
    page_icon="🚁",
    layout="wide"
)

st.title("🚁 3D 도심 빌딩 숲 UAM 드론 배송 관제 시뮬레이터")
st.markdown("##### 🍕 **도심 고층 건물 장애물부터 바람 영향, 배달 음식 신선도까지 실시간 제어**")
st.divider()

# -------------------------------------------------------------------
# 2. 사이드바 입력
# -------------------------------------------------------------------
st.sidebar.header("⚙️ 배송 & 환경 설정")

food_type = st.sidebar.selectbox(
    "📦 배달할 음식 선택", 
    ["🍕 따뜻한 피자/치킨", "🍦 시원한 아이스크림", "☕ 따뜻한 아메리카노"]
)

st.sidebar.subheader("📍 3D 비행 경로 설정")
start_x = st.sidebar.number_input("출발 X (km)", value=0.5, step=0.5)
start_y = st.sidebar.number_input("출발 Y (km)", value=0.5, step=0.5)
target_x = st.sidebar.number_input("목적지 X (km)", value=4.5, step=0.5)
target_y = st.sidebar.number_input("목적지 Y (km)", value=4.5, step=0.5)
flight_alt = st.sidebar.slider("드론 비행 고도 (m)", 20, 100, 60, 5)

st.sidebar.subheader("🌬️ 기상 조건")
wind_speed = st.sidebar.slider("현재 풍속 (m/s)", 0.0, 15.0, 4.0, 0.5)
wind_dir_deg = st.sidebar.slider("풍향 (°)", 0, 360, 45, 5)
outside_temp = st.sidebar.slider("현재 기온 (°C)", -10, 35, 22)

max_speed = 12.0
max_wind_limit = 12.0

# -------------------------------------------------------------------
# 3. 알고리즘 연산
# -------------------------------------------------------------------
distance_km = np.sqrt((target_x - start_x)**2 + (target_y - start_y)**2)
distance_m = distance_km * 1000.0

if distance_km == 0:
    st.error("⚠️ 출발지와 목적지 좌표가 동일합니다!")
elif wind_speed > max_wind_limit:
    st.error(f"🚨 **[강풍 경보]** 풍속({wind_speed}m/s)이 드론 안전 기준을 초과했습니다!")
else:
    dx = target_x - start_x
    dy = target_y - start_y
    flight_angle = np.arctan2(dy, dx)
    wind_angle = np.radians(wind_dir_deg)

    angle_diff = wind_angle - flight_angle
    effective_wind = wind_speed * np.cos(angle_diff)
    ground_speed = max(1.0, max_speed - effective_wind)
    
    flight_time_min = (distance_m / ground_speed) / 60.0
    battery_used = flight_time_min * 8.0 * (1 + wind_speed * 0.1)
    remaining_battery = max(0.0, 100.0 - battery_used)
    extra_cost = int(battery_used * 15)

    # -------------------------------------------------------------------
    # 4. 실시간 상태 대시보드
    # -------------------------------------------------------------------
    st.subheader("📊 1. 비행 대시보드")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 비행 거리", f"{distance_km:.2f} km")
    c2.metric("예상 비행시간", f"{flight_time_min:.1f} 분")
    c3.metric("예상 잔여 배터리", f"{remaining_battery:.1f} %")
    c4.metric("바람 손실 비용", f"약 {extra_cost} 원")

    st.divider()

    # -------------------------------------------------------------------
    # 5. 재미있는 실생활 예측 (음식 & 충격량)
    # -------------------------------------------------------------------
    st.subheader("🍱 2. 배달 상태 & 추락 충격량 예측")
    f_col1, f_col2 = st.columns(2)
    
    with f_col1:
        if "아이스크림" in food_type:
            if flight_time_min > 6.0 or outside_temp > 25:
                st.error("🫠 **[상태: 완전 융해]** 아이스크림이 녹아 국물이 됩니다.")
            else:
                st.success("🍦 **[상태: 최상]** 꽁꽁 언 상태로 안전 배달!")
        else:
            if flight_time_min > 8.0:
                st.warning("🍕 **[상태: 식음]** 도착 시 치즈가 식을 수 있습니다.")
            else:
                st.success("🔥 **[상태: 갓 구움]** 따끈따끈한 상태 유지!")

    with f_col2:
        drone_weight = 3.0
        kinetic_energy = 0.5 * drone_weight * (ground_speed ** 2)
        drop_height = max(1, int(kinetic_energy / 30))
        st.info(f"💥 추락 파괴력: **{kinetic_energy:.0f} J** (볼링공 아파트 **{drop_height}층** 낙하 충격)")

    st.divider()

    # -------------------------------------------------------------------
    # 🔥 6. [초특급 신기한 기능] 3D 도심 빌딩 숲 비행 궤도 시각화
    # -------------------------------------------------------------------
    st.subheader("🏢 3. 3D 도심 빌딩 숲 & 입체 비행 궤도 시각화")
    st.caption("마우스로 3D 공간을 회전하거나 확대/축소하여 도심 건물을 피하는 드론 궤적을 확인하세요.")

    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot(111, projection='3d')

    # 가상의 3D 빌딩(장애물) 생성 함수
    def draw_building(ax, x, y, dx, dy, dz, color='gray'):
        xx = [x, x+dx, x+dx, x, x, x+dx, x+dx, x]
        yy = [y, y, y+dy, y+dy, y, y, y+dy, y+dy]
        zz = [0, 0, 0, 0, dz, dz, dz, dz]
        vertices = [
            [0,1,2,3], [4,5,6,7], 
            [0,1,5,4], [2,3,7,6], 
            [1,2,6,5], [4,7,3,0]
        ]
        faces = [[(xx[i], yy[i], zz[i]) for i in face] for face in vertices]
        poly = Poly3DCollection(faces, facecolors=color, linewidths=0.5, edgecolors='black', alpha=0.6)
        ax.add_collection3d(poly)

    # 도심 건물 배치 (X, Y, 폭, 깊이, 높이)
    buildings = [
        (1.5, 1.0, 0.8, 0.8, 45),
        (2.5, 3.0, 1.0, 0.7, 75),
        (3.0, 1.5, 0.7, 1.2, 55),
        (1.0, 3.5, 0.9, 0.8, 40),
    ]
    for b in buildings:
        draw_building(ax, *b, color='lightslategrey')

    # 3D 비행 궤적 (이륙 -> 목표 고도 비행 -> 착륙)
    steps = 30
    x_path = np.linspace(start_x, target_x, steps)
    y_path = np.linspace(start_y, target_y, steps)
    
    # 이륙 및 착륙 곡선 고도 생성
    z_path = np.full(steps, float(flight_alt))
    z_path[:5] = np.linspace(0, flight_alt, 5)   # 이륙 구간
    z_path[-5:] = np.linspace(flight_alt, 0, 5)  # 착륙 구간

    # 경로선 및 점 렌더링
    ax.plot(x_path, y_path, z_path, color='crimson', linewidth=3, label="Drone Flight Path")
    ax.scatter(start_x, start_y, 0, color='green', s=100, label="Start (Takeoff)")
    ax.scatter(target_x, target_y, 0, color='red', s=100, label="Target (Landing)")

    # 바람 방향 3D 화살표
    mid_idx = steps // 2
    wind_dx = -np.cos(wind_angle) * 0.8
    wind_dy = -np.sin(wind_angle) * 0.8
    ax.quiver(x_path[mid_idx], y_path[mid_idx], z_path[mid_idx], wind_dx, wind_dy, 0, color='darkorange', length=0.8, label="Wind Vector")

    # 축 레이블 및 스타일
    ax.set_xlabel("X (km)")
    ax.set_ylabel("Y (km)")
    ax.set_zlabel("Altitude Z (m)")
    ax.set_zlim(0, 100)
    ax.legend(loc="upper left")

    st.pyplot(fig)
