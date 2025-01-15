from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from contextlib import asynccontextmanager
import utils
import webbrowser
import json
import signal
import sys
import file_operations
print("CHECKING data/chroma...", flush=True)
if not file_operations.os.path.exists("data/chroma"):
    file_operations.embed_file("info_v1.1.txt")

print("READING projects.json...", flush=True)
with open("data/projects.json", "r") as json_file:
    data = json.load(json_file)

# Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up the application...", flush=True)
    # Perform any setup tasks here
    yield  # This pauses until the shutdown phase
    print("Shutting down the application...")
    # Perform cleanup tasks here

app = FastAPI(lifespan=lifespan)
initial_message = True

# Set up templates and static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

class ChatMessage(BaseModel):
    message: str

@app.post("/chat/")
async def chat(input_message: ChatMessage):
    print(f"Received user message {(input_message)}", flush=True)
    user_message = input_message.message
    print("Starting generating the response...", flush=True)
    response = utils.chatbot_response(user_message)
    print("Response Generated:", response, flush=True)
    
    if "GitHub link in a new tab..." in response:
        project = utils.extract_project_name(response)
        project = utils.find_most_similar_project(project, data.keys())
        print(project)
        try: 
            webbrowser.open(data[project]["Project"][0])
        except:
            response = f"Ohh... It seems {project} is private or unavailable. Sorry!"
    return {"response": response}

# Signal handler for SIGINT or SIGTERM
def signal_handler(signal_received, frame):
    print("Signal received. Initiating shutdown...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

