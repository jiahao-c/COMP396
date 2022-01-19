import scrapy
from bs4 import BeautifulSoup
import re
import json

class PostSpiderJSON(scrapy.Spider):
    name = 'posts_JSON'

    start_urls = json.load(open('audacity_links.json'))
    
    # get all authors
    username_xpath = '//p[contains(@class, "author")]//a[contains(@class, "username")]//text()'
    # get all posts
    post_text_xpath = '//div[@class="postbody"]//div[@class="content"]'
    title_css = '#page-body > h2 > a::text'
    time_xpath = '//span[@class="responsive-hide"]/following-sibling::text()'

    def clean_text(self, string):
        # CLEAN HTML TAGS FROM POST TEXT, MARK REPLIES TO QUOTES
        tags = ['blockquote']
        soup = BeautifulSoup(string, 'lxml')
        for tag in tags:
            for i, item in enumerate(soup.find_all(tag)):
                item.replaceWith('<reply-%s>=' % str(i + 1))
        return re.sub(r' +', r' ', soup.get_text()).strip()

   
    def parse(self, response):
        # get the thread ID from the response URL
        #thread_id = response.url.split('t=')[1].split(',')[0]
        thread_title = response.css(self.title_css)[0].get()
        # COLLECT FORUM POST DATA
        usernames = response.xpath(self.username_xpath).extract()
        # post_times =
        n = len(usernames)
        posts = []
        # extract &start=n from the response URL
        if '&start=' in response.url:
            pageIdx = int(response.url.split('&start=')[1]) / 10 
        else:
            pageIdx = 0
        if n > 0:
            post_texts = response.xpath(
                self.post_text_xpath).extract() or (n * [''])
            post_texts = [self.clean_text(s) for s in post_texts]
            post_times = response.xpath(
                self.time_xpath).extract() or (n * [''])
            op = str(usernames[0]).strip()
            # YIELD POST DATA
            for i in range(n):
                post_author = str(usernames[i]).strip()
                type = ""
                if i == 0:
                    type = "IP"
                elif post_author == op:
                    type = "OPR"
                else:
                    type = "NOPR"
                posts.append({
                    'author': post_author,
                    'message': post_texts[i],
                    'type': type,
                    'time': post_times[i].rstrip('\n\t\t\t')
                })
        lenThread = len(posts)
        yield{
            "thread_url": response.url,
            "page_idx":pageIdx,
            "thread_title": thread_title,
            "length": lenThread,
            "posts": posts
        }

        # CLICK THROUGH NEXT PAGE
        next_link = response.css('a[rel=\"next\"]::attr(href)').extract_first()
        if next_link:
            yield scrapy.Request(response.urljoin(next_link), callback=self.parse)
