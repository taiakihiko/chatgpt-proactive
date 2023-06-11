import openai, os, json, time, random, tiktoken
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from history import *

os.chdir(os.path.dirname(os.path.abspath(__file__)))

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No OpenAI API Key found in environment variables.")
openai.api_key = OPENAI_API_KEY

prompts = {}
try:
    with open("prompts.json", "r", encoding="utf-8") as f:
        prompts = json.load(f)
except FileNotFoundError:
    exit("prompts.json not found")

if "history" not in st.session_state:
    st.session_state.history = []
    st.session_state.keyword = []
    st.session_state.last_keyword_detect_history = 0
    st.session_state.icon = [random.choice("🫠😎😺😄🥳"), random.choice("📻📟📠📱💻")]

if "last_answered_time" not in st.session_state:
    st.session_state.last_answered_time = time.time()

if "starter" not in st.session_state:
    st.session_state.starter = ""

title = "ChatGPT 能動発話サンプル"
st.set_page_config(page_title=title, layout="wide")

try:
    with open("script.js", "r", encoding="utf-8") as f:
        script_js = f.read()
except FileNotFoundError:
    exit("script.js not found")
components.html(script_js, height=0, width=0)

def starter_button_clicked(args):
    (starter) = args
    st.session_state.starter = starter
    print(starter)

def main():
    if st.session_state.starter == "":
        col1, col2, col3 = st.columns(3)
        col1.subheader("Which will start the conversation?")
        col2.button("from ChatGPT", type="primary", on_click=starter_button_clicked, args=("C",))
        col2.button("from me", type="primary", on_click=starter_button_clicked, args=("P",))
        st.stop()

    col1, col2 = st.columns([0.7, 0.3])

    history = History(st.session_state.history)
    df = history.as_dataframe()
    col2.write("Total tokens: {}".format(df["tokens"].sum()))
    col2.dataframe(df, height = max(200, history.len() * 45))
    col2.write(st.session_state.keyword)

    col1.markdown("This conversation was started from **{}**".
        format("ChatGPT" if st.session_state.starter == "C" else "You")
    )

    for h in history.all():
        match h["role"]:
            case "user":
                col1.warning(h["content"], icon=st.session_state.icon[0])
            case "assistant":
                col1.success(h["content"], icon=st.session_state.icon[1])

    user_text = col1.text_area("質問文",
        value=prompts["user_text_default"] if st.session_state.starter == "P" else "")

    col1_1, col1_2, col1_3, col1_4, col1_5 = col1.columns([0.5, 0.5, 1, 0.7, 1.3])
    is_generate_clicked = col1_1.button("文章生成", type="primary")
    is_continue_clicked = col1_2.button("続けて")
    enabled_auto_speak = col1_4.checkbox("Auto speak", value=True)
    auto_speak_interval = col1_5.slider('Interval (sec)', 10, 60, 30)

    if st.session_state.starter == "C" and history.len() == 0:
        history.add("system", prompts["init"])
        history.add("system", prompts["start_by_chatgpt"])
        col1.markdown(":red[Generating...]")

        assistant_text = send_and_recieve(history.all(), col1.empty())
        history.add("assistant", assistant_text)
        st.session_state.last_answered_time = time.time()
        st.experimental_rerun()

    elif (is_generate_clicked and user_text) or is_continue_clicked:
        if history.len() == 0:
            history.add("system", prompts["init"])

        if is_continue_clicked:
            history.add("user", prompts["continue"])
        else:
            history.add("user", user_text)
            print(user_text)
        col1.markdown(":red[Generating...]")

        assistant_text = send_and_recieve(history.all(), col1.empty())
        history.add("assistant", assistant_text)
        st.session_state.last_answered_time = time.time()
        st.experimental_rerun()

    else:
        time.sleep(5)
        if "last_answered_time" in st.session_state:
            last_answer_pasted = int(time.time() - st.session_state.last_answered_time)
            print('last answer pasted', last_answer_pasted, 'sec')

            if enabled_auto_speak and last_answer_pasted > auto_speak_interval:
                keyword = random.choice(st.session_state.keyword["words"])
                fairy = random.choice(prompts["fairy"]).format(keyword = keyword)
                history.add("system", fairy)

                assistant_text = send_and_recieve(history.all(), col1.empty())
                history.add("assistant", assistant_text)
                st.session_state.last_answered_time = time.time()
                st.experimental_rerun()

        if "last_keyword_detect_history" in st.session_state:
            if st.session_state.last_keyword_detect_history < history.len() - 1:
                print("auto keyword ", st.session_state.last_keyword_detect_history, history.len())
                words = detect_keywords(history.all())
                print(words)
                if len(words) > 0:
                    st.session_state.keyword = words
                st.session_state.last_keyword_detect_history = history.len()

        st.experimental_rerun()


def send_and_recieve(messages, output_element):
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = messages,
        max_tokens = 200,
        temperature = 1.1,
        stream = True
    )
    partial_words = "" 
    for chunk in response:
        if chunk and "delta" in chunk["choices"][0]:
            choice = chunk["choices"][0]
            if "content" in choice["delta"]:
                partial_words += choice["delta"]["content"]
                output_element.write(partial_words)
            if choice["finish_reason"] is not None:
                print('finish_reason', choice["finish_reason"])
    return partial_words


def detect_keywords(messages):
    concat_history = "\n".join([i["content"] for i in messages])
    query = prompts["keyword"].format(concat_history = concat_history)
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = [{"role": "system", "content": query}],
    )
    print(response.choices[0].message.content)
    words = json.loads(response.choices[0].message.content)
    return words


if __name__ == "__main__":
    main()
