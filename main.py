if 'genre' in df.columns:
        # 결측치를 '미상'으로 채운 뒤 문자열(str) 변환 후 첫 번째 장르 추출
        df['genre_first'] = (
            df['genre']
            .fillna('미상')
            .astype(str)
            .apply(lambda x: x.split('|')[0].strip() if x != 'nan' and x != '' else '미상')
        )
    else:
        df['genre_first'] = '미상'
