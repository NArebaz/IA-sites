import requests
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("localia.evaluator")

SOCIAL_DOMAINS = {
    "facebook.com","instagram.com","twitter.com","t.me","wa.me","whatsapp.com",
    "linkedin.com","yelp.com","foursquare.com","maps.google.com","google.com","tiktok.com"
}

class HTTPClient:
    def __init__(self, timeout=6):
        s = requests.Session()
        retries = Retry(total=2, backoff_factor=0.5, status_forcelist=(429,500,502,503,504))
        s.mount("https://", HTTPAdapter(max_retries=retries))
        s.mount("http://", HTTPAdapter(max_retries=retries))
        self.s = s
        self.timeout = timeout

    def head(self, url):
        return self.s.head(url, allow_redirects=True, timeout=self.timeout)

    def get(self, url):
        return self.s.get(url, allow_redirects=True, timeout=self.timeout)

class WebsiteEvaluator:
    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        self.client = HTTPClient(timeout=self.cfg.get("timeout", 6))
        self._cache = {}

    def is_social(self, url):
        try:
            host = urlparse(url).netloc.lower()
            for d in SOCIAL_DOMAINS:
                if d in host:
                    return True
        except Exception:
            return False
        return False

    def is_professional(self, url):
        if not url:
            return False
        if url in self._cache:
            return self._cache[url]
        try:
            if self.is_social(url):
                logger.debug("URL %s considerada social", url)
                self._cache[url] = False
                return False
            try:
                r = self.client.head(url)
            except Exception:
                r = None
            if not r or r.status_code >= 400:
                try:
                    r = self.client.get(url)
                except Exception:
                    r = None
            if r and r.status_code < 400:
                ct = (r.headers.get("content-type") or "").lower()
                if "text/html" in ct or "application/xhtml+xml" in ct:
                    try:
                        soup = BeautifulSoup(r.text[:20000], "html.parser")
                        if soup.find("nav") or soup.find("meta", {"name":"description"}) or soup.title:
                            self._cache[url] = True
                            return True
                    except Exception:
                        pass
            self._cache[url] = False
            return False
        except Exception as e:
            logger.debug("Erro avaliando site %s: %s", url, e)
            self._cache[url] = False
            return False
