import requests
import re
import base64

def extrair_repositorios(texto):
    """Detecta links de repositórios ou perfis do GitHub no texto."""
    # Padrão para perfis: github.com/usuario
    # Padrão para repos: github.com/usuario/repo
    padrao = r"github\.com/([\w-]+)/?([\w-]+)?"
    matches = re.findall(padrao, texto)
    return matches

def buscar_info_github(usuario, repo=None):
    """Busca informações do GitHub via API pública."""
    base_url = "https://api.github.com"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    try:
        if repo:
            # Busca info de um repositório específico
            url = f"{base_url}/repos/{usuario}/{repo}"
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                # Tenta buscar o README
                readme_url = f"{base_url}/repos/{usuario}/{repo}/readme"
                readme_resp = requests.get(readme_url, headers=headers)
                readme_content = ""
                if readme_resp.status_code == 200:
                    readme_b64 = readme_resp.json().get("content", "")
                    readme_content = base64.b64decode(readme_b64).decode('utf-8')[:2000] # Limite para não estourar tokens
                
                return f"""
                PROJETO GITHUB: {data.get('name')}
                Descrição: {data.get('description')}
                Tecnologias: {data.get('language')}
                Estrelas: {data.get('stargazers_count')}
                Detalhes (README): {readme_content}
                """
        else:
            # Busca repositórios principais do usuário
            url = f"{base_url}/users/{usuario}/repos?sort=updated&per_page=5"
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                repos = resp.json()
                contexto = f"PERFIL GITHUB: {usuario}\n"
                for r in repos:
                    contexto += f"- {r.get('name')}: {r.get('description')} (Tech: {r.get('language')})\n"
                return contexto
    except Exception as e:
        return f"[Erro ao buscar GitHub para {usuario}: {str(e)}]"
    
    return ""
