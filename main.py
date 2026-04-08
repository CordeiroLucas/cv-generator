import streamlit as st
import os
import streamlit.components.v1 as components

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

# Importando nossos módulos locais
from utils import extrair_texto_arquivos, codificar_imagem
from services.ai_service import gerar_html_curriculo

# from services.cache_service import buscar_cache, salvar_cache

st.set_page_config(page_title="Gerador de Currículo", page_icon="⚡", layout="centered")

if not os.path.exists('output'):
    os.makedirs('output')

st.title("📄 Gerador de Currículo")
st.markdown("Envie seus dados e o **Print da Vaga** para gerar um CV 100% compatível.")

# with st.sidebar:
#     st.header("Configurações")
#     api_key = st.text_input("OpenAI API Key", type="password")

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
        accept_multiple_files=True,
        key="files_data"
    )
    
    st.subheader("2. A Vaga")
    st.info("Tire prints da descrição da vaga no LinkedIn/Gupy e envie aqui. A IA vai ler a imagem.")

    uploaded_images = st.file_uploader(
        "Prints da Vaga (máx 2)", 
        type=["png", "jpg"], 
        accept_multiple_files=True
    )

    if uploaded_images and len(uploaded_images) > 2:
        st.warning("⚠️ O uso de mais de 2 prints pode consumir muitos tokens. Considere enviar apenas as partes principais.")
        
    extra_context = st.text_area(
        "Observações Extras", 
        placeholder="Ex: Quero destacar que tenho inglês fluente, mesmo que não esteja nos arquivos...",
        height=100
    )
    
    submitted = st.form_submit_button("Gerar Currículo Otimizado 🚀", use_container_width=True)

if submitted:
    if not API_KEY:
        st.error("⚠️ Insira sua API Key.")
    elif not nome_arquivo:
        st.error("⚠️ Defina um nome para o arquivo.")
    elif not uploaded_files:
        st.warning("⚠️ Envie pelo menos um arquivo com seu histórico profissional.")
    else:
        try:
            # 1. Processar Textos (Histórico)
            with st.spinner("Lendo seu histórico profissional..."):
                texto_historico = extrair_texto_arquivos(uploaded_files)
            
            # 2. Processar Imagens (Vaga)
            imagens_b64 = []
            if uploaded_images:
                with st.spinner("Analisando os prints da vaga (Visão Computacional)..."):
                    for img in uploaded_images:
                        imagens_b64.append(codificar_imagem(img))
            



            # #    --- OTIMIZAÇÃO DE CACHE ---
            # # Criamos uma "assinatura" única do pedido juntando histórico + contexto
            # # Nota: O cache funciona melhor com texto. Se a imagem mudar, o cache pode não pegar 
            # # a menos que convertamos a imagem em texto antes.
            assinatura_pedido = f"{texto_historico[:5000]} || {extra_context}"
            
            html_final = None
            origem = ""

            ## LÓGICA QUE UTILIZA O REDIS COMENTADA ########################

            # with st.spinner("Verificando banco de vetores (Cache Inteligente)..."):
            #     html_cached = buscar_cache(assinatura_pedido, threshold=0.05)
            
            if False and html_cached: ## PROPOSITAL PARA NÃO RODAR
                html_final = html_cached
                origem = "⚡ CACHE REDIS (Custo Zero)"
                st.balloons()
            ### #################
            else:
                with st.spinner("Gerando com OpenAI (Consumindo Tokens)..."):
                    html_final = gerar_html_curriculo(
                        API_KEY, 
                        texto_historico, 
                        extra_context, 
                        imagens_vagas=imagens_b64
                    )
                    # Salva no Redis para a próxima vez
                    # salvar_cache(assinatura_pedido, html_final)
                    origem = "🧠 OPENAI (Novo Gerado)"

            # Feedback visual da economia
            if "CACHE" in origem:
                st.success(f"Sucesso! Resultado carregado do {origem}.")
            else:
                st.info(f"Resultado gerado via {origem}.")
            
            # 4. Salvar e Mostrar
            caminho_arquivo = f"output/{nome_arquivo.strip()}.html"
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                f.write(html_final)
            
            st.success("✅ Currículo Gerado! A IA leu a vaga e adaptou seu perfil.")
            
            col_download, col_view = st.columns([1, 2])
            with col_download:
                st.download_button(
                    label="📥 Baixar HTML",
                    data=html_final,
                    file_name=f"{nome_arquivo.strip()}.html",
                    mime="text/html"
                )
            
            st.markdown("---")
            st.subheader("Pré-visualização:")

            html_preview = f"""
            <style>
                body {{
                    background-color: #FFFFFF !important; /* Força fundo branco */
                    margin: 0; 
                    padding: 0;
                }}
                /* Opcional: Centraliza o conteúdo visualmente como uma folha A4 */
                .container {{
                    min-height: 100vh;
                }}
            </style>
            {html_final}
            """

            st.markdown("---")
            components.html(html_preview, height=800, scrolling=True)

        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")