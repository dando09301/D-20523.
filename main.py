import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="영화 관객 수 분석 앱", layout="wide")


# [1. 데이터 불러오기]
# @st.cache_data를 사용해 캐싱을 적용하면 데이터를 매번 다시 다운로드하지 않고 재사용합니다.
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    df = pd.read_csv(url)

    # [2. 날짜 전처리]
    # 결측치가 포함된 행 삭제
    df = df.dropna()

    # "기준일자" 컬럼을 datetime 형식으로 변환
    df["기준일자"] = pd.to_datetime(df["기준일자"])

    # 기준일자 오름차순 정렬
    df = df.sort_values("기준일자")

    return df


# 데이터 로드
df = load_data()

# 메인 타이틀
st.title("🎬 박스오피스 데이터 분석 웹앱")

# [3. 영화 선택 기능]
# 누적관객수 기준으로 영화명 정렬하기 위해 최고 누적관객수 추출
movie_order = (
    df.groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .index.tolist()
)

# 사이드바에 영화 선택 드롭다운 생성
selected_movie = st.sidebar.selectbox("영화를 선택하세요", options=movie_order)

# 선택한 영화 데이터 필터링
filtered_df = df[df["영화명"] == selected_movie]

# [5. 구역 나누기]
# 첫 번째 분석 구역 (레이아웃 구분을 위해 영역 설정)
st.header("1. 영화별 관객 수 추이")

# [4. 선그래프 그리기]
# 선택된 영화의 기준일자별 해당일관객수 변화 Plotly 그래프 생성
fig1 = px.line(
    filtered_df,
    x="기준일자",
    y="해당일관객수",
    title=f"[{selected_movie}] 일별 관객 수 변화",
    markers=True,
)

# 그래프 화면 표시
st.plotly_chart(fig1, use_container_width=True)

# [5. 인사이트 텍스트 영역]
st.info("💡 **이 그래프로 알 수 있는 것:** ")

# 구분선 추가 (향후 추가될 그래프 구역과 분리)
st.divider()

# 향후 추가될 그래프를 위한 예시 구역 미리 확보
st.header("2. 추가 분석 구역 (예정)")
st.write("이곳에 다음 그래프가 들어갈 자리입니다.")
