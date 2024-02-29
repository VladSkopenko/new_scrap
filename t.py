import asyncio
import aiohttp
import json
from lxml import html



class QuotePageScrapping:
    def __init__(self, main_url):
        self.main_url = main_url
        self.quotes = []
        self.authors = []

    async def fetch_page(self, session, url):
        async with session.get(url) as response:
            return await response.text()

    async def get_quotes_and_authors(self, url):
        async with aiohttp.ClientSession() as session:
            page_content = await self.fetch_page(session, url)
            page_tree = html.fromstring(page_content)

            quotes = page_tree.xpath('//div[@class="quote"]')
            for quote in quotes:
                temp_dict = {
                    'quote': quote.xpath('.//span[@class="text"]/text()')[0].strip(),
                    'author': quote.xpath('.//small[@class="author"]/text()')[0].strip(),
                    'tags': quote.xpath('.//div[@class="tags"]//meta[@class="keywords"]/@content')[0].split(",")
                }
                self.quotes.append(temp_dict)

            author_links = page_tree.xpath('//a[contains(@href, "/author/")]')
            for link in author_links:
                author_url = self.main_url + link.attrib["href"]
                author_content = await self.fetch_page(session, author_url)
                author_tree = html.fromstring(author_content)
                authors = author_tree.xpath('//div[@class="author-details"]')
                for author in authors:
                    temp_dict = {
                        'fullname': author.xpath('.//h3[@class="author-title"]/text()')[0].strip(),
                        'born_date': author.xpath('.//span[@class="author-born-date"]/text()')[0].strip(),
                        'born_location': author.xpath('.//span[@class="author-born-location"]/text()')[0].strip(),
                        'description': author.xpath('.//div[@class="author-description"]/text()')[0].strip(),
                    }
                    self.authors.append(temp_dict)

    async def scrape_all_pages(self, num_pages):
        tasks = []
        async with aiohttp.ClientSession() as session:
            for page_num in range(1, num_pages + 1):
                url = f"{self.main_url}/page/{page_num}/"
                task = asyncio.create_task(self.get_quotes_and_authors(url))
                tasks.append(task)
            await asyncio.gather(*tasks)

    def save_to_json(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


async def main():
    main_url = 'http://quotes.toscrape.com'
    num_pages = 10

    scraper = QuotePageScrapping(main_url)
    await scraper.scrape_all_pages(num_pages)

    scraper.save_to_json(scraper.quotes, 'quotes.json')
    scraper.save_to_json(scraper.authors, 'authors.json')


if __name__ == '__main__':
    asyncio.run(main())
