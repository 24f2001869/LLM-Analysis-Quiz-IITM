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
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--single-process'
                ]
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                java_script_enabled=True
            )
            return True
        except Exception as e:
            print(f"Browser startup failed: {e}")
            return False
    
    async def close(self):
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except:
            pass
    
    async def cleanup_memory(self):
        """Force cleanup to prevent memory leaks"""
        if hasattr(self, 'active_pages'):
            for page in list(self.active_pages):
                try:
                    await page.close()
                except:
                    pass
            self.active_pages.clear()
        gc.collect()
        
    async def get_page_content(self, url: str) -> dict:
        if not self.browser:
            return {
                'html': '',
                'text': 'Browser not available',
                'base64_content': '',
                'url': url,
                'status': 'browser_unavailable'
            }
        
        page = await self.context.new_page()
        try:
            # Set reasonable timeouts
            page.set_default_timeout(30000)
            page.set_default_navigation_timeout(30000)
            
            # Navigate with retry
            for attempt in range(2):
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                    break
                except Exception as e:
                    if attempt == 1:
                        raise e
                    await asyncio.sleep(1)
            
            # Wait for content
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)
            
            # Get content
            content = await page.content()
            text_content = await page.evaluate("() => document.body.innerText")
            
            # Check for base64
            base64_content = ""
            try:
                script_elements = await page.query_selector_all('script')
                for element in script_elements:
                    script_content = await element.inner_text()
                    if 'atob(' in script_content:
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
                'text': f"Page load error: {str(e)}",
                'base64_content': '',
                'url': url,
                'status': 'error',
                'error': str(e)
            }
        finally:
            await page.close()

browser_service = BrowserService()


