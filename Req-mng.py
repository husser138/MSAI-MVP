import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import streamlit as st

load_dotenv()

openai_endpoint = os.getenv("OPENAI_ENDPOINT")
openai_api_key = os.getenv("OPENAI_API_KEY")
chat_model = os.getenv("CHAT_MODEL")
embedding_model = os.getenv("EMBEDDING_MODEL")
search_endpoint=os.getenv("SEARCH_ENDPOINT")
search_api_key=os.getenv("SEARCH_API_KEY")
index_name = os.getenv("INDEX_NAME")


# 환경 변수 로드
# 제목 설정
st.title("고객 요구사항 Portal")

chat_client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=openai_endpoint,
    api_key=openai_api_key
)

st.title("Margie's Travel Assistant")
st.write("Ask your travel-related questions below:")

st.button("RAG Parameters1")
st.button("RAG Parameters2")
st.button("RAG Parameters3")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "You are a requirements manager AI responsible for managing project schedules and monitoring the workloads of analysts and developers. When a new requirement is received, you assign the task to the analyst and developer with the lightest workload"
        },
    ]

# Display chat history
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

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
                    "embedding_dependency": {
                        "type": "deployment_name",
                        "deployment_name": embedding_model,
                    },
                }
            }
        ],
    }
    # 버튼 정의

    # Submit the chat request with RAG parameters
    response = chat_client.chat.completions.create(
        model=chat_model,
        messages=messages,
        extra_body=rag_params
    )

    completion = response.choices[0].message.content
    return completion

# Handle user input
if user_input := st.chat_input("Enter your question: "):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    with st.spinner("응답을 기다리는 중..."):
        response = get_openai_response(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)