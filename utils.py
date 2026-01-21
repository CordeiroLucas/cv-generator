import PyPDF2
from docx import Document
import base64

def ler_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

def ler_docx(file):
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def ler_txt(file):
    return file.getvalue().decode("utf-8")

def extrair_texto_arquivos(uploaded_files):
    texto_completo = ""
    for file in uploaded_files:
        try:
            if file.type == "application/pdf":
                texto_completo += f"\n--- Conteúdo do arquivo {file.name} ---\n"
                texto_completo += ler_pdf(file)
            elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                texto_completo += f"\n--- Conteúdo do arquivo {file.name} ---\n"
                texto_completo += ler_docx(file)
            elif file.type == "text/plain":
                texto_completo += f"\n--- Conteúdo do arquivo {file.name} ---\n"
                texto_completo += ler_txt(file)
        except Exception as e:
            texto_completo += f"\n[ERRO AO LER {file.name}: {str(e)}]\n"
    return texto_completo

# --- NOVA FUNÇÃO ADICIONADA ---
def codificar_imagem(image_file):
    """
    Converte o arquivo de imagem carregado pelo Streamlit para Base64 string.
    """
    # Lê os bytes do arquivo
    bytes_data = image_file.getvalue()
    # Converte para base64
    base64_image = base64.b64encode(bytes_data).decode('utf-8')
    return base64_image