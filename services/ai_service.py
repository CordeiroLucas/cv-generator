from openai import OpenAI
from groq import Groq
import os

SYSTEM_PROMPT = """
Role: Master ATS Optimizer & Senior Resume Designer.
Goal: Create a HIGH-CONVERSION, 1-page A4 CV in HTML, perfectly optimized for ATS bots and human recruiters.

ATS & CONTENT STRATEGY:
1. THE 1-PAGE RULE: Strictly limit content to one A4 page. Prioritize the 3 most relevant experiences/projects. Be concise.
2. KEYWORD TARGETING: Identify the most important keywords from the JOB DESCRIPTION. Integrate them naturally into the 'Professional Summary' and 'Technical Skills' sections.
3. PROJECT SELECTION: From the provided CANDIDATE DATA (and GitHub), select and highlight ONLY the projects that directly prove skills required by the job.
4. STAR METHOD: Use the Situation-Task-Action-Result format for experiences, focusing on quantifiable metrics.
5. NO HALLUCINATIONS: Use ONLY provided facts. If a skill is missing from source, do NOT add it.

VISUAL & SEMANTIC DESIGN (ATS Friendly):
- Semantic HTML: Use <h1> for name, <h2> for sections, <ul>/<li> for lists. Avoid complex tables.
- Modern Typography: Use clean sans-serif fonts (Inter/Roboto).
- Print Optimization: CSS must include @page { size: A4; margin: 1.2cm; } and prevent page breaks inside sections.
- Visual Hierarchy: Bold keywords and job titles to guide the human eye.

TECHNICAL:
- Output: RAW HTML ONLY. No markdown, no intro/outro.
- Temperature: 0.0 (Strict fidelity).
"""

def gerar_html_curriculo(api_key, dados_brutos, instrucoes_extras, imagens_vagas=None, provider="openai", job_text=""):
    """
    Gera o currículo otimizado para ATS em 1 página.
    """
    if provider == "openai":
        client = OpenAI(api_key=api_key)
        model = "gpt-4o-mini"
    else:
        client = Groq(api_key=api_key)
        model = "meta-llama/llama-4-scout-17b-16e-instruct"

    texto_usuario = f"""
    SOURCE DATA (Candidate History):
    {dados_brutos}
    
    TARGET JOB (Keywords to target):
    {job_text}
    
    EXTRA CONTEXT:
    {instrucoes_extras}
    
    STRICT TASK:
    - Create a 1-page A4 CV.
    - Highlight keywords from the TARGET JOB that exist in the SOURCE DATA.
    - Select the best projects to match the job.
    - DO NOT INVENT DATA.
    """

    conteudo_final = texto_usuario

    if imagens_vagas and provider == "openai":
        conteudo_final = [{"type": "text", "text": texto_usuario}]
        for img_b64 in imagens_vagas:
            conteudo_final.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}",
                    "detail": "low"
                }
            })
    elif imagens_vagas and provider == "groq":
        conteudo_final += "\n[Match against provided job text.]"

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
    
    if "```html" in html_content:
        html_content = html_content.split("```html")[1].split("```")[0]
    elif "```" in html_content:
        html_content = html_content.split("```")[1].split("```")[0]
        
    return html_content.strip()