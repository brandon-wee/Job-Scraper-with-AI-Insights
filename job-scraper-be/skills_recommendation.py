import os
import bs4
import pandas as pd
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document
# from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain import hub
from typing import List
from langgraph.graph import START, StateGraph
from dotenv import load_dotenv
import faiss
from uuid import uuid4
import requests
from bs4 import BeautifulSoup
import PyPDF2, io, base64

load_dotenv()

llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY"), temperature=0.7)
# embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = FAISS(embedding_function=embeddings,
                     index = faiss.IndexFlatIP(len(embeddings.embed_query("Hello World!"))),
                     docstore=InMemoryDocstore(),
                     index_to_docstore_id={}
                    )


class State(TypedDict):
    question: str
    context: List   # List of Document objects returned from retrieval
    answer: str

def preprocess(file):
    file = [line.strip() for line in file.splitlines() if line.strip()]

    occupation_specific_information_count = 0
    training_n_credentials = False
    filtered_file = [file[0]]
    for line in file:
        if line == "Occupation-Specific Information":
            occupation_specific_information_count += 1
        
        if occupation_specific_information_count != 2:
            continue
        
        if line == "Related occupations":
            continue
        
        if line == "Training & Credentials":
            training_n_credentials = True
            continue

        if training_n_credentials:
            if line == "back to top":
                training_n_credentials = False
            
            continue

        if line == "Workforce Characteristics":
            break

        filtered_file.append(line.replace("—", "-").replace("”", "'").replace("“", "'").replace("’", "'"))
    
    print(file[0] + " has been processed.")
    return "\n".join(filtered_file), file[0]

def custom_web_loader(doc_links):
    docs = []
    for link in doc_links:
        response = requests.get(link)
        soup = BeautifulSoup(response.content, 'html.parser')
        processed_text, title = preprocess(soup.get_text())
        new_doc = Document(page_content=processed_text, metadata={"link": link, "title": title, "language": "en"})
        docs.append(new_doc)

    return docs

def retrieve(state):
    keyword = state["question"].split('"')[1]
    print(f"Retrieving documents for keyword: {keyword}")
    retrieved_docs = vector_store.similarity_search(keyword, k=2)
    print(retrieved_docs)
    return {"context": retrieved_docs}

def generate(state):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}

def build_graph():
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()
    return graph

def decode_pdf(pdf_data: str) -> bytes:
    """Decodes JSON Base64 string back into PDF bytes."""
    pdf_bytes = base64.b64decode(pdf_data)  # Decode Base64 back to bytes
    return io.BytesIO(pdf_bytes)

def read_pdf(resume_bytes):
    pdf = PyPDF2.PdfReader(decode_pdf(resume_bytes))
    text = ""
    for page in pdf.pages:
            text += page.extract_text() + '\n'
    return text

df = pd.read_csv("All_Occupations.csv")
doc_code = df["Code"].tolist()
doc_links = (f"https://www.onetonline.org/link/summary/{code}" for code in doc_code)

index_path = "faiss_index"

if os.path.exists(index_path):
    print("Loading index...")
    vector_store = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
else:
    
    print("Indexing documents...")
    docs = custom_web_loader(doc_links)
    uuids = [str(uuid4()) for _ in range(len(docs))]
    print(f"Indexed {len(docs)} documents.")
    # text_splitter = RecursiveCharacterTextSplitter()
    # all_splits = text_splitter.split_documents(docs)

    batch_size = 30
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i:i + batch_size]
        batch_uuids = uuids[i:i + batch_size]
        vector_store.add_documents(documents=batch_docs, ids=batch_uuids)

    vector_store.save_local(index_path)
# Define RAG pipeline
prompt = hub.pull("rlm/rag-prompt")

def get_skills_recommendation(job_occupation, resume_bytes):
    graph = build_graph()
    question = """You are an assistant that will help a job seeker identify the skills they need to improve to better match their desired job occupation.
You will now do the following:
- Analyze the skills required for the specified job occupation.
- Compare these skills with the skills listed in the user's resume.
- Recommend which skills the user should focus on improving to align with the job requirements.
- Provide a list of recommendations, with each recommendation including a brief explanation of its importance.
- Use '-' at the beginning of each line for each recommendation.
- If you cannot find the skills required for the specified occupation, find the skills for similar occupations and mention this in your output.
- Do not include your thought process in the output.

The job occupation you are analyzing is "{job_occupation}".
The user's resume skills are as follows: 
{resume_contents}.
"""
    result = graph.invoke({"question": question.format(job_occupation=job_occupation, resume_contents=read_pdf(resume_bytes))})
    context_metadata = [doc.metadata for doc in result["context"]]
    return result["answer"], context_metadata


if __name__ == "__main__":
    occupation = '"Software Developers"'
    print(retrieve({"question": occupation}))
    # print(get_skills_recommendation(occupation, "Python, Machine Learning, Data Analysis, Communication"))