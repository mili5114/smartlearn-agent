"""PDF Summary Tool — extracts text from a PDF and prints a structured summary."""

import os
import sys
from dotenv import load_dotenv
import openai
import pdfplumber


def load_client():
    """Load API key from .env and return an OpenRouter client."""
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit(
            "OPENROUTER_API_KEY is missing. Add it to .env and try again."
        )
    return openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def extract_text(path, page_range=None):
    """Extract text from a PDF, returning (pages_text, has_text).

    pages_text: list of (page_number, text) tuples for pages with content.
    has_text: True if at least one page has extractable text.
    page_range: optional (start, end) tuple to restrict which pages are extracted.
    """
    pages = []
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                if page_range and (i < page_range[0] or i > page_range[1]):
                    continue
                text = page.extract_text()
                if text and text.strip():
                    pages.append((i, text.strip()))
    except Exception as e:
        raise SystemExit(f"Error reading PDF: {e}")

    has_text = len(pages) > 0
    return pages, has_text


def build_prompt_text(pages):
    """Build prompt-ready text with page markers for the LLM."""
    blocks = []
    for page_num, text in pages:
        blocks.append(f"[PAGE {page_num} START]\n{text}\n[PAGE {page_num} END]")
    return "\n\n".join(blocks)


def parse_page_range(range_str):
    """Parse 'START-END' into (start, end).  Returns None + prints help on error."""
    parts = range_str.split("-")
    if len(parts) != 2:
        print(
            f"Oops! '--pages {range_str}' doesn't look right. "
            "The format is START-END (e.g., --pages 1-5)."
        )
        return None
    try:
        start = int(parts[0].strip())
        end = int(parts[1].strip())
    except ValueError:
        print(
            f"Oops! '--pages {range_str}' has non-numeric values. "
            "START and END must be integers (e.g., --pages 1-5)."
        )
        return None
    if start < 1:
        print(f"Oops! START page must be at least 1, but got {start}.")
        return None
    if end < start:
        print(
            f"Oops! END page ({end}) can't be smaller than "
            f"START page ({start})."
        )
        return None
    return (start, end)


def build_messages(prompt_text):
    """Build the system + user messages for the LLM call."""
    system_prompt = (
        "You are a precise document-summarization assistant. "
        "Summarize the provided text using ONLY what appears in it. "
        "Output exactly three sections with these headings:\n\n"
        "## Overview\n"
        "## Key Points\n"
        "## Limitations\n\n"
        "Rules:\n"
        "- Overview: 2-4 sentences summarising the document as a whole.\n"
        "- Key Points: 3-6 bullet points. Every bullet MUST end with a "
        "[Page X] citation referencing the page the information came from. "
        "Only cite pages actually present in the text (e.g. [Page 1], [Page 2]).\n"
        "- Limitations: 1-3 bullet points noting what the summary may miss "
        "(scope, missing details, unclear passages).\n"
        "- Do NOT invent page numbers. Only use the page markers provided.\n"
        "- Do NOT add extra commentary outside these three sections.\n\n"
        "--- DOCUMENT TEXT ---\n"
        f"{prompt_text}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Summarize this document."},
    ]


def main():
    args = sys.argv[1:]
    page_range = None

    # Parse --pages flag
    if "--pages" in args:
        idx = args.index("--pages")
        if idx + 1 >= len(args):
            print("Oops! --pages needs a value (e.g., --pages 1-5).")
            sys.exit(1)
        range_str = args[idx + 1]
        page_range = parse_page_range(range_str)
        if page_range is None:
            sys.exit(1)
        args.pop(idx)      # remove --pages
        args.pop(idx)      # remove the range value

    if len(args) != 1:
        print("Usage: python pdf_summary.py <path-to-pdf> [--pages START-END]")
        sys.exit(1)

    path = args[0]
    if not os.path.isfile(path):
        print(f"Error: '{path}' is not a file or does not exist.")
        sys.exit(1)

    pages, has_text = extract_text(path, page_range)

    if not has_text:
        print(
            "This PDF contains no extractable text. "
            "It may be a scanned document (image-only pages). "
            "OCR processing is not supported by this tool."
        )
        return

    client = load_client()
    prompt_text = build_prompt_text(pages)
    messages = build_messages(prompt_text)

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.5-flash-02-23",
            messages=messages,
            temperature=0.3,
        )
    except openai.APIError as e:
        print(f"API error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
