# -*- coding: UTF-8 -*-
import re
import sys
from functools import cache
import datetime


import requests
url = 'https://leetcode.cn/graphql'
@cache
def loadPage(page):
    query = "{\n  localRankingV2(page:" + str(
        page) + ") {\nmyRank {\nattendedContestCount\ncurrentRatingRanking\ndataRegion\nisDeleted\n" \
                "user {\nrealName\nuserAvatar\nuserSlug\n__typename\n}\n__typename\n}\npage\ntotalUsers\nuserPerPage\n" \
                "rankingNodes {\nattendedContestCount\ncurrentRatingRanking\ndataRegion\nisDeleted\n" \
                "user {\nrealName\nuserAvatar\nuserSlug\n__typename\n}\n__typename\n}\n__typename\n  }\n}\n"
    retry = 0
    while retry < 3:
        resp = requests.post(url=url, json={'query': query})
        if resp.status_code == 200:
            nodes = resp.json()['data']['localRankingV2']['rankingNodes']
            return [(int(nd['currentRatingRanking']), nd['user']['userSlug']) for nd in nodes]
        else:
            retry += 1
    return None

@cache
def getUserRank(uid):
    operationName = "userContest"
    query = "query userContest($userSlug: String!){\n userContestRanking(userSlug: $userSlug){" \
            "\ncurrentRatingRanking\nratingHistory\n}\n}\n "
    variables = {'userSlug': uid}
    retry = 0
    while retry < 3:
        resp = requests.post(url=url, json={
            'operationName': operationName,
            'query': query,
            'variables': variables
        })
        if resp.status_code == 200:
            ranking = resp.json()['data']['userContestRanking']
            score = None
            if ranking and 'ratingHistory' in ranking:
                s = ranking['ratingHistory']
                mth = re.search(r'(\d+(?:\.\d+)?)(?:, null)*]$', s)
                if mth:
                    score = mth.group(1)
            return (ranking['currentRatingRanking'], float(score)) if score else (None, None)
        else:
            retry += 1
    return None, None

def get1600Count():
    l, r = 1, 1000
    while l < r:
        mid = (l + r + 1) // 2
        page = loadPage(mid)
        if not page:
            return 0
        ranking, score = getUserRank(page[0][1])
        if score < 1600:
            r = mid - 1
        else:
            l = mid
    page = loadPage(l)
    l, r = 0, len(page)
    while l < r:
        mid = (l + r + 1) // 2
        ranking, score = getUserRank(page[mid][1])
        if score < 1600:
            r = mid - 1
        else:
            l = mid

    return getUserRank(page[l][1])[0]
@cache
def getUser(rank):
    if rank <= 0:
        raise Exception('error rankings')
    p = (rank - 1) // 25 + 1
    off = (rank - 1) % 25
    page = loadPage(p)
    ranking, score = getUserRank(page[off][1])
    return score, page[off][1]


total = get1600Count()
if not total:
    print('internet error')
    sys.exit()

guardian = int(total * 0.05)
knight = int(total * 0.25)
g_first, g_last = getUser(1), getUser(guardian)
stdout_backup = sys.stdout
# define the log file that receives your log info
log_file = open("message.log", "w")
# redirect print output to log file
sys.stdout = log_file
print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("total is", total)
print(f"Guardian(top 5%): 共{guardian} 名，守门员 {g_last[0]} 分（uid: {g_last[1]}），最高 {g_first[0]} 分（uid: {g_first[1]})")
k_first, k_last = getUser(guardian + 1), getUser(knight)
print(f"Knight(top 25%): 共 {knight} 名，守门员 {k_last[0]} 分（uid: {k_last[1]}），最高 {k_first[0]} 分（uid: {k_first[1]})")
log_file.close()