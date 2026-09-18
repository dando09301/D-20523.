import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="영화 데이터 그래프 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

# 타이틀 설정
st.title("🎬 영화 데이터 그래프 - 분포와 관계")
st.markdown("1년간 박스오피스 10위권에 든 영화 중 해당 기간 개봉한 216편의 데이터 시각화 대시보드")

# 데이터 불러오기 함수
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)
    
    # 장르 처리: 결측치 예외 처리 후 '|' 기준 첫 번째 장르만 추출
    if 'genre' in df.columns:
        df['genre_first'] = (
            df['genre']
            .fillna('미상')
            .astype(str)
            .apply(lambda x: x.split('|')[0].strip() if x not in ['nan', ''] else '미상')
        )
    else:
        df['genre_first'] = '미상'
        
    return df

try:
    df = load_data()
    
    # ---------------------------------------------------------
    # 1번째 그래프: 장르별 영화 편수 (도넛 차트)
    # ---------------------------------------------------------
    st.header("1. 장르별 영화 편수 분포")
    
    genre_counts = df['genre_first'].value_counts().reset_index()
    genre_counts.columns = ['장르', '영화 편수']
    
    fig1 = px.pie(
        genre_counts, 
        values='영화 편수', 
        names='장르', 
        hole=0.4,
        title='장르별 영화 비율 및 편수 (도넛 차트)',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    # 마우스 호버 시 편수와 비율 표기
    fig1.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>영화 편수: %{value}편<br>비율: %{percent}'
    )
    fig1.update_layout(margin=dict(t=50, b=20, l=20, r=20))
    
    st.plotly_chart(fig1, use_container_width=True)
    
    st.info("💡 **이 그래프로 알 수 있는 것:** 국내 박스오피스 상위권에 진입한 영화들의 주요 장르 구성비와 특정 장르 편중도를 한눈에 파악할 수 있습니다.")
    
    st.divider()

    # ---------------------------------------------------------
    # 2번째 그래프: 장르 및 영화별 총 관객수 (트리맵)
    # ---------------------------------------------------------
    st.header("2. 장르 및 영화별 총 관객수 분포 (트리맵)")
    
    fig2 = px.treemap(
        df,
        path=[px.Constant("전체"), 'genre_first', 'movieNm'],
        values='total_audi',
        color='genre_first',
        color_discrete_sequence=px.colors.qualitative.Set3,
        title='장르별 영화 분포 및 총 관객수 (칸 크기: 총 관객수)'
    )
    
    fig2.update_traces(
        hovertemplate='<b>%{label}</b><br>총 관객수: %{value:,.0f}명'
    )
    fig2.update_layout(margin=dict(t=50, b=20, l=20, r=20))
    
    st.plotly_chart(fig2, use_container_width=True)
    
    st.info("💡 **이 그래프로 알 수 있는 것:** 각 장르 내에서 어떤 영화가 흥행을 주도했는지와 장르 전체의 관객수 점유 규모를 한눈에 비교할 수 있습니다.")

    st.divider()

    # ---------------------------------------------------------
    # 3번째 그래프: 총 관객수 분포 (히스토그램)
    # ---------------------------------------------------------
    st.header("3. 총 관객수 분포 (히스토그램)")
    
    fig3 = px.histogram(
        df,
        x='total_audi',
        nbins=30,
        title='영화별 총 관객수 분포',
        labels={'total_audi': '총 관객수(명)', 'count': '영화 편수'},
        color_discrete_sequence=['#4C72B0']
    )
    
    fig3.update_traces(
        hovertemplate='관객수 구간: %{x}<br>영화 편수: %{y}편'
    )
    fig3.update_layout(
        yaxis_title="영화 편수",
        margin=dict(t=50, b=20, l=20, r=20)
    )
    
    st.plotly_chart(fig3, use_container_width=True)
    
    # 데이터 기반 분석 문구 계산
    top_movie = df.loc[df['total_audi'].idxmax()]
    top_movie_name = top_movie['movieNm']
    top_movie_audi = top_movie['total_audi']
    
    # 50만 이하, 100만 이하 영화 비중 계산
    under_100k = len(df[df['total_audi'] <= 1000000])
    under_100k_pct = (under_100k / len(df)) * 100
    
    st.info(
        f"💡 **이 그래프로 알 수 있는 것:** "
        f"대부분의 영화가 관객수 **100만 명 이하 구간**({under_100k}편, 전체의 {under_100k_pct:.1f}%)에 밀집되어 있으며, "
        f"가장 관객이 많은 영화는 **'{top_movie_name}'**(총 {top_movie_audi:,.0f}명)입니다."
    )

    st.divider()

    # 원본 데이터 확인용 Expander
    with st.expander("📄 Raw Data 보기"):
        st.dataframe(df)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
