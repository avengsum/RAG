import json
import os
import pickle
import random
import sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from config import BM25_PATH, MODEL
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

with open(BM25_PATH , "rb") as f:
  data = pickle.load(f)
  docs = data["doc_map"]

llm = ChatGoogleGenerativeAI(model=MODEL)

def create_qna(chunk):
  prompt = f"""
    Based on this text, write one difficult question and its correct answer.
    Output only a JSON object with 'question' and 'correct_ans' keys.
    
    Text: {chunk}
    """
  
  res = llm.invoke(prompt)

  if isinstance(res.content, list):
    response_text = "".join([block.get("text", "") for block in res.content if "text" in block])
  else:
    response_text = str(res.content)

  clean_content = response_text.replace('```json', '').replace('```', '').strip()
        
  return json.loads(clean_content)

test_set = []

## so we get 10 random chunks and generate qna with llm
samples = random.sample(docs,10)

for i, doc in enumerate(samples):
  try:
    print(f"[{i+1}/10] Generating question...")

    ques = create_qna(doc.page_content)

    ques["actual_content"] = doc.page_content

    test_set.append(ques)

  except Exception as e:
    print(f"   ⚠️ Skipping a chunk due to error: {e}")

    continue

## so we will save question in this folder
os.makedirs("data/eval", exist_ok=True)

with open("data/eval/eval.json","w") as f:
  ## so in json with 4 spaces 
  json.dump(test_set,f,indent=4)
