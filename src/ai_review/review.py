import csv
import json
import logging
import random
import re
from datetime import datetime, timezone

import openai
import yaml
from openai import OpenAI

logger = logging.getLogger(__name__)


class ReviewRequestError(RuntimeError):
    """Raised when the configured review service cannot complete a request."""


class InvalidReviewResponse(ValueError):
    """Raised when a model response does not match the review contract."""


def review_chunks(config, paths):
    logger.info(
        f"\n{'*' * 50}\n\nAnalyzing text chunks using: {config['llm']['review']}\n"
    )

    chunk_paths = sorted(paths["chunk_dir"].glob("*.txt"))
    if not chunk_paths:
        logger.warning("No text chunks found in %s", paths["chunk_dir"])
        return {"attempted": 0, "succeeded": 0, "skipped": 0, "failed": 0}

    counts = {"attempted": len(chunk_paths), "succeeded": 0, "skipped": 0, "failed": 0}
    for chunk_name in chunk_paths:
        try:
            review_single_chunk(config, paths, chunk_name)
        except InvalidReviewResponse as error:
            counts["skipped"] += 1
            logger.warning("Skipping chunk %s: %s", chunk_name.name, error)
        except (
            ReviewRequestError,
            OSError,
            csv.Error,
            yaml.YAMLError,
            KeyError,
            TypeError,
        ) as error:
            counts["failed"] += 1
            logger.error("Review failed for chunk %s: %s", chunk_name.name, error)
        except Exception:
            counts["failed"] += 1
            logger.exception("Unexpected review failure for chunk %s", chunk_name.name)
        else:
            counts["succeeded"] += 1

    log_summary = (
        logger.info if counts["failed"] == counts["skipped"] == 0 else logger.warning
    )
    log_summary(
        "LLM review finished: attempted=%d succeeded=%d skipped=%d failed=%d",
        counts["attempted"],
        counts["succeeded"],
        counts["skipped"],
        counts["failed"],
    )
    return counts


def review_single_chunk(config, paths, chunk_name):
    """Review one text chunk and store its validated result."""

    file_name = find_file_name(paths, chunk_name)
    file_info = pull_file_info(paths, file_name)

    system_prompt, prompt_name = load_system_prompt(
        paths, file_info.get("Prompt Name"), return_prompt_name=True
    )

    if chunk_name.stem.endswith("_chunk_000"):
        chunk_text = chunk_name.read_text(encoding="utf-8")
    else:
        chunk_zero = (
            paths["chunk_dir"] / f"{chunk_name.stem.split('_chunk_')[0]}_chunk_000.txt"
        )
        chunk_zero_text = chunk_zero.read_text(encoding="utf-8")
        current_chunk_text = chunk_name.read_text(encoding="utf-8")
        chunk_text = chunk_zero_text + "\n\n" + current_chunk_text

    raw_output, think_output, t_start, t_end = single_analysis(
        config, chunk_name, chunk_text, system_prompt
    )

    json_output = json_check(raw_output)

    audit_flag = json_output["issue_flag"] == 1 or random.random() < (
        config["audit_chance"] / 100
    )

    t_total = int(
        (
            datetime.fromisoformat(t_end) - datetime.fromisoformat(t_start)
        ).total_seconds()
    )

    payload = {
        "audit_flag": audit_flag,
        "file_name": file_name,
        "chunk_name": chunk_name.stem,
        "organization": file_info.get("Organization"),
        "facility": file_info.get("Facility"),
        "city": file_info.get("City"),
        "state": file_info.get("State"),
        "report_type": file_info.get("Report Type"),
        "report_subtype": file_info.get("Report Sub Type"),
        "submission_date": file_info.get("Submission Date"),
        "review_start_time": t_start,
        "review_end_time": t_end,
        "total_review_time": t_total,
        "think_output": think_output,
        "prompt_name": prompt_name,
    }

    json_output.update(payload)

    save_path = paths["review_dir"] / f"{chunk_name.stem}.json"
    with open(save_path, "w", encoding="utf-8") as output_file:
        json.dump(json_output, output_file, indent=2)


def single_analysis(config, chunk_name, chunk_text, sys_prompt):
    """Gives a system prompt to a chosen AI model to conduct an analysis on the chunk of data"""

    t_start = datetime.now(timezone.utc).isoformat()

    try:
        logger.info(f"Reviewing {chunk_name.stem}")

        # Setting up the OpenAI client with the provided configuration
        client = OpenAI(
            api_key=config["llm_api_key"],
            base_url=config["llm_url"],
            timeout=config["llm_timeout"],
            max_retries=config["llm_retries"],
        )
        # Making the request to the OpenAI API with the specified model, system prompt, and chunk text
        response = client.responses.create(
            model=config["llm"]["review"], instructions=sys_prompt, input=chunk_text
        )
        t_end = datetime.now(timezone.utc).isoformat()
        logger.info("Review complete\n")

        # Capturing the "think" output from the response if it exists, otherwise setting it to None
        think_output = (
            "\n".join(
                part.text
                for item in (response.output or [])
                if getattr(item, "type", None) == "reasoning"
                for part in (getattr(item, "summary", None) or [])
                if getattr(part, "text", None)
            )
            or None
        )

        return response.output_text, think_output, t_start, t_end

    except openai.APIConnectionError as error:
        raise ReviewRequestError("review service connection failed") from error
    except openai.RateLimitError as error:
        raise ReviewRequestError("review service rate limit exceeded") from error
    except openai.APIStatusError as error:
        raise ReviewRequestError(
            f"review service returned HTTP {error.status_code}"
        ) from error


