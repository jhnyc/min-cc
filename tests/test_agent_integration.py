import os
import pytest
from min_cc.agent import CodingAgent
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def sandbox(tmp_path):
    """Fixture to create a temporary sandbox directory and change to it."""
    orig_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(orig_cwd)

@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set")
def test_agent_list_directory(sandbox):
    api_key = os.getenv("OPENROUTER_API_KEY")
    agent = CodingAgent(api_key=api_key)
    
    # Pre-create a file to see if the agent can find it
    with open("test_file.txt", "w") as f:
        f.write("sandbox test")
        
    response = agent.run("List the files in the current directory and tell me what you see.")
    
    assert "test_file.txt" in response.lower()

@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set")
def test_agent_create_file(sandbox):
    api_key = os.getenv("OPENROUTER_API_KEY")
    agent = CodingAgent(api_key=api_key)
    
    prompt = "Create a python script named 'invert.py' that implements a function to invert a binary tree."
    agent.run(prompt)
    
    assert os.path.exists("invert.py")
    with open("invert.py", "r") as f:
        content = f.read()
        assert "def invert" in content or "InvertTree" in content.lower()
