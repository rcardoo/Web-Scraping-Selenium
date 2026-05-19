import os
import io
import datetime
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image, PageBreak, KeepTogether,
)

# ══════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════
CSV_PATH   = "resultados.csv"
OUTPUT_PDF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analise_precos.pdf")

COR_AZUL    = "#1E3A5F"
COR_VERDE   = "#16A34A"
COR_VERDE_L = "#DCFCE7"
COR_CINZA   = "#64748B"
COR_LINHA1  = "#F0F4F8"
COR_BORDA   = "#CBD5E1"
PALETTE     = ["#2563EB", "#16A34A", "#DC2626", "#D97706", "#7C3AED"]

W_PAGE = A4[0] - 4 * cm   # largura útil

# ══════════════════════════════════════════════════════════════
# LEITURA E LIMPEZA
# ══════════════════════════════════════════════════════════════
df = pd.read_csv(CSV_PATH, sep=";")

df["Preço"] = df["Preço"].astype(str)
df["Preço"] = df["Preço"].replace(r"^\s*R\$\s*,*\s*$", np.nan, regex=True)
df["Preço"] = df["Preço"].replace("Sem preço", np.nan, regex=True)
df["Preço"] = df["Preço"].str.replace("R$", "", regex=False)
df["Preço"] = (df["Preço"].str.replace(".", "", regex=False)
                           .str.replace(",", ".", regex=False)
                           .str.strip())
df["Preço"] = pd.to_numeric(df["Preço"], errors="coerce").fillna(0)
df = df[df["Preço"] != 0].copy()

# produtos que têm algum preço zero em qualquer loja → removidos
_zeros = df[df["Preço"] == 0]["Pesquisa"].unique()
df = df[~df["Pesquisa"].isin(_zeros)].copy()

# ─────────────────────────────────────────────
# FILTRO DE OUTLIERS NO DF PRINCIPAL
# ─────────────────────────────────────────────
# Remove linhas onde o preço é muito divergente dentro de cada produto
def remover_outliers_por_pesquisa(df, coluna="Preço", grupo="Pesquisa", variacao=0.5):
    """
    Remove preços que desviam mais que `variacao` da mediana do grupo.
    variacao=0.5  →  remove preços fora de [mediana - 50%, mediana + 50%]
    variacao=0.3  →  mais restrito (30%)
    variacao=1.0  →  mais permissivo (100%)
    """
    mediana = df.groupby(grupo)[coluna].transform("median")
    
    lim_inf = mediana * (1 - variacao)
    lim_sup = mediana * (1 + variacao)
    
    mask = (df[coluna] >= lim_inf) & (df[coluna] <= lim_sup)
    
    df_limpo = df[mask].reset_index(drop=True)
    print(f"Linhas removidas: {len(df) - len(df_limpo)} / {len(df)}")
    return df_limpo


df = remover_outliers_por_pesquisa(df, variacao=0.5)

# ══════════════════════════════════════════════════════════════
# ANÁLISES
# ══════════════════════════════════════════════════════════════

# — média por produto × loja
medias_prod_loja = (
    df.groupby(["Pesquisa", "Loja"])["Preço"]
    .mean().round(2).reset_index()
    .rename(columns={"Preço": "Preço Médio"})
)

# — site mais barato por produto
site_barato = []
for produto in df["Pesquisa"].unique():
    sub    = df[df["Pesquisa"] == produto].groupby("Loja")["Preço"].mean()
    loja   = sub.idxmin()
    preco  = sub.min()
    site_barato.append({"Produto": produto, "Loja Mais Barata": loja,
                         "Menor Preço Médio": round(preco, 2)})
df_site_barato = pd.DataFrame(site_barato)

# — ranking geral
media_geral = df.groupby("Loja")["Preço"].mean().sort_values().reset_index()
media_geral.columns = ["Loja", "Preço Médio Geral"]
media_geral["Preço Médio Geral"] = media_geral["Preço Médio Geral"].round(2)
vencedor    = media_geral.iloc[0]["Loja"]
menor_media = media_geral.iloc[0]["Preço Médio Geral"]

# — estatísticas por produto
idx_min = df.groupby("Pesquisa")["Preço"].idxmin()
idx_max = df.groupby("Pesquisa")["Preço"].idxmax()