def load_system_prompt(paths, prompt_name, return_prompt_name=False):
    """Loads the appropriate system prompt based on the file type/name being reviewed"""

    # Load the list of prompts available from the prompts.yml
    prompt_bank_dir = paths["config_dir"] / "prompts.yml"

    with open(prompt_bank_dir, "r", encoding="utf-8") as f:
        prompt_bank = yaml.safe_load(f)

    review_prompts = prompt_bank["review"]
    prompt_name = (prompt_name or "").strip() or "generic"

    if prompt_name not in review_prompts:
        logger.warning(
            f"Invalid or missing prompt name '{prompt_name}'. Defaulting to 'generic'."
        )
        prompt_name = "generic"

    # Selecting the appropriate prompt based on the file type/name
    prompt = review_prompts[prompt_name]

    if return_prompt_name:
        return prompt, prompt_name

    return prompt


def json_check(raw_string):
    """Parse and validate the model's JSON review response."""

    if not isinstance(raw_string, str):
        raise InvalidReviewResponse("Model response must be text containing JSON")

    cleaned = raw_string.strip()

    # Strip markdown fences if present
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```")
        cleaned = cleaned.removesuffix("```").strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise InvalidReviewResponse(
            f"Model returned invalid JSON: {error.msg}"
        ) from error

    if not isinstance(result, dict):
        raise InvalidReviewResponse("Model response must be a JSON object")

    required_fields = {"issue_flag", "issue_descr", "conf_score", "importance"}
    missing_fields = sorted(required_fields - result.keys())
    if missing_fields:
        raise InvalidReviewResponse(
            f"Model response is missing required fields: {', '.join(missing_fields)}"
        )

    issue_flag = result["issue_flag"]
    if isinstance(issue_flag, bool) or issue_flag not in (0, 1):
        raise InvalidReviewResponse("Model field 'issue_flag' must be 0 or 1")
    if not isinstance(result["issue_descr"], str):
        raise InvalidReviewResponse("Model field 'issue_descr' must be a string")
    for field_name in ("conf_score", "importance"):
        value = result[field_name]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= 10
        ):
            raise InvalidReviewResponse(
                f"Model field '{field_name}' must be a number from 0 to 10"
            )

    return result


def store_for_audit(config, paths):
    """Stores associated chunks and the output JSON in an auditing folder for audit at a later time based on issue flags and audit chance defined in settings.yml"""

    logger.info(
        f"\n Selecting all reviews with issued flagged and {config['audit_chance']}% of all other reviews for auditing"
    )

    # PLACEHOLDER FUNCTION - ADD FUNCTIONALITY


def find_file_name(paths, chunk_name):
    """Finds the original file name for a chunk using Document List in report_table.csv."""

    chunk_base = re.sub(r"_chunk_\d+$", "", chunk_name.stem).lower()
    table_path = paths["http_dir"] / "report_table.csv"

    if not table_path.exists():
        return chunk_base

    with open(table_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for doc_name in (row.get("Document List") or "").split("|"):
                doc_name = doc_name.strip()
                if not doc_name:
                    continue

                doc_stem = doc_name.rsplit(".", 1)[0].lower()
                if doc_stem == chunk_base:
                    return doc_name

    return chunk_base


def pull_file_info(paths, file_name):
    """Finds the row for file_name in report_table.csv and returns key file metadata."""

    table_path = paths["http_dir"] / "report_table.csv"
    if not table_path.exists():
        return {}

    target = file_name.lower().strip()

    with open(table_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_names = [
                name.strip()
                for name in (row.get("Document List") or "").split("|")
                if name.strip()
            ]

            for doc_name in doc_names:
                if doc_name.lower() == target:
                    return {
                        "Organization": row.get("Organization"),
                        "Facility": row.get("Facility"),
                        "City": row.get("City"),
                        "State": row.get("State"),
                        "Report Type": row.get("Report Type"),
                        "Report Sub Type": row.get("Report Sub Type"),
                        "Submission Date": row.get("Submission Date"),
                        "Prompt Name": row.get("Prompt Name"),
                    }

    return {}


if __name__ == "__main__":
    from common import startup

    # Setting up logging and loading configuration options and paths from settings.yml
    config, paths = startup.initialize_project()

    review_chunks(config, paths)
