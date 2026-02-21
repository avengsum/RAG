import json 
import os
from config import MODEL
from src.retrieval import Retriever
from src.generation import RagGenerator
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

retriever = Retriever()
generator = RagGenerator()

llm = ChatGoogleGenerativeAI(model=MODEL)

def get_score(ques,correct_ans,rag_ans):
  ## so we will create a prompt it will have question rag answer and correct ans so then the llm we rate our score or give our rag a score

  prompt = f"""
    Grade the RAG system's answer based on the Ground Truth.
    Scale: 
    5: Perfect, matches ground truth.
    3: Partially correct, missing details.
    1: Completely wrong or hallucinated.
    
    Question: {ques}
    Ground Truth: {correct_ans}
    RAG Answer: {rag_ans}
    
    Output JSON: {{"score": <int>, "reason": "<string>"}}
    """
  res = llm.invoke(prompt)
  if isinstance(res.content, list):
    response_text = "".join([block.get("text", "") for block in res.content if "text" in block])
  else:
    response_text = str(res.content)

  clean_content = response_text.replace('```json', '').replace('```', '').strip()
        
  return json.loads(clean_content)

with open("data/eval/eval.json") as f:
  test_set = json.load(f)


results = []

for item in test_set:
  print(f"Testing: {item['question'][:20]}")

  searchDoc = retriever.hybrid_search(item["question"])

  rag_answer = generator.ai_response(item["question"],searchDoc)

  judgeScore = get_score(item["question"],item["correct_ans"],rag_answer)

  ## so we will save our score to avg it

  results.append({**item, "rag_answer": rag_answer, **judgeScore})


avgScore = sum(r['score'] for r in results) / len(results)

print(f"FINAL RAG SCORE: {avgScore}/5.0")


  