stats = df.groupby("Pesquisa")["Preço"].agg(
    Menor_Preco="min", Maior_Preco="max", Preco_Medio="mean",
).reset_index()

stats["Loja_Menor"]  = df.loc[idx_min, "Loja"].values
stats["Loja_Maior"]  = df.loc[idx_max, "Loja"].values
stats["Variacao_pct"]= ((stats["Maior_Preco"] - stats["Menor_Preco"])
                         / stats["Menor_Preco"] * 100).round(2)
stats["Economia"]    = (stats["Maior_Preco"] - stats["Menor_Preco"]).round(2)

menor_total  = stats["Menor_Preco"].sum()
maior_total  = stats["Maior_Preco"].sum()
economia_tot = maior_total - menor_total
eco_pct      = economia_tot / maior_total * 100


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def brl(v):
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def trunc(txt, n=28):
    txt = str(txt)
    return txt[:n] + "..." if len(txt) > n else txt

def fig_to_img(fig, width, height_ratio=0.45):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width, height=width * height_ratio)

def rl_table(rows, col_widths, highlight_col=None, highlight_fn=None):
    """rows: list of lists (first row = header)."""
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND",     (0, 0), (-1,  0), colors.HexColor(COR_AZUL)),
        ("TEXTCOLOR",      (0, 0), (-1,  0), colors.white),
        ("FONTNAME",       (0, 0), (-1,  0), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 8),
        ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor(COR_LINHA1), colors.white]),
        ("GRID",           (0, 0), (-1, -1), 0.4,
         colors.HexColor(COR_BORDA)),
    ]
    if highlight_col is not None and highlight_fn is not None:
        for r, row in enumerate(rows[1:], start=1):
            if highlight_fn(row[highlight_col]):
                style.append(("BACKGROUND", (highlight_col, r),
                               (highlight_col, r),
                               colors.HexColor("#BBF7D0")))
    t.setStyle(TableStyle(style))
    return t


# ══════════════════════════════════════════════════════════════
# GRÁFICOS
# ══════════════════════════════════════════════════════════════
fmt_brl = mticker.FuncFormatter(
    lambda v, _: f"R${v:,.0f}".replace(",", "."))

