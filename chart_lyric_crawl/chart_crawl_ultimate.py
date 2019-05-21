import argparse
import pandas as pd
import time
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pandas import DataFrame
from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoAlertPresentException

parser = argparse.ArgumentParser()
parser.add_argument('type', help='type you wanna crwal 종합:TOTAL 해외:OVERSEA 국내:DOMESTIC')
parser.add_argument('excel_name', help='excel name you wanna save')
parser.add_argument('eng_option', type = int, help='enter 1 if you wanna remove sentence that has eng or enter 2 if you wanna remove only eng stuff')

args = parser.parse_args()

type_ = args.type

eng_option = args.eng_option

# track information sheet
years_list = []
months_list = []
weeks_list = []
time_list = [] # year + month + week
ranks_list = []
ranking_score_list = [] # 1/rank
artists_list = []
titles_list = [] # song's title
genre_list = []
release_date_list = [] 
trackId_list = []
notes_list = [] # list for special case. classify track that 19+(for only adult), track that doesn't exist anymore, track that doesn't have lyric, track that doesn't provide service(can't play).
number_of_lines_list = [] # lyric's number of lines

period_artists_list = [] # 201931 artist1 artist2 ~ artist100

# lyric's sentences sheet
line_list = [] # index for sentence's line
sentence_data_list = [] # list for sentence data
lyrics_sentence_trackId_list = [] # list for sentence's track identifier 

# edit with your path of chromedriver
browser = webdriver.Chrome('/Users/pshkh/chromedriver_win32/chromedriver')

# enter the naver's login page
browser.get('https://nid.naver.com/nidlogin.login')
# if you wanna crawl 19+ song, you have to login
# 수동으로 네이버 로그인을 해줘야한다. 그것을 위한 10초 (캡차 회피 현존 방식은 전부 막힘)
time.sleep(10)

# header for period_artists_list
header = []
header.append('Period')
for i in range(1, 101):
    header.append(i) 

'''
here you have to adjust the period just the way you wanna crawl
'''
# period that you wanna crawl
begin_year = 2019
end_year = 2019
begin_month = 4
end_month = 12

'''
preprocessing lyric
'''
# pattern that I wanna replace
rep = {'<br>':'\n', '<br/>':'\n', 'amp;':'', '-':' ', '_':'', '—':''}
# use these three lines to do the replacement
rep = dict((re.escape(k), v) for k, v in rep.items())
pattern = re.compile("|".join(rep.keys()))
def remove_tags(lyrics):
    # replace pattern that I defined above
    lyrics = pattern.sub(lambda m: rep[re.escape(m.group(0))], lyrics)
    # remove [text] and <text>    
    lyrics = re.sub("[\<\[].*?[\>\]]", "", lyrics)
    return lyrics

