"""
fix_missing_tags.py

Scans index.html for rows with empty/missing tags, determines
the source markdown file from the row's URL, reads the tags
from the frontmatter, and patches the HTML in-place.

Handles two frontmatter tag formats:
  1. Inline:  tags: ["A", "B"]
  2. Multiline YAML block:
       tags:
         [
           "A",
           "B",
         ]
"""

import os
import re
from bs4 import BeautifulSoup

HTML_PATH = r'c:\Users\munbo\bock-directory-page\index.html'
POSTS_DIR = r'c:\Users\munbo\blog-main-new\src\posts'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_tags_from_frontmatter(content: str) -> list:
    """
    Extract tags from markdown frontmatter.
    Supports:
      - tags: ["A", "B"]
      - tags: ['A', 'B']
      - tags:\n  [\n    "A",\n    "B",\n  ]
    Returns a list of tag strings (empty list if not found).
    """
    # Strip frontmatter block
    fm_match = re.match(r'^---\s*(.*?)\s*---', content, re.DOTALL)
    if not fm_match:
        return []
    frontmatter = fm_match.group(1)

    # Try inline: tags: ["A", "B", "C"]
    inline = re.search(r'^tags\s*:\s*\[(.+?)\]', frontmatter, re.MULTILINE)
    if inline:
        raw = inline.group(1)
        return [t.strip().strip('"').strip("'") for t in raw.split(',') if t.strip().strip('"').strip("'")]

    # Try multiline block:
    #   tags:
    #     [
    #       "A",
    #       "B",
    #     ]
    multi = re.search(r'^tags\s*:\s*\n\s*\[(.*?)\]', frontmatter, re.DOTALL | re.MULTILINE)
    if multi:
        raw = multi.group(1)
        tags = []
        for line in raw.splitlines():
            line = line.strip().strip(',')
            if not line:
                continue
            line = line.strip('"').strip("'")
            if line:
                tags.append(line)
        return tags

    # Try simple list:
    #   tags:
    #     - A
    #     - B
    list_match = re.search(r'^tags\s*:\s*\n((?:\s+-\s*.+\n?)+)', frontmatter, re.MULTILINE)
    if list_match:
        raw = list_match.group(1)
        tags = []
        for line in raw.splitlines():
            item = re.sub(r'^\s*-\s*', '', line).strip().strip('"').strip("'")
            if item:
                tags.append(item)
        return tags

    return []


def slug_from_url(url: str) -> str:
    """
    Extract the post slug from a bockdev.com posts URL.
    e.g. https://bockdev.com/posts/how-to-price.html  ->  how-to-price
    """
    basename = url.rstrip('/').split('/')[-1]
    return re.sub(r'\.html$', '', basename)


def get_tags_for_url(url: str) -> list:
    """
    Given a bockdev post URL, locate the .md source file and return its tags.
    Returns empty list if not found.
    """
    slug = slug_from_url(url)
    md_path = os.path.join(POSTS_DIR, f'{slug}.md')
    if not os.path.exists(md_path):
        print(f"  [WARN] Source file not found: {md_path}")
        return []

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return parse_tags_from_frontmatter(content)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def find_rows_with_empty_tags(soup: BeautifulSoup) -> list:
    """
    Return a list of <tr> elements where the .tags div has no non-empty spans.
    """
    tbody = soup.find('tbody')
    if not tbody:
        return []

    empty_rows = []
    for tr in tbody.find_all('tr'):
        tags_div = tr.find('div', class_='tags')
        if not tags_div:
            continue
        tags = [s.text.strip() for s in tags_div.find_all('span', class_='tag')]
        if not any(tags):           # all empty / no tags
            empty_rows.append(tr)
    return empty_rows


def fix_tags(dry_run: bool = False) -> None:
    print(f"Reading {HTML_PATH} ...")
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    empty_rows = find_rows_with_empty_tags(soup)
    print(f"Found {len(empty_rows)} row(s) with empty/missing tags.\n")

    fixed = 0
    skipped = 0

    for tr in empty_rows:
        a_tag = tr.find('a', class_='ref-link')
        url = a_tag['href'] if a_tag else ''
        title_div = tr.find('div', class_='post-title')
        title = title_div.text.strip() if title_div else '(no title)'

        # Only handle bockdev posts; extend elif blocks for other sources
        if 'bockdev.com/posts/' not in url:
            print(f"  [SKIP] Non-posts URL, skipping: {url}")
            skipped += 1
            continue

        tags = get_tags_for_url(url)
        if not tags:
            print(f"  [SKIP] No tags found in source for: {title}")
            skipped += 1
            continue

        print(f"  [FIX]  \"{title}\"")
        print(f"         Tags: {tags}")

        if not dry_run:
            # Rebuild the tags div
            tags_div = tr.find('div', class_='tags')
            tags_div.clear()
            for tag_text in tags:
                span = soup.new_tag('span')
                span['class'] = 'tag'
                span.string = tag_text
                tags_div.append(span)

        fixed += 1

    print(f"\nSummary: {fixed} row(s) fixed, {skipped} row(s) skipped.")

    if dry_run:
        print("[DRY RUN] No changes written.")
    else:
        with open(HTML_PATH, 'w', encoding='utf-8') as f:
            f.write(soup.prettify(formatter="html"))
        print(f"Saved updated HTML to {HTML_PATH}")


if __name__ == '__main__':
    import sys
    dry = '--dry-run' in sys.argv
    fix_tags(dry_run=dry)