def grafico_barras_agrupadas():
    """Preco medio por produto e loja — sem outliers, top 10 produtos."""
    # media geral por produto (todas as lojas) para filtrar outliers e rankear
    media_por_produto = (
        medias_prod_loja.groupby("Pesquisa")["Preço Médio"]
        .mean().reset_index()
    )

    # remove outliers via IQR
    q1, q3 = media_por_produto["Preço Médio"].quantile([0.25, 0.75])
    iqr     = q3 - q1
    sem_out = media_por_produto[
        media_por_produto["Preço Médio"] <= q3 + 1.5 * iqr
    ]

    # top 10 por maior media (mais interessantes de comparar)
    top10 = sem_out.nlargest(10, "Preço Médio")["Pesquisa"].tolist()

    sub      = medias_prod_loja[medias_prod_loja["Pesquisa"].isin(top10)].copy()
    produtos = top10
    lojas    = sub["Loja"].unique()
    x        = np.arange(len(produtos))
    w        = 0.75 / len(lojas)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for i, loja in enumerate(lojas):
        vals = []
        for p in produtos:
            v = sub[(sub["Pesquisa"] == p) & (sub["Loja"] == loja)]["Preço Médio"].values
            vals.append(v[0] if len(v) else 0)
        bars = ax.bar(x + i * w, vals, width=w * 0.9,
                      label=loja, color=PALETTE[i % len(PALETTE)], zorder=3)
        mx = max(v for v in vals if v)
        for bar, val in zip(bars, vals):
            if val:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + mx * 0.01,
                        brl(val), ha="center", va="bottom",
                        fontsize=6.5, rotation=40)

    ax.set_xticks(x + w * (len(lojas) - 1) / 2)
    ax.set_xticklabels([trunc(p, 20) for p in produtos],
                       fontsize=8, rotation=15, ha="right")
    ax.yaxis.set_major_formatter(fmt_brl)
    ax.set_title("Preco Medio por Produto e Loja - Top 10 (sem outliers)",
                 fontsize=11, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    fig.tight_layout()
    return fig_to_img(fig, W_PAGE, 0.55)

def grafico_ranking_geral():
    """Barras horizontais: média geral por loja."""
    fig, ax = plt.subplots(figsize=(7, 3))
    cores = [COR_VERDE if i == 0 else COR_CINZA
             for i in range(len(media_geral))]
    bars = ax.barh(media_geral["Loja"], media_geral["Preço Médio Geral"],
                   color=cores, zorder=3)
    ax.xaxis.set_major_formatter(fmt_brl)
    ax.set_title("Ranking Geral — Preço Médio por Loja",
                 fontsize=11, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.35, zorder=0)
    mx = media_geral["Preço Médio Geral"].max()
    for bar, val in zip(bars, media_geral["Preço Médio Geral"]):
        ax.text(bar.get_width() + mx * 0.01,
                bar.get_y() + bar.get_height() / 2,
                brl(val), va="center", fontsize=8)
    fig.tight_layout()
    return fig_to_img(fig, W_PAGE * 0.85, 0.38)

def grafico_variacao():
    """Barras horizontais: variacao % por produto, sem outliers, top 10."""
    s = stats.copy()

    # remove outliers via IQR
    q1, q3 = s["Variacao_pct"].quantile([0.25, 0.75])
    iqr     = q3 - q1
    s = s[s["Variacao_pct"] <= q3 + 1.5 * iqr]

    # top 10 por variacao, ordem crescente para barras horizontais
    s = s.nlargest(10, "Variacao_pct").sort_values("Variacao_pct")

    fig, ax = plt.subplots(figsize=(8, 4))
    cores = [PALETTE[i % len(PALETTE)] for i in range(len(s))]
    bars  = ax.barh([trunc(p, 28) for p in s["Pesquisa"]],
                    s["Variacao_pct"], color=cores, zorder=3)
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_title("Variacao de Preco por Produto - Top 10 (sem outliers)",
                 fontsize=11, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.35, zorder=0)
    mx = s["Variacao_pct"].max()
    for bar, val in zip(bars, s["Variacao_pct"]):
        ax.text(bar.get_width() + mx * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=8)
    fig.tight_layout()
    return fig_to_img(fig, W_PAGE, 0.50)

def grafico_economia():
    """Barras horizontais: economia por produto."""
    fig, ax = plt.subplots(figsize=(7, 3.5))
    bars = ax.barh([trunc(p, 22) for p in stats["Pesquisa"]],
                   stats["Economia"], color=COR_VERDE, zorder=3)
    ax.xaxis.set_major_formatter(fmt_brl)
    ax.set_title("Economia por Produto (maior - menor preço)",
                 fontsize=11, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.35, zorder=0)
    mx = stats["Economia"].max()
    for bar, val in zip(bars, stats["Economia"]):
        ax.text(bar.get_width() + mx * 0.01,
                bar.get_y() + bar.get_height() / 2,
                brl(val), va="center", fontsize=8)
    fig.tight_layout()
    return fig_to_img(fig, W_PAGE * 0.85, 0.42)


# ══════════════════════════════════════════════════════════════
# ESTILOS REPORTLAB
# ══════════════════════════════════════════════════════════════
styles  = getSampleStyleSheet()
s_title = ParagraphStyle("s_title", parent=styles["Title"],
                          fontSize=20, textColor=colors.HexColor(COR_AZUL),
                          spaceAfter=4)
s_h2    = ParagraphStyle("s_h2", parent=styles["Heading2"],
                          fontSize=12, textColor=colors.HexColor(COR_AZUL),
                          spaceBefore=16, spaceAfter=4)
s_body  = ParagraphStyle("s_body", parent=styles["Normal"],
                          fontSize=9, leading=14)
s_cap   = ParagraphStyle("s_cap", parent=styles["Normal"],
                          fontSize=7.5, textColor=colors.HexColor(COR_CINZA),
                          alignment=TA_CENTER, spaceAfter=6)
s_dest  = ParagraphStyle("s_dest", parent=styles["Normal"],
                          fontSize=10, leading=16,
                          textColor=colors.HexColor("#14532D"),
                          backColor=colors.HexColor(COR_VERDE_L),
                          borderPad=8)
s_warn  = ParagraphStyle("s_warn", parent=styles["Normal"],
                          fontSize=7, textColor=colors.HexColor(COR_CINZA),
                          alignment=TA_CENTER)


# ══════════════════════════════════════════════════════════════
# MONTAGEM DO PDF
# ══════════════════════════════════════════════════════════════
doc   = SimpleDocTemplate(OUTPUT_PDF, pagesize=A4,
                           leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
story = []
HR    = lambda: HRFlowable(width=W_PAGE, thickness=0.6,
                            color=colors.HexColor(COR_BORDA), spaceAfter=6)
SP    = lambda n=0.3: Spacer(1, n*cm)

# ── Capa ──────────────────────────────────────────────────────
story += [
    SP(0.8),
    Paragraph("Análise Comparativa de Preços", s_title),
    HRFlowable(width=W_PAGE, thickness=2.5,
               color=colors.HexColor(COR_AZUL), spaceAfter=6),
    Paragraph(
        f"Gerado em {datetime.datetime.now().strftime('%d/%m/%Y  %H:%M')}  |  "
        f"Produtos: {df['Pesquisa'].nunique()}  |  "
        f"Lojas: {df['Loja'].nunique()}  |  "
        f"Registros: {len(df)}",
        s_cap),
    SP(0.3),
]

# ── Seção 1: Preço médio por produto × loja ───────────────────
story += [Paragraph("1. Preço Médio por Produto e Loja", s_h2), HR()]

rows1 = [["Produto", "Loja", "Preço Médio"]]
for _, r in medias_prod_loja.iterrows():
    rows1.append([trunc(r["Pesquisa"]), r["Loja"], brl(r["Preço Médio"])])
cw1 = [W_PAGE*0.48, W_PAGE*0.27, W_PAGE*0.25]
story += [rl_table(rows1, cw1), SP(0.3), grafico_barras_agrupadas(),
          Paragraph("Fig. 1 — Preço médio por produto e loja.", s_cap)]

# ── Seção 2: Site mais barato por produto ─────────────────────
story += [Paragraph("2. Site Mais Barato por Produto", s_h2), HR()]

rows2 = [["Produto", "Loja Mais Barata", "Menor Preço Médio"]]
for _, r in df_site_barato.iterrows():
    rows2.append([trunc(r["Produto"]), r["Loja Mais Barata"],
                  brl(r["Menor Preço Médio"])])
cw2 = [W_PAGE*0.48, W_PAGE*0.27, W_PAGE*0.25]
story += [rl_table(rows2, cw2), SP(0.4)]

# ── Seção 3: Ranking geral ────────────────────────────────────
story += [Paragraph("3. Ranking Geral — Menor Preço Médio", s_h2), HR()]

rows3 = [["Loja", "Preço Médio Geral"]]
for _, r in media_geral.iterrows():
    rows3.append([r["Loja"], brl(r["Preço Médio Geral"])])
cw3 = [W_PAGE*0.6, W_PAGE*0.4]

# destaca a linha vencedora (menor preço = linha 1 após header)
t3 = rl_table(rows3, cw3)
story += [t3, SP(0.3), grafico_ranking_geral(),
          Paragraph("Fig. 2 — Ranking de preço médio geral por loja (verde = vencedor).", s_cap)]

story.append(PageBreak())

# ── Seção 4: Estatísticas completas ──────────────────────────
story += [Paragraph("4. Estatísticas por Produto", s_h2), HR()]

rows4 = [["Produto", "Menor Preço", "Loja", "Maior Preço", "Loja",
          "Média", "Variação"]]
for _, r in stats.iterrows():
    rows4.append([
        trunc(r["Pesquisa"]),
        brl(r["Menor_Preco"]), r["Loja_Menor"],
        brl(r["Maior_Preco"]), r["Loja_Maior"],
        brl(r["Preco_Medio"]),
        f"{r['Variacao_pct']:.1f}%",
    ])
cw4 = [W_PAGE*0.22, W_PAGE*0.12, W_PAGE*0.13,
       W_PAGE*0.12, W_PAGE*0.13, W_PAGE*0.14, W_PAGE*0.14]
story += [rl_table(rows4, cw4), SP(0.3),
          grafico_variacao(),
          Paragraph("Fig. 3 — Variação percentual entre maior e menor preço por produto.", s_cap)]

# ── Seção 5: Economia ─────────────────────────────────────────
story += [Paragraph("5. Economia — Detalhes por Produto", s_h2), HR()]

rows5 = [["Produto", "Menor Preço", "Maior Preço", "Economia", "Economia %"]]
for _, r in stats.iterrows():
    rows5.append([
        trunc(r["Pesquisa"]),
        brl(r["Menor_Preco"]), brl(r["Maior_Preco"]),
        brl(r["Economia"]),
        f"{r['Variacao_pct']:.1f}%",
    ])
cw5 = [W_PAGE*0.30, W_PAGE*0.17, W_PAGE*0.17, W_PAGE*0.18, W_PAGE*0.18]
story += [rl_table(rows5, cw5), SP(0.3),
          grafico_economia(),
          Paragraph("Fig. 4 — Economia potencial por produto.", s_cap)]

# resumo economia
story += [
    SP(0.2),
    rl_table([
        ["", "Valor"],
        ["Comprando sempre no menor preco", brl(menor_total)],
        ["Comprando sempre no maior preco", brl(maior_total)],
        ["Economia total",                  brl(economia_tot)],
        ["Economia %",                      f"{eco_pct:.1f}%"],
    ], [W_PAGE*0.65, W_PAGE*0.35]),
    SP(0.3),
]

# ── Seção 6: Conclusões ───────────────────────────────────────
story.append(PageBreak())
story += [Paragraph("6. Conclusoes e Recomendacao Final", s_h2),
          HRFlowable(width=W_PAGE, thickness=2,
                     color=colors.HexColor(COR_AZUL), spaceAfter=10)]

max_var_row  = stats.loc[stats["Variacao_pct"].idxmax()]
conclusoes   = [
    f"Foram analisados <b>{df['Pesquisa'].nunique()} produtos</b> em "
    f"<b>{df['Loja'].nunique()} lojas</b>, totalizando {len(df)} registros "
    f"(precos R$&nbsp;0 e produtos que tinha muita diferença nos preços foram excluidos)."
    f"Exemplo: no mercado livre e na kabum o produto custa por volta de R$&nbsp;1000 "
    f"e na amazon custa R$&nbsp;30",

    f"A <b>maior variacao de preço</b> foi no produto "
    f"<b>{trunc(max_var_row['Pesquisa'], 40)}</b>: "
    f"{max_var_row['Variacao_pct']:.1f}% de diferenca entre "
    f"{max_var_row['Loja_Menor']} ({brl(max_var_row['Menor_Preco'])}) e "
    f"{max_var_row['Loja_Maior']} ({brl(max_var_row['Maior_Preco'])}).",

    f"Comprando <b>sempre pelo menor preço</b> por produto o total seria "
    f"<b>{brl(menor_total)}</b>, contra <b>{brl(maior_total)}</b> pagando "
    f"sempre o maior preço, economia de <b>{brl(economia_tot)} ({eco_pct:.1f}%)</b>.",

    f"No <b>ranking geral</b>, a loja com menor preço medio foi "
    f"<b>{vencedor}</b> (media {brl(menor_media)}). "
    f"Concentrar as compras nela tende a ser a opcao mais simples.",
]

for txt in conclusoes:
    story += [Paragraph(f"&#8226; &nbsp;{txt}", s_body), SP(0.25)]

story += [
    SP(0.4),
    Paragraph(
        f"Recomendacao: comprar na <b>{vencedor}</b> para simplicidade, "
        f"ou distribuir item a item pelos menores precos e economizar ate "
        f"<b>{brl(economia_tot)}</b>.",
        s_dest),
    SP(1.0),
    HR(),
    Paragraph(
        "Precos coletados na data da pesquisa e sujeitos a alteracao. "
        "Verifique o valor final antes de concluir a compra.", s_warn),
]

doc.build(story)
print(f"PDF gerado: {OUTPUT_PDF}")