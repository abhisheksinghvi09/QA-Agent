import streamlit as st
from utils import QA_API_Client
import re

def clean_markdown_output(text):
    if not text:
        return ""
    text = re.sub(r"^```[a-zA-Z]*\n", "", text.strip())
    text = re.sub(r"\n```$", "", text.strip())
    return text

st.set_page_config(
    page_title="Autonomous QA Agent",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }
    h1 { font-family: 'Inter', sans-serif; font-weight: 700; letter-spacing: -1px; }
    h2, h3 { font-family: 'Inter', sans-serif; font-weight: 600; }
    
    .stSuccess { border-left: 4px solid #28a745; background-color: #f0fff4; }
    .stError { border-left: 4px solid #dc3545; background-color: #fff5f5; }
</style>
""", unsafe_allow_html=True)

if "api" not in st.session_state:
    st.session_state.api = QA_API_Client()

if "session_ready" not in st.session_state:
    if st.session_state.api.start_session():
        st.session_state.session_ready = True
        st.session_state.session_id = st.session_state.api.session_id
    else:
        st.session_state.session_ready = False

with st.sidebar:
    st.markdown("### 🧬 QA Cortex")
    st.markdown("---")
    
    if st.session_state.session_ready:
        st.success("System Operational")
        st.caption(f"Session: `{st.session_state.session_id[:8]}...`")
    else:
        st.error("Backend Offline")
        st.warning("Please ensure the API server is running.")
        if st.button("Retry Connection"):
            st.rerun()
            
    st.markdown("#### Workflow")
    st.markdown("1. **Ingest**: Upload Docs & HTML")
    st.markdown("2. **Plan**: Generate Test Cases")
    st.markdown("3. **Code**: Build Selenium Scripts")
    
    st.markdown("---")
    st.markdown("v2.0.0 | Production Build")

st.title("Autonomous QA Agent")
st.markdown("### Transform documentation into executable test automation.")

if not st.session_state.session_ready:
    st.info("Waiting for backend connection...")
    st.stop()

tab_ingest, tab_plan, tab_code = st.tabs([
    "1. Knowledge Base", 
    "2. Test Planning", 
    "3. Script Generation"
])

with tab_ingest:
    st.header("Upload Project Assets")
    st.markdown("To generate accurate tests, the agent needs to understand your project requirements and HTML structure.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_files = st.file_uploader(
            "Upload Requirements (MD/TXT) and Target HTML",
            accept_multiple_files=True,
            type=['md', 'txt', 'html', 'pdf', 'json']
        )
    
    with col2:
        st.info("**Tip:** Ensure you upload `checkout.html` and at least one requirement document (e.g., `product_specs.md`).")

    if uploaded_files and st.button("Build Knowledge Base", type="primary"):
        with st.spinner("Processing documents & vectorizing content..."):
            result = st.session_state.api.upload_documents(uploaded_files)
            
            if result["success"]:
                st.success(f"Success! {result['data']['message']}")
                st.session_state.knowledge_base_built = True
            else:
                st.error(f"Error: {result['error']}")

with tab_plan:
    st.header("Generate Test Plan")
    
    if not st.session_state.get("knowledge_base_built"):
        st.warning("⚠️ Please build the Knowledge Base in Tab 1 first.")
    else:
        st.markdown("Describe the feature you want to test. The agent will retrieve relevant rules from your docs.")
        
        user_query = st.text_area(
            "Testing Objective",
            value="Generate positive and negative test cases for the discount code feature.",
            height=100,
            help="Be specific about what feature you want to verify."
        )
        
        if st.button("Generate Test Cases", type="primary"):
            with st.spinner("Analyzing requirements..."):
                result = st.session_state.api.generate_test_plan(user_query)
                
                if result["success"]:
                    st.markdown("### Generated Test Plan")
                    
                    clean_table = clean_markdown_output(result["data"])
                    st.markdown(clean_table)
                    
                    st.session_state.last_plan = clean_table
                else:
                    st.error(f"Error generating plan: {result['error']}")

with tab_code:
    st.header("Generate Automation Script")
    
    if not st.session_state.get("knowledge_base_built"):
         st.warning("Please build the Knowledge Base in Tab 1 first.")
    else:
        st.markdown("Paste a specific test scenario to convert it into Python Selenium code.")
        
        test_case_input = st.text_area(
            "Test Scenario",
            placeholder="e.g., Verify that entering 'SAVE15' reduces the total price by 15%.",
            height=100
        )
        
        if st.button("Write Selenium Code", type="primary"):
            if not test_case_input:
                st.error("Please provide a test scenario.")
            else:
                with st.spinner("Writing code (Selectors, Logic, Assertions)..."):
                    result = st.session_state.api.generate_automation_script(test_case_input)
                    
                    if result["success"]:
                        st.subheader("Python Selenium Script")
                        st.code(result["data"], language="python")
                        st.caption("Copy this code into a .py file to run it.")
                    else:
                        st.error(f"Generation failed: {result['error']}")

