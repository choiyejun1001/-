import streamlit as st
import numpy as np

# -------------------------------------------------------------------
# 1. 페이지 헤더 & 비주얼 타이틀
# -------------------------------------------------------------------
st.set_page_config(page_title="스마트 드론 배송 시뮬레이터", page_icon="🍔", layout="wide")

st.title("🚁 스마트 도심 드론 배송 & 실생활 안전 관제기")
st.markdown("##### 🍕 **바람 계산부터 '음식이 녹는지'와 '추락 충격량'까지 한눈에 확인하는 시각화 시뮬레이터**")
st.divider()

# -------------------------------------------------------------------
# 2. 사이드바 입력 인터페이스
# -------------------------------------------------------------------
st.sidebar.header("⚙️ 배송 & 기상 설정")

# [입력 1] 배달 음식 선택
food_type = st.sidebar.selectbox(
    "📦 배달할 음식 선택", 
    ["🍕 따뜻한 피자/치킨", "🍦 시원한 아이스크림", "☕ 따뜻한 아메리카노"]
)

# [입력 2] 위치 및 기상 정보
st.sidebar.subheader("📍 위치 및 날씨 설정")
start_x = st.sidebar.number_input("출발지 X (km)", value=0.0, step=0.5)
start_y = st.sidebar.number_input("출발지 Y (km)", value=0.0, step=0.5)
target_x = st.sidebar.number_input("목적지 X (km)", value=3.0, step=0.5)
target_y = st.sidebar.number_input("목적지 Y (km)", value=4.0, step=0.5)

wind_speed = st.sidebar.slider("현재 풍속 (m/s)", 0.0, 15.0, 4.0, 0.5)
outside_temp = st.sidebar.slider("현재 야외 기온 (°C)", -10, 35, 22)

# 드론 기본 스펙
max_speed = 12.0  # m/s
max_wind_limit = 12.0

# -------------------------------------------------------------------
# 3. 알고리즘 및 예외 처리
# -------------------------------------------------------------------
distance_km = np.sqrt((target_x - start_x)**2 + (target_y - start_y)**2)
distance_m = distance_km * 1000.0

if distance_km == 0:
    st.error("⚠️ **[입력 오류]** 출발지와 목적지의 좌표가 동일합니다!")

elif wind_speed > max_wind_limit:
    st.error(f"🚨 **[비행 금지]** 현재 풍속({wind_speed}m/s)이 드론 한계 풍속을 초과하여 추락 위험이 높습니다!")

else:
    # 실질 비행 속도 및 시간 산출
    ground_speed = max(1.0, max_speed - wind_speed * 0.7)
    flight_time_min = (distance_m / ground_speed) / 60.0
    
    # 배터리 소모 & 추가 비용 환산
    battery_used = flight_time_min * 8.0 * (1 + wind_speed * 0.1)
    remaining_battery = max(0.0, 100.0 - battery_used)
    extra_cost = int(battery_used * 15)  # 추가 전력비 원화 환산

    # -------------------------------------------------------------------
    # 4. 실시간 대시보드 (메트릭 카드 시각화)
    # -------------------------------------------------------------------
    st.subheader("📊 1. 비행 상태 및 연비 대시보드")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("총 비행 거리", f"{distance_km:.2f} km")
    col2.metric("예상 비행시간", f"{flight_time_min:.1f} 분")
    col3.metric("예상 잔여 배터리", f"{remaining_battery:.1f} %")
    col4.metric("바람에 의한 추가 손실비", f"약 {extra_cost} 원")

    st.divider()

    # -------------------------------------------------------------------
    # 5. [시각화 1] 배달 음식 상태 게이지 및 카드
    # -------------------------------------------------------------------
    st.subheader("🍱 2. 배달 음식 실시간 상태 예측")
    
    food_col1, food_col2 = st.columns([1, 2])
    
    with food_col1:
        # 음식별 신선도 판정 알고리즘
        if "아이스크림" in food_type:
            if flight_time_min > 6.0 or outside_temp > 25:
                st.error("🫠 **[상태: 완전 융해]**\n아이스크림이 녹아 미음(국물) 상태가 됩니다.")
                freshness = 20
            else:
                st.success("🍦 **[상태: 최상]**\n꽁꽁 언 상태로 안전하게 도착합니다!")
                freshness = 95
        elif "피자" in food_type or "치킨" in food_type:
            if flight_time_min > 8.0:
                st.warning("🍕 **[상태: 식음]**\n도착 시 치즈가 굳어 따뜻함이 감소합니다.")
                freshness = 50
            else:
                st.success("🔥 **[상태: 갓 구움]**\n김이 모락모락 나는 따뜻한 상태 유지!")
                freshness = 98
        else: # 커피
            if flight_time_min > 10.0:
                st.warning("☕ **[상태: 미지근함]**\n커피 온도가 낮아집니다.")
                freshness = 60
            else:
                st.success("☕ **[상태: 따끈따끈]**\n완벽한 온도로 배달됩니다.")
                freshness = 90

    with food_col2:
        st.write("**음식 신선도 게이지**")
        st.progress(freshness)
        st.caption(f"현재 야외 기온 ({outside_temp}°C) 및 비행시간 ({flight_time_min:.1f}분) 종합 반영 수치")

    st.divider()

    # -------------------------------------------------------------------
    # 6. [시각화 2] 추락 위험도 & 체감 충격량 비유 시각화
    # -------------------------------------------------------------------
    st.subheader("💥 3. 추락 시 충격량 (운동에너지 $E=\\frac{1}{2}mv^2$) 체감 비유")
    
    drone_weight = 3.0 # kg
    kinetic_energy = 0.5 * drone_weight * (ground_speed ** 2)
    drop_height = max(1, int(kinetic_energy / 30)) # 볼링공 낙하 높이 환산

    impact_col1, impact_col2 = st.columns(2)
    
    with impact_col1:
        st.info(f"💡 현재 속도로 추락 시 충격 에너지: **{kinetic_energy:.0f} Joule**")
        st.write(f"👉 **볼링공(3kg)을 아파트 {drop_height}층 높이에서 떨어뜨린 것과 동일한 파괴력!**")

    with impact_col2:
        # 위험도 바 시각화
        danger_level = min(100, int((kinetic_energy / 300) * 100))
        st.write("**위험 파괴력 지수**")
        st.progress(danger_level)
        if danger_level > 60:
            st.caption("🚨 **[위험]** 안전 매트 설치 지역 우회 비행 권장")
        else:
            st.caption("✅ **[안전]** 충격량 영향권 보행자 통제 가능 수준")

    st.divider()

    # -------------------------------------------------------------------
    # 7. [시각화 3] 비행 경로 인터랙티브 라인 차트
    # -------------------------------------------------------------------
    st.subheader("🗺️ 4. 실시간 비행 경로 좌표 차트")
    
    steps = 10
    x_steps = np.linspace(start_x, target_x, steps)
    y_steps = np.linspace(start_y, target_y, steps)
    
    path_data = {"X 좌표 (km)": x_steps, "Y 좌표 (km)": y_steps}
    st.line_chart(path_data, x="X 좌표 (km)", y="Y 좌표 (km)")
