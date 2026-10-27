import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import re

# -------------------------------------------------------------------
# 1. 페이지 헤더 & 기본 설정
# -------------------------------------------------------------------
st.set_page_config(
    page_title="AI 기반 UAM 3D 도심 드론 관제 시스템",
    page_icon="🚁",
    layout="wide"
)

st.title("🚁 AI 기반 UAM 3D 도심 드론 관제 & 실생활 안전 시뮬레이터")
st.markdown("##### 🍕 **자연어 텍스트 명령어 자동 조종 + 3D 도심 빌딩 숲 관제 시각화**")
st.divider()

# -------------------------------------------------------------------
# 2. [신규 초특급 기능 1] AI 드론 조종사 자연어 명령어 입력창
# -------------------------------------------------------------------
st.subheader("🤖 1. AI 드론 조종사 자연어 음성/텍스트 제어기")
st.caption("예시 입력: '피자 4km 배달해줘 맞바람 6m 불어' / '아이스크림 2km 배달 야외 기온 30도'")

user_command = st.text_input("💬 AI 명령어를 입력하세요 (입력 후 Enter):", placeholder="예: 피자 3km 배달해줘 풍속 5m 야외기온 25도")

# 자연어 명령 해석 (기본값 설정)
parsed_food = "🍕 따뜻한 피자/치킨"
parsed_dist = 3.0
parsed_wind = 4.0
parsed_temp = 22

if user_command:
    # 1) 음식 파싱
    if "아이스크림" in user_command:
        parsed_food = "🍦 시원한 아이스크림"
    elif "커피" in user_command or "아메리카노" in user_command:
        parsed_food = "☕ 따뜻한 아메리카노"
    elif "피자" in user_command or "치킨" in user_command:
        parsed_food = "🍕 따뜻한 피자/치킨"

    # 2) 숫자 추출 (거리, 풍속, 기온)
    dist_match = re.search(r'(\d+(\.\d+)?)\s*km', user_command)
    if dist_match:
        parsed_dist = float(dist_match.group(1))

    wind_match = re.search(r'(\d+(\.\d+)?)\s*m', user_command)
    if wind_match:
        parsed_wind = float(wind_match.group(1))

    temp_match = re.search(r'(\d+)\s*도', user_command)
    if temp_match:
        parsed_temp = int(temp_match.group(1))

    st.success(f"🤖 **[AI 명령어 해석 완료]** 음식: **{parsed_food}** | 거리: **{parsed_dist}km** | 풍속: **{parsed_wind}m/s** | 기온: **{parsed_temp}°C**")

st.divider()

# -------------------------------------------------------------------
# 3. 사이드바 수동 세팅 (AI 연동)
# -------------------------------------------------------------------
st.sidebar.header("⚙️ 관제 수동 세팅")

food_list = ["🍕 따뜻한 피자/치킨", "🍦 시원한 아이스크림", "☕ 따뜻한 아메리카노"]
food_index = food_list.index(parsed_food) if parsed_food in food_list else 0
food_type = st.sidebar.selectbox("📦 배달 음식", food_list, index=food_index)

st.sidebar.subheader("📍 3D 비행 경로 설정")
start_x = 0.5
start_y = 0.5
target_x = st.sidebar.number_input("목적지 X (km)", value=float(min(5.0, start_x + parsed_dist)), step=0.5)
target_y = st.sidebar.number_input("목적지 Y (km)", value=float(min(5.0, start_y + parsed_dist)), step=0.5)
flight_alt = st.sidebar.slider("드론 비행 고도 (m)", 20, 100, 60, 5)

st.sidebar.subheader("🌬️ 기상 조건")
wind_speed = st.sidebar.slider("현재 풍속 (m/s)", 0.0, 15.0, float(parsed_wind), 0.5)
wind_dir_deg = st.sidebar.slider("풍향 (°)", 0, 360, 45, 5)
outside_temp = st.sidebar.slider("현재 기온 (°C)", -10, 35, int(parsed_temp))

max_speed = 12.0
max_wind_limit = 12.0

# -------------------------------------------------------------------
# 4. 공학 연산 및 예외 처리
# -------------------------------------------------------------------
distance_km = np.sqrt((target_x - start_x)**2 + (target_y - start_y)**2)
distance_m = distance_km * 1000.0

if distance_km == 0:
    st.error("⚠️ 출발지와 목적지 좌표가 동일합니다!")
