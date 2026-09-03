# 📚 Exemplos de Uso - Comparações Dinâmicas

## 🎬 Cenário 1: Criador de conteúdo de Tecnologia

### Objetivo
Criar vários vídeos de comparação sobre tech rapidamente.

### Fluxo
1. **Modo:** Selecionar "Comparações Dinâmicas"
2. **Tema:** Tecnologia
3. **Período:** Últimos 7 dias
4. **Quantidade:** 5 comparações

### Resultado Esperado
```json
[
  {
    "item1": "iPhone 15",
    "item2": "Samsung Galaxy S24",
    "reason": "Flagship phones mais vendidos do momento",
    "category": "Smartphones"
  },
  {
    "item1": "ChatGPT",
    "item2": "Claude",
    "reason": "Battle de IAs mais populares",
    "category": "IA"
  },
  {
    "item1": "Meta Quest 3",
    "item2": "Apple Vision Pro",
    "reason": "VR headsets de ponta",
    "category": "VR/AR"
  },
  {
    "item1": "Windows 11",
    "item2": "macOS",
    "reason": "Sistemas operacionais mais usados",
    "category": "SO"
  },
  {
    "item1": "Tesla Model 3",
    "item2": "BYD Song Plus DM-i",
    "reason": "Carros elétricos mais vendidos",
    "category": "Automotivo"
  }
]
```

### Vantagem
- ✅ Não precisa pensar em ideias
- ✅ Todas as comparações são relevantes pro período
- ✅ Pode criar 5 vídeos em meia hora

---

## 🎥 Cenário 2: Criador de conteúdo de Cinema

### Objetivo
Gerar vídeos virais sobre filmes/séries.

### Fluxo
1. **Modo:** Comparações Dinâmicas
2. **Tema:** Cinema e TV
3. **Período:** Último mês
4. **Quantidade:** 3

### O que o App Vai Fazer
```
1. Gera 3 ideias (ex: Marvel vs DC, Barbie vs Oppenheimer, GOT vs HOTD)
2. Você escolhe uma (ex: "Marvel vs DC")
3. Clica "Gerar roteiro"
4. IA escreve:
   - Intro (apresenta os dois universos)
   - Pergunta qual é melhor
   - Explica pontos fortes de Marvel
   - Explica pontos fortes de DC
5. Renderiza o vídeo com coruja apontando
6. Você baixa e posta!
```

### Tempo Total
- Gerar ideias: 5s
- Escolher e gerar roteiro: 10s
- Renderizar vídeo: 2-3 min
- **Total: ~5 minutos por vídeo**

---

## 💪 Cenário 3: Estratégia de Conteúdo - Batch de Vídeos

### Objetivo
Criar 10 vídeos de comparação em uma sessão.

### Fluxo Otimizado

```python
TEMAS = ["Tecnologia", "Esportes", "Cinema e TV"]
PERIODOS = ["Última semana", "Últimos 3 meses"]

Para cada combinação:
  1. Escolhe tema
  2. Escolhe período
  3. Gera 3-5 comparações
  4. Cria vídeos das top 3
```

### Resultado
- 3 temas × 2 períodos = 6 combinações
- 3 vídeos por combinação = **18 vídeos** em uma sessão
- Tempo: ~1h de renderização (pode rodar em background)

---

## 🎯 Cenário 4: Teste A/B - Qual Tema Funciona?

### Objetivo
Descobrir qual tema gera mais engagement.

### Fluxo
```
Semana 1:
  - Comparações de Tecnologia
  - Comparações de Esportes
  - Comparações de Animais

Medir:
  - Views, likes, comentários
  - Taxa de conclusão do vídeo
  - Compartilhamentos
  
Resultado:
  - Tecnologia = 50k views
  - Esportes = 30k views
  - Animais = 80k views ← Focar nesse!
```

### Como Implementar
```streamlit
1. Seleciona "Animais"
2. Período: "Toda a semana"
3. Gera 10 comparações
4. Cria vídeos e publica todos
5. Monitora performance
```

---

## 📊 Exemplos de Comparações por Tema

### Tecnologia
```
1. iPhone 15 vs Samsung Galaxy S24
2. ChatGPT vs Claude
3. Meta Quest 3 vs Apple Vision Pro
4. Windows 11 vs macOS
5. Tesla vs BYD
```

### Esportes
```
1. Cristiano Ronaldo vs Lionel Messi
2. NBA vs Euroliga
3. Floyd Mayweather vs Manny Pacquiao
4. Real Madrid vs Manchester United
5. Futebol vs Basketball (popularidade)
```

### Mitologia
```
1. Mitologia Grega vs Nórdica
2. Zeus vs Odin
3. Héracles vs Sigurd
4. Poseidon vs Loki
5. Deuses vs Mortais
```

### Personalidades
```
1. Elon Musk vs Jeff Bezos
2. Taylor Swift vs Beyoncé
3. Cristiano Ronaldo vs Messi
4. Michael Jordan vs LeBron James
5. Einstein vs Stephen Hawking
```

