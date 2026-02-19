import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage , SystemMessage , AIMessage

from config import MODEL

load_dotenv()

class RagGenerator:
  def __init__(self):
    print("----- Gerneration started -----")
    self.model = ChatGoogleGenerativeAI(model=MODEL)
    self.chat_history = []
    self.max_history = 5

  def _system_prompt(self) -> Dict[str, Any]:
        return {
            "type": "text",
            "text": (
                "You are an expert AI assistant. Answer the user's question using the provided context.\n"
                "The context contains Text, Tables (in HTML), and Images.\n"
                "Use ALL available data to answer accurately.\n"
                "If the answer is found in an image or table, explicitly mention it.\n"
                "Cite the source document name where possible.\n"
                "Use the conversation history to maintain context across questions.\n"
            )
        }
  
  def _prompt_content(self,query:str,docs:List[Document]) -> List[Dict[str, Any]]:
    ## so in prompt we will give text strings images so we will desingn in that way

    prompt = []

    prompt.append({
      "type": "text",
            "text": "\n--- START OF CONTEXT ---\n"
      })

    for i, doc in enumerate(docs):
      ## sorce of document
      src = doc.metadata.get("source","Unknown Source")
      prompt.append({
        "type": "text",
         "text": f"\nDocument {i+1} (Source: {src})\n"
      })

      ## so raw text over summary

      raw_content = doc.metadata.get("original_text", doc.page_content)

      prompt.append({
        "type": "text",
        "text": f"TEXT CONTENT:\n{raw_content}\n"
      })

      if "tables_html" in doc.metadata:
        try:
          tables = json.loads(doc.metadata["tables_html"])
          if tables:
            prompt.append({
              "type": "text",
              "text": "TABLES:\n" + "\n".join(tables) + "\n"
            })
            for t in tables:
              prompt.append(t) 
        
        except:
          pass
      
      if "images_base64" in doc.metadata:
        try:
          images_b64 = json.loads(doc.metadata["images_base64"])
          if images_b64:
              prompt.append({
                "type": "text",
                "text": "IMAGES (visual data associated with this text):\n"
              })

              for img_str in images_b64:
                if img_str:
                  ## we are going to pass image
                  prompt.append({
                    "type": "image_url", 
                    "image_url":{
                          "url": f"data:image/jpeg;base64,{img_str}"  
                      }
                  })
        
        except Exception as e:
          print(f"Error in loading image in doc {i} : {e}")

    prompt.append({
       "type": "text",
        "text": "\n--- END OF CONTEXT ---\n"
    })   
    prompt.append({
      "type": "text",
      "text": f"USER QUESTION: {query}\n"
    })   

    return prompt
  
  
  def ai_response(self,query:str,retrieved_doc:List[Document]) -> str:
    print(f"Generating Answer with {len(retrieved_doc)} chunks")

    try:

      # for history
      messages = []

      ## adding system prompt
      if not self.chat_history:
        messages.append(SystemMessage(
          content =[self._system_prompt()]
        ))
      
      if len(self.chat_history) > 0:
        number_of_messages = self.max_history * 2
        recent_history = self.chat_history[-number_of_messages:]

        for r in recent_history:
          messages.append(r)

      prompt = self._prompt_content(query=query,docs=retrieved_doc)
      
      ## because langchain require role and msg so this handle this
      message = HumanMessage(content=prompt)
      messages.append(message)

      res = self.model.invoke(messages)

      if isinstance(res.content, list):
          # Join all text blocks together
          final_text = "".join([block.get("text", "") for block in res.content if block.get("type") == "text"])
      else:
        # It's already a string
        final_text = str(res.content)
      
      self.chat_history.append(HumanMessage(content=query))

      self.chat_history.append(AIMessage(content=final_text))

      return final_text
    
    except Exception as e:
      print(f"Generation Failed: {e}")
      return "Generation failed"
    
  

    



