import json
import base64
import requests
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

TOKEN_PATH = Path(__file__).parent.parent / "lib" / "tokens" / "ticktick_tokens.json"

class TickTickClient:
    """
    Client for the TickTick API using OAuth2 authentication.
    """
    def __init__(self):
        self._load_tokens()
        self.base_url = "https://api.ticktick.com/open/v1"
        self.token_url = "https://ticktick.com/oauth/token"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": 'ticktick-mcp-client'
        }

    def _load_tokens(self):
        if not TOKEN_PATH.exists():
            # Vytvoř složku a soubor, pokud neexistuje
            TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(TOKEN_PATH, "w", encoding="utf-8") as f:
                json.dump({}, f)
            raise RuntimeError(f"Soubor s tokenem neexistoval, vytvořen prázdný: {TOKEN_PATH}")
        
        try:
            with open(TOKEN_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    # Soubor je prázdný, vytvoř prázdný JSON
                    data = {}
                else:
                    data = json.loads(content)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Neplatný JSON v souboru {TOKEN_PATH}: {e}")
        
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")
        self.client_id = data.get("client_id")
        self.client_secret = data.get("client_secret")
        
        if not self.access_token:
            raise RuntimeError("Chybí access_token v ticktick_tokens.json. Přihlas se přes UI.")

    def _refresh_access_token(self) -> bool:
        if not self.refresh_token or not self.client_id or not self.client_secret:
            logger.warning("Chybí refresh token nebo client credentials.")
            return False
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode("ascii")).decode("ascii")
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        try:
            response = requests.post(self.token_url, data=token_data, headers=headers)
            response.raise_for_status()
            tokens = response.json()
            self.access_token = tokens.get('access_token')
            if 'refresh_token' in tokens:
                self.refresh_token = tokens.get('refresh_token')
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            # Ulož nové tokeny zpět do JSON souboru
            with open(TOKEN_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }, f, ensure_ascii=False, indent=2)
            logger.info("Access token refreshed successfully.")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing access token: {e}")
            return False

    def _make_request(self, method: str, endpoint: str, data=None) -> Dict:
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            if response.status_code == 401:
                logger.info("Access token expired. Attempting to refresh...")
                if self._refresh_access_token():
                    # Retry the request with the new token
                    if method == "GET":
                        response = requests.get(url, headers=self.headers)
                    elif method == "POST":
                        response = requests.post(url, headers=self.headers, json=data)
                    elif method == "DELETE":
                        response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            if response.status_code == 204 or response.text == "":
                return {}
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {"error": str(e)}

    # Project methods
    def get_projects(self) -> List[Dict]:
        """Gets all projects for the user."""
        return self._make_request("GET", "/project")
    
    def get_project(self, project_id: str) -> Dict:
        """Gets a specific project by ID."""
        return self._make_request("GET", f"/project/{project_id}")
    
    def get_project_with_data(self, project_id: str) -> Dict:
        """Gets project with tasks and columns."""
        return self._make_request("GET", f"/project/{project_id}/data")
    
    def create_project(self, name: str, color: str = "#F18181", view_mode: str = "list", kind: str = "TASK") -> Dict:
        """Creates a new project."""
        data = {
            "name": name,
            "color": color,
            "viewMode": view_mode,
            "kind": kind
        }
        return self._make_request("POST", "/project", data)
    
    def update_project(self, project_id: str, name: str = None, color: str = None, 
                       view_mode: str = None, kind: str = None) -> Dict:
        """Updates an existing project."""
        data = {}
        if name:
            data["name"] = name
        if color:
            data["color"] = color
        if view_mode:
            data["viewMode"] = view_mode
        if kind:
            data["kind"] = kind
            
        return self._make_request("POST", f"/project/{project_id}", data)
    
    def delete_project(self, project_id: str) -> Dict:
        """Deletes a project."""
        return self._make_request("DELETE", f"/project/{project_id}")
    
    # Task methods
    def get_task(self, project_id: str, task_id: str) -> Dict:
        """Gets a specific task by project ID and task ID."""
        return self._make_request("GET", f"/project/{project_id}/task/{task_id}")
    
    def create_task(self, title: str, project_id: str, content: str = None, 
                   start_date: str = None, due_date: str = None, 
                   priority: int = 0, is_all_day: bool = False) -> Dict:
        """Creates a new task."""
        data = {
            "title": title,
            "projectId": project_id
        }
        
        if content:
            data["content"] = content
        if start_date:
            data["startDate"] = start_date
        if due_date:
            data["dueDate"] = due_date
        if priority is not None:
            data["priority"] = priority
        if is_all_day is not None:
            data["isAllDay"] = is_all_day
            
        return self._make_request("POST", "/task", data)
    
    def update_task(self, task_id: str, project_id: str, title: str = None, 
                   content: str = None, priority: int = None, 
                   start_date: str = None, due_date: str = None) -> Dict:
        """Updates an existing task."""
        data = {
            "id": task_id,
            "projectId": project_id
        }
        
        if title:
            data["title"] = title
        if content:
            data["content"] = content
        if priority is not None:
            data["priority"] = priority
        if start_date:
            data["startDate"] = start_date
        if due_date:
            data["dueDate"] = due_date
            
        return self._make_request("POST", f"/task/{task_id}", data)
    
    def complete_task(self, project_id: str, task_id: str) -> Dict:
        """Marks a task as complete."""
        return self._make_request("POST", f"/project/{project_id}/task/{task_id}/complete")
    
    def delete_task(self, project_id: str, task_id: str) -> Dict:
        """Deletes a task."""
        return self._make_request("DELETE", f"/project/{project_id}/task/{task_id}")
    
    def create_subtask(self, subtask_title: str, parent_task_id: str, project_id: str, 
                      content: str = None, priority: int = 0) -> Dict:
        """
        Creates a subtask for a parent task within the same project.
        
        Args:
            subtask_title: Title of the subtask
            parent_task_id: ID of the parent task
            project_id: ID of the project (must be same for both parent and subtask)
            content: Optional content/description for the subtask
            priority: Priority level (0-3, where 3 is highest)
        
        Returns:
            API response as a dictionary containing the created subtask
        """
        data = {
            "title": subtask_title,
            "projectId": project_id,
            "parentId": parent_task_id
        }
        
        if content:
            data["content"] = content
        if priority is not None:
            data["priority"] = priority
            
        return self._make_request("POST", "/task", data)