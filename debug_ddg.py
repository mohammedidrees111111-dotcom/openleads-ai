from ddgs import DDGS

keyword = "lawyer"
location = "Dubai"
max_results = 5
query = f"{keyword} {location}"

leads = []
with DDGS() as ddgs:
    for r in ddgs.text(query, max_results=max_results):
        leads.append(r)

print(f"Raw results: {len(leads)}")
for r in leads:
    title = r.get("title", "")
    link = r.get("href", "")
    snippet = r.get("body", "")
    blocked = any(x in link.lower() for x in ["duckduckgo.com", "google.com", "youtube.com"])
    print(f"  title={title[:50]} blocked={blocked}")
    print(f"  link={link[:80]}")
