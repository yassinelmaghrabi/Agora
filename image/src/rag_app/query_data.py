import argparse
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama

from src.rag_app.get_embedding_function import get_embedding_function

BOOK_DB = "./src/data/bookchroma"
GREEK_DB = "./src/data/greekchroma"


PROMPT_TEMPLATE = """
You are a helpful and knowledgeable assistant specializing in ancient Greek texts.

Use the information provided in the following context to answer the question. use your outside knowledge of greek vocabulary. If the answer is not clearly supported by the context, state that explicitly.
Do Not Hallucinate.
Context from the book:
{book_context}

Context from ancient Greek sources:
{greek_context}

---

Based on the above context, answer the following question as precisely and thoroughly as possible:

{question}
"""


def main():
    # Create CLI.
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text
    query_rag(query_text)


def query_rag(query_text: str):
    # Prepare the DB.
    embedding_function = get_embedding_function()
    book_db = Chroma(persist_directory=BOOK_DB, embedding_function=embedding_function)
    greek_db = Chroma(persist_directory=GREEK_DB, embedding_function=embedding_function)
    # Search the DB.
    book_results = book_db.similarity_search_with_score(query_text, k=5)
    greek_results = greek_db.similarity_search_with_score(query_text, k=5)

    book_context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in book_results])
    greek_context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in greek_results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(book_context=book_context_text,greek_context=greek_context_text, question=query_text)
    

    model = Ollama(model="llama2")
    response_text = model.invoke(prompt)

    sources = [f"{doc.metadata.get("source", None)} - Score: {_score}" for doc, _score in greek_results]
    formatted_response = (
    f"\033[94mQuestion:\033[0m {query_text}\n"
    f"\033[92mResponse:\033[0m {response_text}\n"
    f"\033[93mSources:\033[0m {sources}"
)

    print(formatted_response)
    return response_text


if __name__ == "__main__":
    main()
