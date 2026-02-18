import json
import os
from dotenv import load_dotenv
from config import CHROMA_PATH, EMBEDDING_MODEL, VISION_MODEL
from langchain_google_genai import ChatGoogleGenerativeAI
import base64
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

embedding_model = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
vision_model = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct")

def ai_summary(text,tables,image_b64):
  ## so this is to summerize text tables image base64

  print("calling ai to get summerize mixed content")

  try:
    prompt = [f"Analyze this document chunk for retrieval. \nTEXT CONTENT:\n{text}"]

    for t in tables:
      prompt.append(f"\nTABLE DATA:\n{t}")
    
    for img in image_b64:
      if img:
        img_bytes = base64.b64decode(img)
        prompt.append({'mime_type': 'image/jpeg', 'data': img_bytes})

    prompt.append("\nTASK: Provide a detailed text summary of this content, including data from the tables and details from the images.")

    res = vision_model.invoke(prompt)
    return res.text
  
  except Exception as e:
    print(f"      ❌ Error in AI summary: {e}")
    return text


def chunking(file_path):
  print(f"Started ingestion for {file_path}")
  
  print("partitioning PDF")

  elements = partition_pdf(
    filename=file_path,
    strategy="hi_res",
    infer_table_structure=True, ## get HTML for tables
    extract_image_block_types=["Image"],
    extract_image_block_to_payload=True # to get Base64 data
  )

  ## chunking

  print("Chunking")

  chunks = chunk_by_title(
            elements,
            max_characters=4000,
            combine_text_under_n_chars=500
            )
  
  process_data = [] ## to summerize by ai

  for i , chunk in enumerate(chunks):
    chunk_text = chunk.text
    tables = []
    images = []

    ## unstructuted stores original elemenets in metadata
    if hasattr(chunk, 'metadata') and hasattr(chunk.metadata, 'orig_elements'):
        for el in chunk.metadata.orig_elements:
            el_type = type(el).__name__
                
            if el_type == 'Table':
                 # to get table in HTML
                tables.append(getattr(el.metadata, 'text_as_html', el.text))
                
            if el_type == 'Image':
                # Get Image Base64
                if hasattr(el.metadata, 'image_base64'):
                    images.append(el.metadata.image_base64)
  
    if tables or images:
      ai_content = ai_summary(chunk_text,tables,images)
  
    else:
      ai_content = chunk_text
  
    data = Document(
       page_content=ai_content,
       metadata={
          "source": file_path,
          "original_text": chunk_text,
          "tables_html": json.dumps(tables),
          "images_base64": json.dumps(images)
        }
      )

    process_data.append(data)


  ## save in vectorDB

  print(f"saving {len(process_data)} chunks in in chromaDB")

  vectordb = Chroma.from_documents(
    documents=process_data,
    embedding=embedding_model,
    persist_directory=CHROMA_PATH, 
    collection_metadata={"hnsw:space": "cosine"}
  )

  return vectordb



chunking(r"C:\Users\sy710\Desktop\gen-ai\rag\data\attention-is-all-you-need-Paper.pdf")