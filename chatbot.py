from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages

load_dotenv()
llm = ChatGroq(model="llama3-8b-8192", temperature=0.0)

class Chatbot(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: Chatbot):
    messages = state["messages"]
    response = llm.invoke(messages)           # returns an AIMessage
    return {"messages": messages + [response]}  # append, don’t replace

checkpointer = InMemorySaver()

graph = StateGraph(Chatbot)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

