import json
import codecs
import os
import sys
import re
import bs4

import htmlGetter

# 生放送の動画のIDをVIDEO_IDに代入
VIDEO_ID = "8cTopYQzpuU"
OUTPUT_DIR = "./CommentFiles/"

CONTINUATION_URL_FORMAT = "https://www.youtube.com/live_chat_replay?continuation={continuation}"


# htmlファイルから目的のjsonファイルを取得する
def get_json(html):
    soup = bs4.BeautifulSoup(html, "lxml")

    json_dict = None
    for script in soup.find_all("script"):
        if 'window["ytInitialData"]' in str(script):
            #print(script.string)
            json_line = re.findall(r"window\[\"ytInitialData\"\] = (.*);", script.string)[0]
            #print(json_line)
            json_dict = json.loads(json_line)
    return json_dict

# 最初の動画のURLからcontinuationを引っ張ってくる
def get_initial_continuation(url):
    html = htmlGetter.get_html(url)

    json_dict = get_json(html)

    continuation = json_dict['contents']['twoColumnWatchNextResults']['conversationBar']['liveChatRenderer']['continuations'][0]['reloadContinuationData']['continuation']
    print('InitialContinuation : ', continuation)
    return continuation

# htmlから抽出したjson形式の辞書からcontinuationの値を抜き出す
def get_continuation(json_dict):
    try:
        continuation = json_dict['continuationContents']['liveChatContinuation']['continuations'][0]['liveChatReplayContinuationData']['continuation']
        print("NextContinuation: ", continuation)
    except KeyError:
        continuation = ""
        print("Continuation NotFound")
    return continuation

# コメントデータから文字列を取得する
def get_chat_text(actions):
    lines = []
    for item in actions:
        # ユーザーによるコメント要素のみ取得する
        try:
            # ユーザー名やテキスト、アイコンなどのデータが入っている
            comment_data = item['replayChatItemAction']['actions'][0]['addChatItemAction']['item']['liveChatTextMessageRenderer']
            time = comment_data['timestampText']['simpleText']
            name = comment_data['authorName']['simpleText']
            text = comment_data['message']['runs'][0]['text']
            line = "{time}\t{name}\t{text}\n".format(time=time, name=name, text=text)
            lines.append(line)
            print(line)
        except KeyError:
            continue
    # 最後の行のコメントデータが次のcontinuationの最初のコメントデータを一致するため切り捨て
    if len(lines) > 1:
        del lines[len(lines) - 1]
    return lines

# 与えられたcontinuationから順次コメントを取得する
def get_live_chat_replay(continuation):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with codecs.open(OUTPUT_DIR + VIDEO_ID + '.tsv', mode='a', encoding='utf-8') as f:
        while continuation:
            url = CONTINUATION_URL_FORMAT.format(continuation=continuation)
            html = htmlGetter.get_html(url)

            json_dict = get_json(html)
            #print(json_dict)

            # key:actions中に各ユーザーのコメントが格納されている
            actions = json_dict["continuationContents"]["liveChatContinuation"]["actions"]
            # 複数件のコメントをlist形式で取得
            lines = get_chat_text(actions)
            # 次のcontinuationを取得する
            continuation = get_continuation(json_dict)

            f.writelines(lines)

if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1:
        VIDEO_ID = args[1]
    url = "https://www.youtube.com/watch?v="+VIDEO_ID
    # 生放送の録画ページから最初のcontinuationを取得する
    initial_continuation = get_initial_continuation(url)
    get_live_chat_replay(initial_continuation)


