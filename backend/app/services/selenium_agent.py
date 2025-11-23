from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("selenium_agent")

class SeleniumAgent:
    def __init__(self):
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
            raise ValueError("Missing API Key in Settings")

        self.prompt = ChatPromptTemplate.from_template(
            """
            You are a Senior QA Automation Engineer. Write a Python Selenium script.
            
            TEST CASE:
            {test_case}
            
            HTML SOURCE:
            {html_content}
            
            REQUIREMENTS:
            1. Use 'webdriver_manager' and 'headless' Chrome options.
            2. Use robust selectors (ID, Name) from the provided HTML.
            3. Return ONLY the Python code. No markdown backticks.
            """
        )

    def generate_script(self, test_case: str, html_content: str):
        logger.info(f"Generating script for case: {test_case[:30]}...")
        chain = self.prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "test_case": test_case,
            "html_content": html_content
        })