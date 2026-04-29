import requests
import re
from urllib.parse import urlparse

def extrair_repositorios(texto):
    """
    Extrai duplas (usuario, repo) de links do GitHub usando Regex.
    Suporta links de perfis e repositórios.
    """
    pattern = r"github\.com/([\w-]+)/?([\w-]+)?"
    matches = re.findall(pattern, texto)
    # Filtra para evitar pegar 'features', 'pulls', etc como usuários
    blacklist = ['features', 'pulls', 'issues', 'marketplace', 'explore', 'trending']
    return [m for m in matches if m[0] not in blacklist]

def buscar_info_github(usuario, repo=None):
    """
    Busca informações técnicas do GitHub para enriquecer o contexto da IA.
    Implementa validação básica contra SSRF.
    """
    try:
        # Validação Estrita de Segurança
        if not re.match(r'^[\w-]+$', usuario):
            return ""
        if repo and not re.match(r'^[\w.-]+$', repo):
            return ""

        if repo:
            url = f"https://api.github.com/repos/{usuario}/{repo}"
            readme_url = f"https://raw.githubusercontent.com/{usuario}/{repo}/main/README.md"
        else:
            url = f"https://api.github.com/users/{usuario}/repos"
            readme_url = None

        # Headers para evitar rate limit (opcional, mas bom ter)
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return ""

        dados = response.json()
        
        if repo:
            info = f"\nProjeto: {dados.get('name')}\nDescrição: {dados.get('description')}\nLinguagem: {dados.get('language')}\n"
            # Tenta pegar um pedaço do README para contexto técnico
            try:
                r_readme = requests.get(readme_url, timeout=3)
                if r_readme.status_code == 200:
                    info += f"Trecho do README: {r_readme.text[:1000]}\n"
            except:
                pass
            return info
        else:
            # Se for usuário, pega resumo dos 5 principais repos
            resumo = f"\nUsuário GitHub: {usuario}\nRepositórios Recentes:\n"
            for r in dados[:5]:
                resumo += f"- {r.get('name')}: {r.get('description')} ({r.get('language')})\n"
            return resumo

    except Exception as e:
        print(f"Erro ao acessar GitHub: {e}")
        return ""
