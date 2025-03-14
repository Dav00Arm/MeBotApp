import requests
import json
from openai import OpenAI
import file_operations
import test_messages
import re
import string

# Initialize memory (global or class-level variable)
chat_memory = []


client = OpenAI(
    api_key="Your OpenAI key"
)

def generate_chatgpt_response(retrieved_text, user_question, memory_limit=5):
    """
    Generate a response using ChatGPT with memory of recent interactions.
    
    Args:
        retrieved_text (str): Information to base the response on.
        user_question (str): The current question from the user.
        memory_limit (int): The maximum number of past interactions to remember.

    Returns:
        str: The response generated by ChatGPT.
    """
    global chat_memory

    # Add the current user question to memory
    chat_memory.append({"role": "user", "content": user_question})

    # Prepare context messages
    messages = [
        {
            "role": "system", 
            "content": test_messages.message1
        }
    ]

    # Add recent chat memory (limited to memory_limit interactions)
    messages.extend(chat_memory[-memory_limit * 2:])  # User and assistant pairs count as 2 messages

    # Add current user question with retrieved context
    messages.append({
        "role": "user",
        "content": (
            "You have received the following question:\n\n"
            f"{user_question}\n\n"
            f"Here is the relevant context (if available):\n{retrieved_text}\n"
            f"Here are previous user questions and your answers (if available):\n{chat_memory}\n"
        )
    })
    # Call the ChatGPT API
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use "gpt-4" for better responses if available
            messages=messages,
            temperature=0.3,  
        )
        
        # Get assistant's response
        assistant_response = response.choices[0].message.content

        # Add the assistant's response to memory
        chat_memory.append({"role": "assistant", "content": assistant_response})
        # print(100*"*","\n", messages, "\n", 100*"*")
        
        return assistant_response
    except Exception as e:
        return f"Error generating response: {e}"


def retrieve_information(question, context="", k=3):
    """
    Retrieve information using a similarity search, with optional context.
    
    Args:
        question (str): The user's question.
        context (str): Context from previous interactions.
        k (int): Number of relevant documents to retrieve.

    Returns:
        str: Retrieved information combined from the similarity search results.
    """
    enriched_query = question
    if context:
        enriched_query = f"{context}\n{question}"

    vectordb = file_operations.load_vectordb("data/chroma")
    docs = vectordb.similarity_search(enriched_query, k=k)
    return "\n".join([doc.page_content for doc in docs])


def get_context_from_memory(memory, memory_limit=5):
    """
    Extract relevant context from the chat memory.
    
    Args:
        memory (list): The chat memory.
        memory_limit (int): Number of recent interactions to consider.

    Returns:
        str: A string representation of recent interactions for context.
    """
    relevant_memory = memory[-memory_limit * 2:]  # Limit to recent interactions
    return "\n".join([f"{msg['role']}: {msg['content']}" for msg in relevant_memory if msg['role'] == 'assistant'])

# Chatbot logic
def chatbot_response(question):
    # if category:
    retrieved_text = retrieve_information(question, context=get_context_from_memory(chat_memory))
    if not retrieved_text.strip():
        return f"Sorry, I couldn't find relevant information."
    return generate_chatgpt_response(retrieved_text, question)
    
# Retrieving  the README.md file from GitHub
# project_name: Name of the project the readme.md is needed -> str
# return: readme as raw text -> str
def get_readme_content(project_name: str):
    data_json = "data/data.json"
    with open(data_json, 'r') as file:
        data = json.load(file)

    # Process and print each project and its details
    keys = data[project_name]

    try:
        # Send a GET request to fetch the raw content
        if isinstance(keys['ReadMe'], list):
            readme_content = ""
            for url in keys["ReadMe"]:
                response = requests.get(url)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

                # Print the content of the README.md file
                readme_content += response.text
                # print(f"{project_name}: Successful.")
            return readme_content
        
        elif keys["ReadMe"] is None:
            print(f"{project_name}: No ReadMe available.")
            return None
            
        else:
            response = requests.get(keys["ReadMe"])
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

            # Print the content of the README.md file
            readme_content = response.text
            return readme_content
            
    
    except requests.exceptions.RequestException as e:
        print(f"{project_name}. An error occurred: {e}")

def extract_project_name(sentence):
    # Extract the project name using a regular expression
    print("Sentence:", sentence)
    match = re.search(r"Opening (.+?)'s GitHub link in a new tab...", sentence)
    
    if match:  # Check if a match was found
        project_name = match.group(1)
        # Remove the word "project" if it is in the project name
        if "project" in project_name.lower():
            project_name = project_name.lower().replace("project", "").strip()
        if "**" in project_name:
            project_name = project_name.replace("**", "").strip()
        return project_name
    
    return "No project name found"

from difflib import get_close_matches

def find_most_similar_project(input_name, project_names):
    # Normalize the input name for comparison (convert to lowercase and remove spaces)
    input_name_normalized = input_name.lower().replace(" ", "")
    # Normalize project names as well
    normalized_projects = {name: name.lower().replace(" ", "") for name in project_names}
    
    # Get the closest matches using difflib
    matches = get_close_matches(input_name_normalized, normalized_projects.values(), n=1, cutoff=0.5)
    
    if matches:
        # Find the original project name from the normalized dictionary
        for original_name, normalized_name in normalized_projects.items():
            if normalized_name == matches[0]:
                return original_name
    return "No similar project found"  