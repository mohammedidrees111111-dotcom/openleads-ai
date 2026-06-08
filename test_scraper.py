from app.services.scraper import GoogleScraper

s = GoogleScraper()
r = s.search('real estate agent', 'Dubai', 10)
print(f'Results: {len(r)}')
for x in r:
    name = x.get('name', '?')[:40]
    web = x.get('website', '?')[:40]
    email = x.get('email', '?')
    print(f'  - {name} | {web} | email={email}')