### Personagens de Ficção
```
1. Batman vs Superman
2. Harry Potter vs Percy Jackson
3. Spider-Man vs Iron Man
4. Gandalf vs Alvo Dumbledore
5. Wolverine vs Homem-Aranha
```

---

## 💡 Dicas Práticas

### Dica 1: Otimizar para Trending
```python
# Escolha períodos curtos para pegar trends
período = "Últimos 7 dias"  # Maior chance de viral
```

### Dica 2: Diversificar Temas
```python
# Não faça sempre o mesmo tema
Semana 1: Tecnologia
Semana 2: Esportes
Semana 3: Cinema
```

### Dica 3: Testar Quantidade
```python
# Comece pequeno, escale depois
1ª tentativa: 2 comparações
2ª tentativa: 5 comparações
3ª tentativa: 10 comparações
```

### Dica 4: Manter Consistência
```python
# Sempre edite os roteiros gerados pela IA
Mude palavras genéricas por mais específicas
Adicione humor/personalidade
Corrija pronúncia difícil
```

### Dica 5: Usar Fallback Inteligentemente
```python
# Se IA falhar, as ideias padrão são MUITO boas
# Não é problema usar elas! São baseadas em trending
```

---

## 🔄 Fluxo Completo: Do Zero ao Vídeo

### Passos Detalhados

```
┌─────────────────────────────────────────────────────────┐
│ 1. ABRIR APP (streamlit run app.py)                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. CONFIGURAR GERAL                                     │
│   - Selecionar idioma                                   │
│   - Colocar Groq API Key (opcional)                     │
│   - Escolher voz                                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. SELECIONAR MODO: "Comparações Dinâmicas"             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. ESCOLHER TEMA + PERÍODO + QUANTIDADE                 │
│   Tema: "Esportes"                                      │
│   Período: "Últimos 3 meses"                            │
│   Quantidade: 3                                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 5. CLICAR "Gerar ideias de comparação" (⏱️ 5s)          │
│   App gera 3 ideias diferentes                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 6. VER 3 IDEIAS EM CARDS EXPANSÍVEIS:                   │
│   📊 Comparação 1: Neymar vs Vinícius Jr                │
│   📊 Comparação 2: Premier League vs La Liga            │
│   📊 Comparação 3: Futebol vs Basquete                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 7. ESCOLHER UMA COMPARAÇÃO (selectbox)                  │
│   Seleciona: "Neymar vs Vinícius Jr"                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 8. CLICAR "Gerar roteiro" (⏱️ 10s com Groq)             │
│   IA escreve as 4 falas da comparação                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 9. REVISAR E EDITAR (⏱️ 2-3 min)                        │
│   - Títulos dos jogadores                              │
│   - Termos de busca de imagem                           │
│   - As 4 falas da narração                              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 10. CLICAR "Renderizar vídeo final" (⏱️ 2-3 min)        │
│    App busca imagens, gera áudio, monta vídeo           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 11. BAIXAR VÍDEO                                        │
│    Clica botão "⬇️ Baixar vídeo"                        │
│    Arquivo: video_comparison_0.mp4 salvo!              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 12. POSTAR EM TIKTOK / YOUTUBE SHORTS                   │
│    ✅ Pronto! Vídeo viral de comparação                 │
└─────────────────────────────────────────────────────────┘
```

**Tempo Total: ~5-7 minutos por vídeo** 🚀

---

## 🎮 Modo "Streamlit Dev" (para testers)

Se quiser testar sem Groq API Key:

```bash
# Rode assim pra pegar as ideias padrão (fallback)
GROQ_API_KEY="" streamlit run app.py

# Vai usar as comparações pre-carregadas, mais rápido
```

---

## ✨ Bonus: Prompt Customizado para IA

Se quiser modificar o prompt da IA, edite em `modules/content.py`:

**Antes (genérico):**
```python
prompt = f"""Você é um especialista em criar conteúdo viral...
Preciso de {num_comparisons} ideias...
"""
```

**Depois (específico para seu nicho):**
```python
prompt = f"""Você é um especialista em GAMES e STREAMERS.
Preciso de {num_comparisons} comparações VIRAIS entre streamers.
Foque em:
- Rivalidades populares
- Diferenças de gameplay
- Comunidades engajadas
...
"""
```

---

## 🐛 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| "Nenhuma ideia gerada" | Certifique Groq/Ollama está configurado |
| "Mesmas ideias sempre" | Normal sem IA, use Groq API Key |
| "Erro ao buscar imagem" | Tente um termo mais genérico em inglês |
| "Vídeo saiu muito curto" | Aumente duração em segundos |
| "Áudio com sotaque estranho" | Mude a voz (escolha outra no selectbox) |

---

## 🎯 Meta para Produção

**Objetivo: 1 vídeo por dia**

```
Segunda: Tecnologia (3 vídeos)
Terça: Esportes (3 vídeos)
Quarta: Cinema (3 vídeos)
Quinta: Esportes (3 vídeos)
Sexta: Tecnologia (3 vídeos)
Fim de semana: Posts dos melhores

Total: 15 vídeos por semana = 60 vídeos por mês 📈
```

---

Divirta-se criando! 🚀
