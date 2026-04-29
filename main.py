import streamlit as st
import os
import streamlit.components.v1 as components
from dotenv import load_dotenv
from utils import extrair_texto_arquivos, codificar_imagem
from services.ai_service import gerar_html_curriculo
from services.github_service import extrair_repositorios, buscar_info_github

load_dotenv()

st.set_page_config(page_title="Gerador de Currículo", page_icon="⚡", layout="centered")

# --- Ponte para LocalStorage (Cache do Navegador) ---
# Esse componente invisível permite ler/gravar dados no navegador do usuário
def local_storage_bridge():
    js_code = """
    <script>
    const parent = window.parent;
    
    // Função para enviar dados para o Streamlit
    function sendToStreamlit(key, value) {
        parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: {key: key, value: value}
        }, '*');
    }

    // Escuta comandos do Streamlit para salvar
    window.addEventListener('message', function(event) {
        if (event.data.type === 'save_keys') {
            localStorage.setItem('cv_gen_keys', JSON.stringify(event.data.keys));
        }
    });

    // Ao carregar, tenta ler as chaves e enviar de volta
    const saved = localStorage.getItem('cv_gen_keys');
    if (saved) {
        const keys = JSON.parse(saved);
        // Enviamos um evento customizado que o Streamlit pode capturar via query_params ou session_state
        // No Streamlit puro sem componentes extras, usamos um pequeno hack de input invisível
        window.parent.document.dispatchEvent(new CustomEvent('keys_loaded', {detail: keys}));
    }
    </script>
    """
    components.html(js_code, height=0)

# Para manter simples e sem dependências extras pesadas, usaremos o session_state 
# e daremos a opção de preencher via campo de texto que persiste na sessão.
# Como o Streamlit reseta o estado ao fechar a aba, o ideal para "cache real" 
# no Streamlit de forma simples é o arquivo local (que já tínhamos).

# MAS, se você quer evitar o arquivo, vou remover o .user_keys.json 
# e usar o session_state, que mantém enquanto a aba estiver aberta.

if not os.path.exists('output'):
    os.makedirs('output')

st.title("📄 Gerador de Currículo")
st.markdown("Gere um currículo premium adaptado para a vaga em segundos.")

def truncar_texto(texto, limite=8000):
    if len(texto) > limite:
        return texto[:limite] + "\n... [Conteúdo truncado] ..."
    return texto

with st.sidebar:
    st.header("⚙️ Configurações")
    provider = st.selectbox("Provedor de IA", ["OpenAI", "Groq (Grátis/Rápido)"], index=0)
    
    # Usamos session_state para manter a chave durante a navegação
    if provider == "OpenAI":
        if "openai_key" not in st.session_state:
            st.session_state.openai_key = ""
        API_KEY = st.text_input("OpenAI API Key", value=st.session_state.openai_key, type="password")
        st.session_state.openai_key = API_KEY
    else:
        if "groq_key" not in st.session_state:
            st.session_state.groq_key = ""
        API_KEY = st.text_input("Groq API Key", value=st.session_state.groq_key, type="password")
        st.session_state.groq_key = API_KEY
        st.info("💡 Groq é ultra-rápido e grátis.")

    st.caption("As chaves são mantidas no cache da sessão do navegador.")

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
        st.warning("⚠️ Envie pelo menos um arquivo com seu histórico.")
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