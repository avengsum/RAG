import pickle
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import CHROMA_PATH, BM25_PATH, EMBEDDING_MODEL
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from typing import List, Dict, Set
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize

load_dotenv()

embedding_model = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
GroqLLm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct")

class Retriever:
  def __init__(self):
    print("starting retrieval")

    self.vectordb = Chroma(
      persist_directory=CHROMA_PATH,
      embedding_function=embedding_model,
      collection_metadata={"hnsw:space": "cosine"}
    )

    print("-- Loading bm25 index --")

    with open(BM25_PATH,"rb") as f:
      ## read binary
      bm25_data = pickle.load(f)
      self.bm25_model = bm25_data["model"]
      self.doc_map = bm25_data["doc_map"]
      self.doc_lookup = {i.metadata['chunk_id']: i for i in self.doc_map}
  
  def get_more_query(self,ori_query:str) -> List[str]:

    print(f"getting more query from llm original query{ori_query}")

    prompt = f"""You are an AI assistant optimizing queries for a RAG system. 
        Generate 4 different search queries based on this user question: "{ori_query}".
        
        Types of variations needed:
        1. Keyword-focused (for BM25)
        2. Semantic/Conceptual (for Vector Search)
        3. A specific question form
        4. A broader topic form

        Output ONLY the 4 queries, separated by newlines. No numbering."""
    
    response = GroqLLm.invoke(prompt)

    variations = response.content.strip().split("\n")

    ## clean and add original query

    queries = [q.strip() for q in variations if q.strip()]

    queries.append(ori_query)

    print(f"      -> Generated {len(queries)} variations.")

    print("Generated Query Variations:")

    for i , v in enumerate(queries):
      print(f"{i}: {v}")

    ## using set to remove duplicate
    return list(set(queries)) 

  def recipoccal_rank_fusion(self,result:Dict[str,Dict[str,float]],k=60):

    fused_scores = {}

    for qury in result.values():
      for rank, (doc,_) in enumerate(qury):

        doc_id = doc.metadata.get("chunk_id", "unknown")

        if doc_id not in fused_scores:
          fused_scores[doc_id] = 0
        
        ## RRF formaul  1 + (k + rank)

        fused_scores[doc_id] += 1/(k + rank)
    
    sort_id = sorted(fused_scores.items,key=lambda x: x[1], reverse=True)

    return sort_id
  

  def hybrid_search(self,query:str,top_k=10):

    ## vector search or dense search

    ## so thsi will give [(Document,0.87)] so it will give simmilarity socre and document

    vector_result = self.vectordb.similarity_search_with_score(query=query,k=top_k)

    ## sparse/keyword search

    ## so tokeinsse the content hello world -> ["hello","world"]
    tokenzied_query = word_tokenize(query.lower())

    ## so it will give score to our query

    bm25_score = self.bm25_model.get_scores(tokenzied_query)

    top_indices = sorted(range(len(bm25_score)), key=lambda i: bm25_score[i],reverse=True)[:top_k]

    sparse_results = [self.doc_map[i] for i in top_indices]

    doc_lookup = {}
    for d, _ in vector_result:
      cid = d.metadata.get("chunk_id")
      if cid is not None:
        doc_lookup[cid] = d

    for d in sparse_results:
      cid = d.metadata.get("chunk_id")
      if cid is not None:
        doc_lookup[cid] = d
    
    results_to_fuse = {
    "dense": [(doc, score) for doc, score in vector_result],
    "sparse": [(doc, 0) for doc in sparse_results]
    }

    fused_ids = self.reciprocal_rank_fusion(results_to_fuse)

    final_docs = []

    for doc_id, score in fused_ids[:top_k]:
      if doc_id in doc_lookup:
        final_docs.append(doc_lookup[doc_id])
    
    return final_docs

    



        


  
    
  

  

