"""PDF clarifier: uses pdfplumber to extract x0 coordinates for layout-based
text classification. Adapted from Prism's PDF_Clarifier."""
import re
import os
from .markdown_refiner import MarkdownRefine

def _scene_heading_pattern() -> re.Pattern:
    return re.compile(r"^(EXT\./INT\.|EXT\.|INT\.)\s+[A-Z0-9].*")

def pdf_clarify(input_path: str, output_path: str | None = None) -> str:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input not found: {input_path}")
    import pdfplumber
    cleaned_lines = []
    in_body = False
    heading_re = _scene_heading_pattern()

    with pdfplumber.open(input_path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text_lines()
            for line_dict in lines:
                text = line_dict["text"].strip()
                if not text:
                    continue
                x0_points = line_dict["x0"]
                abs_inches = x0_points / 72.0

                if not in_body:
                    if heading_re.match(text):
                        in_body = True
                    else:
                        continue
                if "THE END" in text.upper():
                    break
                if text.isdigit():
                    continue
                text = re.sub(r"\s+", " ", text)

                # Strip parenthetical suffixes for character name test
                char_test = re.sub(r"\s*\((?:CONT['’]?D|CONTINUED|V\.O\.|O\.S\.)\)", "", text, flags=re.IGNORECASE).strip()

                if heading_re.match(text):
                    cleaned_lines.append(f"\n# {text}")
                elif char_test.isupper() and len(char_test) < 40 and not char_test.endswith((".", "?", "!")) and abs_inches > 3.0:
                    cleaned_lines.append(f"\n### {char_test}")
                elif text.startswith("(") and text.endswith(")"):
                    cleaned_lines.append(text)
                elif abs_inches > 2.0:
                    cleaned_lines.append(f"> {text}")
                else:
                    cleaned_lines.append(text)
            else:
                continue
            break

    raw_md = "\n".join(cleaned_lines).strip()
    final_md = MarkdownRefine(raw_md)
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_md)
    return final_md

