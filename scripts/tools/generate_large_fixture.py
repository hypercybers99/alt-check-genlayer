import sys
import os

items = []
for i in range(1600):
    items.append(f'      <li><a href="/item/{i}">Link item {i}</a></li>')
list_html = '\n'.join(items)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Large Page Fixture</title>
</head>
<body>
  <header>
    <h1>Large Page Fixture</h1>
    <p>A fixture page containing over 3200 DOM elements to trigger element-cap partial audit.</p>
  </header>
  <main>
    <section>
      <h2>Section 1: Large List of Resource Links</h2>
      <ul>
{list_html}
      </ul>
    </section>
  </main>
  <footer>
    <p>&copy; 2026 AltCheck Fixtures</p>
  </footer>
</body>
</html>
"""

repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
fixtures_local = os.path.join(repo_root, "fixtures-local", "large.html")
with open(fixtures_local, "w", encoding="utf-8") as f:
    f.write(html)

fixtures_remote = os.path.join(os.path.dirname(repo_root), "alt-check-fixtures", "large.html")
with open(fixtures_remote, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Generated {fixtures_local} and {fixtures_remote}, bytes: {len(html.encode('utf-8'))}")
