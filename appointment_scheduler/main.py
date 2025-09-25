import streamlit as st 
from PIL import Image
# from markrag import get_answer
from agents import agent_executor
from dotenv import load_dotenv

load_dotenv()



def main() -> None:

    icon = Image.open("D:/VRNeXGen/virtual assistance/virtual_assistance_project/logo.png")

    st.set_page_config(
        page_title = "VRNeXGen",
        page_icon = icon,
        layout = "centered"
    )

    # intialize the session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # print("Initial chat history:", st.session_state["chat_history"])

    
    st.markdown(
        """
        <h1 style='font-size: 46px; display: flex; align-items: center;'>
            <span style='color:#800000;'>VR</span>NeXGen
        </h1>
        <h8>Modernize 🔺 Automate 🔺 Innovate</h8>
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # st.sidebar.write("All chats")
    
    
    # Display chat history
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.chat_message("user").write(chat["content"])
        else:
            st.chat_message("assistant").write(chat["content"])
    
    
    
    user_input = st.chat_input("Say something", key = "input_key")
    # check user entered the input.
    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        
        # Here you would typically call your chatbot API or function
        response = agent_executor(
            {
                "input": user_input
            }
        )
        
        st.session_state["chat_history"].append({"role": "assistant", "content": response["output"]})
        if response:
            st.chat_message("assistant").write(response["output"])

    # print("Chat history:", st.session_state.chat_history)




if __name__ == "__main__":
    main()