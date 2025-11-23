from __future__ import annotations

from langchain.prompts import PromptTemplate

BASE_INSTRUCTIONS = (
    "You are a professional AI assistant. Use the knowledge base context below as your primary source. "
    "When the context does not fully address the question, supplement it with your own general knowledge. "
    "Always provide a confident, well-structured answer and close with a concise summary."
)

STUFF_PROMPT = PromptTemplate(
    input_variables=["context", "question", "instructions"],
    template=(
    "{instructions}\n\n"
    "<Knowledge Base>\n{context}\n</Knowledge Base>\n\n"
    "Question: {question}\n"
    "Respond in English with a direct answer and add bullet points when helpful."
    ),
).partial(instructions=BASE_INSTRUCTIONS)

MAP_PROMPT = PromptTemplate(
    input_variables=["context", "question", "instructions"],
    template=(
        "{instructions}\n\n"
    "The following are knowledge snippets. Extract the points that relate to the question.\n"
    "<Snippets>\n{context}\n</Snippets>\n\n"
    "Question: {question}\n"
    "List the key information that addresses the question."
    ),
).partial(instructions=BASE_INSTRUCTIONS)

COMBINE_PROMPT = PromptTemplate(
    input_variables=["context", "question", "instructions"],
    template=(
        "{instructions}\n\n"
    "You have collected several summaries:\n"
    "<KeyPoints>\n{context}\n</KeyPoints>\n\n"
    "Answer the question using these points: {question}\n"
    "Add general knowledge when helpful and deliver a complete answer in English."
    ),
).partial(instructions=BASE_INSTRUCTIONS)
