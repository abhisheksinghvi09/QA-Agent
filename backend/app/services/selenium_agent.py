import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Import Settings & Logger
from app.core.config import settings
from app.core.logger import get_logger

# Import LLM Clients
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

logger = get_logger("selenium_agent")

class SeleniumAgent:
    def __init__(self, session_id: str):
        self.session_id = session_id
        
        # 1. Initialize Embeddings (Must match IngestionService)
        # Check if using OpenAI or fallback
        if settings.OPENAI_API_KEY:
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY
            )
        else:
            # Fallback for local dev if needed, but per previous steps we use OpenAI
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # 2. Connect to the Session-Specific Vector Store
        self.vector_store = Chroma(
            collection_name=f"session_{self.session_id}",
            persist_directory=settings.VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )
        
        # 3. Create Retriever
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 2} # Fetch top 2 relevant rules
        )

        # 4. Initialize LLM
        if settings.GROQ_API_KEY:
            self.llm = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model="llama3-70b-8192",
                temperature=0.1
            )
        elif settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model="gpt-4o",
                temperature=0.1
            )
        else:
            raise ValueError("Missing LLM API Key in Settings")

        # 5. Define the "Smart" Prompt
        # It now includes {context} from the Vector DB
        self.prompt = ChatPromptTemplate.from_template(
            """
            You are a Senior QA Automation Engineer. Write a Python Selenium script to automate the following test case.
            
            1. TEST CASE:
            {test_case}
            
            2. DOCUMENTATION RULES (Logic/UI requirements):
            {context}
            
            3. TARGET HTML PAGE SOURCE (For Selectors):
            {html_content}
            
            REQUIREMENTS:
            - Use 'webdriver_manager' and 'headless' Chrome options.
            - Use robust selectors (ID, Name, CSS) based strictly on the provided HTML.
            - ASSERTIONS: Use the DOCUMENTATION RULES to write specific assertions (e.g., if doc says error is red, check CSS color).
            - If the documentation contradicts the HTML, trust the HTML for selectors but note the logic discrepancy in comments.
            - Return ONLY the Python code. No markdown backticks.
            """
        )

    def generate_script(self, test_case: str, html_content: str):
        logger.info(f"Session {self.session_id}: Generating script for '{test_case[:20]}...'")
        
        # Helper to format docs
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # Define the Chain: Retrieve Context -> Pass to Prompt -> LLM
        chain = (
            {
                "context": self.retriever | format_docs, 
                "test_case": RunnablePassthrough(),
                "html_content": lambda x: html_content # Pass raw HTML through
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        try:
            # We invoke with just the test_case first (for retriever), 
            # but we need to inject html_content into the chain inputs manually
            # So we restructure the invoke:
            
            # Retrieve specific docs relevant to the test case
            relevant_docs = self.retriever.invoke(test_case)
            context_str = format_docs(relevant_docs)
            
            logger.info(f"Retrieved {len(relevant_docs)} context chunks for scripting.")
            
            # Final Generation
            response = self.prompt.invoke({
                "context": context_str,
                "test_case": test_case,
                "html_content": html_content
            })
            
            return self.llm.invoke(response).content
            
        except Exception as e:
            logger.error(f"Script Generation Failed: {e}")
            return f"# Error generating script: {str(e)}"