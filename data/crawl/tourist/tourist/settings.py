# Scrapy settings for tourist project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "tourist"

SPIDER_MODULES = ["tourist.spiders"]
NEWSPIDER_MODULE = "tourist.spiders"
# Tắt obey robots.txt (thường chặn bot)
ROBOTSTXT_OBEY = False  

# Tăng số request song song
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 8

# Giảm delay (nếu web không chặn gắt)
DOWNLOAD_DELAY = 0.25  

# Tắt cookies (tránh overhead)
COOKIES_ENABLED = False  

# Tắt Telnet (ít khi cần)
TELNETCONSOLE_ENABLED = False  

# Tắt AutoThrottle (vì bạn muốn nhanh)
AUTOTHROTTLE_ENABLED = False  

# Tắt HTTP cache (tránh lưu cache gây chậm)
HTTPCACHE_ENABLED = False  

# Giữ encoding chuẩn
FEED_EXPORT_ENCODING = "utf-8"



