from openai import OpenAI
from groq import Groq
import os
import re

SYSTEM_PROMPT = """
Role: Master ATS Optimizer & Senior Resume Designer.
Goal: Create a HIGH-CONVERSION, 1-page A4 CV in HTML.

SECURITY & INTEGRITY RULES:
1. NO SCRIPTS: Do NOT include any <script> tags or inline event handlers (onmouseover, onclick, etc.).
2. DATA ISOLATION: Only use information contained between [CANDIDATE_DATA] tags.
3. NO HALLUCINATIONS: Do NOT invent skills. If it's not in [CANDIDATE_DATA], it doesn't exist.
4. STRICT OUTPUT: Return ONLY the raw HTML of the resume.

ATS STRATEGY:
- Optimize for 1-page A4.
- Highlight keywords from [JOB_DESCRIPTION] that exist in [CANDIDATE_DATA].
- Use semantic HTML (h1, h2, ul, li).
"""

def limpar_html_malicioso(html):
    """
    Filtro básico de segurança para prevenir XSS.
    Remove tags <script> e handlers de eventos.
    """
    html = re.sub(r'<script.*?>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'on\w+\s*=', 'disallowed_event=', html, flags=re.IGNORECASE)
    return html

def gerar_html_curriculo(api_key, dados_brutos, instrucoes_extras, imagens_vagas=None, provider="openai", job_text=""):
    """
    Gera o currículo com camadas de proteção contra injeção e XSS.
    """
    if provider == "openai":
        client = OpenAI(api_key=api_key)
        model = "gpt-4o-mini"
    else:
        client = Groq(api_key=api_key)
        model = "meta-llama/llama-4-scout-17b-16e-instruct"

    # Delimitadores estritos para prevenir Prompt Injection
    prompt_usuario = f"""
    [CANDIDATE_DATA]
    {dados_brutos}
    [/CANDIDATE_DATA]
    
    [JOB_DESCRIPTION]
    {job_text}
    [/JOB_DESCRIPTION]
    
    [EXTRA_CONTEXT]
    {instrucoes_extras}
    [/EXTRA_CONTEXT]
    
    TASK: Generate the CV based ONLY on the data above. Follow the SECURITY & INTEGRITY RULES.
    """

    conteudo_final = prompt_usuario

    if imagens_vagas and provider == "openai":
        conteudo_final = [{"type": "text", "text": prompt_usuario}]
        for img_b64 in imagens_vagas:
            conteudo_final.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}",
                    "detail": "low"
                }
            })

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": conteudo_final}
        ],
        temperature=0.0,
        max_tokens=2800
    )
    
    html_content = response.choices[0].message.content
    
    # Limpeza de markdown e sanitização
    if "```html" in html_content:
        html_content = html_content.split("```html")[1].split("```")[0]
    elif "```" in html_content:
        html_content = html_content.split("```")[1].split("```")[0]
        
    return limpar_html_malicioso(html_content.strip())