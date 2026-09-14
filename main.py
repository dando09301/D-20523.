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

# 선택한 영화 데이터 필터링 (1, 2번 그래프용)
filtered_df = df[df["영화명"] == selected_movie]

# -------------------------------------------------------------------
# [첫 번째 구역: 개별 영화 일별 관객 수 선그래프]
# -------------------------------------------------------------------
st.header("1. 개별 영화 일별 관객 수 추이")

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
st.info(
    f"💡 **이 그래프로 알 수 있는 것:** {selected_movie}의 특정 일자별 관객 수 증감 폭과 개봉 초기/주말 등의 일별 흥행 추이를 파악할 수 있습니다."
)

# 구분선 추가
st.divider()

# -------------------------------------------------------------------
# [두 번째 구역: 개별 영화 누적 관객 수 영역차트]
# -------------------------------------------------------------------
st.header("2. 개별 영화 누적 관객 수 추이")

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
st.info(
    f"💡 **이 그래프로 알 수 있는 것:** {selected_movie}의 시간이 지남에 따른 누적 관객 수의 누적 성장세와 최종 성적 도달 속도를 볼 수 있습니다."
)

# 구분선 추가
st.divider()

# -------------------------------------------------------------------
# [세 번째 구역: 20일 이상 장기 상영작 중 TOP 5 누적 관객 수 비교]
# -------------------------------------------------------------------
st.header("3. 20일 이상 차트인 영화 중 TOP 5 누적 관객 수 비교")

# 1. 영화별 TOP 10 진입 일수(데이터 행 수) 계산
movie_days = df["영화명"].value_counts()

# 2. 20일 이상 등장한 영화의 목록 추출
long_running_movies = movie_days[movie_days >= 20].index.tolist()

# 3. 20일 이상 등장한 영화 중에서 누적관객수 상위 5개 영화 선택
top5_long_running = (
    df[df["영화명"].isin(long_running_movies)]
    .groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .head(5)
    .index.tolist()
)

# 4. 상위 5개 장기 흥행 영화의 데이터만 필터링
top5_long_df = df[df["영화명"].isin(top5_long_running)]

# 5. color='영화명' 속성을 사용해 범례와 함께 다중 선그래프 생성
fig3 = px.line(
    top5_long_df,
    x="기준일자",
    y="누적관객수",
    color="영화명",  # 영화별 선 색상 및 범례 구분
    title="20일 이상 TOP10 차트인 영화 중 누적 관객 수 TOP 5 추이 비교",
    markers=True,
)

# 그래프 화면 표시
st.plotly_chart(fig3, use_container_width=True)

# 인사이트 텍스트 영역
st.info(
    "💡 **이 그래프로 알 수 있는 것:** 최소 20일 이상 박스오피스 TOP 10에 머물며 롱런(Long-run)한 대표 흥행작 5편의 누적 관객 수 증가 패턴과 장기 흥행 동력을 한눈에 비교할 수 있습니다."
)
