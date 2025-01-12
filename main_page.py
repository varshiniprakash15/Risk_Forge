import streamlit as st
import bcrypt
import sqlite3
import side_bar as comp
import stTools as tools
import default_page
import portfolio_page
import model_page

# Database connection
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create table (run this only once)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
""")
conn.commit()

# Function to register a new user
def register_user(username, password):
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Authentication function
def authenticate(username, password):
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    record = cursor.fetchone()
    if record and bcrypt.checkpw(password.encode(), record[0].encode()):
        return True
    return False

# Streamlit app
st.set_page_config(
    page_title="RiskForge",
    layout="wide"
)

tools.remove_white_space()

# Initialize session state for login
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

if st.session_state.authenticated:
    # Show logout button in the upper-right corner
    st.sidebar.button("Logout", key="logout", on_click=lambda: st.session_state.update(authenticated=False, username=""))

    st.title(f"Welcome, {st.session_state.username}!")
    
    # Main functionality (Portfolio Risk Assessment)
    comp.load_sidebar()

    if "load_portfolio_check" not in st.session_state:
        st.session_state["load_portfolio_check"] = False

    if "run_simulation_check" not in st.session_state:
        st.session_state["run_simulation_check"] = False

    if not st.session_state.load_portfolio_check:
        default_page.load_page()

    elif not st.session_state.run_simulation_check and st.session_state.load_portfolio_check:
        portfolio_page.load_page()

    elif st.session_state.run_simulation_check:
        model_page.load_page()

else:
    # Show login and registration options
    st.title("Portfolio Risk Assessment")
    tab = st.radio("Choose an option", ["Login", "Register"])

    if tab == "Register":
        st.subheader("Create a new account")
        new_username = st.text_input("Enter a username", placeholder="Username")
        new_password = st.text_input("Enter a password", type="password", placeholder="Password")
        if st.button("Register"):
            if new_username and new_password:
                if register_user(new_username, new_password):
                    st.success("Registration successful! You can now log in.")
                else:
                    st.error("Username already exists. Please choose a different one.")
            else:
                st.error("Please fill out all fields.")

    elif tab == "Login":
        st.subheader("Login to your account")
        username = st.text_input("Username", placeholder="Username")
        password = st.text_input("Password", type="password", placeholder="Password")
        if st.button("Login"):
            if authenticate(username, password):
                st.success(f"Welcome, {username}!")
                st.session_state.authenticated = True
                st.session_state.username = username
            else:
                st.error("Invalid username or password")

# Add custom CSS for better styling
st.markdown("""
    <style>
    .stTextInput>div>div>input {
        border: 2px solid #4CAF50;
        border-radius: 5px;
        padding: 10px;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    </style>
""", unsafe_allow_html=True)