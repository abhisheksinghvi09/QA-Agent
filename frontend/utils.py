import requests
import os
import time

BASE_API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")

class QA_API_Client:
    def __init__(self):
        self.base_url = BASE_API_URL
        self.session_id = None

    def health_check(self):
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def start_session(self):
        try:
            resp = requests.post(f"{self.base_url}/session/start", timeout=5)
            if resp.status_code == 200:
                self.session_id = resp.json().get("session_id")
                return True
            return False
        except Exception:
            return False

    def upload_documents(self, files):
        if not self.session_id:
            return {"success": False, "error": "Session not active. Please refresh."}

        url = f"{self.base_url}/ingest"
        
        headers = {"session-id": self.session_id} 
        
        files_payload = [
            ("files", (f.name, f.getvalue(), f.type)) for f in files
        ]

        try:
            resp = requests.post(url, headers=headers, files=files_payload)
            if resp.status_code == 200:
                return {"success": True, "data": resp.json()}
            return {"success": False, "error": resp.json().get("detail", f"Error {resp.status_code}")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_test_plan(self, query):
        if not self.session_id:
            return {"success": False, "error": "Session lost."}

        try:
            payload = {"query": query, "session_id": self.session_id}
            resp = requests.post(f"{self.base_url}/generate-tests", json=payload)
            
            if resp.status_code == 200:
                return {"success": True, "data": resp.json().get("result")}
            return {"success": False, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_automation_script(self, test_case):
        if not self.session_id:
            return {"success": False, "error": "Session lost."}

        try:
            payload = {"test_case": test_case, "session_id": self.session_id}
            resp = requests.post(f"{self.base_url}/generate-script", json=payload)
            
            if resp.status_code == 200:
                return {"success": True, "data": resp.json().get("script")}
            return {"success": False, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}