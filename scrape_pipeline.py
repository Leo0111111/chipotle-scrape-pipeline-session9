import os
import re
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
SEARCH_QUERY = "Chipotle Mexican Grill investor relations annual report leadership"
SEARCH_LIMIT = 10
OUTPUT_DIR = Path("knowledge/raw")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:60]


def next_file_number(output_dir: Path) -> int:
    existing = list(output_dir.glob("[0-9][0-9]-*.md"))
    if not existing:
        return 1
    nums = []
    for f in existing:
        m = re.match(r"^(\d+)-", f.name)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1


def search_and_scrape() -> None:
    if not FIRECRAWL_API_KEY:
        raise ValueError("FIRECRAWL_API_KEY not set — add it to .env")

    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "query": SEARCH_QUERY,
        "limit": SEARCH_LIMIT,
        "scrapeOptions": {"formats": ["markdown"]},
    }

    print(f"Searching Firecrawl: '{SEARCH_QUERY}'")
    response = requests.post(
        "https://api.firecrawl.dev/v1/search",
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    results = response.json().get("data", [])
    print(f"Found {len(results)} results")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    start_num = next_file_number(OUTPUT_DIR)
    saved = 0

    for i, result in enumerate(results, start=start_num):
        title = result.get("title") or result.get("url", "unknown")
        url = result.get("url", "")
        markdown = result.get("markdown") or result.get("content", "")

        if not markdown:
            print(f"  Skipping (no markdown): {url}")
            continue

        slug = slugify(title)
        filename = f"{i:02d}-{slug}.md"
        filepath = OUTPUT_DIR / filename

        content = f"---\nsource: {url}\ntitle: {title}\n---\n\n{markdown}"
        filepath.write_text(content, encoding="utf-8")
        print(f"  Saved: {filename}")
        saved += 1

    print(f"\nDone — saved {saved} files to {OUTPUT_DIR}/")


if __name__ == "__main__":
    search_and_scrape()
