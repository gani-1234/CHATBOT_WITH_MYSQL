import sqlite3

import streamlit as st
from pathlib import Path
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.sql_database import SQLDatabase
from sqlalchemy import create_engine
from langchain_groq import ChatGroq
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

import os
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="CHATBOT")
st.title("LANGCHAIN CHATBOT")

LOCALDB="USE_LOCALDB"
MYSQL="USE_MYSQL"

# radio_option=[
#     "connect to your local MYSQL Databse",
#     # "use SQLITE3 DATABASE - Student.db"
# ]

# selected_option=st.sidebar.radio(label="choose database",options=radio_option)

# if radio_option.index(selected_option)==0:
#     db_uri=MYSQL
#     mysql_host = st.sidebar.text_input("Enter your DB host", placeholder="localhost")
#     mysql_user = st.sidebar.text_input("Enter your username", placeholder="root")
#     mysql_password = st.sidebar.text_input("Enter your password", type="password")
#     mysql_db = st.sidebar.text_input("Enter your database name", placeholder="test_db")

# else:
#     db_uri=LOCALDB

st.sidebar.title("MYSQL")
db_uri=MYSQL
mysql_host = st.sidebar.text_input("Enter your DB host", placeholder="localhost")
mysql_user = st.sidebar.text_input("Enter your username", placeholder="root")
mysql_password = st.sidebar.text_input("Enter your password", type="password")
mysql_db = st.sidebar.text_input("Enter your database name", placeholder="test_db")

api_key=st.sidebar.text_input("Enter your Groq api key",placeholder="Groq api",type="password")

if not api_key:
    st.info("please enter groq api_key")
    st.stop()

if not db_uri:
    st.info("Provide database information and URI")

# LLM model 
llm=ChatGroq(groq_api_key=api_key,model_name="Llama3-8b-8192",streaming=True)

@st.cache_resource(ttl=3600)
def configure_db(db_uri, mysql_host=None, mysql_user=None, mysql_password=None, mysql_db=None):
    if db_uri == LOCALDB:
        db_path = Path("student.db").absolute()  # Removed __file__
        engine = create_engine(f"sqlite:///{db_path}")  # Corrected SQLite URI
        return SQLDatabase(engine)
    elif db_uri == MYSQL:
        if not (mysql_db and mysql_host and mysql_user and mysql_password):  # Corrected tuple check
            st.error("Provide all required MySQL details")
            st.stop()
        engine = create_engine(f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}")
        return SQLDatabase(engine)  # Used SQLDatabase instead of SQLDatabaseToolkit

if db_uri==MYSQL:
    db=configure_db(db_uri,mysql_host,mysql_user,mysql_password,mysql_db)
else:
    db=configure_db(db_uri)

# create Toolkit

toolkit=SQLDatabaseToolkit(db=db,llm=llm)

agent=create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)


if "messages" not in st.session_state or st.sidebar.button("clear chat history"):
    st.session_state["messages"]=[{"role":"assistant","content":"How can i help you?"}]
for msg in st.session_state.messages :
    st.chat_message(msg["role"]).write(msg["content"])

user_query=st.chat_input(placeholder="Ask anything from database")

if user_query:
    st.session_state.messages.append({"role":"user","content":user_query})
    st.chat_message("user").write(user_query)
    with st.chat_message("assistant"):
        streamlit_callbacks = StreamlitCallbackHandler(st.container())
        response = agent.run(user_query, callbacks=[streamlit_callbacks])
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.write(response)

