import json
import os
from datetime import datetime, timezone
from openai import OpenAI

# -----------------------------
# CONFIG
# -----------------------------

OUTPUT_FILE = "future-news.xml"
MEMORY_FILE = "world_state.json"
HEADLINES_PER_RUN = 10

CHANNEL_TITLE = "Interstellar Systems Newswire"
CHANNEL_DESCRIPTION = "Official reports from human-colonized space, Year 2479"
CHANNEL_LINK = "https://YOUR_GITHUB_USERNAME.github.io/future-news"

MODEL = "gpt-4.1-mini"  # stable, cheap, good tone control

# -----------------------------
# PROMPT PACK (DO NOT DRIFT)
# -----------------------------

SYSTEM_PROMPT = """
You are an interstellar news wire service in the year 2479.

Writing rules (mandatory):
- Tone is calm, factual, restrained, professional
- Style is Reuters / Associated Press
- No humor, no irony, no poetic language
- No exclamation points
- No second-person language
- Headlines sound routine, not sensational

World assumptions:
- Humanity has colonized nearby star systems and parts of Andromeda
- Advanced technologies exist (teleportation gates, stellar engineering, AI governance)
- These technologies are common and treated as infrastructure

Output rules:
- Headlines only
- One sentence per headline
- No numbering
- No quotation marks
"""

USER_PROMPT_TEMPLATE = """
Current world state:
{world_state}

Generate {count} headlines dated in the year 2479.

Guidelines:
- Reference existing locations and technologies when appropriate
- Occasionally introduce a new location or system event
- Treat major events with understatement
- Avoid repeating exact phrasing from earlier headlines
"""

# -----------------------------
# LOAD / SAVE WORLD MEMORY
# -----------------------------

def load_world_state():
    if not os.path.exists(MEMORY_FILE):
        return {
            "year": 2479,
            "known_systems": [
                "Epsilon Eridani",
                "Kepler-442",
                "Andromeda Transit Hub",
                "Tau Ceti"
            ],
            "technologies": [
                "Teleportation Gates",
                "Stellar Shield Arrays",
                "Quantum Courier Network",
                "Autonomous Governance AIs"
            ],
            "recent_events": []
        }

    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_world_state(state):
    with open(MEMORY_FILE, "w") as f:
        json.dump(state, f, indent=2)


# -----------------------------
# GENERATE HEADLINES
# -----------------------------

def generate_headlines(world_state):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    user_prompt = USER_PROMPT_TEMPLATE.format(
        world_state=json.dumps(world_state, indent=2),
        count=HEADLINES_PER_RUN
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )

    text = response.choices[0].message.content
    headlines = [line.strip() for line in text.split("\n") if line.strip()]

    return headlines


# -----------------------------
# BUILD RSS
# -----------------------------

def build_rss(headlines):
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    items = ""
    for i, headline in enumerate(headlines):
        guid = f"future-{int(datetime.now().timestamp())}-{i}"
        items += f"""
    <item>
      <title>{headline}</title>
      <pubDate>{now}</pubDate>
      <guid>{guid}</guid>
    </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{CHANNEL_TITLE}</title>
    <description>{CHANNEL_DESCRIPTION}</description>
    <link>{CHANNEL_LINK}</link>
    {items}
  </channel>
</rss>
"""
    return rss.strip()


# -----------------------------
# MAIN
# -----------------------------

def main():
    world_state = load_world_state()
    headlines = generate_headlines(world_state)

    # Update memory with recent events
    world_state["recent_events"] = (
        headlines + world_state["recent_events"]
    )[:20]

    save_world_state(world_state)

    rss = build_rss(headlines)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(rss)

    print(f"Generated {len(headlines)} headlines.")


if __name__ == "__main__":
    main()
