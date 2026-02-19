import base64
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict, Any
from langchain_core.documents import Document

from config import MODEL

load_dotenv()

class RagGenerator:
  def __init__(self):
    print("----- Gerneration started -----")
    self.model = ChatGoogleGenerativeAI(MODEL)
  
  def _prompt_content(self,query:str,docs:List[Document]) -> List[Any]:
    ## so in prompt we will give text strings images so we will desingn in that way

    prompt = [
      "You are an expert AI assistant. Answer the user's question using the provided context.",
            "The context contains Text, Tables (in HTML), and Images.",
            "Use ALL available data to answer accurately.",
            "If the answer is found in an image or table, explicitly mention it.",
            "Cite the source document name where possible.",
            "\n--- START OF CONTEXT ---\n"
    ]

    for i, doc in enumerate(docs):
      ## sorce of document
      src = doc.metadata.get("source","Unknown Source")
      prompt.append(f"\n Document {i+1} (: {src})")

      ## so raw text over summary

      raw_content = doc.metadata.get("original_text", doc.page_content)

      prompt.append(f"TEXT CONTENT : \n {raw_content}")

      if "tables_html" in doc.metadata:
        try:
          tables = json.loads(doc.metadata["tables_html"])
          if tables:
            prompt.append("TABLES:")
            for t in tables:
              prompt.append(t) 
        
        except:
          pass
      
      if "images_base64" in doc.metadata:
        try:
          images_b64 = json.loads(doc.metadata["images_base64"])
          if images_b64:
              prompt.append("IMAGES (visual data associated with this text):")

              for img_str in images_b64:
                if img_str:
                  ## decode Base64 string to bytes
                  img_bytes = base64.b64decode(img_str)

                  prompt.append({
                    "mime_type":"image/jpeg",
                    "data":img_bytes
                  })
        
        except Exception as e:
          print(f"Error in loading image in doc {i} : {e}")

    prompt.append("\n---- END OF CONTEXT ---\n")   
    prompt.append(f"USER QUESTION: {query}")   

    return prompt



