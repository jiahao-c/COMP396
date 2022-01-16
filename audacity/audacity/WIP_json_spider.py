import scrapy
from bs4 import BeautifulSoup
import re


class PostSpiderJSON(scrapy.CrawlSpider):
    name = 'posts_JSON_CrawlSpider'

    start_urls = ["https://forum.audacityteam.org/viewtopic.php?f=46&t=121645"]
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

    def parse_additional_page(self, response,item):
        # COLLECT FORUM POST DATA
        usernames = response.xpath(self.username_xpath).extract()
        # post_times =
        n = len(usernames)
        posts = []
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
        item['posts'].extend(posts)

    def parse(self, response):
        item = scrapy.Item()

        # get the thread ID from the response URL
        #thread_id = response.url.split('t=')[1].split(',')[0]
        thread_title = response.css(self.title_css)[0].get()
        # COLLECT FORUM POST DATA
        usernames = response.xpath(self.username_xpath).extract()
        # post_times =
        n = len(usernames)
        posts = []
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
        item['thread_url'] = response
        item['thread_title'] = thread_title
        item['thread_posts'] = posts
        # CLICK THROUGH NEXT PAGE
        next_link = response.css('a[role=\"button\"]::attr(href)').extract_first()
        if next_link:
            return response.follow(response.urljoin(next_link),self.parse_additional_page, cb_kwargs=dict(item=item))
        else:
            return item


   
        