# ====================================================================
# ADICIONE ISSO AO SEU modules/content.py
# ====================================================================

def generate_dynamic_comparisons(theme, time_period, num_comparisons, language, groq_api_key=None, use_ollama=False, ollama_model="llama3.1"):
    """
    Gera múltiplas ideias de comparação baseado em um tema e período.
    
    Args:
        theme: str - Tema escolhido (ex: "Tecnologia", "Cinema", etc)
        time_period: str - Período (ex: "Últimos 7 dias", "Ano passado")
        num_comparisons: int - Quantas comparações gerar (1-10)
        language: str - Código do idioma (ex: "pt", "en")
        groq_api_key: str opcional - Chave da API Groq
        use_ollama: bool - Usar Ollama localmente
        ollama_model: str - Modelo do Ollama
        
    Returns:
        list - Lista de dicts com {item1, item2, reason, category}
    """
    import json
    
    # Prompt em português/inglês baseado no idioma
    if language == "pt":
        prompt = f"""Você é um especialista em criar conteúdo viral para redes sociais.
        
Preciso de {num_comparisons} ideias criativas de comparação para vídeos de TikTok/YouTube Shorts.

TEMA: {theme}
PERÍODO: {time_period}

Para cada comparação, escolha dois itens/pessoas/personagens DIFERENTES e INTERESSANTES que façam sentido nesse tema e período.

IMPORTANTE:
- Cada comparação deve ser ÚNICA, não repetir itens
- Escolha coisas que geram engajamento e são controversas/interessantes
- Não escolha a mesma coisa vs ela mesma
- Os itens devem ser conhecidos o suficiente para as pessoas entenderem

Retorne EXATAMENTE em JSON (sem markdown, sem formatação extra):
[
  {{"item1": "Nome Item 1", "item2": "Nome Item 2", "reason": "Por que essa comparação é interessante (1-2 frases curtas)", "category": "Categoria do conteúdo"}},
  ...
]

Gere {num_comparisons} comparações diferentes e criativas."""
    else:
        prompt = f"""You are an expert in creating viral social media content.

I need {num_comparisons} creative comparison ideas for TikTok/YouTube Shorts videos.

THEME: {theme}
TIME PERIOD: {time_period}

For each comparison, choose two DIFFERENT and INTERESTING items/people/characters that make sense in this theme and time period.

IMPORTANT:
- Each comparison must be UNIQUE, don't repeat items
- Choose things that generate engagement and are controversial/interesting
- Don't choose the same thing vs itself
- The items should be known enough for people to understand

Return EXACTLY in JSON (no markdown, no extra formatting):
[
  {{"item1": "Item 1 Name", "item2": "Item 2 Name", "reason": "Why this comparison is interesting (1-2 short sentences)", "category": "Content category"}},
  ...
]

Generate {num_comparisons} different and creative comparisons."""

    try:
        if groq_api_key:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
            )
            raw_response = response.choices[0].message.content
        elif use_ollama:
            import ollama
            response = ollama.chat(
                model=ollama_model,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            raw_response = response["message"]["content"]
        else:
            # Fallback com ideias padrão
            return _get_default_comparisons(theme, num_comparisons)

        # Limpar resposta (remover markdown se houver)
        raw_response = raw_response.strip()
        if raw_response.startswith("```"):
            raw_response = raw_response.split("```")[1]
            if raw_response.startswith("json"):
                raw_response = raw_response[4:]
        if raw_response.endswith("```"):
            raw_response = raw_response[:-3]
        raw_response = raw_response.strip()

        comparisons = json.loads(raw_response)
        
        # Validação básica
        if isinstance(comparisons, list) and len(comparisons) > 0:
            # Filtra apenas comparações válidas (com os campos necessários)
            valid_comparisons = [
                c for c in comparisons 
                if isinstance(c, dict) and "item1" in c and "item2" in c and c["item1"] != c["item2"]
            ]
            
            # Retorna no máximo o número solicitado
            return valid_comparisons[:num_comparisons]
        
        return _get_default_comparisons(theme, num_comparisons)
        
    except json.JSONDecodeError:
        return _get_default_comparisons(theme, num_comparisons)
    except Exception as e:
        print(f"Erro ao gerar comparações dinâmicas: {e}")
        return _get_default_comparisons(theme, num_comparisons)


def _get_default_comparisons(theme, num_comparisons):
    """Retorna comparações padrão se a IA falhar"""
    
    tema_comparacoes = {
        "Tecnologia": [
            {"item1": "iPhone 15", "item2": "Samsung Galaxy S24", "reason": "Flagship phones mais vendidos do momento", "category": "Smartphones"},
            {"item1": "ChatGPT", "item2": "Claude", "reason": "Battle de IAs mais populares", "category": "IA"},
            {"item1": "Meta Quest 3", "item2": "Apple Vision Pro", "reason": "VR headsets de ponta", "category": "VR/AR"},
            {"item1": "Windows 11", "item2": "macOS", "reason": "Sistemas operacionais mais usados", "category": "SO"},
            {"item1": "Tesla Model 3", "item2": "BYD Song Plus DM-i", "reason": "Carros elétricos mais vendidos", "category": "Automotivo"},
        ],
        "Cinema e TV": [
            {"item1": "Marvel", "item2": "DC", "reason": "Universos de superheroísmo rivais", "category": "Filmes"},
            {"item1": "Game of Thrones", "item2": "House of the Dragon", "reason": "Séries epic fantasy de GOT", "category": "TV"},
            {"item1": "Barbie", "item2": "Oppenheimer", "reason": "Blockbusters de 2023 com visual oposto", "category": "Filmes"},
            {"item1": "The Office", "item2": "Parks and Recreation", "reason": "Mockumentaries clássicas", "category": "TV"},
        ],
        "Esportes": [
            {"item1": "Cristiano Ronaldo", "item2": "Lionel Messi", "reason": "A rivalidade mais lendária do futebol", "category": "Futebol"},
            {"item1": "NBA", "item2": "Euroliga", "reason": "Ligas de basquete mais competitivas", "category": "Basquete"},
            {"item1": "Floyd Mayweather", "item2": "Manny Pacquiao", "reason": "Lutadores lendários do boxe", "category": "Boxe"},
        ],
        "Mitologia": [
            {"item1": "Mitologia Grega", "item2": "Mitologia Nórdica", "reason": "Dois universos mitológicos mais populares", "category": "Mitologia"},
            {"item1": "Zeus", "item2": "Odin", "reason": "Deuses supremos de duas culturas", "category": "Mitologia"},
            {"item1": "Héracles", "item2": "Sigurd", "reason": "Heróis lendários em suas culturas", "category": "Mitologia"},
        ],
        "História": [
            {"item1": "Napoleão", "item2": "Alexandre, o Grande", "reason": "Conquistas e legados militares", "category": "História"},
            {"item1": "Primeira Guerra", "item2": "Segunda Guerra", "reason": "Guerras mundiais que moldaram o mundo", "category": "História"},
            {"item1": "Império Romano", "item2": "Império Persa", "reason": "Impérios antigos rivais", "category": "História"},
        ],
        "Ciência": [
            {"item1": "Relatividade", "item2": "Mecânica Quântica", "reason": "Pilares da física moderna", "category": "Física"},
            {"item1": "Darwin", "item2": "Lamarck", "reason": "Teorias diferentes de evolução", "category": "Biologia"},
            {"item1": "Energia Nuclear", "item2": "Energia Solar", "reason": "Fontes de energia do futuro", "category": "Energia"},
        ],
        "Animais": [
            {"item1": "Leão", "item2": "Tigre", "reason": "Dois grandes felinos em comparação", "category": "Animais"},
            {"item1": "Águia", "item2": "Coruja", "reason": "Aves de rapina comparadas", "category": "Pássaros"},
            {"item1": "Tubarão", "item2": "Crocodilo", "reason": "Predadores antigos em confronto", "category": "Répteis"},
        ],
        "Comida": [
            {"item1": "Pizza Italiana", "item2": "Hambúrguer Americano", "reason": "Dois ícones de comida no mundo", "category": "Comida"},
            {"item1": "Sushi", "item2": "Tempura", "reason": "Pratos clássicos japoneses", "category": "Culinária"},
            {"item1": "Café", "item2": "Chá", "reason": "Bebidas mais consumidas do mundo", "category": "Bebidas"},
        ],
        "Personalidades": [
            {"item1": "Elon Musk", "item2": "Jeff Bezos", "reason": "Bilionários empreendedores rivais", "category": "Empresários"},
            {"item1": "Taylor Swift", "item2": "Beyoncé", "reason": "Popstars mais influentes da atualidade", "category": "Música"},
        ],
        "Personagens de Ficção": [
            {"item1": "Batman", "item2": "Superman", "reason": "Dois heróis DC em comparação", "category": "Superheroísmo"},
            {"item1": "Harry Potter", "item2": "Percy Jackson", "reason": "Protagonistas de sagas de fantasia", "category": "Fantasia"},
            {"item1": "Homem-Aranha", "item2": "Homem de Ferro", "reason": "Heróis Marvel com diferentes abordagens", "category": "Superheroísmo"},
        ],
    }
    
    # Pega comparações do tema, ou usa as de tecnologia como fallback
    comparacoes = tema_comparacoes.get(theme, tema_comparacoes["Tecnologia"])
    
    # Retorna apenas o número solicitado
    return comparacoes[:num_comparisons]
