import json
import os
from dotenv import load_dotenv
from config import BM25_PATH, CHROMA_PATH, EMBEDDING_MODEL
import base64
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize ## to tokenize the word
import nltk
nltk.download('punkt',quiet=True)
import pickle
from unstructured.partition.auto import partition

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

def build_save_bm25(chunks):
  print("Buildinng BM25 index")

   ## so we are builind here so that when the user query we should not build there we will just load

  ## each chunk has page content so we will get that
  docs_text = [doc.page_content for doc in chunks]

  ## so we will tokenized the text so 
  ## "Hello Worold" -> ["hello","world"] beacuse bm25 works upon words not strings
  tokenized = [word_tokenize(doc.lower()) for doc in docs_text]

  bm25 = BM25Okapi(tokenized)

  ## so we are stroing model and orginal document both so that we can return original content in query time

  bm25_data= {
     "model":bm25,
     "doc_map": chunks
  }

  os.makedirs(os.path.dirname(BM25_PATH),exist_ok=True)

  with open(BM25_PATH,"wb") as f: 
     # "wb" write binary so we are using pickle to save the data in the disk
    pickle.dump(bm25_data,f)
  
  print(f"bm25 index save in {BM25_PATH}  number of documents {len(docs_text)}")


def chunking(file_path):
  print(f"Started ingestion for {file_path}")
  
  print("partitioning PDF")

  extension = os.path.splitext(file_path)[1]

  if extension == ".pdf":
    elements = partition_pdf(
    filename=file_path,
    strategy="hi_res",
    infer_table_structure=True, ## get HTML for tables
    extract_image_block_types=["Image","Table"],
    extract_image_block_to_payload=True # to get Base64 data
  )
  
  elif extension in [".docx",".pptx"]:
     elements = partition(
        filename=file_path,
        strategy="hi_res",
        infer_table_structure=True,
        extract_image_block_types=["Image", "Table"],
        extract_image_block_to_payload=True
      )
  
  elif extension in [".txt",".md",".html"]:
     elements = partition(
        filename=file_path,
        strategy="auto",
      )
  
  else:
    print(f" Unsupported file type: {extension}")
    return None

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
          "chunk_id": i, ## so this for retrival to know two documents are diffrent
          "original_text": chunk_text,
          "tables_html": json.dumps(tables),
          "images_base64": json.dumps(images)
        }
      )

    process_data.append(data)
  
  if process_data:
    print(f"\n✅ Sample document metadata:")
    print(f"   chunk_id: {process_data[0].metadata.get('chunk_id')} (type: {type(process_data[0].metadata.get('chunk_id'))})")
    print(f"   source: {process_data[0].metadata.get('source')}")

  ## save in vectorDB

  print(f"saving {len(process_data)} chunks in in chromaDB")

  vectordb = Chroma.from_documents(
    documents=process_data,
    embedding=embedding_model,
    persist_directory=CHROMA_PATH, 
    collection_metadata={"hnsw:space": "cosine"}
  )

  build_save_bm25(process_data)

  print("Ingestion completed")

  return vectordb



chunking(r"C:\Users\sy710\Desktop\gen-ai\rag\data\attention-is-all-you-need-Paper.pdf")