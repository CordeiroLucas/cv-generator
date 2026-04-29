import streamlit as st
import os
import json
import streamlit.components.v1 as components
from dotenv import load_dotenv
from utils import extrair_texto_arquivos, codificar_imagem
from services.ai_service import gerar_html_curriculo
from services.github_service import extrair_repositorios, buscar_info_github

load_dotenv()

KEYS_FILE = ".user_keys.json"

def carregar_chaves():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "r") as f:
            return json.load(f)
    return {}

def salvar_chaves(openai_key, groq_key):
    with open(KEYS_FILE, "w") as f:
        json.dump({"openai": openai_key, "groq": groq_key}, f)

st.set_page_config(page_title="Gerador de Currículo", page_icon="⚡", layout="centered")

if not os.path.exists('output'):
    os.makedirs('output')

saved_keys = carregar_chaves()

st.title("📄 Gerador de Currículo")
st.markdown("Gere um currículo premium adaptado para a vaga em segundos.")

def truncar_texto(texto, limite=8000):
    if len(texto) > limite:
        return texto[:limite] + "\n... [Conteúdo truncado] ..."
    return texto

with st.sidebar:
    st.header("⚙️ Configurações")
    provider = st.selectbox("Provedor de IA", ["OpenAI", "Groq (Grátis/Rápido)"], index=0)
    
    if provider == "OpenAI":
        default_key = saved_keys.get("openai", "")
        API_KEY = st.text_input("OpenAI API Key", value=default_key, type="password")
    else:
        default_key = saved_keys.get("groq", "")
        API_KEY = st.text_input("Groq API Key", value=default_key, type="password")
        st.info("💡 Groq é ultra-rápido e grátis.")

    if st.button("💾 Salvar Chaves Localmente"):
        if provider == "OpenAI":
            salvar_chaves(API_KEY, saved_keys.get("groq", ""))
        else:
            salvar_chaves(saved_keys.get("openai", ""), API_KEY)
        st.success("Chaves salvas com sucesso!")

with st.form("cv_form"):
    col1, col2 = st.columns(2)
    with col1:
        nome_usuario = st.text_input("Nome do Candidato", placeholder="João Silva")
    with col2:
        nome_arquivo = st.text_input("Nome do Arquivo Final", placeholder="cv_joao_vaga_x")
    
    st.subheader("1. Seus Dados (Histórico)")
    uploaded_files = st.file_uploader(
        "Seus currículos antigos ou arquivos de texto", 
        type=["pdf", "docx", "txt"], 
        accept_multiple_files=True
    )
    
    links_input = st.text_area(
        "Links Relevantes (GitHub, Portfólio)", 
        placeholder="https://github.com/seu-usuario/seu-projeto",
        height=70
    )
    
    st.subheader("2. A Vaga")
    tab_text, tab_image = st.tabs(["Texto da Vaga", "Prints da Vaga"])
    
    with tab_text:
        job_description_text = st.text_area(
            "Cole a descrição da vaga aqui", 
            placeholder="Ex: Requisitos: Python, AWS...",
            height=150
        )
    
    with tab_image:
        st.info("A IA vai ler o conteúdo dos prints.")
        uploaded_images = st.file_uploader(
            "Prints da Vaga (máx 2)", 
            type=["png", "jpg"], 
            accept_multiple_files=True
        )

    extra_context = st.text_area(
        "Observações Extras", 
        placeholder="Ex: Quero destacar que tenho inglês fluente...",
        height=100
    )
    
    submitted = st.form_submit_button("Gerar Currículo Premium 🚀", use_container_width=True)

if submitted:
    if not API_KEY:
        st.error("⚠️ Insira sua API Key na barra lateral.")
    elif not nome_arquivo:
        st.error("⚠️ Defina um nome para o arquivo.")
    elif not uploaded_files:
        st.warning("⚠️ Envie pelo menos um arquivo com seu histórico profissional.")
    else:
        try:
            with st.spinner("Lendo seu histórico..."):
                texto_historico = extrair_texto_arquivos(uploaded_files)
            
            texto_github = ""
            github_links = extrair_repositorios(links_input + " " + extra_context)
            if github_links:
                with st.spinner(f"Buscando dados do GitHub..."):
                    for usuario, repo in github_links:
                        texto_github += buscar_info_github(usuario, repo)
            
            dados_completos = f"{texto_historico}\n\n--- DADOS GITHUB ---\n{texto_github}"
            dados_completos = truncar_texto(dados_completos)
            
            imagens_b64 = []
            if uploaded_images:
                with st.spinner("Analisando prints..."):
                    for img in uploaded_images:
                        imagens_b64.append(codificar_imagem(img))
            
            prov_id = "openai" if provider == "OpenAI" else "groq"
            with st.spinner(f"IA selecionando e gerando o melhor CV..."):
                html_final = gerar_html_curriculo(
                    API_KEY, 
                    dados_completos, 
                    extra_context, 
                    imagens_vagas=imagens_b64,
                    provider=prov_id,
                    job_text=job_description_text
                )

            caminho_html = f"output/{nome_arquivo.strip()}.html"
            with open(caminho_html, "w", encoding="utf-8") as f:
                f.write(html_final)

            st.success("✅ Currículo Gerado com Sucesso!")
            
            st.download_button(
                label="📥 Baixar HTML Premium",
                data=html_final,
                file_name=f"{nome_arquivo.strip()}.html",
                mime="text/html",
                use_container_width=True
            )
            
            html_preview = f"<style>body {{ background: white; }}</style>{html_final}"
            st.markdown("---")
            st.subheader("Pré-visualização:")
            components.html(html_preview, height=800, scrolling=True)

        except Exception as e:
            st.error(f"Erro: {e}")