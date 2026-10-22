"""Capture the real Swagger UI from a locally running service.

Optional tooling: pip install playwright; playwright install chromium
Run from the repository root: python docs/capture_docs.py
No credentials are entered or captured by this script.
"""
from pathlib import Path
import argparse
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8000/docs')
args = parser.parse_args()
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 820})
    page.goto(args.url, wait_until='networkidle')
    page.get_by_role('heading', name='Task Service', exact=False).wait_for()
    page.screenshot(path=str(Path(__file__).with_name('swagger-ui.png')))
    browser.close()
