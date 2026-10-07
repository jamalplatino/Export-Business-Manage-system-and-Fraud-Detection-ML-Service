from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from typing import List

# --- Embeddings + vector store (already working) ---
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    encode_kwargs={"normalize_embeddings": True},
)

vector_store = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    collection_name="documents",
    url="http://localhost:6333",
)

# --- Retriever ---
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3},
)

# --- LLM ---
llm = ChatOllama(model="llama3.2:3b", temperature=0)

# --- Prompt ---
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Answer only from the context below. "
               "If the context doesn't contain the answer, say you don't know."),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

# --- Format retrieved docs into a single string ---
def format_docs(docs: List[Document]) -> str:
    return "\n\n".join(d.page_content for d in docs)

# --- The chain ---
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# --- Ask questions ---
questions = [
    "How long do refunds take?",
    "How long does shipping take?",
    "What is deep learning good at?",
]

for q in questions:
    print(f"\nQ: {q}")
    print(f"A: {chain.invoke(q)}")