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
st.markdown("##### 🍕 **자유로운 배달 음식 입력 + 자연어 자동 조종 + 3D 도심 관제 시각화**")
st.divider()

# -------------------------------------------------------------------
# 💡 세션 상태(Session State) 초기화 (피자로 되돌아가는 현상 완벽 방지)
# -------------------------------------------------------------------
if "food_name" not in st.session_state:
    st.session_state.food_name = "마라탕"
if "parsed_dist" not in st.session_state:
    st.session_state.parsed_dist = 3.0
if "parsed_wind" not in st.session_state:
    st.session_state.parsed_wind = 4.0
if "parsed_temp" not in st.session_state:
    st.session_state.parsed_temp = 22

# -------------------------------------------------------------------
# 2. AI 드론 조종사 자연어 명령어 입력창
# -------------------------------------------------------------------
st.subheader("🤖 1. AI 드론 조종사 자연어 음성/텍스트 제어기")
st.caption("예시 입력: '마라탕 4km 배달해줘 맞바람 6m 불어' / '배스킨라빈스 아이스크림 2km 배달 야외 기온 30도'")

user_command = st.text_input(
    "💬 AI 명령어를 자유롭게 입력하세요 (입력 후 Enter):", 
    placeholder="예: 갓 튀긴 탕수육 3.5km 배달해줘 풍속 5m 야외기온 25도"
)

if user_command:
    # 1) 수치 파싱 (거리, 풍속, 기온)
    dist_match = re.search(r'(\d+(\.\d+)?)\s*km', user_command)
    if dist_match:
        st.session_state.parsed_dist = float(dist_match.group(1))

    wind_match = re.search(r'(\d+(\.\d+)?)\s*m', user_command)
    if wind_match:
        st.session_state.parsed_wind = float(wind_match.group(1))

    temp_match = re.search(r'(\d+)\s*도', user_command)
    if temp_match:
        st.session_state.parsed_temp = int(temp_match.group(1))

    # 2) 음식명 파싱 (불필요한 수치 및 명령어 단어 제거)
    temp_cmd = user_command
    temp_cmd = re.sub(r'(\d+(\.\d+)?)\s*(km|m|m/s|도|°C)', '', temp_cmd)
    stop_words = ["배달해줘", "배달", "해줘", "풍속", "맞바람", "야외", "기온", "현재", "바람", "불어"]
    for word in stop_words:
        temp_cmd = temp_cmd.replace(word, "")
    
    extracted_food = temp_cmd.strip()
    if extracted_food:
        st.session_state.food_name = extracted_food

    st.success(f"🤖 **[AI 명령어 해석 완료]** 음식: **'{st.session_state.food_name}'** | 거리: **{st.session_state.parsed_dist}km** | 풍속: **{st.session_state.parsed_wind}m/s** | 기온: **{st.session_state.parsed_temp}°C**")

st.divider()

# -------------------------------------------------------------------
# 3. 사이드바 세팅 (자유 커스텀 입력 지원)
# -------------------------------------------------------------------
st.sidebar.header("⚙️ 관제 수동 세팅")

# 💡 세션에 저장된 값을 가져와서 직접 수정도 가능하게 함
custom_food_input = st.sidebar.text_input("📦 배달할 음식 직접 수정/입력", value=st.session_state.food_name)
st.session_state.food_name = custom_food_input.strip() if custom_food_input.strip() else "배달 음식"

st.sidebar.subheader("📍 비행 경로 설정")
start_lat, start_lon = 37.5665, 126.9780 # 서울시청 기준
target_dist = float(st.session_state.parsed_dist)

flight_alt = st.sidebar.slider("드론 비행 고도 (m)", 20, 150, 80, 5)

st.sidebar.subheader("🌬️ 기상 조건")
wind_speed = st.sidebar.slider("현재 풍속 (m/s)", 0.0, 15.0, float(st.session_state.parsed_wind), 0.5)
wind_dir_deg = st.sidebar.slider("풍향 (°)", 0, 360, 45, 5)
outside_temp = st.sidebar.slider("현재 기온 (°C)", -10, 35, int(st.session_state.parsed_temp))

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

# -------------------------------------------------------------------
# 5. 동적 음식 상태 판정 알고리즘
# -------------------------------------------------------------------
food_name = st.session_state.food_name

f_col1, f_col2 = st.columns(2)
with f_col1:
    st.write(f"🍱 **[{food_name}] 실시간 상태 및 온습도 예측**")
    
    # 키워드 기반 차가운 음식 / 따뜻한 음식 자동 구분
    cold_keywords = ["아이스", "빙수", "스무디", "냉면", "회", "초밥", "아이스크림", "주스", "음료"]
    is_cold = any(kw in food_name for kw in cold_keywords)

    if is_cold:
        if flight_time_min > 6.0 or outside_temp > 25:
            st.error(f"🫠 **[상태: 변질/융해]** 비행 지연({flight_time_min:.1f}분) 및 기온({outside_temp}°C)으로 인해 **{food_name}**이(가) 녹거나 미지근해집니다!")
            freshness = 20
        else:
            st.success(f"❄️ **[상태: 최상]** 차가운 상태 그대로 **{food_name}** 배달 성공!")
            freshness = 95
    else:
        if flight_time_min > 8.0 or outside_temp < 5:
            st.warning(f"❄️ **[상태: 식음]** 비행 지연으로 인해 **{food_name}**의 온도가 식을 수 있습니다.")
            freshness = 50
        else:
            st.success(f"🔥 **[상태: 갓 만듦]** 따끈따끈하고 맛있는 상태로 **{food_name}** 배달 성공!")
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
# 6. Streamlit 3D 도심 지도 렌더링
# -------------------------------------------------------------------
st.subheader("🏢 3. 3D 도심 빌딩 숲 & 입체 비행 궤도 시각화")
st.caption("💡 마우스 우클릭 드래그로 3차원 화면 각도를 조절하고, 휠로 확대/축소하세요!")

building_data = [
    {"name": "빌딩 A", "coordinates": [126.9770, 37.5660], "height": 60, "color": [120, 140, 160]},
    {"name": "빌딩 B", "coordinates": [126.9790, 37.5670], "height": 110, "color": [100, 120, 150]},
    {"name": "빌딩 C", "coordinates": [126.9760, 37.5680], "height": 85, "color": [140, 150, 170]},
    {"name": "빌딩 D", "coordinates": [126.9800, 37.5650], "height": 70, "color": [110, 130, 140]},
]

target_lon = start_lon + (distance_km * 0.008)
target_lat = start_lat + (distance_km * 0.005)

path_coords = [
    [start_lon, start_lat, 0],
    [start_lon + 0.001, start_lat + 0.0005, flight_alt],
    [target_lon - 0.001, target_lat - 0.0005, flight_alt],
    [target_lon, target_lat, 0]
]

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
    get_color=[255, 50, 50, 255],
    width_scale=5,
    width_min_pixels=3,
)

view_state = pdk.ViewState(
    latitude=start_lat + 0.003,
    longitude=start_lon + 0.003,
    zoom=14.5,
    pitch=55,
    bearing=30
)

st.pydeck_chart(
    pdk.Deck(
        layers=[building_layer, path_layer],
        initial_view_state=view_state,
        tooltip={"text": "{name}\n높이: {height}m"}
    )
)
