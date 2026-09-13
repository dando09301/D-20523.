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

# -------------------------------------------------------------------
# [첫 번째 구역: 일별 관객 수 선그래프]
# -------------------------------------------------------------------
st.header("1. 영화별 일별 관객 수 추이")

# 선택된 영화의 기준일자별 해당일관객수 변화 Plotly 선그래프 생성
fig1 = px.line(
    filtered_df,
    x="기준일자",
    y="해당일관객수",
    title=f"[{selected_movie}] 일별 관객 수 변화",
    markers=True,
)

# 그래프 화면 표시
st.plotly_chart(fig1, use_container_width=True)

# 인사이트 텍스트 영역
st.info(f"💡 **이 그래프로 알 수 있는 것:** {selected_movie}의 특정 일자별 관객 수 증감 폭과 개봉 초기/주말 등의 일별 흥행 추이를 파악할 수 있습니다.")

# 구분선 추가
st.divider()

# -------------------------------------------------------------------
# [두 번째 구역: 누적 관객 수 영역차트]
# -------------------------------------------------------------------
st.header("2. 영화별 누적 관객 수 추이")

# 선택된 영화의 기준일자별 누적관객수 변화 Plotly 영역차트(area) 생성
fig2 = px.area(
    filtered_df,
    x="기준일자",
    y="누적관객수",
    title=f"[{selected_movie}] 누적 관객 수 변화",
    markers=True,
)

# 그래프 화면 표시
st.plotly_chart(fig2, use_container_width=True)

# 인사이트 텍스트 영역
st.info(f"💡 **이 그래프로 알 수 있는 것:** {selected_movie}의 시간이 지남에 따른 누적 관객 수의 누적 성장세와 최종 성적 도달 속도를 볼 수 있습니다.")
