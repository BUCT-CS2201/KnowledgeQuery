import streamlit as st
import streamlit.components.v1 as components
import api

# 清空对话
def clear_chat():
    st.session_state.messages = [
        {"role": "assistant", "content": "快来问吧! :kissing_heart:"}
    ] 
    st.session_state.input = ""
    print(st.session_state.history_window)
    api.refresh_history(st.session_state.history_window)

# 定义JavaScript代码，用于页面下滑s
scroll_js =  """
    <script>
        console.log("scroll down");
        function scrollToBottom() {
            console.log("scroll down");
            var contentDiv = parent.document.getElementsByClassName('main st-emotion-cache-bm2z3a ea3mdgi8');
            contentDiv[0].scrollTop = contentDiv[0].scrollHeight;
            console.log("scrollTop",contentDiv[0].scrollTop);
        }
        scrollToBottom();
    </script>
"""
def scroll_down():
    components.html(scroll_js,height=0,width=0)

# session初始化
def session_init():
    if "model_name" not in st.session_state.keys(): 
        st.session_state.model_name = " " # 初始化模型
    if "limit" not in st.session_state.keys(): 
        st.session_state.limit = None 
    if "audio" not in st.session_state.keys(): 
        st.session_state.audio = 0
    if "input" not in st.session_state.keys(): 
        st.session_state.input = ""
    if "voice_input" not in st.session_state.keys(): 
        st.session_state.voice_input = ""
    if "query" not in st.session_state.keys(): 
        st.session_state.query = ""
    if "inputBarClear" not in st.session_state.keys(): 
        st.session_state.inputBarClear = False
    if "history_window" not in st.session_state.keys(): 
        st.session_state.history_window = 5

# 提交查询
def Submit():
    print("submit")
    st.session_state.input = " "
    st.session_state.query = st.session_state.inputBar

#用户输入栏
def user_input():
    chatInput = st.container()
    with chatInput:
        textInput,audioInput = st.columns([99,1])
        with textInput:
            with st.form(key="chat_input",clear_on_submit=True,border=False):
                Input, submit = st.columns([90,10])
                with Input:
                    st.text_input("##### 想问点什么? :blush:",key="inputBar",value=st.session_state.input + st.session_state.voice_input)
                    st.session_state.input = st.session_state.inputBar
                    st.session_state.voice_input = ""
                with submit:
                    st.write(" ")
                    st.write(" ")
                    st.write(" ")
                    st.form_submit_button(label=":heavy_check_mark:", on_click=Submit)
                    
        with audioInput:
            st.write(" ")
            st.write(" ")
            st.write(" ")
            if st.session_state.audio == 0:
                if st.button(":microphone:"):
                    api.start_audio()
                    st.session_state.audio = 1
                    st.rerun()
            else:
                if st.button(":black_square_for_stop:"):
                    st.session_state.voice_input = api.stop_audio()
                    st.session_state.audio = 0
                    st.rerun()
    chatInput.float("bottom: 5px;")