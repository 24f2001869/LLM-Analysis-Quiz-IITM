from playwright.async_api import async_playwright
import asyncio
import base64
import gc  # ADD THIS IMPORT
from app.config import config

class BrowserService:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.active_pages = set()  # CRITICAL: Track pages for cleanup
    
    async def start(self):
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',  # Prevents memory issues
                    '--disable-gpu',
                    '--disable-web-security',
                    '--single-process',  # Reduces memory usage
                    '--no-zygote',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--max_old_space_size=256'  # Limits memory
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
        """Proper cleanup to prevent memory leaks"""
        # Close all pages first
        for page in list(self.active_pages):
            try:
                await page.close()
            except:
                pass
        self.active_pages.clear()
        
        # Then close context and browser
        try:
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            print(f"Browser cleanup error: {e}")
        finally:
            gc.collect()  # Force garbage collection
    
    async def cleanup_memory(self):
        """Force cleanup to prevent memory leaks"""
        # Close any lingering pages
        for page in list(self.active_pages):
            try:
                await page.close()
            except:
                pass
        self.active_pages.clear()
        gc.collect()  # Now gc is imported
    
    async def get_page_content(self, url: str) -> dict:
        if not self.browser:
            return {
                'html': '',
                'text': 'Browser not available',
                'base64_content': '',
                'url': url,
                'status': 'browser_unavailable'
            }
        
        page = None
        try:
            page = await self.context.new_page()
            self.active_pages.add(page)  # TRACK the page
            
            # Reduced timeouts to prevent memory buildup
            page.set_default_timeout(15000)  # Reduced from 30000
            page.set_default_navigation_timeout(15000)
            
            # Single attempt navigation (reduced from 2 attempts)
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_load_state('networkidle')
            
            # Get only essential content
            content = await page.content()
            text_content = await page.evaluate("() => document.body.innerText")
            
            # Limited base64 extraction (only first script)
            base64_content = ""
            try:
                script_element = await page.query_selector('script')
                if script_element:
                    script_content = await script_element.inner_text()
                    if 'atob(' in script_content:
                        base64_content = script_content
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
            # CRITICAL: Always remove and close page
            if page:
                try:
                    self.active_pages.discard(page)
                    await page.close()
                except:
                    pass
            gc.collect()  # Force cleanup after each request

browser_service = BrowserService()
