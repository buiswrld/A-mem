"""Run a small MedMCQA evaluation with or without A-MEM retrieval.

This is an integration check: the memory condition stores the sampled
questions and options in A-MEM before asking the agent. It shows that a
MedMCQA row can move through A-MEM and back into the QA prompt; it is not a
held-out generalisation benchmark.
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from agents import Agent, Runner

from Amem.agentic_memory.memory_system import AgenticMemorySystem


SAMPLE_PATH = Path("medmcqa/sample.json")
ANSWER_LETTERS = "ABCD"


def load_questions(path: Path = SAMPLE_PATH) -> List[Dict[str, Any]]:
    with path.open() as file:
        return json.load(file)


def format_question(row: Dict[str, Any]) -> str:
    """Format a MedMCQA row as the question the answering agent will see."""
    return f"""Question: {row['question']}
Options:
A. {row['opa']}
B. {row['opb']}
C. {row['opc']}
D. {row['opd']}"""


def row_to_memory_note(row: Dict[str, Any]) -> str:
    """Create a clean A-MEM note without MedMCQA answer material."""
    return format_question(row)


def gold_letter(row: Dict[str, Any]) -> str:
    """Convert MedMCQA's one-based `cop` field to A, B, C, or D."""
    return ANSWER_LETTERS[int(row["cop"]) - 1]


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M")


def parse_prediction(output: str) -> Optional[str]:
    """Read a required {\"answer\": \"A\"} response, with a small fallback."""
    try:
        parsed = json.loads(output.strip())
        answer = str(parsed.get("answer", "")).upper()
        if answer in ANSWER_LETTERS:
            return answer
    except (json.JSONDecodeError, AttributeError):
        pass

    match = re.search(r'"answer"\s*:\s*"?([A-D])', output, flags=re.IGNORECASE)
    return match.group(1).upper() if match else None


def build_prompt(row: Dict[str, Any], retrieved_memories: List[str]) -> str:
    memories = "\n\n".join(f"- {memory}" for memory in retrieved_memories)
    if not memories:
        memories = "(No memories were retrieved.)"

    return f"""You are answering a medical multiple-choice question. Use the
retrieved memories if they are relevant, but do not assume they are always
correct.

Retrieved memories:
{memories}

{format_question(row)}

Return only valid JSON with exactly one key and one answer letter:
{{"answer":"A"}}
"""


def create_memory_system(rows: List[Dict[str, Any]]) -> AgenticMemorySystem:
    memory_system = AgenticMemorySystem(
        model_name="all-MiniLM-L6-v2",
        llm_backend="openai",
        llm_model="gpt-4o-mini",
    )
    for row in rows:
        memory_system.add_note(
            content=row_to_memory_note(row),
            tags=row["topic_name"] or "unknown",
            category=row["subject_name"],
            timestamp=timestamp(),
        )
    return memory_system


async def evaluate(
    agent: Agent, rows: List[Dict[str, Any]], memory: bool
) -> List[Dict[str, Any]]:
    memory_system = create_memory_system(rows) if memory else None
    results = []

    for index, row in enumerate(rows, start=1):
        retrieved = []
        if memory_system:
            matches = memory_system.search_agentic(format_question(row), k=2)
            retrieved = [match["content"] for match in matches]

        response = await Runner.run(agent, build_prompt(row, retrieved))
        prediction = parse_prediction(response.final_output)
        expected_note = row_to_memory_note(row)
        results.append(
            {
                "id": row["id"],
                "question": row["question"],
                "retrieved_memories": retrieved,
                "expected_memory_retrieved": expected_note in retrieved if memory else None,
                "raw_response": response.final_output,
                "prediction": prediction,
                "gold": gold_letter(row),
                "correct": prediction == gold_letter(row),
            }
        )
        print(f"Question {index}/{len(rows)}: {prediction or 'unparsed'} (gold: {gold_letter(row)})")

    return results


def write_results(path: Path, memory: bool, results: List[Dict[str, Any]]) -> None:
    correct = sum(result["correct"] for result in results)
    parsed = sum(result["prediction"] is not None for result in results)
    payload = {
        "run": {
            "memory_enabled": memory,
            "question_count": len(results),
            "correct": correct,
            "accuracy": correct / len(results) if results else 0,
            "parsed_predictions": parsed,
            "created_at": datetime.now().isoformat(),
        },
        "results": results,
    }
    with path.open("w") as file:
        json.dump(payload, file, indent=2)
    print(f"Wrote results to {path}")
    print(f"Accuracy: {correct}/{len(results)} ({payload['run']['accuracy']:.1%})")


@click.command()
@click.option("--memory/--no-memory", default=False, help="Enable A-MEM retrieval.")
@click.option("--output", type=click.Path(path_type=Path), default=None, help="Result JSON path.")
def run_agent(memory: bool, output: Optional[Path]) -> None:
    rows = load_questions()
    agent = Agent(
        name="Medical Assistant",
        instructions="You answer medical questions accurately and concisely.",
        model="gpt-4o-mini",
    )
    results = asyncio.run(evaluate(agent, rows, memory))
    tag = "memory" if memory else "nomem"
    default_output = f"evaluation-results-{tag}-{timestamp()}.json"
    write_results(output or Path(default_output), memory, results)


if __name__ == "__main__":
    run_agent()
