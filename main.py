import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 제목 표시
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="일별 박스오피스 조회",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 일별 박스오피스 순위")

# -----------------------------------------------------------------------------
# 2. 한국 시간 기준 '어제' 날짜 계산 (선택 가능한 최신 날짜)
# -----------------------------------------------------------------------------
kst = pytz.timezone('Asia/Seoul')
now_kst = datetime.now(kst)

# 오늘 데이터는 집계 전이므로 선택할 수 있는 가장 최신 날짜는 '어제'입니다.
yesterday_dt = (now_kst - timedelta(days=1)).date()

# -----------------------------------------------------------------------------
# 3. 사이드바 - 날짜 선택 달력 기능
# -----------------------------------------------------------------------------
st.sidebar.header("🗓️ 날짜 선택")

# date_input을 이용해 달력에서 날짜를 선택받습니다.
# max_value를 어제로 지정하여 오늘/미래 날짜 선택을 막습니다.
selected_date = st.sidebar.date_input(
    label="조회할 날짜를 골라주세요",
    value=yesterday_dt,      # 기본값: 어제
    max_value=yesterday_dt  # 최대 선택 가능한 날짜: 어제
)

# API 검색용 YYYYMMDD 문자열로 변환
target_dt = selected_date.strftime("%Y%m%d")

st.caption(f" 기준 날짜: {selected_date.strftime('%Y년 %m월 %d일')} (한국 시간 기준)")

# -----------------------------------------------------------------------------
# 4. KOBIS API 데이터 불러오기 함수 (캐시 적용)
# -----------------------------------------------------------------------------
# 선택한 날짜별로 결과를 기억하도록 date_str을 매개변수로 받아 1시간 동안 저장합니다.
@st.cache_data(ttl=3600)
def fetch_box_office_data(api_key, date_str):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": api_key,
        "targetDt": date_str
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return None, f"서버 통신 실패 (상태 코드: {response.status_code})"
            
        data = response.json()
        
        # API 오류 상자(faultInfo) 체크
        if "faultInfo" in data:
            error_message = data["faultInfo"].get("message", "알 수 없는 API 에러")
            return None, f"API 오류 발생: {error_message}"
            
        box_office_list = data.get("boxOfficeResult", {}).get("dailyBoxOfficeList", [])
        
        # 영화 목록이 비어있는 경우
        if not box_office_list:
            return None, "EMPTY_DATA"
            
        return box_office_list, None

    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 중 에러가 발생했습니다: {e}"

# -----------------------------------------------------------------------------
# 5. Secrets에서 API 키 가져오기 및 데이터 조회
# -----------------------------------------------------------------------------
if "KOBIS_KEY" not in st.secrets:
    st.error("🔑 API 인증키(KOBIS_KEY)가 설정되지 않았습니다.")
    st.info("""
    **확인 방법:**
    1. Streamlit Cloud 관리 화면의 App Settings > **Secrets**로 이동하세요.
    2. 아래 형식으로 KOBIS 인증키를 추가해 주세요:
    ```toml
    KOBIS_KEY = "발급받은_실제_API_키"
    ```
    """)
    st.stop()

api_key = st.secrets["KOBIS_KEY"]
data_list, error_msg = fetch_box_office_data(api_key, target_dt)

# -----------------------------------------------------------------------------
# 6. 에러 및 빈 데이터 처리
# -----------------------------------------------------------------------------
if error_msg == "EMPTY_DATA":
    # 고른 날짜에 영화 목록이 비어 있을 때 출력할 문구
    st.warning(f"ℹ️ {selected_date.strftime('%Y년 %m월 %d일')}은 아직 집계 전입니다.")
elif error_msg:
    st.error(f"🚨 데이터를 가져오지 못했습니다: {error_msg}")
    st.warning("""
    🛠️ **다음 사항을 확인해 보세요:**
    - Streamlit Secrets에 저장된 **KOBIS_KEY**가 정확한지 확인해 주세요.
    - 영화진흥위원회(KOBIS) API 서비스의 일시적 장애일 수 있습니다.
    """)
