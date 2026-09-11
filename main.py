import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 제목 표시
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="어제 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제 일별 박스오피스 순위")

# -----------------------------------------------------------------------------
# 2. 날짜 계산 (한국 시간 기준 '어제')
# -----------------------------------------------------------------------------
# 배포 서버의 시계 위치와 상관없이 한국 표준시(KST)를 기준으로 시간을 가져옵니다.
kst = pytz.timezone('Asia/Seoul')
now_kst = datetime.now(kst)

# 박스오피스 집계 특성상 '오늘' 데이터는 없으므로 하루 전(어제) 날짜를 구합니다.
yesterday = now_kst - timedelta(days=1)

# API 요구 형식에 맞게 YYYYMMDD (8자리 숫자) 문자열로 변환합니다.
target_dt = yesterday.strftime("%Y%m%d")

# 사용자에게 어떤 날짜 기준인지 보여줍니다. (YYYY-MM-DD 형식)
st.caption(f" 기준 날짜: {yesterday.strftime('%Y-%m-%d')} (한국 시간 기준)")

# -----------------------------------------------------------------------------
# 3. KOBIS API 데이터 불러오기 함수 (캐시 적용)
# -----------------------------------------------------------------------------
# @st.cache_data를 사용하면 한 번 불러온 데이터를 1시간(3600초) 동안 기억해 둡니다.
# 덕분에 같은 날짜로 API를 중복해서 요청하지 않고 빠르게 보여줍니다.
@st.cache_data(ttl=3600)
def fetch_box_office_data(api_key, date_str):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": api_key,
        "targetDt": date_str
    }
    
    try:
        # API 서버에 데이터를 요청합니다. (타임아웃 10초 설정)
        response = requests.get(url, params=params, timeout=10)
        
        # HTTP 통신 에러가 없는지 확인합니다.
        if response.status_code != 200:
            return None, f"서버 통신 실패 (상태 코드: {response.status_code})"
            
        data = response.json()
        
        # API 응답 안에 'faultInfo'(인증 키 오류 등)가 있는지 체크합니다.
        if "faultInfo" in data:
            error_message = data["faultInfo"].get("message", "알 수 없는 API 에러")
            return None, f"API 오류 발생: {error_message}"
            
        # 영화 데이터 목록 추출
        box_office_list = data.get("boxOfficeResult", {}).get("dailyBoxOfficeList", [])
        
        # 영화 목록이 비어있는 경우
        if not box_office_list:
            return None, "해당 날짜의 박스오피스 데이터가 비어 있습니다."
            
        return box_office_list, None

    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 중 에러가 발생했습니다: {e}"

# -----------------------------------------------------------------------------
# 4. Secrets에서 API 키 가져오기 및 데이터 조회 실행
# -----------------------------------------------------------------------------
# Streamlit Cloud의 Secrets(비밀 금고)에서 KOBIS_KEY 값을 읽어옵니다.
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

# Secrets에서 키를 변수에 담습니다.
api_key = st.secrets["KOBIS_KEY"]

# 데이터를 가져옵니다.
data_list, error_msg = fetch_box_office_data(api_key, target_dt)

# -----------------------------------------------------------------------------
# 5. 에러 처리 및 결과 출력
# -----------------------------------------------------------------------------
if error_msg:
    # 에러 발생 시 사용자에게 친절히 안내
    st.error(f"🚨 데이터를 가져오지 못했습니다: {error_msg}")
    st.warning("""
    🛠️ **다음 사항을 확인해 보세요:**
    - Streamlit Secrets에 저장된 **KOBIS_KEY**가 정확한지 확인해 주세요.
    - 영화진흥위원회(KOBIS) API 서비스의 일시적 장애일 수 있습니다.
    - 인터넷 연결 상태를 확인해 주세요.
    """)
else:
    # -------------------------------------------------------------------------
    # 6. 데이터 전처리 (문자열 -> 숫자 변환)
    # -------------------------------------------------------------------------
    df = pd.DataFrame(data_list)
    
    # KOBIS API는 숫자 값이 문자열로 오므로 계산/정렬을 위해 숫자 형식으로 바꿉니다.
    numeric_columns = ['rank', 'audiCnt', 'audiAcc', 'scrnCnt']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 순위 기준(1위~10위)으로 정렬합니다.
    df = df.sort_values(by='rank', ascending=True)

    # -------------------------------------------------------------------------
    # 7. 1위 영화 지표 카드 (Metrics)
    # -------------------------------------------------------------------------
    top_movie = df.iloc[0]
    
    st.subheader(f"🥇 어제 1위: {top_movie['movieNm']}")
    
    # 3개의 기둥(컬럼)을 나누어 큰 지표 카드로 표시합니다.
    col1, col2, col3 = st.columns(3)
    col1.metric("어제 관객수", f"{int(top_movie['audiCnt']):,} 명")
    col2.metric("누적 관객수", f"{int(top_movie['audiAcc']):,} 명")
    col3.metric("스크린수", f"{int(top_movie['scrnCnt']):,} 개")

    st.divider()

    # -------------------------------------------------------------------------
    # 8. 관객수 상위 5편 막대그래프
    # -------------------------------------------------------------------------
    st.subheader("📊 관객수 상위 5개 영화")
    
    # 상위 5개 데이터를 추출합니다.
    top_5_df = df.head(5)
    
    # 막대그래프 생성을 위해 차트에 필요한 컬럼만 추출하여 정돈합니다.
    chart_data = top_5_df[['movieNm', 'audiCnt']].set_index('movieNm')
    chart_data.columns = ['어제 관객수']
    
    st.bar_chart(chart_data)

    st.divider()

    # -------------------------------------------------------------------------
    # 9. 전체 순위 표 (Table)
    # -------------------------------------------------------------------------
    st.subheader("📋 전체 박스오피스 순위")
    
    # 화면에 보여줄 컬럼만 선택하고 이름을 보기 좋게 바꿉니다.
    display_df = df[['rank', 'movieNm', 'openDt', 'audiCnt', 'audiAcc', 'scrnCnt']].copy()
    display_df.columns = ['순위', '영화명', '개봉일', '어제 관객수', '누적 관객수', '스크린수']
    
    # 숫자에 1,000 단위 쉼표(,)를 넣어 가독성을 높입니다.
    formatted_df = display_df.copy()
    formatted_df['어제 관객수'] = formatted_df['어제 관객수'].apply(lambda x: f"{int(x):,}명")
    formatted_df['누적 관객수'] = formatted_df['누적 관객수'].apply(lambda x: f"{int(x):,}명")
    formatted_df['스크린수'] = formatted_df['스크린수'].apply(lambda x: f"{int(x):,}개")
    
    # 인덱스 번호 없이 깨끗한 표로 출력합니다.
    st.dataframe(formatted_df, use_container_width=True, hide_index=True)
