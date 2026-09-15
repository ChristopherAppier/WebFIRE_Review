import csv
import logging
import re
from pathlib import Path

import openai
import yaml
from openai import OpenAI

logger = logging.getLogger(__name__)


def select_prompts(config, paths):
    """
    Selects the appropriate system prompt for each pdf based on the contents at the beginning of the report and writes it to the report table.

    Args:
        config: Configuration settings for the prompt selection process.
        paths: Paths to the necessary files and directories.
    """
    # Logging the start of the prompt selection process
    logger.info(f"\n{'*' * 50}\n\nStarting prompt selection process\n")

    # Creating a list of chunk paths
    chunks = list_chunks(paths["chunk_dir"])

    # Looping through first chunk of each PDF
    for chunk_path in chunks:
        if chunk_path.stem.endswith("_chunk_000"):
            # Chooses the appropriate system prompt based on the contents of this chunk
            prompt_name = choose_system_prompt(chunk_path, config, paths)
            # Write the selected prompt to the report table
            save_to_table(chunk_path, prompt_name, paths["http_dir"])


def list_chunks(chunk_dir):
    """
    Creates a list of chunk names from the specified chunk directory.

    Args:
        chunk_dir: The directory containing the chunk files.

    Returns:
        A list of chunk names.
    """

    return sorted(f for f in Path(chunk_dir).iterdir() if f.is_file())


def choose_system_prompt(chunk_name, config, paths):
    """
    Chooses the appropriate system prompt based on the contents of the specified chunk.

    Args:
        chunk_name: The name of the chunk file.

    Returns:
        The selected system prompt as a string.
    """
    # Combining the system prompt selection prompt, the chunk, and system prompt descriptions
    instructions_prompt = load_system_prompt(paths, "selection")
    prompt_descriptions = load_system_prompt(paths, "review_desc")

    prompt_descriptions_text = yaml.safe_dump(prompt_descriptions, sort_keys=True)
    system_prompt = (
        f"{instructions_prompt}\n\nPrompt choices:\n{prompt_descriptions_text}"
    )

    with open(chunk_name, "r", encoding="utf-8") as f:
        chunk_text = f.read()

    # Sending the prompt to the model for system prompt selection
    response = choose_prompt(config, system_prompt, chunk_text, chunk_name)

    # Checking the model's response and defaulting to a generic prompt if the response is invalid
    prompt_name = check_model_response(response, prompt_descriptions.keys())

    return prompt_name


def load_system_prompt(paths, prompt_name):
    """Loads the appropriate system prompt based on the file type/name being reviewed (currently just uses a single default prompt for MVP implementation)"""  # TODO update

    # Load the list of prompts available from the prompts.yml
    prompt_bank_dir = paths["config_dir"] / "prompts.yml"

    with open(prompt_bank_dir, "r", encoding="utf-8") as f:
        prompt_bank = yaml.safe_load(f)

    # Selecting the appropriate prompt based on the file type/name (currently all use one default)
    prompt = prompt_bank[prompt_name]

    return prompt


def choose_prompt(config, system_prompt, chunk_text, chunk_name):
    """Gives a system prompt to a chosen AI model to conduct an analysis on the chunk of data"""

    try:
        logger.info(f"Choosing system prompt for {chunk_name.stem}")

        # Setting up the OpenAI client with the provided configuration
        client = OpenAI(
            api_key=config["llm_api_key"],
            base_url=config["llm_url"],
            timeout=config["llm_timeout"],
            max_retries=config["llm_retries"],
        )
        # Making the request to the OpenAI API with the specified model, system prompt, and chunk text
        response = client.responses.create(
            model=config["llm"]["review"], instructions=system_prompt, input=chunk_text
        )
        logger.info("System prompt chosen\n")

        return response.output_text

    except openai.APIConnectionError as e:
        logger.error(f"The server could not be reached: {e.__cause__}")
        return "The server could not be reached."
    except openai.RateLimitError:
        logger.error("A 429 status code was received; back off requests.")
        return "A 429 status code was received; back off requests."
    except openai.APIStatusError as e:
        logger.error(
            f"Another non-200-range status code was received: {e.status_code}, {e.response}"
        )
        return f"Another non-200-range status code was received: {e.status_code}, {e.response}"


def check_model_response(response, valid_prompts):
    """
    Checks the model's response and defaults to a generic prompt if the response is invalid.

    Args:
        response: The response from the model.

    Returns:
        The validated system prompt name as a string.
    """
    prompt_name = response.strip()

    if prompt_name in valid_prompts:
        return prompt_name
    logger.warning(f"Invalid response received: {response}. Defaulting to 'generic'.")
    return "generic"


def save_to_table(chunk_name, prompt_name, http_dir):
    """
    Records the selected prompt to the report table.

    Args:
        chunk_name: The name of the chunk file.
        prompt_name: The name of the selected system prompt.
        http_dir: The path to the HTTP directory containing the report table.
    """

    # Stripping the chunk suffix from the chunk name to find the original document name
    chunk_base = re.sub(r"_chunk_\d+$", "", Path(chunk_name).stem).lower()
    table_path = Path(http_dir) / "report_table.csv"

    # Checking if the report table exists before trying to read it
    if not table_path.exists():
        logger.error(f"report_table.csv not found at {table_path}")
        return

    # Reading the report table into memory so the matching row can be updated
    with open(table_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    # Adding the Prompt Name column if it is missing from the report table
    if "Prompt Name" not in fieldnames:
        fieldnames.append("Prompt Name")

    # Finding the corresponding row in the report table for the given chunk name
    match_found = False
    for row in rows:
        for doc_name in (row.get("Document List") or "").split("|"):
            doc_stem = Path(doc_name.strip()).stem.lower()
            if doc_stem == chunk_base:
                # Writing the selected prompt to the matching row in the Prompt Name column
                row["Prompt Name"] = prompt_name
                match_found = True
                logger.info(f"Saved system prompt '{prompt_name}' for {chunk_name}")
                break
        else:
            continue
        break

    if not match_found:
        logger.warning(f"No report table row matched chunk: {chunk_name}")

    # Rewriting the report table with the selected system prompt added
    with open(table_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    from common import startup

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = startup.initialize_project()

    select_prompts(config, paths)
