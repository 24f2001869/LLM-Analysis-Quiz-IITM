from playwright.async_api import async_playwright
import asyncio
import base64
from app.config import config

class BrowserService:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
    
    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=config.HEADLESS,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
    
    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def get_page_content(self, url: str) -> dict:
        page = await self.context.new_page()
        try:
            # Navigate to URL
            await page.goto(url, timeout=config.BROWSER_TIMEOUT, wait_until='networkidle')
            
            # Wait for JavaScript execution
            await page.wait_for_timeout(2000)
            
            # Get rendered content
            content = await page.content()
            
            # Extract text content
            text_content = await page.evaluate("""
                () => {
                    return document.body.innerText;
                }
            """)
            
            # Check for base64 encoded content (common in the project)
            base64_elements = await page.query_selector_all('script')
            base64_content = ""
            for element in base64_elements:
                script_content = await element.inner_text()
                if 'atob(' in script_content or 'base64' in script_content:
                    base64_content = script_content
            
            return {
                'html': content,
                'text': text_content,
                'base64_content': base64_content,
                'url': url
            }
            
        except Exception as e:
            raise Exception(f"Browser error: {str(e)}")
        finally:
            await page.close()

browser_service = BrowserService()