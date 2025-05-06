import argparse
import os
import shutil

from langchain.document_loaders.pdf import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain.vectorstores.chroma import Chroma
from src.GTE.GTE import greek_text_from_text

DATA_PATH = "./src/data/source/"
BOOK_DB = "./src/data/bookchroma"
GREEK_DB = "./src/data/greekchroma"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    if args.reset:
        print("✨ Clearing Database")
        clear_database()

    documents = load_documents()
    chunks = split_documents(documents)
    add_to_book(chunks)
    add_to_greek(documents[0])

def load_documents():
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()

def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def add_to_book(chunks: list[Document]):
    book_db = Chroma(
        persist_directory=BOOK_DB, embedding_function=None #TODO: embedding_function 
    )
    
    chunks_with_ids = calculate_chunk_ids(chunks)

    # Add or Update the documents.
    existing_items = book_db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that don't exist in the DB.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        book_db.add_documents(new_chunks, ids=new_chunk_ids)
        book_db.persist()
    else:
        print("✅ No new documents to add")
def add_to_greek(text: Document):
    if os.path.exists(GREEK_DB):
        shutil.rmtree(GREEK_DB)
    greek_db = Chroma(
        persist_directory=GREEK_DB, embedding_function=None #TODO: embedding_function
    )
    chunks = greek_text_from_text(text.page_content)
    new_chunks = []
    for chunk in chunks:
        new_chunks.append(Document(
            page_content=chunk["text"],
            metadata={"source": chunk["clause"]}
        ))
    if len(new_chunks):
            print(f"👉 Adding new documents: {len(new_chunks)}")
            greek_db.persist()


def calculate_chunk_ids(chunks):


    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id

    return chunks


def clear_database():
    if os.path.exists(BOOK_DB):
        shutil.rmtree(BOOK_DB)
    if os.path.exists(GREEK_DB):
        shutil.rmtree(GREEK_DB)
