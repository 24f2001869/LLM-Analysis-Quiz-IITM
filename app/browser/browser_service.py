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
            headless=True,  # Always headless in container
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            java_script_enabled=True
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
            # Set longer timeouts for slow pages
            page.set_default_timeout(45000)
            page.set_default_navigation_timeout(45000)
            
            # Navigate to URL with retry logic
            for attempt in range(3):
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise e
                    await asyncio.sleep(2)
            
            # Wait for network to be mostly idle
            await page.wait_for_load_state('networkidle')
            
            # Additional wait for JavaScript execution
            await asyncio.sleep(2)
            
            # Get rendered content
            content = await page.content()
            
            # Extract text content
            text_content = await page.evaluate("""
                () => {
                    return document.body.innerText;
                }
            """)
            
            # Check for base64 encoded content
            base64_content = ""
            try:
                script_elements = await page.query_selector_all('script')
                for element in script_elements:
                    script_content = await element.inner_text()
                    if 'atob(' in script_content or 'base64' in script_content:
                        base64_content = script_content
                        break
            except:
                pass
            
            return {
                'html': content,
                'text': text_content,
                'base64_content': base64_content,
                'url': url,
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'html': '',
                'text': f"Error loading page: {str(e)}",
                'base64_content': '',
                'url': url,
                'status': 'error',
                'error': str(e)
            }
        finally:
            await page.close()

browser_service = BrowserService()
