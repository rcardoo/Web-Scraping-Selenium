# 🔨 PriceScraper – Pesquisa de Preços de Eletrônicos

> Trabalho acadêmico de Web Scraping | Automação completa de coleta, análise e envio de relatório de preços em marketplaces brasileiros.

---

## 📋 Sobre o Projeto

O **PriceScraper** simula uma situação real de pesquisa de preços para compra de materiais de reforma doméstica. A automação percorre **3 marketplaces diferentes**, coleta dados de **25 itens**, realiza uma análise exploratória dos dados (EDA) e gera um **relatório completo em PDF**, enviado automaticamente por e-mail ao final da execução.

Todo o processo é registrado em **logs estruturados** e uma **gravação de vídeo da execução** é gerada para fins de auditoria e apresentação.

---

## 🎯 Objetivo

Construir uma pipeline de raspagem de dados capaz de:

1. Buscar 25 itens em 3 marketplaces
2. Coletar os **3 primeiros produtos** exibidos em cada busca
3. Identificar o **produto mais barato** entre os três primeiros resultados
4. Realizar análise exploratória dos dados coletados (EDA)
5. Gerar um **relatório PDF** com os resultados e gráficos
6. **Enviar o relatório por e-mail** automaticamente
7. Registrar toda a execução em **logs** e em **vídeo**

---

## 🛒 Marketplaces Pesquisados

| # | Marketplace |
|---|-------------|
| 1 | Mercado Livre |
| 2 | Amazon Brasil |
| 3 | Shopee |

---

## 📦 Dados Coletados

Para cada produto encontrado, são coletadas as seguintes informações:

| Campo | Descrição |
|---|---|
| `nome_produto` | Nome completo do produto conforme exibido |
| `preco` | Preço em reais (R$) |
| `quantidade` | Quantidade/unidade quando exibida separadamente |
| `url` | Link direto para o produto (recomendado) |
| `marketplace` | Página/loja de onde o item foi coletado |


---

## 🔍 Regras de Coleta

- São coletados os **3 primeiros produtos** exibidos na página de resultados de busca de cada marketplace.
- Caso um item não seja encontrado em algum marketplace, a linha é registrada com valores nulos e devidamente logada.

---

## 🛠️ Tecnologias Utilizadas

| Biblioteca | Finalidade |
|---|---|
| `selenium` | Automação do navegador e raspagem de dados dinâmicos |
| `pandas` | Manipulação, limpeza e análise dos dados coletados |
| `numpy` | Suporte a operações numéricas na EDA |
| `email.mime` | Composição e envio automático do relatório por e-mail |
| `matplotlib`| Geração de gráficos para o relatório |
| `logging` | Registro estruturado de logs da execução |

---

## 📊 Análise Exploratória (EDA)

A EDA realizada sobre os dados coletados inclui:

- **Distribuição de preços** por marketplace 
- **Comparativo de preços médios** por item entre os marketplaces
- **Percentual de itens mais baratos** por marketplace
- **Ranking dos itens com maior variação de preço** entre plataformas
- **Economia potencial** ao comprar sempre no marketplace mais barato
- Estatísticas descritivas: média, mediana, desvio padrão, mín. e máx. por item

---


## 📁 Estrutura do Projeto

```
priceScraper/
│
├── Atividade_Final.ipynb    # Descrição do objetivo da atividade
│
├── Scraping.ipynb           # Raspagem dos dados e email automatico
│
├── analise_pdf.py           # Análise descritiva dos dados e gera o PDF
│
└── README.md
```

---

## ⚙️ Instalação e Execução

### Pré-requisitos

- Python 3.10+
- Google Chrome instalado
- ChromeDriver compatível com a versão do Chrome

---


## 📌 Observações

- O scraper utiliza **Selenium com ChromeDriver** para lidar com conteúdo dinâmico (JavaScript).
- Pausas aleatórias (`time.sleep`) são aplicadas entre requisições para evitar bloqueios.
- O projeto é estritamente acadêmico e respeita os Termos de Uso dos marketplaces.

---

Desenvolvido como trabalho acadêmico da disciplina de **Web Scraping**.

---

## 📜 Licença

Este projeto é de uso **exclusivamente acadêmico**.
