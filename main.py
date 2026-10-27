import streamlit as st
import numpy as np
import pydeck as pdk
import re

# -------------------------------------------------------------------
# 1. 페이지 헤더 & 기본 설정
# -------------------------------------------------------------------
st.set_page_config(
    page_title="AI UAM 3D 도심 드론 관제 시스템",
    page_icon="🚁",
    layout="wide"
)

st.title("🚁 AI 기반 UAM 3D 도심 드론 관제 & 실생활 안전 시뮬레이터")
st.markdown("##### 🍕 **자연어 텍스트 명령어 자동 조종 + 3D 도심 빌딩 숲 실시간 관제**")
st.divider()

# -------------------------------------------------------------------
# 2. AI 드론 조종사 자연어 명령어 입력창
# -------------------------------------------------------------------
st.subheader("🤖 1. AI 드론 조종사 자연어 음성/텍스트 제어기")
st.caption("예시 입력: '피자 4km 배달해줘 맞바람 6m 불어' / '아이스크림 2km 배달 야외 기온 30도'")

user_command = st.text_input("💬 AI 명령어를 입력하세요 (입력 후 Enter):", placeholder="예: 피자 3km 배달해줘 풍속 5m 야외기온 25도")

parsed_food = "🍕 따뜻한 피자/치킨"
parsed_dist = 3.0
parsed_wind = 4.0
parsed_temp = 22

if user_command:
    if "아이스크림" in user_command:
        parsed_food = "🍦 시원한 아이스크림"
    elif "커피" in user_command or "아메리카노" in user_command:
        parsed_food = "☕ 따뜻한 아메리카노"
    elif "피자" in user_command or "치킨" in user_command:
        parsed_food = "🍕 따뜻한 피자/치킨"

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
# 3. 사이드바 세팅
# -------------------------------------------------------------------
st.sidebar.header("⚙️ 관제 수동 세팅")

food_list = ["🍕 따뜻한 피자/치킨", "🍦 시원한 아이스크림", "☕ 따뜻한 아메리카노"]
food_index = food_list.index(parsed_food) if parsed_food in food_list else 0
food_type = st.sidebar.selectbox("📦 배달 음식", food_list, index=food_index)

st.sidebar.subheader("📍 비행 경로 설정")
start_lat, start_lon = 37.5665, 126.9780 # 서울시청 기준 좌표
target_dist = float(parsed_dist)

flight_alt = st.sidebar.slider("드론 비행 고도 (m)", 20, 150, 80, 5)

st.sidebar.subheader("🌬️ 기상 조건")
wind_speed = st.sidebar.slider("현재 풍속 (m/s)", 0.0, 15.0, float(parsed_wind), 0.5)
wind_dir_deg = st.sidebar.slider("풍향 (°)", 0, 360, 45, 5)
outside_temp = st.sidebar.slider("현재 기온 (°C)", -10, 35, int(parsed_temp))

max_speed = 12.0
max_wind_limit = 12.0

# -------------------------------------------------------------------
# 4. 연산 및 메트릭
# -------------------------------------------------------------------
distance_km = target_dist
distance_m = distance_km * 1000.0

ground_speed = max(1.0, max_speed - wind_speed * 0.6)
flight_time_min = (distance_m / ground_speed) / 60.0
battery_used = flight_time_min * 8.0 * (1 + wind_speed * 0.1)
remaining_battery = max(0.0, 100.0 - battery_used)
extra_cost = int(battery_used * 15)

st.subheader("📊 2. 비행 대시보드 & 실생활 예측")
c1, c2, c3, c4 = st.columns(4)
c1.metric("총 비행 거리", f"{distance_km:.2f} km")
c2.metric("예상 비행시간", f"{flight_time_min:.1f} 분")
c3.metric("예상 잔여 배터리", f"{remaining_battery:.1f} %")
c4.metric("바람 손실 비용", f"약 {extra_cost} 원")

st.divider()

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
# 5. 🔥 Streamlit 전용 3D 도심 지도 렌더링 (100% 작동 보장)
# -------------------------------------------------------------------
st.subheader("🏢 3. 3D 도심 빌딩 숲 & 입체 비행 궤도 시각화")
st.caption("💡 마우스 우클릭 드래그로 3차원 화면 각도를 조절하고, 휠로 확대/축소하세요!")

# 도심 3D 건물 데이터
building_data = [
    {"name": "빌딩 A", "coordinates": [126.9770, 37.5660], "height": 60, "color": [120, 140, 160]},
    {"name": "빌딩 B", "coordinates": [126.9790, 37.5670], "height": 110, "color": [100, 120, 150]},
    {"name": "빌딩 C", "coordinates": [126.9760, 37.5680], "height": 85, "color": [140, 150, 170]},
    {"name": "빌딩 D", "coordinates": [126.9800, 37.5650], "height": 70, "color": [110, 130, 140]},
]

# 3D 드론 비행 궤적 데이터
target_lon = start_lon + (distance_km * 0.008)
target_lat = start_lat + (distance_km * 0.005)

path_coords = [
    [start_lon, start_lat, 0],
    [start_lon + 0.001, start_lat + 0.0005, flight_alt],
    [target_lon - 0.001, target_lat - 0.0005, flight_alt],
    [target_lon, target_lat, 0]
]

# PyDeck 3D Layer 설정
building_layer = pdk.Layer(
    "ColumnLayer",
    data=building_data,
    get_position="coordinates",
    get_elevation="height",
    radius=40,
    get_fill_color="color",
    elevation_scale=1,
    pickable=True,
    auto_highlight=True
)

path_layer = pdk.Layer(
    "PathLayer",
    data=[{"path": path_coords}],
    get_path="path",
    get_color=[255, 50, 50, 255], # 빨간색 3D 비행선
    width_scale=5,
    width_min_pixels=3,
)

view_state = pdk.ViewState(
    latitude=start_lat + 0.003,
    longitude=start_lon + 0.003,
    zoom=14.5,
    pitch=55, # 3D 기울기
    bearing=30 # 3D 회전각
)

# 3D 맵 출력
st.pydeck_chart(
    pdk.Deck(
        layers=[building_layer, path_layer],
        initial_view_state=view_state,
        tooltip={"text": "{name}\n높이: {height}m"}
    )
)
