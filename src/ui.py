"""Helper UI Streamlit: CSS, loader data ber-cache, tema grafik, komponen kartu."""
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from .config import ASSETS_DIR, RESULTS_DIR, COMMODITIES
from .data_loader import load_long
from .preprocessing import last_observed_month

# Palet utama: #91EAAF (mint) · #C3E956 (lime) · #4D7111 (olive) · #F4FFFC (cream)
OLIVE, OLIVE_DEEP = "#4D7111", "#2B4208"
MINT, LIME, CREAM = "#91EAAF", "#C3E956", "#F4FFFC"
MINT_DEEP, LIME_DEEP, CORAL = "#2FA86A", "#7FA41C", "#E8734A"
NAVY, GREEN = OLIVE_DEEP, OLIVE            # alias agar kode lama tetap jalan
PALETTE = [OLIVE, MINT_DEEP, LIME_DEEP, CORAL, OLIVE_DEEP, MINT, "#6AA84F"]
MIN_MARKETS_FOR_NATIONAL = 100   # bulan dengan <100 pasar teramati tidak dipakai utk rata-rata nasional

ILLUS_DIR = ASSETS_DIR / "illustrations"
# kode komoditas -> (nama file ilustrasi, warna latar lingkaran)
ILLUS = {
    "eggs": ("telur", LIME),
    "garlic": ("bawang_putih", MINT),
    "meat_chicken": ("daging_ayam", "#FBD9C7"),
    "oil": ("minyak", "#D5F7E4"),
    "onions": ("bawang_merah", "#FBD9C7"),
    "rice": ("beras", "#EAF8D0"),
    "sugar": ("gula", LIME),
}

ARROW_UP = ("<svg class='pc-arrow' viewBox='0 0 10 10' aria-hidden='true'>"
            "<path d='M5 1.5 9 8.5H1Z' fill='currentColor'/></svg>")
ARROW_DOWN = ("<svg class='pc-arrow' viewBox='0 0 10 10' aria-hidden='true'>"
              "<path d='M5 8.5 9 1.5H1Z' fill='currentColor'/></svg>")


def arrow_icon(up: bool) -> str:
    return ARROW_UP if up else ARROW_DOWN


def illus_svg(code: str) -> str:
    """SVG ilustrasi satu baris (aman untuk st.markdown)."""
    name = ILLUS[code][0]
    return (ILLUS_DIR / f"{name}.svg").read_text(encoding="utf-8").strip().replace("\n", "")


def inject_css():
    css = (ASSETS_DIR / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner="Memuat dataset...")
def get_long() -> pd.DataFrame:
    return load_long()


@st.cache_data
def get_obs() -> pd.DataFrame:
    """Hanya harga observasi valid (bukan estimasi, bukan outlier)."""
    d = get_long()
    d = d[d["price_clean"].notna()].copy()
    for c in ["geo_id", "adm1_name", "adm2_name", "mkt_name", "commodity", "commodity_name"]:
        d[c] = d[c].astype(str)
    return d


@st.cache_data
def get_national() -> pd.DataFrame:
    """Rata-rata harga observasi antarpasar per bulan & komoditas (bulan dgn cakupan pasar memadai)."""
    o = get_obs()
    g = o.groupby(["date", "commodity", "commodity_name"]).agg(price=("price_clean", "mean"),
                                                                n_markets=("geo_id", "nunique")).reset_index()
    return g[g["n_markets"] >= MIN_MARKETS_FOR_NATIONAL].sort_values(["commodity", "date"])


@st.cache_data
def last_obs_month() -> pd.Timestamp:
    return last_observed_month(get_long())


@st.cache_data
def read_csv_result(name: str) -> pd.DataFrame:
    return pd.read_csv(RESULTS_DIR / name)


def idr(x, d=0):
    return "-" if x is None or pd.isna(x) else "Rp " + f"{x:,.{d}f}".replace(",", ".")


def fmt_pct(x, signed=False, d=1):
    t = f"{x:+.{d}f}" if signed else f"{x:.{d}f}"
    return t.replace(".", ",") + "%"


def fmt_month(ts) -> str:
    bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus",
             "September", "Oktober", "November", "Desember"]
    return f"{bulan[ts.month - 1]} {ts.year}"


def page_header(title, subtitle):
    st.markdown(f"<div class='pc-header'><h1>{title}</h1><p>{subtitle}</p></div>", unsafe_allow_html=True)


def section_title(title, sub=""):
    st.markdown(f"<div class='pc-sec'><h2>{title}</h2><p>{sub}</p></div>", unsafe_allow_html=True)


def stat_card(label, value, sub="", tone=""):
    st.markdown(f"<div class='pc-card {tone}'><div class='pc-label'>{label}</div>"
                f"<div class='pc-value'>{value}</div><div class='pc-sub'>{sub}</div></div>",
                unsafe_allow_html=True)


def style_fig(fig: go.Figure, height=380) -> go.Figure:
    fig.update_layout(height=height, template="plotly_white", font=dict(family="Nunito, sans-serif", color=OLIVE_DEEP),
                      margin=dict(l=10, r=10, t=70, b=10), legend_title_text="", colorway=PALETTE,
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title_text=""),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E4EFD7")
    return fig


def show(fig):
    st.plotly_chart(fig, width="stretch", theme=None)


def movers_card(up_name, up_pct, dn_name, dn_pct) -> str:
    """Kartu ringkasan (ditaruh di grid) untuk komoditas paling naik & paling turun."""
    return ("<div class='pc-mini pc-movers'><div class='pc-mname'>Sorotan bulan ini</div>"
            f"<div class='pc-mv'><span class='pc-delta up'>{ARROW_UP}{fmt_pct(up_pct)}</span>{up_name} paling naik</div>"
            f"<div class='pc-mv'><span class='pc-delta down'>{ARROW_DOWN}{fmt_pct(abs(dn_pct))}</span>{dn_name} paling turun</div>"
            "</div>")


def price_grid(items, extra=""):
    """Kartu harga responsif. items: [(kode_komoditas, nama, harga_str, delta_str, naik_bool)]"""
    cards = []
    for code, name, val, delta, up in items:
        blob = ILLUS[code][1]
        cards.append(f"<div class='pc-mini'><div class='pc-blob' style='--blob:{blob}'>{illus_svg(code)}</div>"
                     f"<div class='pc-mname'>{name}</div>"
                     f"<div class='pc-mval'>{val} <span class='pc-unit'>/kg</span></div>"
                     f"<div class='pc-delta {'up' if up else 'down'}'>{arrow_icon(up)}{delta}</div></div>")
    st.markdown("<div class='pc-grid'>" + "".join(cards) + extra + "</div>", unsafe_allow_html=True)


def hero(title, text, chips=(), strip=False):
    ch = "".join(f"<span class='pc-chip'>{c}</span>" for c in chips)
    strip_html = ("<div class='pc-strip'>" + "".join(illus_svg(k) for k in ILLUS) + "</div>") if strip else ""
    st.markdown(f"<div class='pc-hero'><div class='pc-hero-text'><h1>{title}</h1><p>{text}</p>"
                f"<div class='pc-chips'>{ch}</div></div>{strip_html}</div>", unsafe_allow_html=True)


def insight(text):
    st.markdown(f"<div class='pc-insight'>{text}</div>", unsafe_allow_html=True)


def step(n, text):
    st.markdown(f"<div class='pc-step'><span>{n}</span>{text}</div>", unsafe_allow_html=True)


def help_box(title, md):
    with st.expander(title):
        st.markdown(md)
