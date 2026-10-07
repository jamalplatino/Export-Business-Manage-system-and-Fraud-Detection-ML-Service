from typing import Annotated, TypedDict
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
import pprint, os, httpx, json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langgraph.store.memory import InMemoryStore  
from langgraph.checkpoint.memory import InMemorySaver  
from langgraph.types import interrupt, Command
from datetime import datetime, timezone
from pathlib import Path

AUDIT_LOG_PATH = Path(__file__).parent / "email_audit.log"

def log_email(recipient: str, subject: str, body: str, status: str):
    """Append one JSON line per email event. status: 'sent' | 'denied' | 'failed'."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "status": status,
    }
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# Module-level: loaded once when the script starts
_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    encode_kwargs={"normalize_embeddings": True},
)
_vector_store = QdrantVectorStore.from_existing_collection(
    embedding=_embeddings,
    collection_name="documents",
    url="http://localhost:6333",
)

checkpointer = InMemorySaver()
store = InMemoryStore()


@tool
def rag_search(question: str) -> str:
    """Search documents about refunds, shipping, returns, or machine learning concepts."""
    try:
        results = _vector_store.similarity_search(question, k=3, timeout=30)
        return "\n\n".join(d.page_content for d in results)
    except Exception as e:
        return f"Search failed: {type(e).__name__}: {e}. Please try again or rephrase the question."


@tool
def fraud_check(
    log_amount: float,
    hour: int,
    dow: int,
    cust_avg: float,
    cust_count: int,
    ratio_to_avg: float,
) -> str:
    """Score a payment for fraud using the ML model."""
    try:
        resp = httpx.post(
            "http://127.0.0.1:8002/score",
            json={
                "log_amount": log_amount,
                "hour": hour,
                "dow": dow,
                "cust_avg": cust_avg,
                "cust_count": cust_count,
                "ratio_to_avg": ratio_to_avg,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return f"Fraud probability: {data['probability']}, flagged: {data['is_fraud']}"
    except Exception as e:
        return f"Failed to check fraud: {e}"

ALLOWED_DOMAINS = {"gmail.com", "update.ng"}

@tool
def send_mail(to: str, subject: str, body: str) -> str:
    """Send an email to the specified recipient with the given subject and body."""
    domain = to.split("@")[-1].lower()
    if domain not in ALLOWED_DOMAINS:
        return f"Refused: {to} is not on the allowlist."
    
    import smtplib
    from email.message import EmailMessage

    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    smtp_host = os.environ.get("SMTP_HOST", "mail.update.ng")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    msg = EmailMessage()
    msg['From'] = 'test@update.ng'
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()  # Secure the connection
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
    return f"Email sent to {to} with subject '{subject}'"


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

llm = ChatOllama(model="llama3.2:3b", temperature=0)
llm_with_tools = llm.bind_tools([rag_search, fraud_check, send_mail])

def agent_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def route_after_agent(state: AgentState) -> str:
    last = state["messages"][-1]
    if not getattr(last, "tool_calls", None):
        return "end"

    # Does any tool call require approval?
    needs_approval = any(tc["name"] == "send_mail" for tc in last.tool_calls)
    if needs_approval:
        return "approve"

    return "tools"


def approve_email_node(state: AgentState):
    """Pause for human approval before sending email."""
    last = state["messages"][-1]
    email_call = next(
        (tc for tc in last.tool_calls if tc["name"] == "send_mail"),
        None,
    )
    if email_call is None:
        return {"messages": []}

    # PAUSE — control returns to the caller
    decision = interrupt({
        "type": "email_approval",
        "tool_call_id": email_call["id"],
        "args": email_call["args"],
    })

    approved = decision.get("approved", False)

    if not approved:
        # Log the denial
        log_email(recipient=email_call["args"]["to"],
                  subject=email_call["args"]["subject"],
                  body=email_call["args"]["body"],
                  status="denied")
        return {
            "messages": [
                ToolMessage(
                    content="Email cancelled by user.",
                    tool_call_id=email_call["id"],
                )
            ]
        }

    # Approved — actually send
    result = send_mail.invoke(email_call["args"])
    log_email(recipient=email_call["args"]["to"],
              subject=email_call["args"]["subject"],
              body=email_call["args"]["body"],
              status="sent")
    return {
        "messages": [
            ToolMessage(content=result, tool_call_id=email_call["id"])
        ]
    }


graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode([rag_search, fraud_check]))   # send_mail removed
graph.add_node("approve", approve_email_node)

graph.set_entry_point("agent")

graph.add_conditional_edges(
    "agent",
    route_after_agent,
    {
        "tools": "tools",
        "approve": "approve",
        "end": END,
    },
)

graph.add_edge("tools", "agent")
graph.add_edge("approve", "agent")   # after approval/denial, back to agent

app = graph.compile(checkpointer=checkpointer)


questions = [
    "How long do refunds take?",
    "What is deep learning good at?",
    "Is a payment of $10000 at 5am on Tuesday, by a customer who averages $100, with 10 past payments and a ratio of 50, fraudulent?",
    "send an email to jamalplatino3@gmail.com with subject 'Test' and body 'This is a test email.'",
]

for question in questions:
    print(f"\nQ: {question}")
    config = {"configurable": {"thread_id": question}}

    result = app.invoke(
        {"messages": [HumanMessage(content=question)]},
        config=config,
    )

    # Did the graph pause?
    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print(f"\n⚠ Approval required for email:")
        print(f"   To: {payload['args']['to']}")
        print(f"   Subject: {payload['args']['subject']}")
        print(f"   Body: {payload['args']['body']}")

        answer = input("   Approve? (y/n): ").strip().lower()
        approved = answer == "y"

        result = app.invoke(
            Command(resume={"approved": approved}),
            config=config,
        )

    # Graph done — print final message
    print("A:", result["messages"][-1].content)