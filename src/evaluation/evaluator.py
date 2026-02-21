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
total_hits = 0

for i, item in enumerate(test_set):
  print(f"{i+1} Testing: {item['question'][:20]}")

  searchDoc = retriever.hybrid_search(item["question"])

  ## so we are checking if the doc we get appwar in our result
  is_hit = False

  ## so this actual conternt we added in our eval.json
  actual_content = item["actual_content"].strip()[:100]

  for doc in searchDoc:
    if actual_content in doc.page_content.strip():
      is_hit = True
      break
  
  if is_hit:
    total_hits +=1

  rag_answer = generator.ai_response(item["question"],searchDoc)

  judgeScore = get_score(item["question"],item["correct_ans"],rag_answer)

  ## so we will save our score to avg it

  results.append({
    "question": item["question"],
    "correct_answer": item["correct_ans"],
    "rag_answer": rag_answer,
    "retrieval_hit": is_hit,
    "score": judgeScore['score'],   
    "reason": judgeScore['reason']
  })


avgScore = sum(r['score'] for r in results) / len(results)
hit_rate = (total_hits / len(test_set)) * 100

print(f"FINAL RAG SCORE: {avgScore}/5.0")
print(f"🎯 Retrieval Hit Rate:    {hit_rate:.1f}%")