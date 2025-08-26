import gradio as gr
from langchain_core.messages import HumanMessage
from chatbot import chatbot  # compiled graph

def chat_fn(message, history):
    try:
        # Send only the NEW user message; the checkpointer keeps the rest
        response = chatbot.invoke(
            {"messages": [HumanMessage(content=message)]},
            config={"configurable": {"thread_id": "chat-session-1"}}
        )

        # Get the latest AI reply from the returned state
        messages = response["messages"]
        # Prefer the last AI message explicitly:
        ai = next((m for m in reversed(messages) if getattr(m, "type", "") == "ai"), None)
        bot_text = ai.content if ai else messages[-1].content
        return bot_text

    except Exception as e:
        return f"⚠️ Error: {e}"

demo = gr.ChatInterface(
    fn=chat_fn,
    title="LangGraph 🤖 Chatbot",
    description="A simple chatbot powered by LangGraph + Groq LLM",
    theme="soft",
    type="messages"  # avoids the deprecation warning
)

if __name__ == "__main__":
    demo.launch()
