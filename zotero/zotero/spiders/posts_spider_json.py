import scrapy
import re


class PostsSpiderJSON(scrapy.Spider):
    name = 'posts_JSON'

    start_urls = json.load(open('zotero_links.json'))

    def is_addtional_page(self,url:str):
        return len(url.split('/'))>6
    
    def strip_message(self, message):
        return message.lstrip('<div class=\"Message\">\n').rstrip('</div>').strip()

    def parse(self, response):
        # clean data
        CLEANER = re.compile('<.*?>')

        postList = []

        # parse the op
        opTitleSelector = response.css('h1::text')[2]
        opSelector = response.css('a.Username::text')[0]
        opTimeSelector = response.css('time::attr(datetime)')[0]
        opMessageSelector = response.css('.Message')[0]

        op = opSelector.get().strip()
        title = opTitleSelector.get().strip()
        clean_op_message = clean_message = re.sub(CLEANER, '', opMessageSelector.get()).replace(
            '\n', '').replace('\r', '').strip()
        op_time = opTimeSelector.get().strip()
        postList.append({
            'type': 'IP',
            'author': op,
            'message': clean_op_message,
            'time': op_time
        })
        # parse the replies

        # loop through comments
        for comment in response.xpath("//ul[@class='MessageList DataList Comments']/*"):
            post_author = comment.css('a.Username::text').get().strip()
            postType = ""
            if post_author == op:
                postType = "OPR"
            else:
                postType = "NOPR"
            post_time = comment.css('time::attr(datetime)').get().strip()
            raw_message = comment.css('.Message')[0].get()
            clean_message = re.sub(CLEANER, '', raw_message).replace(
                '\n', '').replace('\r', '').strip()
            postList.append({
                'type': postType,
                'author': comment.css('a.Username::text').get(),
                'message': clean_message,
                'time': post_time
            })  
        
        tid = response.url.split('/')[4]
        if self.is_addtional_page(response.url):
            yield{
                "thread_id" : tid,
                "additional_posts": postList
            }
        else:
            yield {
                "thread_url": response.url,
                "thread_title": title,
                "posts": postList
            }

        # CLICK THROUGH NEXT PAGE
        next_link = response.css('a[rel=\"next\"]::attr(href)').extract_first()
        if next_link:
            yield scrapy.Request(next_link, callback=self.parse)

