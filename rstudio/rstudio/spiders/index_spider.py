
import scrapy
import json


class IndexSpider(scrapy.Spider):
    name = "posts_JSON"
    # read file with thread urls
    start_urls = json.load('rstudio_longlinks.json')

    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
        'DOWNLOAD_DELAY': 0.6,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 1
    }

    # Gets info of the responses including (author, text, mentions, time)
    def parse(self, response):
        publish_times = []
        publish_times.extend(response.css('*[itemprop=\"datePublished\"]::attr(datetime)').extract())
        publish_times.extend(response.css('*[itemprop=\"datePublished\"]::attr(content)').extract())
        ordered_times = sorted(publish_times)
        comments = response.css('div.topic-body')
        if len(comments)>len(ordered_times):
            comments.pop() # remove the navigation link, which is not a real comment

        op = comments[0].css('div span a span::text').extract_first()
        posts = []
        title = response.xpath(
            '//title/text()').extract_first().split('-')[0].strip()
        for idx, comment in enumerate(comments):
            author = comment.css('div span a span::text').extract_first()
            if(author == 'system'):
                continue

            message = ' '.join(comment.css('div.post p::text').extract())
            post_type = ''
            if idx == 0:
                post_type = 'IP'
            elif author == op:
                post_type = 'OPR'
            else:
                post_type = 'NOPR'
            posts.append({
                'author': author,
                'message': message,
                'type': post_type,
                'time': ordered_times[idx]
            })
        
        if "?page=" in response.url:
            tid = response.url.split('/')[-1].split('?')[0]
            yield{
                "thread_id" : tid,
                "additional_posts": posts
            }
        
        yield {
            'thread_url': response.url,
            'thread_title': title,
            'posts': posts
        }
        # CLICK THROUGH NEXT PAGE
        next_link = response.css('a[rel=\"next\"]::attr(href)').extract_first()
        if next_link:
            yield scrapy.Request(response.urljoin(next_link), callback=self.parse)


