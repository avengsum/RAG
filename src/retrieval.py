import os
import pickle
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import CHROMA_PATH, BM25_PATH, EMBEDDING_MODEL
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from typing import List, Dict, Set
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize
import cohere

load_dotenv()

cohere_client = cohere.Client()


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
      self.doc_lookup = {i.metadata.get('chunk_id'): i for i in self.doc_map if i.metadata.get('chunk_id') is not None}

    print(f"Loaded {len(self.doc_map)} documents into BM25")
    print(f"Created lookup for {len(self.doc_lookup)} documents with chunk_id")

    if len(self.doc_lookup) == 0 and len(self.doc_map) > 0:
      print("\n⚠️ WARNING: No documents have chunk_id in metadata!")
      print("Sample document metadata:")
      print(f"  Keys: {list(self.doc_map[0].metadata.keys())}")
      print(f"  Values: {self.doc_map[0].metadata}")
  
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

  def recipoccal_rank_fusion(self,result:Dict[str,List],k=60):

    fused_scores = {}

    for qury , doc_list in result.items():
      for rank, (doc,_) in enumerate(doc_list):

        doc_id = doc.metadata.get("chunk_id", "unknown")

        ## skip document without chunk_id
        if doc_id == "unknown":
          continue

        if doc_id not in fused_scores:
          fused_scores[doc_id] = 0
        
        ## RRF formaul  1 + (k + rank)

        fused_scores[doc_id] += 1/(k + rank)
    
    sort_id = sorted(fused_scores.items(),key=lambda x: x[1], reverse=True)

    print(f"   RRF fused {len(sort_id)} unique documents")

    return sort_id
  

  def hybrid_search(self,query:str,top_k=10):

    print(f"   Hybrid search for: '{query[:50]}...'")

    ## vector search or dense search

    ## so thsi will give [(Document,0.87)] so it will give simmilarity socre and document

    vector_result = self.vectordb.similarity_search_with_score(query=query,k=top_k)
    print(f"      -> Vector search returned {len(vector_result)} results")

    ## sparse/keyword search

    ## so tokeinsse the content hello world -> ["hello","world"]
    tokenzied_query = word_tokenize(query.lower())

    ## so it will give score to our query

    bm25_score = self.bm25_model.get_scores(tokenzied_query)

    top_indices = sorted(range(len(bm25_score)), key=lambda i: bm25_score[i],reverse=True)[:top_k]

    sparse_results = [(self.doc_map[i] , bm25_score[i]) for i in top_indices]

    doc_lookup = {}

    for d, score in vector_result:
      cid = d.metadata.get("chunk_id")
      if cid is not None and cid not in doc_lookup:
        doc_lookup[cid] = d

    for d , score in sparse_results:
      cid = d.metadata.get("chunk_id")
      if cid is not None and cid not in doc_lookup:
        doc_lookup[cid] = d
    
    results_to_fuse = {
    "dense": vector_result,
    "sparse": sparse_results
    }

    fused_ids = self.recipoccal_rank_fusion(results_to_fuse)

    final_docs = []

    for doc_id, score in fused_ids[:top_k]:
      if doc_id in doc_lookup:
        final_docs.append(doc_lookup[doc_id])

    print(f"      -> Hybrid search returned {len(final_docs)} fused results")
    return final_docs
  

  def retrieval(self,user_query:str):

    ## getting more varition of our query
    queries = self.get_more_query(user_query)

    ## hybrid search

    print(" Running multiple hybrid search  ")

    all_results = {}

    for i , q in enumerate(queries):
      ## running hybrid search in loop for per query

      docs = self.hybrid_search(q,top_k=10)

      all_results[f"q_{i}"] = [(d, 0) for d in docs]
    
    print("performing global RRF")

    Global_RRF = self.recipoccal_rank_fusion(all_results)

    all_docs_flat = {}
    
    for q_res in all_results.values():
      for d , _ in q_res:
        cid = d.metadata.get("chunk_id")
        if cid is not None:
          all_docs_flat[cid] = d

    ## get top 25 documents

    top25_ids = Global_RRF[:25]

    RRF_docs = []
    
    for doc_id , score in top25_ids:
      if doc_id in all_docs_flat:
        RRF_docs.append(all_docs_flat[doc_id])
    

    ## now cohere Reranking

    if len(RRF_docs) == 0:
      print("⚠️ No documents found after RRF. Returning empty results.")
      return []

    print(f"Reranking {len(RRF_docs)} chunk with cohere")

    docs_text = [d.page_content for d in RRF_docs]

    try:
      rerank_results = cohere_client.rerank(
      model="rerank-english-v3.0",
      query=user_query, 
      documents=docs_text,
      top_n=min(8,len(RRF_docs))
    )
    
    except Exception as e:
      print(f"⚠️ Cohere failed: {e}. Returning top RRF results.")
      return RRF_docs[:8]


    final_docs = []

    for result  in rerank_results.results:
      doc = RRF_docs[result.index]

      doc.metadata["rerank_score"] = result.relevance_score

      final_docs.append(doc)
    
    print(f"Final selection: {len(final_docs)} chunks")

    return final_docs


retriever = Retriever()

results = retriever.retrieval("How does attention work?")

for i , doc in enumerate(results):
  print(f"\n--- Result {i+1} (Score: {doc.metadata.get('rerank_score',0):.3f}) ---")
  print(doc.page_content[:200] + "...")
    



        


  
    
  

  

