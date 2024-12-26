# Chatbot Project - Document Ingestion and Query System

## Overview
This project implements a chatbot system designed to process and interpret uploaded documents (PDFs) to provide accurate, fact-based responses. The chatbot utilizes Large Language Model (LLM) APIs along with retrieval techniques for generating contextually relevant answers.

## Features
1. **Responsive REST APIs:**
   - Provides endpoints for chat interaction and file uploads.
2. **Simple UI:**
   - Built with Streamlit for ease of use and accessibility.
3. **Document Ingestion:**
   - Supports PDF uploads with text extraction and processing.
4. **LLM Integration:**
   - Utilizes Groq API for language model queries.
5. **Context Verification:**
   - Embedding-based retrieval to ensure responses are grounded in document content.
6. **Authentication:**
   - User sign-up and login with Firebase for secure data management.
7. **Chat History Management:**
   - Save, retrieve, and delete chat sessions using Firebase.

## Good-to-Have Enhancements
- **Bulk Uploads:** Supports multiple document uploads for batch processing.
- **Security by Design:** User authentication and secure storage.
- **Enhanced User Experience:** Improved UI/UX with custom styling and dynamic responses.
- **Prevention of Hallucinations:** Ensures responses directly reference the uploaded documents.

---

## System Requirements
- Python 3.9 or higher
- Dependencies:
  - Streamlit
  - FastAPI
  - Firebase Admin SDK
  - PDF Processing Libraries:
    - pdfplumber
    - pdf2image
    - pytesseract
  - Sentence Transformers for Embeddings
  - FAISS for vector search
  - Groq API for LLM interaction

---

## Architecture
1. **Frontend (Streamlit):**
   - Handles user authentication, chat interactions, and file uploads.
2. **Backend (FastAPI):**
   - Processes PDF files, extracts text, creates embeddings, and manages chat sessions.
3. **Database (Firebase Firestore):**
   - Stores user data and chat history securely.
4. **LLM Integration (Groq API):**
   - Provides AI-driven responses to user queries.

---

## Installation and Setup
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-repo/chatbot.git
   cd chatbot
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv env
   source env/bin/activate   # For Linux/Mac
   env\Scripts\activate     # For Windows
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Firebase:**
   - Download `serviceAccountKey.json` from Firebase console.
   - Place it in the project directory.

5. **Run the Backend (FastAPI):**
   ```bash
   uvicorn main:app --reload
   ```

6. **Run the Frontend (Streamlit):**
   ```bash
   streamlit run frontend.py
   ```

---

## Usage
1. **Sign Up or Login:**
   - Access the chatbot through the UI and create an account.
2. **Upload PDF Files:**
   - Upload a document to analyze its content.
3. **Chat Interaction:**
   - Enter queries to retrieve specific information or summaries from the document.
4. **View and Manage Chats:**
   - Save chat history and delete sessions as needed.

---

## REST API Endpoints
1. **Chat Endpoint:**
   - URL: `/chat`
   - Method: POST
   - Body:
     ```json
     {
       "message": "Your query here"
     }
     ```
   - Response:
     ```json
     {
       "response": "Generated response"
     }
     ```

2. **Upload PDF Endpoint:**
   - URL: `/upload-pdf`
   - Method: POST
   - Body: File Upload
   - Response:
     ```json
     {
       "message": "PDF uploaded successfully"
     }
     ```

3. **Delete Chat Endpoint:**
   - URL: `/delete-chat/{chat_name}`
   - Method: DELETE
   - Response:
     ```json
     {
       "message": "Chat deleted successfully."
     }
     ```

---

## Important Notes
- Ensure `pytesseract` is installed and configured properly for text extraction.
- Replace `Groq API Key` with a valid key in the backend code.
- Temporary files are deleted after processing to maintain security.

---

## Future Improvements
- Add support for bulk document uploads.
- Implement streaming APIs for real-time responses.
- Integrate additional security measures (e.g., JWT authentication).
- Expand LLM capabilities with custom prompts and fine-tuned models.

---

## Contributors
- **Your Name** - Developer
- **Team Members** - CRG Fintech Team

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.