else:
    # -------------------------------------------------------------------------
    # 7. 데이터 전처리 (문자열 -> 숫자 변환)
    # -------------------------------------------------------------------------
    df = pd.DataFrame(data_list)
    
    # rankInten(순위 증감)을 포함하여 숫자로 형변환합니다.
    numeric_columns = ['rank', 'rankInten', 'audiCnt', 'audiAcc', 'scrnCnt']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 순위 기준 정렬
    df = df.sort_values(by='rank', ascending=True)

    # -------------------------------------------------------------------------
    # 8. 1위 영화 지표 카드 (Metrics)
    # -------------------------------------------------------------------------
    top_movie = df.iloc[0]
    
    # 1위 영화가 100만 관객 돌파시 트로피 표시
    top_trophy = " 🏆" if top_movie['audiAcc'] >= 1000000 else ""
    st.subheader(f"🥇 1위: {top_movie['movieNm']}{top_trophy}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("해당일 관객수", f"{int(top_movie['audiCnt']):,} 명")
    col2.metric("누적 관객수", f"{int(top_movie['audiAcc']):,} 명")
    col3.metric("스크린수", f"{int(top_movie['scrnCnt']):,} 개")

    st.divider()

    # -------------------------------------------------------------------------
    # 9. 관객수 상위 5편 막대그래프
    # -------------------------------------------------------------------------
    st.subheader("📊 관객수 상위 5개 영화")
    top_5_df = df.head(5)
    chart_data = top_5_df[['movieNm', 'audiCnt']].set_index('movieNm')
    chart_data.columns = ['관객수']
    st.bar_chart(chart_data)

    st.divider()

    # -------------------------------------------------------------------------
    # 10. 순위 증감 기호 및 트로피 적용 함수 정의
    # -------------------------------------------------------------------------
    # 순위 증감(rankInten)에 따라 화살표 가공
    def format_rank_inten(val):
        if val > 0:
            return f"🔺 +{int(val)}"  # 양수: 상승 (빨간 위 화살표)
        elif val < 0:
            return f"🔹 {int(val)}"    # 음수: 하강 (파란 아래 화살표)
        else:
            return "-"                # 변동 없음

    # 누적관객 100만 이상일 때 영화명에 트로피 🏆 추가
    def format_movie_title(row):
        title = row['movieNm']
        if row['audiAcc'] >= 1000000:
            return f"{title} 🏆"
        return title

    # 가공된 데이터 생성
    df['display_movieNm'] = df.apply(format_movie_title, axis=1)
    df['display_rankInten'] = df['rankInten'].apply(format_rank_inten)

    # -------------------------------------------------------------------------
    # 11. 전체 순위 표 (Table)
    # -------------------------------------------------------------------------
    st.subheader("📋 전체 박스오피스 순위")
    
    # 표에 표시할 컬럼 선택 및 이름 변경
    display_df = df[['rank', 'display_rankInten', 'display_movieNm', 'openDt', 'audiCnt', 'audiAcc', 'scrnCnt']].copy()
    display_df.columns = ['순위', '순위 증감', '영화명', '개봉일', '해당일 관객수', '누적 관객수', '스크린수']
    
    # 숫자 천 단위 쉼표 포맷팅
    formatted_df = display_df.copy()
    formatted_df['해당일 관객수'] = formatted_df['해당일 관객수'].apply(lambda x: f"{int(x):,}명")
    formatted_df['누적 관객수'] = formatted_df['누적 관객수'].apply(lambda x: f"{int(x):,}명")
    formatted_df['스크린수'] = formatted_df['스크린수'].apply(lambda x: f"{int(x):,}개")
    
    # 표 출력
    st.dataframe(formatted_df, use_container_width=True, hide_index=True)
