import asyncio
import os

from browser_use import Agent
from langchain_ollama import ChatOllama

# Add project root to path for local imports
from utils.paths import ROOT as PROJECT_ROOT

os.sys.path.insert(0, str(PROJECT_ROOT))

async def main():
    """Auto-generate test cases by exploring a feature with browser automation and AI."""
    # 1. Setup the Local Model
    # 'num_ctx': 8192 keeps RAM usage low (approx 10-11GB total for a 14B model)
    print("✓ Initializing local LLM at http://localhost:11434...")
    llm = ChatOllama(
        model="qwen2.5-coder:14b-instruct-q4_K_M", 
        base_url="http://localhost:11434",
        num_ctx=8192, 
        temperature=0.0  # Low temperature is better for structured test cases
    )


    # 2. Define the Agent's task
    # We ask it to 'think' and explore a specific module
    task = (
        "Go to https://opensource-demo.orangehrmlive.com/. "
        "Explore the module PIM and generate test cases from functional, negative and edge case perspectives, "
        "including one edge case, mandatory form values, and negative test cases. "
        "Output the test cases in a clear list with detailed steps, test data to use, and expected results. "
        "Use the following format for each test case:\n"
        "Test Case Title: <title>\n"
        "Pre-conditions: <any setup needed>\n"
        "Test Steps:\n"
        "1. <step 1>\n"
        "2. <step 2>\n"
        "...\n"
        "Expected Results: <what should happen>\n"
    )

    agent = Agent(
        task=task,
        llm=llm,
    )

    # 3. Run it!
    print("✓ Starting browser automation and test case generation...")
    print("-" * 80)
    result = await agent.run()
    print("-" * 80)
    print("✓ Test case generation complete!")
    print("\n=== GENERATED TEST CASES ===\n")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
