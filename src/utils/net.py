import time, random, requests, os
from dotenv import load_dotenv
load_dotenv()

UA = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36")
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))

def get(url, headers=None, timeout=None, retries=3):
    h = {"User-Agent": UA, "Accept-Language": "id,en;q=0.8"}
    if headers: h.update(headers)
    last_err = None
    for i in range(retries):
        try:
            r = requests.get(url, headers=h, timeout=timeout or TIMEOUT)
            r.raise_for_status()
            time.sleep(random.uniform(0.6, 1.4))
            return r
        except Exception as e:
            last_err = e
            time.sleep(1.2 * (i+1))
    raise last_err
