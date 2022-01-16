import scrapy
from bs4 import BeautifulSoup
import re


class PostSpiderJSON(scrapy.Spider):
    name = 'posts_JSON'

    # start_urls = json.load(open('vlc_links.json'))
    start_urls = ['https://forum.videolan.org/viewtopic.php?f=14&t=105955']
    # get all authors
    username_xpath = '//p[contains(@class, "author")]//a[contains(@class, "username")]//text()'
    # get all posts
    post_text_xpath = '//div[@class="postbody"]//div[@class="content"]'
    title_css = '#page-body > h2 > a::text'
    time_xpath = '//span[@class="responsive-hide"]/following-sibling::text()'

    def strip_message(self, message):
        return message.lstrip('<div class=\"Message\">\n').rstrip('</div>').strip()

    def clean_text(self, string):
        # CLEAN HTML TAGS FROM POST TEXT, MARK REPLIES TO QUOTES
        tags = ['blockquote']
        soup = BeautifulSoup(string, 'lxml')
        for tag in tags:
            for i, item in enumerate(soup.find_all(tag)):
                item.replaceWith('<reply-%s>=' % str(i + 1))
        return re.sub(r' +', r' ', soup.get_text()).strip()

    def parse(self, response):

        thread_title = response.css(self.title_css)[0].get()
        # COLLECT FORUM POST DATA
        usernames = response.xpath(self.username_xpath).extract()
        n = len(usernames)
        posts = []
        if n > 0:
            post_times = response.xpath(
                self.time_xpath).extract() or (n * [''])
            post_texts = response.xpath(
                self.post_text_xpath).extract() or (n * [''])
            post_texts = [self.clean_text(s) for s in post_texts]
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
        tid = response.url.split('&t=')[1].split('&')[0]

        if '&start=' in response.url:
            yield{
                "thread_id" : tid,
                "addtiinal_posts": posts
            }
        else:
            yield{
                "thread_url": response.url,
                "thread_title": thread_title,
                "posts": posts
            }

        # CLICK THROUGH NEXT PAGE
        next_link = response.css('a[rel=\"next\"]::attr(href)').extract_first()
        if next_link:
            yield scrapy.Request(response.urljoin(next_link), callback=self.parse)
