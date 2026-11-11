"""Helper UI Streamlit: CSS, loader data ber-cache, tema grafik, kartu statistik."""
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from .config import ASSETS_DIR, RESULTS_DIR, COMMODITIES
from .data_loader import load_long
from .preprocessing import last_observed_month

NAVY, GREEN, SOFT, OFF = "#0A2F4F", "#14A38B", "#E3F6F1", "#F2FAF8"
PALETTE = ["#14A38B", "#1B6CA8", "#F5A623", "#E4572E", "#0A2F4F", "#7BCFC0", "#6AA9D8"]
ICONS = {"eggs": "🥚", "garlic": "🧄", "meat_chicken": "🍗", "oil": "🛢️", "onions": "🧅", "rice": "🌾", "sugar": "🍬"}
MIN_MARKETS_FOR_NATIONAL = 100   # bulan dengan <100 pasar teramati tidak dipakai utk rata-rata nasional


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


def page_header(title, subtitle, icon=""):
    st.markdown(f"<div class='pc-header'><h1>{icon} {title}</h1><p>{subtitle}</p></div>", unsafe_allow_html=True)


def stat_card(label, value, sub="", tone=""):
    st.markdown(f"<div class='pc-card {tone}'><div class='pc-label'>{label}</div>"
                f"<div class='pc-value'>{value}</div><div class='pc-sub'>{sub}</div></div>",
                unsafe_allow_html=True)


def style_fig(fig: go.Figure, height=380) -> go.Figure:
    fig.update_layout(height=height, template="plotly_white", font=dict(family="Inter, sans-serif", color=NAVY),
                      margin=dict(l=10, r=10, t=70, b=10), legend_title_text="", colorway=PALETTE,
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title_text=""),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="#E3E7E4")
    return fig


def show(fig):
    st.plotly_chart(fig, width="stretch", theme=None)


def price_grid(items):
    """Kartu harga responsif. items: [(kode_komoditas, nama, harga_str, delta_str, naik_bool)]"""
    html = "<div class='pc-grid'>" + "".join(
        f"<div class='pc-mini'><div class='pc-emoji'>{ICONS.get(c, '')}</div><div class='pc-mname'>{n}</div>"
        f"<div class='pc-mval'>{v} <span class='pc-unit'>/kg</span></div>"
        f"<div class='pc-delta {'up' if u else 'down'}'>{'▲' if u else '▼'} {d}</div></div>"
        for c, n, v, d, u in items) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


def hero(title, text, chips=()):
    ch = "".join(f"<span class='pc-chip'>{c}</span>" for c in chips)
    st.markdown(f"<div class='pc-hero'><h1>{title}</h1><p>{text}</p><div class='pc-chips'>{ch}</div></div>",
                unsafe_allow_html=True)


def insight(text):
    st.markdown(f"<div class='pc-insight'>💡 {text}</div>", unsafe_allow_html=True)


def step(n, text):
    st.markdown(f"<div class='pc-step'><span>{n}</span>{text}</div>", unsafe_allow_html=True)


def help_box(title, md):
    with st.expander(f"❓ {title}"):
        st.markdown(md)