elif wind_speed > max_wind_limit:
    st.error(f"🚨 **[강풍 경보]** 풍속({wind_speed}m/s)이 드론 안전 한계를 초과하여 추락 위험이 높습니다!")
else:
    # 삼각함수 물리 연산
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
    # 5. 실시간 상태 대시보드
    # -------------------------------------------------------------------
    st.subheader("📊 2. 실시간 비행 연비 대시보드")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 비행 거리", f"{distance_km:.2f} km")
    c2.metric("예상 비행시간", f"{flight_time_min:.1f} 분")
    c3.metric("예상 잔여 배터리", f"{remaining_battery:.1f} %")
    c4.metric("바람 손실 비용", f"약 {extra_cost} 원")

    st.divider()

    # -------------------------------------------------------------------
    # 6. 실생활 예측 (음식 신선도 & 추락 충격량)
    # -------------------------------------------------------------------
    st.subheader("🍱 3. 배달 상태 & 추락 파괴력 체감 예측")
    f_col1, f_col2 = st.columns(2)
    
    with f_col1:
        if "아이스크림" in food_type:
            if flight_time_min > 6.0 or outside_temp > 25:
                st.error("🫠 **[상태: 완전 융해]** 비행 지연으로 아이스크림이 녹아 국물이 됩니다.")
                freshness = 15
            else:
                st.success("🍦 **[상태: 최상]** 꽁꽁 언 상태로 안전하게 배달됩니다!")
                freshness = 95
        else:
            if flight_time_min > 8.0:
                st.warning("🍕 **[상태: 식음]** 도착 시 치즈가 식어 맛이 떨어질 수 있습니다.")
                freshness = 50
            else:
                st.success("🔥 **[상태: 갓 구움]** 따끈따끈한 상태로 유지됩니다!")
                freshness = 98
        st.progress(freshness)

    with f_col2:
        drone_weight = 3.0
        kinetic_energy = 0.5 * drone_weight * (ground_speed ** 2)
        drop_height = max(1, int(kinetic_energy / 30))
        st.info(f"💥 추락 충격 에너지: **{kinetic_energy:.0f} Joule**")
        st.write(f"👉 **볼링공(3kg)을 아파트 {drop_height}층 높이에서 떨어뜨린 파괴력!**")

    st.divider()

    # -------------------------------------------------------------------
    # 7. [신규 초특급 기능 2] 3D 도심 빌딩 숲 & 회전 비행 궤도 시각화
    # -------------------------------------------------------------------
    st.subheader("🏢 4. 3D 도심 빌딩 숲 & 입체 비행 궤도 시각화")
    st.caption("💡 Matplotlib 3D 뷰어: 그래프를 마우스로 자유롭게 클릭·드래그하면 360도 입체 관전이 가능합니다.")

    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot(111, projection='3d')

    # 3D 빌딩 생성 함수
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
        poly = Poly3DCollection(faces, facecolors=color, linewidths=0.5, edgecolors='black', alpha=0.5)
        ax.add_collection3d(poly)

    # 3D 도심 빌딩 숲 배치 (X, Y, dx, dy, 높이m)
    buildings = [
        (1.2, 1.0, 0.8, 0.8, 45),
        (2.5, 3.0, 1.0, 0.7, 75),
        (3.0, 1.2, 0.7, 1.2, 55),
        (1.0, 3.5, 0.9, 0.8, 40),
        (4.0, 2.5, 0.8, 0.8, 65)
    ]
    for b in buildings:
        draw_building(ax, *b, color='lightslategrey')

    # 3D 입체 경로 궤적 (이륙 -> 비행 -> 착륙)
    steps = 30
    x_path = np.linspace(start_x, target_x, steps)
    y_path = np.linspace(start_y, target_y, steps)
    z_path = np.full(steps, float(flight_alt))
    z_path[:5] = np.linspace(0, flight_alt, 5)   # 이륙
    z_path[-5:] = np.linspace(flight_alt, 0, 5)  # 착륙

    # 3D 선 및 점 그리기
    ax.plot(x_path, y_path, z_path, color='crimson', linewidth=3, label="3D Flight Path")
    ax.scatter(start_x, start_y, 0, color='green', s=100, label="Start (Takeoff)")
    ax.scatter(target_x, target_y, 0, color='red', s=100, label="Target (Landing)")

    # 바람 방향 3D 화살표 (Vector)
