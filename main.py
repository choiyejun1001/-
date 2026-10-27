import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# -------------------------------------------------------------------
# 1. 페이지 기본 설정 및 기본 정보 표시 (요소 ①: 문제 정의)
# -------------------------------------------------------------------
st.set_page_config(
    page_title="도심 드론 배송 안전 진단기",
    page_icon="🚁",
    layout="wide"
)

st.title("🚁 도심 드론 배송 풍속·풍향 대응 안전 진단 시뮬레이터")
st.markdown("""
본 프로그램은 **기계공학의 유체역학 및 동역학 개념(상대 풍속 벡터, 항력 모델)**을 활용하여 
바람 조건에 따른 드론의 **비행 가능 여부**와 **예상 배터리 소모량**을 실시간으로 진단하고 시각화합니다.
""")
st.divider()

# -------------------------------------------------------------------
# 2. 사용자 입력 인터페이스 (사이드바)
# -------------------------------------------------------------------
st.sidebar.header("⚙️ 배송 및 기상 조건 설정")

# [입력 1] 드론 스펙 설정
st.sidebar.subheader("1. 드론 스펙 입력")
battery_capacity = st.sidebar.number_input("배터리 용량 (mAh)", min_value=1000, max_value=20000, value=5000, step=500)
max_speed = st.sidebar.slider("드론 최대 비행 속도 (m/s)", min_value=5.0, max_value=25.0, value=10.0, step=0.5)
max_wind_limit = 12.0  # 드론이 견딜 수 있는 한계 풍속 (m/s)

# [입력 2] 2D 좌표 위치 설정
st.sidebar.subheader("2. 배송 좌표 설정 (km)")
start_x = st.sidebar.number_input("출발지 X 좌표", value=0.0, step=0.5)
start_y = st.sidebar.number_input("출발지 Y 좌표", value=0.0, step=0.5)
target_x = st.sidebar.number_input("목적지 X 좌표", value=3.0, step=0.5)
target_y = st.sidebar.number_input("목적지 Y 좌표", value=4.0, step=0.5)

# [입력 3] 기상 정보 설정
st.sidebar.subheader("3. 기상 조건 입력")
wind_speed = st.sidebar.slider("풍속 (m/s)", min_value=0.0, max_value=20.0, value=5.0, step=0.5)
wind_dir_deg = st.sidebar.slider("풍향 (바람이 불어오는 각도 °)", min_value=0, max_value=360, value=45, step=5)

# -------------------------------------------------------------------
# 3. 알고리즘 및 연산 & 예외 처리 (요소 ⑤, ⑥: 알고리즘 및 예외처리)
# -------------------------------------------------------------------

# 1) 비행 거리 산출 (피타고라스 정리)
distance_km = np.sqrt((target_x - start_x)**2 + (target_y - start_y)**2)
distance_m = distance_km * 1000.0

# [예외 처리 1] 출발지와 목적지가 동일한 경우 (ZeroDivisionError 방지)
if distance_km == 0:
    st.error("⚠️ **[입력 오류]** 출발지와 목적지의 좌표가 동일합니다. 서로 다른 좌표를 입력해 주세요.")

# [예외 처리 2] 드론의 한계 풍속을 초과하는 강풍 발생 시
elif wind_speed > max_wind_limit:
    st.error(f"🚨 **[비행 금지 - 강풍 경보]** 현재 풍속({wind_speed} m/s)이 드론의 안전 한계 풍속({max_wind_limit} m/s)을 초과하여 비행이 불가능합니다!")

else:
    # 2) 삼각함수 기반 상대 풍속 및 실질 비행 속도 산출
    dx = target_x - start_x
    dy = target_y - start_y
    flight_angle = np.arctan2(dy, dx)          # 드론 비행 각도 (라디안)
    wind_angle = np.radians(wind_dir_deg)        # 風向 각도 (라디안)

    # 비행 방향과 바람 방향 사이의 각도 차이를 이용한 맞바람/뒷바람 성분 계산
    angle_diff = wind_angle - flight_angle
    effective_wind = wind_speed * np.cos(angle_diff) 
    
    # 실질 비행 속도 (드론 속도 - 맞바람 성분)
    ground_speed = max_speed - effective_wind

    # [예외 처리 3] 강한 맞바람으로 전진하지 못하는 경우 (무한 루프/다운 방지)
    if ground_speed <= 0:
        st.error("🚨 **[비행 불가 - 전진 불가능]** 역풍(맞바람)이 너무 강해 드론이 전진할 수 없습니다!")

    else:
        # 3) 비행 시간 및 공기저항 반영 배터리 소모 계산
        flight_time_sec = distance_m / ground_speed
        flight_time_min = flight_time_sec / 60.0
        
        # 공기저항(항력) 수식 반영: 풍속이 셀수록 배터리 소모율 가중
        base_drain_rate = 12.0  # 기본 분당 배터리 소모율 (%)
        wind_factor = 1.0 + 0.04 * (wind_speed ** 1.5)
        total_battery_used = flight_time_min * base_drain_rate * wind_factor
        remaining_battery = max(0.0, 100.0 - total_battery_used)

        # -------------------------------------------------------------------
        # 4. 안전 진단 결과 출력 패널 (요소 ③: 정확한 기능 구현)
        # -------------------------------------------------------------------
        st.subheader("📊 안전 진단 및 배송 예측 결과")
        
        # 3열 메트릭 카드 배치
        col1, col2, col3 = st.columns(3)
        col1.metric("총 비행 거리", f"{distance_km:.2f} km")
        col2.metric("예상 비행 시간", f"{flight_time_min:.1f} 분")
        col3.metric("예상 잔여 배터리", f"{remaining_battery:.1f} %")

        # [예외 처리 4] 배터리 방전 위험 진단
        if remaining_battery < 20.0:
            st.warning("⚠️ **[주의 - 추락 위험]** 목적지 도착 후 잔여 배터리가 20% 미만입니다. 비행 중 추락 위험이 있으니 경로를 재설정하세요.")
        else:
            st.success("✅ **[비행 승인]** 기상 조건 및 배터리 잔류량이 안전 기준을 충족합니다.")

        st.divider()

        # -------------------------------------------------------------------
        # 5. 경로 및 기상 벡터 2D 시각화 (Matplotlib)
        # -------------------------------------------------------------------
        st.subheader("🗺️ 비행 경로 및 풍향 벡터 시각화")

        fig, ax = plt.subplots(figsize=(8, 5))
        
        # 출발지-목적지 경로선 및 점 표시
        ax.plot([start_x, target_x], [start_y, target_y], 'b--o', linewidth=2, label="Flight Path")
        ax.plot(start_x, start_y, 'go', markersize=10, label="Start Point")
        ax.plot(target_x, target_y, 'ro', markersize=10, label="Target Point")

        # 경로 중앙에 바람 방향 화살표(Vector) 표시
        mid_x = (start_x + target_x) / 2.0
        mid_y = (start_y + target_y) / 2.0
        wind_arrow_dx = -np.cos(wind_angle) * 0.8
        wind_arrow_dy = -np.sin(wind_angle) * 0.8
        
        ax.quiver(mid_x, mid_y, wind_arrow_dx, wind_arrow_dy, color='darkorange', scale=4, label="Wind Vector")

        # 그래프 축 및 그리드 설정
        ax.set_title("2D Drone Flight Path & Wind Vector", fontsize=12)
        ax.set_xlabel("X Axis (km)")
        ax.set_ylabel("Y Axis (km)")
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend(loc="upper left")

        # Streamlit 화면에 그래프 띄우기
        st.pyplot(fig)
