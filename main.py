import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.retrieval import Retriever
from src.generation import RagGenerator

def main():
    print("STARTING RAG SYSTEM...")
    try:
        retriever = Retriever()
        generator = RagGenerator()
        print("\n System Ready! Type 'exit' to quit.\n")
    except Exception as e:
        print(f"Starting Failed: {e}")
        return

## taking user query
    while True:
        user_query = input("🔎 Enter Query: ").strip()
        
        if user_query.lower() in ['exit', 'quit']:
            print("Bye Bye...")
            break
        
        if not user_query:
            continue

        docs = retriever.retrieval(user_query)
        
        if not docs:
            print("⚠️ No relevant documents found.")
            continue

        # GENERATION 
        print(" Generating Answer...")
        AI_ans = generator.ai_response(user_query, docs)

        # AI RESPONSE
        print("AI ANSWER:")
        print(AI_ans)

if __name__ == "__main__":
    main()