import streamlit as st
import requests
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase initialization
cred = credentials.Certificate("serviceAccountKey.json")

# Check if Firebase app is already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

BACKEND_URL = "http://127.0.0.1:8000"

# Set up the page configuration
st.set_page_config(
    page_title="CHATBOT",
    page_icon="📨",
    layout="wide",
    initial_sidebar_state="expanded"
)

def set_custom_css():
    style = """
    <style>
    /* Style for the sidebar */
    section[data-testid="stSidebar"] {
        background-image: linear-gradient(-20deg, #e9defa 0%, #fbfcdb 100%);     
        color: #262730;
    }
    /* Style for the chat area */
    .chat-container {
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# Apply custom CSS
set_custom_css()

# Initialize session state for login and chat history
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Authentication functions
def login(username, password):
    user_ref = db.collection('users').document(username).get()
    if user_ref.exists:
        user_data = user_ref.to_dict()
        if user_data['password'] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            fetch_chat_history(username)
            return True
    return False

def signup(username, password):
    # Check if user already exists
    if db.collection('users').document(username).get().exists:
        return False  # User already exists
    # Create new user document with password and an empty chat history
    db.collection('users').document(username).set({
        'password': password,
        'chats': []
    })
    return True

# Define logout function
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.messages = []
    st.session_state.page = "login"
    st.rerun()  # Force a rerun to refresh the page


def fetch_chat_history(username):
    user_ref = db.collection('users').document(username).get()
    if user_ref.exists:
        user_data = user_ref.to_dict()
        st.session_state.messages = user_data.get('chats', [])

def save_chat_to_firebase(chat_data):
    # Get the current number of chats to create a dynamic name like chat_1, chat_2, etc.
    user_ref = db.collection('users').document(st.session_state.username)
    user_data = user_ref.get().to_dict()
    chat_count = len(user_data.get('chats', []))
    chat_name = f"chat_{chat_count + 1}"
    
    # Save the chat as chat_1, chat_2, etc.
    user_ref.update({
        'chats': firestore.ArrayUnion([{'chat_name': chat_name, 'messages': chat_data}])
    })

def load_chat_from_firebase(chat_name):
    user_ref = db.collection('users').document(st.session_state.username)
    user_data = user_ref.get().to_dict()
    chats = user_data.get('chats', [])
    
    # Find the chat by its name
    for chat in chats:
        if chat.get('chat_name') == chat_name:
            return chat.get('messages', [])
    return []

def delete_chat_from_firebase(chat_name):
    # Delete the specified chat from Firebase
    user_ref = db.collection('users').document(st.session_state.username)
    user_data = user_ref.get().to_dict()
    chats = user_data.get('chats', [])
    
    # Filter out the chat to delete
    updated_chats = [chat for chat in chats if chat['chat_name'] != chat_name]
    
    # Update the user's chat list with the removed chat
    user_ref.update({
        'chats': updated_chats
    })

# Default page is login
if 'page' not in st.session_state:
    st.session_state.page = "login"

# Login and Sign-Up navigation
if not st.session_state.logged_in:
    st.sidebar.markdown("""
    ≡ **Navigation**
    """)
    if st.sidebar.button("Sign-In", use_container_width=True):
        st.session_state.page = "login"
    if st.sidebar.button("Sign-Up", use_container_width=True):
        st.session_state.page = "signup"

# Login Page (only show login if not logged in)
if st.session_state.page == "login" and not st.session_state.logged_in:
    st.title("Login")
    st.markdown("Please enter your username and password to log in.")
    # Create columns to control the width of the text input
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:  # Use the middle column for the input
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

    # Login button with logic
    if st.button("Login"):
        if username and password:
            if login(username, password):
                st.success("Login successful!")
                st.session_state.page = "chat"  # Navigate to chat page
                st.rerun()  # Force a rerun to clear login elements
            else:
                st.error("Incorrect username or password.")
        else:
            st.error("Please enter both username and password.")

# Sign-Up Page (only show signup if not logged in)
if st.session_state.page == "signup" and not st.session_state.logged_in:
    st.title("Sign-Up")
    st.markdown("Create a new account with your username and password.")

    # Sign-Up Form
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")

    if st.button("Sign-Up"):
        if new_username and new_password:
            if signup(new_username, new_password):
                st.success("Sign-Up successful! You can now log in.")
                st.session_state.page = "login"  # Automatically navigate to login after signup
                st.rerun()  # Force a rerun to clear signup elements
            else:
                st.error("Username already exists, please choose another one.")
        else:
            st.error("Please fill in both fields.")
 # Main Chat Page after login
if st.session_state.logged_in:
    st.sidebar.title("HAPPY CHAT")
    st.sidebar.write(f"Welcome, {st.session_state.username}!")

    # Add the logout button in the sidebar
    if st.sidebar.button("Logout", on_click=logout):
        logout()

    # Create a function to get the chat response from the backend
    def get_chat_response(prompt):
        response = requests.post(f"{BACKEND_URL}/chat", json={"message": prompt})
        return response.json().get("response", "Error fetching response")

    # Function to send uploaded PDF to backend
    def upload_file(file):
        files = {"file": file.getvalue()}
        response = requests.post(f"{BACKEND_URL}/upload-pdf", files=files)
        return response.json()

    # Set custom CSS for the chat area
    st.markdown("""
    <style>
    .chat-container {
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create a div for the chat container to center it
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        # User input for chat
        if prompt := st.chat_input("Say something..."):
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Get response from backend and display it
            response = get_chat_response(prompt)
            st.chat_message("assistant").markdown(response)

            # Store assistant's response in session state
            st.session_state.messages.append({"role": "assistant", "content": response})

            # Save current chat to Firebase
            #save_chat_to_firebase(st.session_state.messages)

        # File upload functionality
        uploaded_file = st.file_uploader("Upload a file (optional)", type=["pdf"])

        if uploaded_file is not None:
            file_response = upload_file(uploaded_file)
            file_details = {
                "Filename": uploaded_file.name,
                "FileType": uploaded_file.type,
                "FileSize": uploaded_file.size,
            }
            st.write("Uploaded File Details:")
            st.json(file_details)

        st.markdown('</div>', unsafe_allow_html=True)
