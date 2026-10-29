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
# 2. AI 드론 조종사 자연어 명령어 입력창
# -------------------------------------------------------------------
st.subheader("🤖 1. AI 드론 조종사 자연어 음성/텍스트 제어기")
st.caption("예시 입력: '마라탕 4km 배달해줘 맞바람 6m 불어' / '배스킨라빈스 아이스크림 2km 배달 야외 기온 30도'")

user_command = st.text_input(
    "💬 AI 명령어를 자유롭게 입력하세요 (입력 후 Enter):", 
    placeholder="예: 갓 튀긴 탕수육 3.5km 배달해줘 풍속 5m 야외기온 25도"
)

# 기본 세팅값
parsed_food = "갓 구운 피자"
parsed_dist = 3.0
parsed_wind = 4.0
parsed_temp = 22

if user_command:
    # 1) 수치 파싱 (거리, 풍속, 기온)
    dist_match = re.search(r'(\d+(\.\d+)?)\s*km', user_command)
    if dist_match:
        parsed_dist = float(dist_match.group(1))

    wind_match = re.search(r'(\d+(\.\d+)?)\s*m', user_command)
    if wind_match:
        parsed_wind = float(wind_match.group(1))

    temp_match = re.search(r'(\d+)\s*도', user_command)
    if temp_match:
        parsed_temp = int(temp_match.group(1))

    # 2) 음식명 파싱 (불필요한 수치 및 명령어 단어 제거)
    temp_cmd = user_command
    # 수치 형태 제거 (3.5km, 5m, 25도 등)
    temp_cmd = re.sub(r'(\d+(\.\d+)?)\s*(km|m|m/s|도|°C)', '', temp_cmd)
    # 불필요한 동사/조사 제거
    stop_words = ["배달해줘", "배달", "해줘", "풍속", "맞바람", "야외", "기온", "현재", "바람", "불어"]
    for word in stop_words:
        temp_cmd = temp_cmd.replace(word, "")
    
    extracted_food = temp_cmd.strip()
    if extracted_food:
        parsed_food = extracted_food

    st.success(f"🤖 **[AI 명령어 해석 완료]** 음식: **'{parsed_food}'** | 거리: **{parsed_dist}km** | 풍속: **{parsed_wind}m/s** | 기온: **{parsed_temp}°C**")

st.divider()

# -------------------------------------------------------------------
# 3. 사이드바 세팅 (자유 커스텀 입력 지원)
# -------------------------------------------------------------------
st.sidebar.header("⚙️ 관제 수동 세팅")

# 💡 원하는 음식을 직접 타이핑할 수 있는 텍스트 박스
custom_food_input = st.sidebar.text_input("📦 배달할 음식 직접 수정/입력", value=parsed_food)
food_name = custom_food_input.strip() if custom_food_input.strip() else "배달 음식"

st.sidebar.subheader("📍 비행 경로 설정")
start_lat, start_lon = 37.5665, 126.9780 # 서울시청 기준
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

# -------------------------------------------------------------------
# 5. 동적 음식 상태 판정 알고리즘
# -------------------------------------------------------------------
f_col1, f_col2 = st.columns(2)
with f_col1:
    st.write(f"🍱 **[{food_name}] 실시간 상태 및 온습도 예측**")
    
    # 키워드 기반 차가운 음식 / 따뜻한 음식 자동 구분
    cold_keywords = ["아이스", "빙수", "스무디", "냉면", "회", "초밥", "아이스크림", "주스", "음료"]
    is_cold = any(kw in
