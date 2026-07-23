"""Markdown refiner: cleans up raw markdown by stripping residuals and
enforcing paragraph separation."""

def MarkdownRefine(raw_markdown: str) -> str:
    lines = raw_markdown.split("\n")
    processed = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        processed.append(line)
    return "\n\n".join(processed)

