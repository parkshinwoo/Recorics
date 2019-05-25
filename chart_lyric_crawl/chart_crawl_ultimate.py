import argparse
import pandas as pd
import time
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pandas import DataFrame

parser = argparse.ArgumentParser()
parser.add_argument('year', type = int, help='year you wanna crawl')
parser.add_argument('type', help='chart type, DOMESTIC / OVERSEA / TOTAL')

args = parser.parse_args()

# DOMESTIC : 국내 / OVERSEA : 해외 / TOTAL : 종합
type_ = args.type

# period that you wanna crawl
begin_month = 1
end_month = 12
begin_year = args.year
end_year = args.year

# track information sheet
years_list = []
months_list = []
weeks_list = []
time_list = [] # year + month + week
ranks_list = []
ranking_score_list = [] # 1/rank
artists_list = []
titles_list = [] # song's title

trackId_list = []

period_artists_list = [] # 201931 artist1 artist2 ~ artist100

# header for period_artists_list
header = []
header.append('Period')
for i in range(1, 101):
    header.append(i) 

for year in range(begin_year, end_year+1, 1): 
    for month in range(begin_month, end_month+1, 1):
        
        # 차트 type -> 종합 : TOTAL / 국내 : DOMESTIC / 해외 : OVERSEA
        
        html = urlopen("https://music.naver.com/listen/history/index.nhn?type=%s&year=%d&month=%02d&week=%d" % (type_, year, month, 1))
        
        # Check 4 weeks per a month or 5 weeks per a month
        max_week = len(BeautifulSoup(html, "lxml").find_all('a', class_='_a_week'))-1

        for week in range(1, max_week+1, 1):

            # temporary list for second sheet
            tmp_artist_list = []
            tmp_artist_list.append(str(year)+str(month)+str(week))

            # page 1 : Top 1~50, page 2 : Top 51~100
            for page in range(0, 2):
                
                # 차트 type -> 종합 : TOTAL / 국내 : DOMESTIC / 해외 : OVERSEA

                html = urlopen("https://music.naver.com/listen/history/index.nhn?type=%s&year=%d&month=%02d&week=%d&page=%d" % (type_, year, month, week, page+1))

                rankSoup = BeautifulSoup(html, "lxml")
                
                # information about tracks
                tracks = rankSoup.find_all('tr', class_='_tracklist_move')
                
                # 서비스 중인 곡은 _title, 서비스 종료된 곡은 title
                songs = rankSoup.find_all(['a', 'span'], class_=re.compile(r"^(title|_title)$")) 
                artists = rankSoup.find_all('td', class_='_artist')

                rank = 1 # rank starts at 1

                for song in songs:
                    # index : 0 Trackid, 2 서비스 유무, 4 19금 유무, 9 가사 유무
                    trackinfo = tracks[rank]['trackdata'].split('|') 

                    artist = artists[rank]

                    # TrackInfo Sheet
                    years_list.append(year)
                    months_list.append(month)
                    weeks_list.append(week)
                    ranks_list.append(rank + 50*page)
                    time_list.append(str(year)+str(month)+str(week))
                    ranking_score_list.append(1/(rank + 50*page))
                    artists_list.append(artist.text.strip())
                    titles_list.append(song.text)
                    trackId_list.append(trackinfo[0])
                    
                    artist_item = artist.text.strip()

                    # 연관규칙분석 알고리즘을 위해 중복 항목은 제거한다.
                    if(artist_item in tmp_artist_list):
                        pass
                    else:
                        tmp_artist_list.append(artist.text.strip())

                    rank += 1 # increase rank, rank is in range 1~100

             # 중복을 제거하면 100개 미만의 데이터가 존재할 것이다. 한행이 100개를 유지하도록 뒤에 공백을 삽입한다.
            length = len(tmp_artist_list)
            for i in range(length, 101): # 맨 처음 시작은 기간 컬럼 (Period) 그 이후 부터 100개
                tmp_artist_list.append('')

            period_artists_list.append(tmp_artist_list)

chart_list = {
'year/month/week' : time_list,
'rank': ranks_list,
'artist': artists_list,
'title': titles_list,
'rank_score' : ranking_score_list,
'year': years_list,
}

df_chart_info = pd.DataFrame.from_dict(chart_list, orient='index')
df_chart_info = df_chart_info.transpose()

df_period_artist = pd.DataFrame(period_artists_list)

writer = pd.ExcelWriter("%s.xlsx" % args.year)

df_chart_info.to_excel(writer, sheet_name='Top100_chart', startrow=1, header=True)
df_period_artist.to_excel(writer, sheet_name='Period_artist', startrow=1, header=header)

writer.save()


