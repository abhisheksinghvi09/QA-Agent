from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("rag_agent")

class TestGenAgent:
    def __init__(self, session_id: str):
        self.session_id = session_id

        if not settings.OPENAI_API_KEY:
             raise ValueError("OPENAI_API_KEY is missing in .env config")
             
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.OPENAI_API_KEY
        )
        
        self.vector_store = Chroma(
            collection_name=f"session_{session_id}", 
            persist_directory=settings.VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )
        
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )

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
            logger.error("No LLM API Key found in settings.")
            raise ValueError("LLM Configuration Error")

        self.prompt = ChatPromptTemplate.from_template(
            """
            You are an expert QA Automation Lead. Generate comprehensive test cases strictly based on the provided documentation.
            
            CONTEXT:
            {context}
            
            REQUEST: 
            {question}
            
            OUTPUT:
            Return a Markdown table with columns: | Test Case ID | Feature | Test Scenario | Expected Result | Source Document |
            """
        )

    def generate_tests(self, query: str):
        logger.info(f"Session {self.session_id}: Generating tests for query '{query}'")
        
        rag_chain = (
            {"context": self.retriever | self._format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        try:
            response = rag_chain.invoke(query)
            return response
        except Exception as e:
            logger.error(f"RAG Generation failed: {e}")
            return "Error generating test cases. Please ensure documents are uploaded."

    def _format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)