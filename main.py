from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import io
from typing import Dict, Any, List
from dataclasses import dataclass
from PIL import Image
from pdf2image import convert_from_path
import pytesseract
from langgraph.graph import END, Graph
from sentence_transformers import SentenceTransformer
import faiss
from groq import Groq
import pdfplumber
import json
import tempfile 
import os
from fastapi.responses import JSONResponse

app = FastAPI()

# Function to simulate chatbot response (You can replace this with actual logic or model)
def generate_chat_response(prompt: str) -> str:
    return f"Response to: {prompt} gagagg"

# Set up Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ChatMessage(BaseModel):
    message: str

@dataclass
class WorkflowState:
    pdf_path: str
    extracted_text: str = ""
    embeddings: Any = None
    context: str = ""
    query: str = ""
    response: str = ""
    is_summary_query: bool = False

def is_summary_related(query: str) -> bool:
    """Check if the query is related to summarization."""
    summary_keywords = [
        'summary', 'summarize', 'summarise', 'overview', 'brief', 'what does this doc say', 'what does this document say', 'explain the doc', 'explain this doc', 'explain pdf', 'explain doc', 'what does the document say'
        'gist', 'recap', 'outline', 'sum up', 'key points', 'what does this pdf say', 'explain the document', 'explain the pdf', 'explain this pdf', 'explain this document', 'explain document', 'what does the doc say', 'what does the pdf say'
    ]
    return any(keyword in query.lower() for keyword in summary_keywords)

def extract_text_for_summary(pdf_path: str) -> str:
    """Extract text from PDF for summarization purposes."""
    try:
        images = convert_from_path(pdf_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return ""

def process_summary_query(text: str) -> str:
    """Process text for summarization using Groq LLM."""
    client = Groq(
        api_key="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"
    )
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""Analyze and summarize the following text: ```{text}```
                Please provide a comprehensive summary of the main points and key information."""
            }
        ],
        model="llama3-8b-8192",
        temperature=0.7,
        max_tokens=1024
    )
    return chat_completion.choices[0].message.content

def process_pdf_query(pdf_path: str, query: str) -> str:
    """Process a PDF and answer a query about it."""
    # Check if it's a summary-related query
    if is_summary_related(query):
        extracted_text = extract_text_for_summary(pdf_path)
        return process_summary_query(extracted_text)
    
    # For non-summary queries, use the original workflow
    initial_state = WorkflowState(
        pdf_path=pdf_path,
        query=query
    )
    
    workflow = create_workflow()
    compiled_workflow = workflow.compile()
    final_state = compiled_workflow.invoke(initial_state)
    
    return final_state.response

# Original workflow functions remain the same
def extract_text_from_pdf(state: WorkflowState) -> WorkflowState:
    """Extract text from PDF using OCR and pdfplumber."""
    
    images = convert_from_path(state.pdf_path)
    extracted_text = []
    
    for page_number, image in enumerate(images):
        text = pytesseract.image_to_string(image)
        if text.strip():
            extracted_text.append(f"Page {page_number + 1}: {text}")
    
    state.extracted_text = "\n\n".join(extracted_text)
    return state

def create_embeddings(state: WorkflowState) -> WorkflowState:
    """Create embeddings for the extracted text."""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Initialize FAISS index
    embedding_dim = 384
    index = faiss.IndexFlatL2(embedding_dim)
    
    # Split text into chunks and create embeddings
    chunks = state.extracted_text.split("\n\n")
    metadata = []
    
    for chunk in chunks:
        if chunk.strip():
            embedding = model.encode(chunk).astype("float32")
            index.add(embedding.reshape(1, -1))
            metadata.append({"content": chunk})
    
    state.embeddings = {
        "index": index,
        "metadata": metadata,
        "model": model
    }
    return state

def retrieve_context(state: WorkflowState) -> WorkflowState:
    """Retrieve relevant context based on the query."""
    query_embedding = state.embeddings["model"].encode(state.query).astype("float32")
    
    # Get top 5 relevant chunks
    k = 5
    distances, indices = state.embeddings["index"].search(
        query_embedding.reshape(1, -1), k
    )
    
    retrieved_chunks = [
        state.embeddings["metadata"][i]["content"] 
        for i in indices[0] 
        if i < len(state.embeddings["metadata"])
    ]
    
    state.context = "\n\n".join(retrieved_chunks)
    return state

def generate_response(state: WorkflowState) -> WorkflowState:
    """Generate response using Groq LLM."""
    client = Groq(
        api_key="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"  # Replace with your API key
    )
    
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "user", "content": state.query},
            {"role": "system", "content": f"The most relevant PDF content:\n\n{state.context}"},
            {"role": "system", "content": "Answer the question based strictly on the provided content."}
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False
    )
    
    state.response = completion.choices[0].message.content
    return state

def create_workflow() -> Graph:
    """Create and configure the workflow graph."""
    workflow = Graph()
    
    workflow.add_node("extract_text", extract_text_from_pdf)
    workflow.add_node("create_embeddings", create_embeddings)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_response", generate_response)
    
    workflow.add_edge("extract_text", "create_embeddings")
    workflow.add_edge("create_embeddings", "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_response")
    
    workflow.set_entry_point("extract_text")
    workflow.set_finish_point("generate_response")
    
    return workflow

@app.get("/")
def read_root():
    return {"message": "Welcome to the Chatbot API!"}

@app.post("/chat")
async def chat(message: ChatMessage):
    global temp_pdf_path
    try:
        if not temp_pdf_path or not os.path.exists(temp_pdf_path):
            client = Groq(
                api_key="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"
            )
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": message.message
                    }
                ],
                model="llama3-8b-8192",
                temperature=0.7,
                max_tokens=1024
            )
            response = chat_completion.choices[0].message.content
            return JSONResponse(content={"response": response})

        # Use the uploaded PDF file in the chat logic
        response = process_pdf_query(temp_pdf_path, message.message)

        # Clean up the temporary PDF file after processing
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            temp_pdf_path = None

        return JSONResponse(content={"response": response})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error processing chat request")

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    global temp_pdf_path
    try:
        # Save the uploaded file temporarily
        temp_dir = tempfile.gettempdir()
        temp_pdf_path = os.path.join(temp_dir, file.filename)

        with open(temp_pdf_path, "wb") as f:
            f.write(await file.read())

        return JSONResponse(content={"message": "PDF uploaded and stored temporarily"})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error processing PDF file")

@app.delete("/delete-chat/{chat_name}")
async def delete_chat(chat_name: str):
    # Here you can delete the chat from Firebase
    # For now, simulate the deletion
    return JSONResponse(content={"message": f"Chat {chat_name} deleted successfully."})
