from Amem.agentic_memory.memory_system import AgenticMemorySystem
from agents import Agent,Runner
from dotenv import dotenv_values
import json
import asyncio
import click
import datetime


env = dotenv_values(".env")

with open("medmcqa/sample.json","r") as f:
    data = json.load(f)

def structureQuestion(n: int):
    structuredOut = f"""
    Question: {data[n]["question"]}
    Options:
    A. {data[n]["opa"]} 
    B. {data[n]["opb"]}
    C. {data[n]["opc"]}
    D. {data[n]["opd"]}
    Explanation: {data[n]["exp"]}
    """
    return structuredOut

def getTimeStamp():
    now = datetime.datetime.now()
    formatted = now.strftime("%Y%m%d%H%M")
    return formatted


@click.command()
@click.option("--memory", default=False,help="Run agent and flag to determine if memory is active or not")
def runAgent(memory: bool):
    if not memory:    
        async def agent_runner(n:int):
            result = await Runner.run(agent,
            f"""
            You will be asked a series of multiple choice medical questions. Please output your answer succinctly and simply along with the correct option.

            {data[n]["question"]}, options:

            A. {data[n]["opa"]},\nB. {data[n]["opb"]},\nC. {data[n]["opc"]},\nD. {data[n]["opd"]}
            """)
            with open ("agentoutput-nomem.md", "a") as f:
                f.write("\n"+ result.final_output)

        for i in range(1, len(data)+1):
            print(f"Running agent on question {i}...")
            asyncio.run(agent_runner(i))
    elif memory:
        memory_system = AgenticMemorySystem(
                model_name='all-MiniLM-L6-v2',  # Embedding model for ChromaDB
                llm_backend="openai",           # LLM backend (openai/ollama)
                llm_model="gpt-4o-mini"         # LLM model name
        )
        for i in range(0,len(data)):
            memory_id = memory_system.add_note(
                    content = structureQuestion(i),
                    tags = "unknown" if data[i]["topic_name"] == 'null' else data[i]["topic_name"],
                    category = data[i]["subject_name"],
                    timestamp = getTimeStamp()
                    )

        async def agent_runner_mem(n:int):
            related = memory_system.search_agentic(structureQuestion(n), k=2)
            memory_context = "\n".join(
                f"- {m['content']} (context: {m['context']}, tags: {m['tags']})"
                for m in related
            )

            result = await Runner.run(agent,
            f"""
            You will be asked a series of multiple choice medical questions. Please output your answer succinctly and simply along with the correct option.

            Here are related notes retrieved from your memory that may help:
            {memory_context}

            {data[n]["question"]}, options:

            A. {data[n]["opa"]},\nB. {data[n]["opb"]},\nC. {data[n]["opc"]},\nD. {data[n]["opd"]}
            """)
            with open("agentoutput-mem.md", "a") as f:
                f.write("\n"+ result.final_output)

        for i in range(0, len(data)):
            print(f"Running memory agent on question {i}...")
            asyncio.run(agent_runner_mem(i))


if __name__ == "__main__":
    agent = Agent(
            name="Medical Assistant",
            instructions="You answer medical questions accurately and concisely.",
            model = "gpt-4o-mini"
    )
    runAgent()



