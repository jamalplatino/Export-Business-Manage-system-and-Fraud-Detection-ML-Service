from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from typing import List


llm = ChatOllama(model="llama3.2:3b", temperature=0)
# Fake documents — later these come from Qdrant
docs = [
    Document(page_content="Refunds are processed within 14 business days from the date of approval.",
             metadata={"source": "policy.pdf"}),
    Document(page_content="Shipping takes 3-5 business days for domestic orders.",
             metadata={"source": "shipping.pdf"}),
    Document(page_content="Returns must be requested within 30 days of delivery.",
             metadata={"source": "returns.pdf"}),
]


prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Answer only from the context below. "
               "If the context doesn't contain the answer, say you don't know."),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])


print("Documents loaded:")
for d in docs:
    print(f"  - {d.page_content[:60]}...")



class SimpleRetriever(BaseRetriever):
    docs: List[Document]

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> List[Document]:
        query_words = set(query.lower().split())
        scored = []
        for doc in self.docs:
            doc_words = set(doc.page_content.lower().split())
            score = len(query_words & doc_words)
            scored.append((score, doc))
        scored.sort(key=lambda x: -x[0])
        return [doc for _, doc in scored[:2]]


retriever = SimpleRetriever(docs=docs)

results = retriever.invoke("How long do refunds take?")
print("\nRetrieved:")
for r in results:
    print(f"  - {r.page_content}")



from langchain_core.runnables import RunnablePassthrough

def format_docs(retrieved_docs: List[Document]) -> str:
    return "\n\n".join(d.page_content for d in retrieved_docs)


chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

answer = chain.invoke("How long do refunds take?")
print("\nAnswer:")
print(answer)