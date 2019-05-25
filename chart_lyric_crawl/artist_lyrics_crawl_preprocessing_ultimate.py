import argparse
import pandas as pd
import time
import re
import urllib.request
import urllib.parse
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pandas import DataFrame

parser = argparse.ArgumentParser()
parser.add_argument('artist_name', help='artist name you wanna crawl')

args = parser.parse_args()

artist_name = args.artist_name

# track information sheet
artists_list = []
titles_list = [] # song's title
trackId_list = []
number_of_lines_list = [] # lyric's number of lines
song_list = []

# 가사 분석을 순수 한글로만 이루어진 가사 데이터로만 진행하고 싶을때 사용하기 위함입니다.
has_alphabet_list = [] # check if lyric has alphabet

# lyric data sheet
lyrics_list = []

# lyric's sentences sheet
line_list = [] # index for sentence's line
sentence_data_list = [] # list for sentence data 
lyrics_sentence_trackId_list = [] # list for sentence's track identifier

# pattern that I wanna replace
rep = {'<br>':'\n', '<br/>':'\n', 'amp;':''}#, '-':' ', '_':'', '—':''}
# use these three lines to do the replacement
rep = dict((re.escape(k), v) for k, v in rep.items())
pattern = re.compile("|".join(rep.keys()))
def remove_tags(lyrics):
    # replace pattern that I defined above
    lyrics = pattern.sub(lambda m: rep[re.escape(m.group(0))], lyrics)
    # remove [text] and <text>    
    lyrics = re.sub("[\<\[].*?[\>\]]", "", lyrics)
    return lyrics

url1 = "https://music.naver.com/search/search.nhn?query="

# using parse module -> convert korean to unicode
url2 = urllib.parse.quote_plus(artist_name)

full_url = url1 + url2

html = urllib.request.urlopen(full_url)
 
artistSoup = BeautifulSoup(html, "lxml")

# 아티스트 id 추출
artist = artistSoup.find('dd', class_='desc').find('a')['href']
index = artist.find('=')
artist_id = artist[index+1:]

html = urlopen("https://music.naver.com/artist/track.nhn?artistId=%s&filteringOptions=RELEASE&sorting=newRelease"%artist_id)

# 1페이지가 최대인경우 a태그가 존재하지 않으므로 수동으로 설정해야함
max_page = len(BeautifulSoup(html, "lxml").find('div', class_='paginate2').find_all('a'))
if(max_page==0):
    max_page=1

for page in range(1, max_page+1, 1):
    html = urlopen("https://music.naver.com/artist/track.nhn?artistId=%s&filteringOptions=RELEASE&sorting=newRelease&page=%d"%(artist_id,page))

    tr_list = BeautifulSoup(html, "lxml").find_all('tr', class_='_tracklist_move')

    for tr in tr_list:
        trackinfo = tr['trackdata'].split('|')
        # tr.find('td', class_='tb_artist').find('span', class_='tit') != None 는 가수 두명 이상의 곡을 제외하고 싶을때 추가하면 됨
        # 가사 포함된 곡만 가져오기, Inst 들어간 제목 거르기, Ver 들어간 제목 거르기, cover 들어간 제목 거르기, MR 들어간 제목 거르기,Remix 거르기,Edit 거르기, 아카펠라 & 어쿠스틱 거르기, 노래 중복 거르기
        # song.find('Feat') == -1 and song.find('With') == -1 이 조건도 포함하면 다른 아티스트가 피쳐링한 곡도 거르고 찾는 아티스트가 다른 아티스트에게 피쳐링한 곡도 거름
        # DJ, By 포함된 곡 거르고 싶으면 song.find('DJ') == -1 and song.find('By') == -1
        song = tr.find('td', class_='tb_name').find('span',class_='tit').text.strip('\n')
        if(trackinfo[9]=='true' and song.find('Inst') == -1 and song.find('Ver') == -1 and song.find('cover') == -1 and song.find('MR') == -1 and song.find('remix') == -1 and song.find('Remix') == -1 and song.find('REMIX') == -1 and song.find('Remastered') == -1 and song.find('Acappella') == -1 and song.find('Acoustic') == -1 and song.find('Edit') == -1 and song not in song_list):
            trackId_list.append(trackinfo[0])
            song_list.append(song)

for t in trackId_list:
    html = urlopen("https://music.naver.com/lyric/index.nhn?trackId=%s"%t)
 
    trackSoup = BeautifulSoup(html, "lxml")

    title = trackSoup.find('span', class_='ico_play').text
    
    artist = str(trackSoup.find('span', class_='artist').find('a'))

    artist = str(re.findall(r'\>(.*?)\<', artist))[2:-2]

    lyrics = str(trackSoup.find('div', class_='show_lyrics'))

    lyrics = remove_tags(lyrics)

    # split with \n
    lyrics_sentence_list = lyrics.split('\n')

    '''
    # remove punctuation
    lyrics_sentence_list = [re.sub(r'[^\w\s]', '', lyrics, re.UNICODE) for lyrics in lyrics_sentence_list]
    '''

    '''
    # remove row in lyric has alphabet. use this code if you wanna pure korean lyrics
    # 영어로 된 문장 혹은 알파벳이 포함된 문장 전체를 제거합니다. 순수한글로만 이루어진 가사만 얻고 싶을때 사용합시다.
    lyrics_sentence_list = list(filter(lambda w: not re.match(r'[a-zA-Z]+', w), lyrics_sentence_list)) 
    '''

    '''
    # remove only english from row of lyric consist of kor and eng.
    # 한영 혼용 문장에서 오직 영어만을 제거합니다. (한글 부분은 남습니다.) 
    lyrics_sentence_list = [re.sub(r'[a-zA-Z]', '', lyrics) for lyrics in lyrics_sentence_list]
    '''

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

    # TrackInfo Sheet
    artists_list.append(artist)
    titles_list.append(title)
    number_of_lines_list.append(len(lyrics_sentence_list))

    # entire lyric
    lyrics_list.append(lyrics)

    # lyric's sentence      
    if t not in lyrics_sentence_trackId_list:     
        line = 1                           
        for ly in lyrics_sentence_list:
            lyrics_sentence_trackId_list.append(t)
            sentence_data_list.append(ly)
            line_list.append(line)
            line +=1

    check_has_alphabet = "False"
    for ly in lyrics_sentence_list:
        alpahbet_val = re.search('[a-zA-Z]+',ly)
        if(alpahbet_val == None): 
            pass
        else:
            if(alpahbet_val[0].isalpha()):
                check_has_alphabet = "True"
                break

    has_alphabet_list.append(check_has_alphabet)

trackInfoSheet_column_list = {
'Artist': artists_list,
'Title': titles_list,
'Track_Id' : trackId_list,   
'Number_Of_Lines' : number_of_lines_list,
'Has_English' : has_alphabet_list,
}

SentenceSheet_column_list = {
'Track_Id' : lyrics_sentence_trackId_list,
'Lyric_Sentence' : sentence_data_list,
'Line' : line_list,
}

df_track_info = pd.DataFrame.from_dict(trackInfoSheet_column_list, orient='index')
df_track_info = df_track_info.transpose()

df_sentence_data = pd.DataFrame.from_dict(SentenceSheet_column_list, orient='index')
df_sentence_data = df_sentence_data.transpose()

writer = pd.ExcelWriter("%s.xlsx" % artist_name)

df_track_info.to_excel(writer, sheet_name='track_info', startrow=1, header=True)
df_sentence_data.to_excel(writer, sheet_name='Sentence_data', startrow=1, header=True)

writer.save()