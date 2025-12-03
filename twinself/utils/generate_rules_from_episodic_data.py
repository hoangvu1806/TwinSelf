"""
Generate procedural rules from episodic conversation examples using LLM analysis.
Refactored to use centralized configuration.
"""

import os
import json
from typing import List, Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from ..core.config import config
from ..core.exceptions import DataLoadingError

# --- Helper Functions ---


def load_episodic_examples(directory: str) -> List[Dict[str, str]]:
    """Load episodic examples from JSON files in the specified directory."""
    examples = []
    if not os.path.exists(directory):
        raise DataLoadingError(f"Episodic data directory '{directory}' does not exist.")

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and filename.endswith(".json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if "user_query" in item and "your_response" in item:
                                examples.append(item)
                            else:
                                print(
                                    f"Warning: Skipping malformed item in {filename}."
                                )
                    else:
                        print(
                            f"Warning: Skipping {filename}. Expected JSON list format."
                        )
            except json.JSONDecodeError as e:
                raise DataLoadingError(f"Error decoding JSON from {filename}: {e}")
            except Exception as e:
                raise DataLoadingError(f"Error loading {filename}: {e}")

    if not examples:
        raise DataLoadingError("No valid episodic examples found.")

    return examples


def generate_procedural_rules(
    episodic_examples: List[Dict[str, str]], llm_model_name: str = None
) -> List[Dict[str, str]]:
    """
    Use LLM to analyze episodic examples and generate procedural rules.

    Args:
        episodic_examples: List of conversation examples
        llm_model_name: LLM model to use. Uses config default if None.
    """
    if not episodic_examples:
        raise DataLoadingError("No episodic examples provided to generate rules from.")

    model_name = llm_model_name or config.chat_llm_model
    print(
        f"\n--- Analyzing {len(episodic_examples)} episodic examples with {model_name} ---"
    )

    # Format examples for the prompt
    formatted_examples = "\n\n".join(
        [
            f"User Query: {ex['user_query']}\nMy Response: {ex['your_response']}"
            for ex in episodic_examples
        ]
    )

    # Define the output format for the LLM
    # This is the literal JSON string that the LLM should see, defining its output structure.
    output_format_json_literal = json.dumps(
        {
            "rules": [
                {
                    "rule_name": "general_persona",
                    "rule_content": "Description of overall persona, e.g., friendly, expert, enthusiastic.",
                },
                {
                    "rule_name": "tone_guidelines",
                    "rule_content": "Specific instructions on tone, e.g., use emojis, be concise.",
                },
                {
                    "rule_name": "interaction_strategy",
                    "rule_content": "General interaction patterns, e.g., always ask follow-up questions.",
                },
                {
                    "rule_name": "fallback_behavior",
                    "rule_content": "How to handle unknown questions, e.g., suggest contacting real person.",
                },
            ]
        },
        indent=2,
    )
    output_format = """
{
"rules": [
    {"rule_name": "general_persona", "rule_content": "..."},
    {"rule_name": "tone_guidelines", "rule_content": "..."},
    {"rule_name": "interaction_strategy", "rule_content": "..."},
    {"rule_name": "fallback_behavior", "rule_content": "..."}
]
}
"""

    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an AI assistant specialized in analyzing conversation patterns and extracting "
                "procedural rules for a digital persona. Your goal is to infer the persona, tone, "
                "and interaction style based on the given conversation examples. "
                "Formulate these inferences as clear, actionable rules for an AI chatbot. "
                "Output the rules in JSON format as specified below. Be concise but comprehensive.",
            ),
            (
                "human",
                "Here are examples of conversation responses:\n\n"
                "{examples}\n\n"
                "Based on these examples, infer and define procedural rules for the AI chatbot persona, "
                "tone, and interaction strategy. Focus on general guidelines, not specific answers. "
                "Also, suggest rules for handling questions outside its knowledge base (fallback behavior). "
                "Output in the following JSON format, providing at least 4 distinct rules:\n"
                f"```json\n{output_format.replace('{','{{').replace('}','}}')}\n```",
            ),
        ]
    )

    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.7)
    parser = JsonOutputParser()
    chain = prompt_template | llm | parser

    try:
        raw_rules = chain.invoke({"examples": formatted_examples})

        # Ensure the output conforms to the expected list of dicts format
        if (
            isinstance(raw_rules, dict)
            and "rules" in raw_rules
            and isinstance(raw_rules["rules"], list)
        ):
            generated_rules = raw_rules["rules"]
            print(f"\nSuccessfully generated {len(generated_rules)} procedural rules.")
            return generated_rules
        else:
            print(
                f"Warning: LLM output did not match expected format. Raw output: {raw_rules}"
            )
            return []
    except Exception as e:
        print(f"Error invoking LLM for rule generation: {e}")
        return []


def save_generated_rules(
    rules: List[Dict[str, str]],
    output_dir: str,
    filename: str = "generated_procedural_rules.json",
):
    """
    Saves the generated procedural rules to a JSON file.
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=2, ensure_ascii=False)
        print(f"Generated rules saved to: {filepath}")
    except Exception as e:
        print(f"Error saving generated rules to file: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    print("\n--- Starting Procedural Rule Generation from Episodic Examples ---")

    try:
        # Load episodic examples
        episodic_examples = load_episodic_examples(config.episodic_data_dir)

        # Generate procedural rules using LLM
        generated_rules = generate_procedural_rules(episodic_examples)

        if generated_rules:
            # Save generated rules
            save_generated_rules(generated_rules, config.procedural_data_dir)
            print(f"Successfully generated {len(generated_rules)} procedural rules.")
        else:
            print("No rules were generated by the LLM.")

        print("\n--- Procedural Rule Generation Process Completed Successfully ---")

    except Exception as e:
        print(f"\n--- Error: {e} ---")
        exit(1)
