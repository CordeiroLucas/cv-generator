import asyncio
from playwright.async_api import async_playwright
import os

async def html_para_pdf(html_content, output_path):
    """
    Converte HTML em PDF usando Playwright (Chromium).
    Garante que o design CSS premium seja respeitado.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Define o conteúdo HTML na página
        await page.set_content(html_content, wait_until="networkidle")
        
        # Gera o PDF com configurações de A4
        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "0cm", "bottom": "0cm", "left": "0cm", "right": "0cm"},
            display_header_footer=False,
            scale=1.0
        )
        
        await browser.close()

def gerar_pdf_sync(html_content, output_path):
    """Wrapper síncrono para ser chamado pelo Streamlit."""
    asyncio.run(html_para_pdf(html_content, output_path))
