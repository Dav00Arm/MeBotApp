from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os

embedding = OpenAIEmbeddings()
def embed_file(filename):
    file_path = os.path.join("data/", filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {filename} not found in data/")
    
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_text(content)
    
    print(f"Embedding content from {filename}...")
    vectordb = Chroma.from_texts(splits, embedding=embedding, persist_directory="data/chroma/")
    vectordb.persist()
    print(f"Embedding complete for {filename}.")
    return vectordb

# Load vector database
def load_vectordb(persist_directory):
    if not os.path.exists(persist_directory) or not os.listdir(persist_directory):
        raise FileNotFoundError(f"No embeddings found in {persist_directory}. Please embed files first.")
    return Chroma(persist_directory=persist_directory, embedding_function=embedding)