from typing import List , Dict , Any
from pypdf import PdfReader
import re


class PDFIngestion:
  def __init__(self,chunk_size: int = 500, overlap: int = 50):
    self.chunk_size = chunk_size
    self.overlap = overlap

  
  def _extract_text_from_pdf(self,file_path:str) -> List[Dict]:
    ## our pdf reader exact text here and add page number and add page number

    reader = PdfReader(file_path)
    pages = []

    for i , page in enumerate(reader.pages):
      text = page.extract_text()

      if text:
        pages.append({"page number": i +1, "text":text})
    
    return pages
  
  def _clean_text(self,text:str) -> str:
    # in this we remove spaces and clean our text
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)

    ## new line replace with space
    text = text.replace('\n', ' ')
    ## large space remove like "hello   world" -> "hello world"
    text = re.sub(r'\s+', ' ', text)

    return text.strip()
  
  def _semantic_chunk(self,text:str) -> List[str]:

    ## so wherner it see . ? ! it breake the work like this "hello! hi" it becomes ["hello!", "hi"] so now we have clean sentence
    sentences = re.split(r'(?<=[.?!])\s+', text)

    chunks = []
    current_chunk = ""

    ## so isme hum sentence ko chunk me break karege aur overlay dalege isme 

    for sen in sentences:
      if len(current_chunk) + len(sen) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else ""
                current_chunk = overlap_text + " " + sen
      else:
        current_chunk += " " + sen
        
    if current_chunk:
        chunks.append(current_chunk.strip())
            
    return chunks


  def readPdf(self,file_path:str) -> List[Dict[str,Any]]:

    print(f"reading file {file_path}")

    raw_pages = self._extract_text_from_pdf(file_path)

    all_chunks = []

    for page_data in raw_pages:
       clened_text = self._clean_text(page_data["text"])

       page_chunks = self._semantic_chunk(clened_text)
       
       for chunk_text in page_chunks:
          all_chunks.append({
             "content":chunk_text,
             "metadata":{
                "source":file_path,
                "page_number":page_data["page_number"],
                "chunk_length":len(chunk_text)
             }
          })
    
    print(f"Processed {len(all_chunks)} chunks from {file_path}")
    return all_chunks

    
    