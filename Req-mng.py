import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from openai import AzureOpenAI  

#from langchain_community.chat_models import ChatOpenAI
#from langchain.schema import HumanMessage

# 환경 변수 설정
load_dotenv()
# 환경 변수에서 OpenAI 및 Azure 설정 불러오기
openai_endpoint = os.getenv("OPENAI_ENDPOINT")
openai_api_key = os.getenv("OPENAI_API_KEY")
chat_model = os.getenv("CHAT_MODEL")
embedding_model = os.getenv("EMBEDDING_MODEL")
search_endpoint=os.getenv("SEARCH_ENDPOINT")
search_api_key=os.getenv("SEARCH_API_KEY")
index_name = os.getenv("INDEX_NAME")     


#print("openai_end:", openai_endpoint)
#print("search_endpoint:", search_endpoint)
#print("chat_model:", chat_model)
print("embedding_model:", embedding_model)


openai_endpoint = "https://hsw-openai1.openai.azure.com/"
openai_api_key = "DQ6cfI9qSnjkiozlfWu55qiffjZeAmzo6Jy6UM9T7BgGSVvUFJY5JQQJ99BFACMsfrFXJ3w3AAABACOG6PI1"
chat_model = "hsw-4o-mini"
embedding_model = "hsw-embedding-3-small"
search_endpoint="https://hsw-aisearch.search.windows.net"
search_api_key="YcMqjxzjE58KpysnSvN3Wz2yX9nWdkY32p5Ww2L7CQAzSeBOgw97"
index_name = "hsw-rag-1"
#index_name = "hswazureblob-index"

print("openai_end:", openai_endpoint)
print("search_endpoint:", search_endpoint)
print("chat_model:", chat_model)
print("index_name", index_name)
print("embedding_model:", embedding_model)


# 📌 페이지 설정 (가장 첫 줄에서 호출)
st.set_page_config(page_title="요구사항 & 개발자 통계",layout="wide")

# 엑셀 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_excel("요구사항.xlsx")
    return df

df = load_data()

st.header("📊 요구사항 통계 & 개발자별 진행률")

# 상단: 요구사항 통계 및 개발자별 통계 (가로 배치)
col1, col2, col3, col4 = st.columns(4, gap="small")
#col1, col2 = st.columns(2, gap="small")
#col3, col4 = st.columns(2, gap="small")
# 그래프 크기 설정
graph_width = 300
graph_height = 400

# 요구사항 통계 및 개발자별 통계
with col1:
    st.subheader("📌 요구사항 처리 상태별 건수")
    status_counts = df["처리상태"].value_counts()
    st.bar_chart(status_counts,width=graph_width, height=graph_height,use_container_width=False)

with col2:
    st.subheader("👨‍💻 서비스별 미접수 내역")
    requst_status = df[df["처리상태"] == "1.요청"]
    requst_counts = requst_status["고객서비스"].value_counts()
    st.bar_chart(requst_counts,width=graph_width, height=graph_height,use_container_width=False)

with col3:
    st.subheader("👨‍💻 분석가별 분석 건수")
    received = df[df["처리상태"] == "2.접수"]
    analyst_counts = received["분석가"].value_counts()
    st.bar_chart(analyst_counts,width=graph_width, height=graph_height,use_container_width=False)

with col4:
    st.subheader("👨‍💻 개발자별 개발중 건수")
    dev_in_progress = df[df["처리상태"] == "3.개발중"]
    developer_counts = dev_in_progress["개발자"].value_counts()
    st.bar_chart(developer_counts,width=graph_width, height=graph_height,use_container_width=False)


# 챗봇 설정
chat_client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=openai_endpoint,
    api_key=openai_api_key
)

#chat 화면

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "요구사항은 요청이 오면 요청단계에서 분석가가 접수하면 접수단계에서 개발자가 개발중이면 개발단계에서 요구사항이 완료되면 완료 단계이며, 사용자의 물음에 요구사항 데이터를 기준으로 도움을 주는 챗봇이고 모르면 보른다고 답 드리겠습니다."
        },
    ]

# Display chat history
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"],)

st.subheader("안녕하세요! 요구사항 관리 챗봇입니다. 무엇을 도와드릴까요?")

def get_openai_response(messages):
    # Additional parameters to apply RAG pattern using the AI Search index
    rag_params = {
        "data_sources": [
            {
                # he following params are used to search the index
                "type": "azure_search",
                "parameters": {
                    "endpoint": search_endpoint,
                    "index_name": index_name,
                    "authentication": {
                        "type": "api_key",
                        "key": search_api_key,                
                    },
                    # The following params are used to vectorize the query
                    "query_type": "vector",
                    #"vectorize_query": True,                                        
                    "embedding_dependency": {
                        "type": "deployment_name",
                        "deployment_name": embedding_model,
                    },
                }
            }
        ],
    }
    
    response = chat_client.chat.completions.create(
        model=chat_model,
        messages=messages,
        extra_body=rag_params
    )

    completion = response.choices[0].message.content
    return completion


if user_input := st.chat_input("문의 사항을 입력해주세요."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    with st.spinner("응답을 기다리는 중..."):
        response = get_openai_response(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)
