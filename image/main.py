from src.rag_app.query_data import query_rag
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, nargs="?", default="", help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text

    if query_text:  # If a query text is provided, use it
        query_rag(query_text)
    else:  # If no query text is provided, test all predefined queries
        test_queries = [
            "Search for the different types of relative clauses in ancient Greek texts.",
            "Identify the syntactical function of participial clauses in Classical Greek literature.",
            "Find examples of indirect speech clauses used in ancient Greek drama.",
            "What are the most common ways conditional clauses are expressed in ancient Greek texts?",
            "Analyze the use of temporal clauses in the works of Herodotus.",
            "Give examples of causative clauses found in the writings of Aristotle.",
            "What is the role of infinitival clauses in Homer's 'Iliad'?",
            "Identify the use of subordinate clauses in Plato's dialogues.",
            "Find passages where causal and purpose clauses occur together in ancient Greek philosophical texts.",
            "Tell me about marriage clauses and the vocabulary they use"
        ]
        
        for query in test_queries:
            query_rag(query)

   
if __name__ == "__main__":
    main()
