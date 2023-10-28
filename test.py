import re


def parse_chapter_number(input_str):
    pattern = re.compile(
        r"(?:chapter|ch|issue|\/|\s|-|_)\s*(\d+(?:[\.-]\d+)?)", re.IGNORECASE
    )
    matches = pattern.findall(input_str)

    # Filter only those numbers which have preceding markers like "chapter", "ch" or "issue"
    filtered_matches = [
        m
        for m, full in [(m, f) for m in matches for f in input_str.split(m)]
        if "chapter" in full.lower() or "ch" in full.lower() or "issue" in full.lower()
    ]

    if filtered_matches:
        last_match = filtered_matches[-1]
        return (
            float(last_match.replace("-", "."))
            if ("." in last_match or "-" in last_match)
            else int(last_match)
        )
    elif matches:
        # If no filtered match is found, revert to the last found match as a fallback.
        last_match = matches[-1]
        return (
            float(last_match.replace("-", "."))
            if ("." in last_match or "-" in last_match)
            else int(last_match)
        )
    return None


# Test cases
test_cases = [
    '<a href="https://w2.tonikakukawaii.com/manga/tonikaku-cawaii-chapter-147-2/">tonikaku cawaii chapter 147.2</a>',
    '<a href="https://w2.tonikakukawaii.com/manga/tonikaku-cawaii-chapter-139-5/">',
    '"https://w2.tonikakukawaii.com/manga/tonikaku-cawaii-chapter-139-5/',
    "https://ak603.anime-kage.eu/ak/manga/fairy-tail-100-years-quest/129",
    "https://ak603.anime-kage.eu/ak/manga/kimi-wa-houkago-insomnia-manga/7",
    "https://ak603.anime-kage.eu/ak/mangafairy-tail-100-years-quest/71-5",
    "https://www.crunchyroll.com/manga/inside-mari/read/1",
    "https://w2.tonikakukawaii.com/manga/tonikaku-cawaii-chapter-113-5/",
    "chapter_3",
    "Please don’t bully me, nagatoro, Vol.4 Chapter 30: Let’s Play Rock, Paper, Scissors, Senpai",
    "https://nagatoromanga.com/manga/please-don-t-bully-me-nagatoro-vol-4-chapter-30-let-s-play-rock-paper-scissors-senpai/",
    "https://nagatoromanga.com/manga/please-don-t-bully-me-nagatoro-vol-4-chapter-30-5-omake-1-2-extra/",
]

expected_outputs = [147.2, 139.5, 139.5, 129, 7, 71.5, 1, 113.5, 3, 30, 30, 30.5]

for i, test_case in enumerate(test_cases):
    result = parse_chapter_number(test_case)
    print(f"For test case {i+1}, input: '{test_case}'")
    print(f"Expected output: {expected_outputs[i]}, Actual output: {result}")
    print("---")