for year in range(begin_year, end_year+1, 1):
    
    '''
    here you have to adjust the period just the way you wanna crawl
    '''
    # 2019년은 4월까지만 크롤링
    if year == 2019:
        end_month = 4
    
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

                    # for genre & release date
                    urldata = urlopen("http://music.naver.com/track/index.nhn?trackId=%s" % (trackinfo[0]))
                    trackSoup = BeautifulSoup(urldata, "lxml")
                    try:
                        trackdata = trackSoup.find("dl", class_="desc").find_all("dd") # for genre & release date
                    except AttributeError:
                        # 트랙 없음
                        genre_list.append('')   
                        release_date_list.append('')
                    else: 
                        genre_list.append(trackdata[1].text[1:])
                        release_date_list.append(trackdata[2].text)

                    if trackinfo[9] == 'true':
                        browser.get("https://music.naver.com/lyric/index.nhn?trackId=%s" % (trackinfo[0]))
                        try:
                            Alert(browser).accept()
                            lyrics = ''  
                            lyrics_sentence_list = ['']
                            note = '트랙 없음'

                            if trackinfo[4] == 'true':
                                note += '&19금'
                            if trackinfo[2] == 'false':
                                note += '&서비스 종료'
                        except NoAlertPresentException:
                            html = browser.page_source
                            lyricsSoup = BeautifulSoup(html, "html.parser")

                            lyrics = str(lyricsSoup.find('div', class_='show_lyrics'))

                            lyrics = remove_tags(lyrics)

                            # split with \n
                            lyrics_sentence_list = lyrics.split('\n')

                            # remove punctuation
                            lyrics_sentence_list = [re.sub(r'[^\w\s]', '', lyrics, re.UNICODE) for lyrics in lyrics_sentence_list]

                            # preprocessing about eng
                            if(eng_option == 1):
                                # remove row in lyric has alphabet. use this code if you wanna pure korean lyrics
                                # 영어로 된 문장 혹은 알파벳이 포함된 문장 전체를 제거합니다. 순수한글로만 이루어진 가사만 얻고 싶을때 사용합시다.
                                lyrics_sentence_list = list(filter(lambda w: not re.match(r'[a-zA-Z]+', w), lyrics_sentence_list)) 
                            elif(eng_option == 2):                            
                                # remove only english from row of lyric consist of kor and eng.
                                # 한영 혼용 문장에서 오직 영어만을 제거합니다. (한글 부분은 남습니다.) 
                                lyrics_sentence_list = [re.sub(r'[a-zA-Z]', '', lyrics) for lyrics in lyrics_sentence_list]
                        
                            # remove blank 
                            lyrics_sentence_list = list(filter(lambda a : a != '', lyrics_sentence_list))   
                            lyrics_sentence_list = list(filter(lambda a : a.isspace() != True, lyrics_sentence_list)) 
                            lyrics_sentence_list = [re.sub(' +', ' ', ly) for ly in lyrics_sentence_list]
                            lyrics_sentence_list = [ly.strip() for ly in lyrics_sentence_list]
                                
                            # remove blank from entire lyric
                            lyrics = '\n'.join(lyrics_sentence_list)

                            if(lyrics == 'None' or lyrics == '가사가 존재하지 않습니다'):
                                lyrics = ''
                                lyrics_sentence_list = ['']

                            note = ''

                            if trackinfo[4] == 'true':
                                note = '19금'
                                if trackinfo[2] == 'false':
                                    note += '&서비스 종료'
                            else:
                                if trackinfo[2] == 'false':
                                    note = '서비스 종료'
                    else :   
                        note = '가사 등록 안됨'

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
                    notes_list.append(note)
                    
                    artist_item = artist.text.strip()

                    # 연관규칙분석 알고리즘을 위해 중복 항목은 제거한다.
                    if(artist_item in tmp_artist_list):
                        pass
                    else:
                        tmp_artist_list.append(artist.text.strip())

                    # sentence sheet
                    number_of_lines_list.append(len(lyrics_sentence_list))

                    if trackinfo[0] not in lyrics_sentence_trackId_list:
                        line = 1    # use if you wanna write lyric to excel sentence by sentence
                        for ly in lyrics_sentence_list:
                            lyrics_sentence_trackId_list.append(trackinfo[0])
                            sentence_data_list.append(ly)
                            line_list.append(line)
                            line +=1

                    rank += 1 # increase rank, rank is in range 1~100

             # 중복을 제거하면 100개 미만의 데이터가 존재할 것이다. 한행이 100개를 유지하도록 뒤에 공백을 삽입한다.
            length = len(tmp_artist_list)
            for i in range(length, 101): # 맨 처음 시작은 기간 컬럼 (Period) 그 이후 부터 100개
                tmp_artist_list.append('')

            period_artists_list.append(tmp_artist_list)

chart_list = {
'Year': years_list,
'Month': months_list,
'Week': weeks_list,
'Year/Month/Week' : time_list,
'Ranking': ranks_list,
'Ranking_Score' : ranking_score_list,
'Artist': artists_list,
'Title': titles_list,
'Genre' : genre_list,
'Release_Date' : release_date_list,
'Note' : notes_list,
'Track_Id' : trackId_list,
}

SentenceSheet_column_list = {
'Track_Id' : lyrics_sentence_trackId_list,
'Lyric_Sentence' : sentence_data_list,
'Line' : line_list,
}

df_chart_info = pd.DataFrame.from_dict(chart_list, orient='index')
df_chart_info = df_chart_info.transpose()

df_period_artist = pd.DataFrame(period_artists_list)

df_sentence_data = pd.DataFrame.from_dict(SentenceSheet_column_list, orient='index')
df_sentence_data = df_sentence_data.transpose()

writer = pd.ExcelWriter("%s.xlsx" % args.excel_name)

df_chart_info.to_excel(writer, sheet_name='Top100_chart', startrow=1, header=True)
df_period_artist.to_excel(writer, sheet_name='Period_artist', startrow=1, header=header)
df_sentence_data.to_excel(writer, sheet_name='Sentence_data', startrow=1, header=True)

writer.save()


