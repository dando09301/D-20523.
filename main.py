import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------------------------------------
# 페이지 기본 설정
# -------------------------------------------------------------
st.set_page_config(
    page_title="박스오피스 데이터 분석기",
    layout="wide"
)

st.title("🎬 영화 박스오피스 데이터 분석")
st.write("KOBIS 1개년 박스오피스 데이터를 기반으로 다양한 관객 지표를 시각화합니다.")

# -------------------------------------------------------------
# [1. 데이터 불러오기 및 2. 전처리]
# @st.cache_data를 사용해 데이터를 캐싱하여 앱 재실행 시 속도를 높입니다.
# -------------------------------------------------------------
@st.cache_data
def load_and_preprocess_data():
    csv_url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    
    # CSV 데이터 로드
    df = pd.read_csv(csv_url)
    
    # 결측치(NaN)가 포함된 행 삭제
    df = df.dropna()
    
    # '기준일자' 컬럼을 datetime 형식으로 변환
    df["기준일자"] = pd.to_datetime(df["기준일자"])
    
    # 전체 데이터를 기준일자 오름차순으로 정렬
    df = df.sort_values(by="기준일자")
    
    return df

# 데이터 로드 실행
df = load_and_preprocess_data()

# -------------------------------------------------------------
# [3. 영화 선택 목록 구성]
# 영화별 최대 누적관객수를 기준으로 내림차순 정렬하여 선택 목록 생성
# -------------------------------------------------------------
movie_rank = (
    df.groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .index
    .tolist()
)

# 사이드바에서 영화 선택
st.sidebar.header("🔍 검색 및 필터")
selected_movie = st.sidebar.selectbox(
    "분석할 영화를 선택하세요:",
    options=movie_rank
)

# 선택한 영화의 데이터만 추출
filtered_df = df[df["영화명"] == selected_movie]

# -------------------------------------------------------------
# [4. 그래프 1: 일별 관객수 추이 (단일 선 그래프)]
# -------------------------------------------------------------
st.subheader("📈 섹션 1: 일별 관객수 변화 추이")

if not filtered_df.empty:
    fig_daily = px.line(
        filtered_df,
        x="기준일자",
        y="해당일관객수",
        title=f"'{selected_movie}' 일자별 관객수 변화",
        markers=True,
        labels={"기준일자": "날짜", "해당일관객수": "일별 관객수(명)"}
    )
    fig_daily.update_layout(hovermode="x unified")
    st.plotly_chart(fig_daily, use_container_width=True)
    
    # 그래프 요약 문구
    st.info(f"💡 **이 그래프로 알 수 있는 것:** '{selected_movie}'의 개봉 초기 관객 집중도 및 요일별(주말/평일) 관객수 등락 패턴을 파악할 수 있습니다.")
else:
    st.warning("선택한 영화의 데이터가 존재하지 않습니다.")

st.markdown("---")

# -------------------------------------------------------------
# [5. 그래프 2: 누적 관객수 추이 (영역 차트)]
# -------------------------------------------------------------
st.subheader("📊 섹션 2: 누적 관객수 성장 추이 (영역 차트)")

if not filtered_df.empty:
    fig_area = px.area(
        filtered_df,
        x="기준일자",
        y="누적관객수",
        title=f"'{selected_movie}' 기준일자별 누적관객수 성장 곡선",
        labels={"기준일자": "날짜", "누적관객수": "누적 관객수(명)"}
    )
    fig_area.update_layout(hovermode="x unified")
    st.plotly_chart(fig_area, use_container_width=True)
    
    # 그래프 요약 문구
    st.info(f"💡 **이 그래프로 알 수 있는 것:** 시간이 지남에 따라 관객 총량이 어떻게 누적되는지 곡선의 기울기(성장 가속도 및 완만해지는 정체기)를 한눈에 직관적으로 파악할 수 있습니다.")

st.markdown("---")

# -------------------------------------------------------------
# [6. 그래프 3: 20일 이상 장기 상영작 중 TOP 5 누적관객수 비교 (다중 선 그래프)]
# -------------------------------------------------------------
st.subheader("🏆 섹션 3: 장기 흥행(20일 이상 차트인) TOP 5 영화 누적관객수 비교")

chart_days = df.groupby("영화명")["기준일자"].nunique()
long_run_movies = chart_days[chart_days >= 20].index

