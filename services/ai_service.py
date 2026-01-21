from openai import OpenAI
from config import PROMPT

SYSTEM_PROMPT = """

**Role:** You are an Expert Tech Recruiter and ATS Specialist. Your goal is to create a high-impact, single-page A4 CV in HTML format.
**Task:** Based on the user's provided information and a specific job description, build a resume optimized for the target company's culture and technical requirements.
**Optimization Rules:**
* **ATS Optimization:** Rewrite descriptions to be result-oriented, incorporating industry keywords and standard section headings.
* **Integrity:** Use ONLY the information provided by the user. Do not invent skills or experiences.
* **Content Structure:** Use the STAR method (Situation, Task, Action, Result) for experience descriptions.


**Technical Constraints:**
* **Layout:** Header, Professional Summary, Skills (2-column grid), Experience (STAR), and Education.
* **Format:** Must fit perfectly on one A4 page when printed/saved as PDF.
* **Styling:** Minimalist design. Use minified CSS within a `<style>` tag.
* **CSS Specs:** `@page { size: A4; margin: 1cm; } body { font-size: 10pt; line-height: 1.1; font-family: sans-serif; }`
* **Output:** Return **ONLY** the raw HTML code. No Markdown formatting, no backticks (```), no introductory text, and no extra whitespace.
* **Visuals:** Ensure a clean, structured, and professional hierarchy.


"""

# SYSTEM_PROMPT = PROMPT

def gerar_html_curriculo(api_key, dados_brutos, instrucoes_extras, imagens_vagas=None):
    """
    Envia texto e imagens (opcional) para a OpenAI.
    """
    client = OpenAI(api_key=api_key)
    
    # Monta a parte de texto da mensagem do usuário
    texto_usuario = f"""
    DADOS DO CANDIDATO (Meu histórico):
    {dados_brutos}
    
    INSTRUÇÕES EXTRAS:
    {instrucoes_extras}
    
    Se houver imagens anexadas, elas são PRINTS DA VAGA. O currículo deve ser TOTALMENTE ADAPTADO para o que está escrito nessas imagens.
    """

    # Estrutura da mensagem (Lista de conteúdos)
    conteudo_mensagem = [
        {"type": "text", "text": texto_usuario}
    ]

    # Se houver imagens, adiciona ao payload
    if imagens_vagas:
        for img_b64 in imagens_vagas:
            conteudo_mensagem.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}",
                    "detail": "low"
                }
            })

    # Chamada API
    response = client.chat.completions.create(
        model="gpt-4.1-nano", # Necessário usar modelo que suporta visão
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": conteudo_mensagem}
        ],
        temperature=0.7
    )
    
    html_content = response.choices[0].message.content
    html_content = html_content.replace("```html", "").replace("```", "")
    
    return html_content