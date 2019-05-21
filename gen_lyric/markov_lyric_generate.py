import codecs
from bs4 import BeautifulSoup
from konlpy.tag import Okt
import os, re, json, random, sys
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('artist_name', help='artist name you wanna generate lyric')

args = parser.parse_args()

artist = args.artist_name

# 마르코프 체인 딕셔너리 만들기 (세 단어가 한 세트)
def make_dic(words):
    tmp = ["@"]
    dic = {}
    for word in words:
        tmp.append(word)
        if len(tmp) < 3: continue
        if len(tmp) > 3: tmp = tmp[1:]
        set_word3(dic, tmp)
        if word == ";":
            tmp = ["@"]
            continue
    return dic

# 딕셔너리에 데이터 등록하기 
def set_word3(dic, s3):
    w1, w2, w3 = s3
    if not w1 in dic: dic[w1] = {}
    if not w2 in dic[w1]: dic[w1][w2] = {}
    if not w3 in dic[w1][w2]: dic[w1][w2][w3] = 0
    dic[w1][w2][w3] += 1

# 문장 만들기 
def make_sentence(dic):
    ret = []
    if not "@" in dic: return "no dic" 
    top = dic["@"]
    w1 = word_choice(top)
    w2 = word_choice(top[w1])
    ret.append(w1)
    ret.append(w2)
    while True:
        w3 = word_choice(dic[w1][w2])
        ret.append(w3)
        if w3 == ";": break
        w1, w2 = w2, w3
    ret = " ".join(ret)

    return ret

def word_choice(sel):
    keys = sel.keys()
    return random.choice(list(keys))
 
lyric_file = "%s.txt"%artist
dict_file = "markov-%s.json"%artist
if not os.path.exists(dict_file):
    fp = codecs.open(lyric_file, "r", encoding="utf-8")
    soup = BeautifulSoup(fp, "lxml")
    text = soup.getText()
    text = text.replace("…", "") # 현재 koNLPy가 …을 구두점으로 잡지 못하는 문제 임시 해결
    # 형태소 분석
    okt = Okt()
    malist = okt.pos(text, norm=True)
    words = []
    for word in malist:
        # 구두점 등은 대상에서 제외(단 세미콜론 포함)
        if not word[1] in ["Punctuation"]:
            words.append(word[0])
        if word[0] == ";":
            words.append(word[0])
    # 딕셔너리 생성
    dic = make_dic(words)
    json.dump(dic, open(dict_file,"w", encoding="utf-8"))
else:
    dic = json.load(open(dict_file,"r"))

def gen_lyric():
    s = make_sentence(dic)
    s = s.replace(';', '')

    s_list = s.split('\n')

    s_list = list(filter(lambda a : a != '', s_list))   
    s_list = list(filter(lambda a : a.isspace() != True, s_list)) 
    s_list = [re.sub(' +', ' ', ly) for ly in s_list]
    s_list = [ly.strip() for ly in s_list]

    s = '\n'.join(s_list)
   
    return s

lyric_result = gen_lyric()

while(True):
    if(len(lyric_result) > 10):
        print(lyric_result)
        sys.exit(0)
    else:
        continue