top5_long_run_movies = (
    df[df["영화명"].isin(long_run_movies)]
    .groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .head(5)
    .index
    .tolist()
)

top5_df = df[df["영화명"].isin(top5_long_run_movies)]

if not top5_df.empty:
    fig_top5 = px.line(
        top5_df,
        x="기준일자",
        y="누적관객수",
        color="영화명",
        title="20일 이상 차트인한 장기 흥행 TOP 5 영화의 누적관객수 추이",
        markers=False,
        labels={"기준일자": "날짜", "누적관객수": "누적 관객수(명)", "영화명": "영화 제목"}
    )
    fig_top5.update_layout(
        hovermode="x unified",
        legend_title_text="영화 순위 (장기 흥행 TOP 5)"
    )
    st.plotly_chart(fig_top5, use_container_width=True)
    
    # 그래프 요약 문구
    st.info(f"💡 **이 그래프로 알 수 있는 것:** 단기 반짝 흥행이나 기획전/재개봉작을 제외하고, 최소 20일 이상 박스오피스 상위권을 지킨 '진짜 장기 흥행작'들의 관객 모객 파워와 최종 스코어 도달 속도를 비교할 수 있습니다.")

st.markdown("---")

# -------------------------------------------------------------
# [7. 그래프 4: 기준일자별 전체 관객수 합계 추이 (선 그래프)]
# -------------------------------------------------------------
st.subheader("🗓️ 섹션 4: 일자별 전체 박스오피스 관객 총합 추이")

# 기준일자별로 모든 영화의 해당일관객수를 합산
daily_total_df = (
    df.groupby("기준일자")["해당일관객수"]
    .sum()
    .reset_index()
    .rename(columns={"해당일관객수": "일별전체관객수"})
)

fig_daily_total = px.line(
    daily_total_df,
    x="기준일자",
    y="일별전체관객수",
    title="박스오피스 전체 일별 총 관객수 변화",
    labels={"기준일자": "날짜", "일별전체관객수": "전체 관객수(명)"}
)
fig_daily_total.update_layout(hovermode="x unified")
st.plotly_chart(fig_daily_total, use_container_width=True)

# 그래프 요약 문구
st.info(f"💡 **이 그래프로 알 수 있는 것:** 개별 영화가 아닌 영화 시장 전체의 일자별 흐름을 보여주며, 주말 관객 폭증과 평일 급감 사이클 및 명절/연휴 특수를 확인할 수 있습니다.")

st.markdown("---")

# -------------------------------------------------------------
# [8. 그래프 5: 월별 전체 관객수 합계 (막대그래프)]
# -------------------------------------------------------------
st.subheader("📅 섹션 5: 월별(연-월) 전체 박스오피스 총 관객수 비교")

# 1) 기준일자에서 '연-월(YYYY-MM)' 문자열 컬럼 생성
daily_total_df["연월"] = daily_total_df["기준일자"].dt.strftime("%Y-%m")

# 2) 연월 단위로 묶어서 전체 관객수 합계 집계
monthly_total_df = (
    daily_total_df.groupby("연월")["일별전체관객수"]
    .sum()
    .reset_index()
    .rename(columns={"일별전체관객수": "월별전체관객수"})
)

# 3) Plotly 막대그래프(Bar Chart) 생성
fig_monthly_bar = px.bar(
    monthly_total_df,
    x="연월",
    y="월별전체관객수",
    title="월별(연-월) 전체 박스오피스 총 관객수",
    text_auto=".2s",  # 막대 상단에 관객수 수치 간략 표기 (예: 1.2M)
    labels={"연월": "연-월", "월별전체관객수": "월간 총 관객수(명)"}
)

# X축 레이블 순서 유지 및 막대 서식 설정
fig_monthly_bar.update_layout(
    xaxis={"type": "category"},
    hovermode="x unified"
)

st.plotly_chart(fig_monthly_bar, use_container_width=True)

# 그래프 요약 문구 자리
st.info(f"💡 **이 그래프로 알 수 있는 것:** 여름 휴가철(7~8월), 연말(12월), 명절 시즌 등 영화계의 전통적인 성수기와 비수기(봄, 가을) 간의 월별 극장가 관객 규모 차이를 한눈에 직관적으로 비교할 수 있습니다.")
