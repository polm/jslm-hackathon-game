import json
import random
import os

from fireworks.client import Fireworks

import streamlit as st

# if this isn't set the code won't run
API_KEY = os.environ["FIREWORKS_API_KEY"]

RULES = """このゲームであなたはいろんな危険な場面を生き抜けなければなりません。状況に応じて取る行動を入力し、AIの判断を受けましょう。生存できると判断されたらそのまま進みますが、できなかったらLIFEが一つ減ります。あなたは最後まで生き残れるでしょうか？"""

# These aren't interesting, they're just placeholders for now.
INTROS = [
        "あなたは孤島に遭難します。脱出すべく、孤島の探索にかかります。",
        ]

CONCLUSIONS = [
        "不思議な島を探索していると、脱出に使える船を見つけました。良かったですね！"
        ]

# If expanded, this could go in another file.
PROBLEMS = [
    "あなたは火山の火口に落ちそうになります。",
    "ジャングルを探索していると、魅惑的なオアシスを発見した。そこでは、水が喋り。突然、あなたが水底に向かって泳いでいることに気づきました。",
    "洞窟を探索していると、突然入口が崩壊し、脱出路なしで土に埋められます。",
    "ジャングルで巨大な植物があなたを引きずり込もうとします。",
    "森の中、毒ガスを放出する胞子を持っている植物のトラップに閉じ込められています。",
    "夜に海辺を歩いていると、突然暗闇から大量の爪と触手を備えた海の怪物に襲われます。",
    "洞窟を探索していると、翅が光る巨大な蛾に襲われます。",
    "ジャングルの中で毒ベビに噛まれてしまいました。",
    "ビーチに沿って歩いているとき、サメに襲われます。",
    "ゴリラの群れが追いかけてきます。",
    "誤って古代のアーティファクトを起動し、その結果、異世界への転送を余儀なくされそうになります。",
    "森に迷って出られなくなります。",
    "島を探索していると、深い穴に落ちてしまいます。",
    "崖を登っていると、大きいなハゲタカに襲われます。",
    "吊橋を渡る途中、鳥の群れに襲われます。",
    "洞窟の中を調べると、大きい試験管の中でよく分からないトカゲみたい生物が浮かんでいます。突然グラスを割れて襲いかかってきます！",
    "可愛い犬が走ってきます。しかしよく近づいてくると、口の中から触手を出して襲ってきます！",
    "背の高い草の茂みを通ると、厚い霧が空気を満たしています。突然、草の中で何かが動くのを聞いて、よく見ると、闇から何かがこちらをじっと見ています。",
    "謎めいた寺院に沿って歩くと、地面が揺れ始め、地震が始まります。",
    "海岸に沿って歩くと、突然の嵐が空を覆っています。悪天候に直面して洞窟を探して、そこに住んでいる何かがあなたを待っていることに気付きます。",
    "廃れた研究所で、壊れたガラスの瓶や壊れたテスト管にいっぱいの暗く湿った部屋に入ります。壁には奇妙な生き物の粘着性の染みがあり、床には何かを歩くと頻繁に聞こえる不均一な音がします。",

    ]

st.title("Stability Japan Hackathon Game")

def shuffled(ll):
    # shuffle the list
    return random.sample(ll, len(ll))

def get_survival_prompt(situation, action):
    prompt = f"""プレイヤーは以下の状況で次のように行動したら生存できますか？
    OKかNGで答えてください。その後判断の説明を書いてください。
    状況:{situation}
    行動:{action}"""
    return prompt


def parse_result(res):
    # the format should be like this:
    #   OK
    #   blah blah blah reason blah
    # But even at the best of times it's unreliable after the first two characters.
    # Sometimes even this format doesn't work.

    survive = res[:2] == "OK"
    reason = res
    return survive, reason


def handle_result(survive, hp):
    # TODO it would be good to vary language here more
    msg = None
    if survive:
        return "うまく逃げました！"
    else:
        if hp > 0:
            return "あなたの行動はうまくいけませんでしたが、それでも今回はなんとか生存できました。"
        else:
            return "残念ながらあなたは逃げられませんでした。今回の冒険はここでおしまい。"


def fireworks(prompt):
    client = Fireworks(api_key=API_KEY)
    response = client.chat.completions.create(
        model="accounts/stability/models/japanese-stablelm-instruct-beta-70b",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )
    return response.choices[0].message.content


def do_scene(problem, action, hp):
    # judge input
    prompt = get_survival_prompt(problem, action)
    res = fireworks(prompt)
    survive, reason = parse_result(res)
    msg = handle_result(survive, hp)
    return survive, reason, msg

def game_over():
    with st.chat_message("assistant"):
        st.write("GAME OVER")
        if st.button("やり直し"):
            del st.session_state.messages
            st.rerun()

def win_game():
    with st.chat_message("assistant"):
        st.balloons()
        st.write("おめでとう！あなたは無事不思議な島から脱出できました。")
        st.write("もう一度遊ぶ場合、ページを再読み込みしてください。")

def status_bar(state):
    return f"LIFE: {state.hp} | PROGRESS: {state.progress}/{len(state.challenges)}"

def main():

    # initialize session state
    # these can all be initialized at once
    if "messages" not in st.session_state:
        st.session_state.messages = []
        with st.chat_message("assistant"):
            st.write(RULES)
            st.write(INTROS[0])

        st.session_state.challenges = shuffled(PROBLEMS)[:10]
        st.session_state.hp = 5

        st.session_state.progress = 0 # track how many to go

        with st.chat_message("assistant"):
            state = st.session_state
            status = status_bar(state)
            current_challenge = state.challenges[state.progress]
            st.write(status)
            state.messages.append({"role": "assistant", "content": status})
            st.write(current_challenge)
            state.messages.append({"role": "assistant", "content": current_challenge})

    # write message history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    action = st.chat_input("どうしますか？")
    if action is not None:
        state = st.session_state
        challenge = state.challenges[state.progress]
        hp = state.hp
        survive, reason, msg = do_scene(challenge, action, hp)

        with st.chat_message("user"):
            state.messages.append({"role": "user", "content": action})
            st.write(action)
        with st.chat_message("assistant"):
            state.messages.append({"role": "assistant", "content": msg})
            st.write(msg)
            state.messages.append({"role": "assistant", "content": reason})
            st.write(reason)

        if not survive:
            hp -=1 
        if hp < 1:
            game_over()
        else:
            if state.progress == len(state.challenges):
                win_game()
            state.progress += 1
            state.hp = hp

            # ready the next challenge
            with st.chat_message("assistant"):
                status = status_bar(state)
                current_challenge = state.challenges[state.progress]
                state.messages.append({"role": "assistant", "content": status})
                state.messages.append({"role": "assistant", "content": current_challenge})

                st.write(status)
                st.write(current_challenge)


if __name__ == "__main__":
    main()
