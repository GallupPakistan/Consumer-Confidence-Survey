import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import os
import importlib.util

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SBP Consumer Confidence Survey",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  GLOBAL STYLE
# ─────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#0d1117; color:#e6edf3; }
[data-testid="stSidebar"] { background:#161b22; border-right:1px solid #21262d; }
[data-testid="stSidebar"] * { color:#c9d1d9 !important; }
[data-testid="stSidebar"] .stRadio label { color:#c9d1d9 !important; }
[data-testid="stSidebar"] .stCheckbox label { color:#c9d1d9 !important; }

.dash-header {
    background: linear-gradient(135deg,#0a3d62 0%,#1a1a2e 60%,#16213e 100%);
    border-radius:12px; padding:22px 30px 18px;
    margin-bottom:22px; border:1px solid #21262d;
}
.dash-header h1 { color:#ffffff; font-size:24px; font-weight:700; margin:0 0 6px; }
.dash-header .sub {
    color:#c9d1d9; font-size:14px; margin:0 0 10px; font-weight:400; letter-spacing:0.2px;
}
.dash-header .badge {
    background:rgba(56,139,253,0.15); border:1px solid rgba(56,139,253,0.35);
    border-radius:6px; padding:4px 12px; color:#79c0ff;
    font-size:12px; font-weight:500; display:inline-block;
}

/* ── KPI Cards ── */
.kpi-row { display:flex; gap:12px; margin-bottom:28px; flex-wrap:wrap; }
.kpi-card {
    flex:1; min-width:160px;
    background:#161b22; border:1px solid #21262d;
    border-radius:10px; padding:18px 20px;
    position:relative; overflow:hidden;
}
.kpi-card::before { content:""; position:absolute; top:0; left:0; right:0; height:3px; }
.kpi-card.cci::before  { background:#388bfd; }
.kpi-card.cec::before  { background:#3fb950; }
.kpi-card.eec::before  { background:#d29922; }
.kpi-card.ie::before   { background:#f85149; }
.kpi-card.avg::before  { background:#bc8cff; }

.kpi-label { font-size:11px; color:#8b949e; font-weight:600; text-transform:uppercase; margin-bottom:8px; white-space: nowrap; }
.kpi-value { font-size:36px; font-weight:800; line-height:1; margin-bottom:6px; }
.kpi-card.cci .kpi-value { color:#388bfd; }
.kpi-card.cec .kpi-value { color:#3fb950; }
.kpi-card.eec .kpi-value { color:#d29922; }
.kpi-card.ie  .kpi-value { color:#f85149; }
.kpi-card.avg .kpi-value { color:#bc8cff; }

.kpi-delta { font-size:13px; font-weight:600; margin-bottom:2px; }
.kpi-delta.up   { color:#3fb950; }
.kpi-delta.down { color:#f85149; }
.kpi-delta.flat { color:#8b949e; }
.kpi-note { font-size:11px; color:#8b949e; margin-top:2px; }

.section-title { font-size:20px; font-weight:700; color:#ffffff; margin:36px 0 16px; border-bottom:1px solid #30363d; padding-bottom:8px; }
.insight-box { background:#161b22; border:1px solid #21262d; border-left:3px solid #388bfd; border-radius:8px; padding:12px 16px; font-size:13px; color:#8b949e; margin-top:6px; margin-bottom: 16px; }
.insight-box b { color:#c9d1d9; }
.dev-box { text-align:center; padding:60px 20px; background:#161b22; border:1px dashed #30363d; border-radius:12px; margin-top:20px; }
.dev-box h2 { color:#c9d1d9; margin-bottom:10px; }
.dev-box p { color:#8b949e; font-size:14px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  PLOTLY BASE CONFIG (ANTI-OVERLAP RULES)
# ─────────────────────────────────────────────
BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d1117",
    font=dict(family="Inter,sans-serif", color="#c9d1d9", size=12),
    margin=dict(l=40, r=20, t=50, b=60), # Generous margins to prevent clipping
    # Legend moved to bottom center to prevent side-clipping on small screens
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, font=dict(size=11, color="#c9d1d9")),
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickfont=dict(size=11)),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickfont=dict(size=11)),
    hoverlabel=dict(bgcolor="#161b22", bordercolor="#388bfd", font=dict(color="#c9d1d9", size=12)),
)

C = dict(
    cci="#388bfd", cec="#3fb950", eec="#d29922", ie="#f85149",
    rural="#388bfd", urban="#d29922", male="#79c0ff", female="#bc8cff",
    edu1="#3fb950", edu2="#d29922", edu3="#388bfd",
    p1="#388bfd", p2="#3fb950", p3="#d29922", p4="#f85149",
    y1="#8b949e", y2="#3fb950", y3="#d29922", y4="#388bfd",
)

def apply_layout(fig, title="", height=400, yrange=None, xtickangle=0):
    kw = {**BASE, "height": height, "title": dict(text=title, font=dict(size=14, color="#ffffff"), x=0.01, xanchor="left")}
    fig.update_layout(**kw)
    fig.update_xaxes(tickangle=xtickangle)
    if yrange: fig.update_yaxes(range=yrange)

def add_threshold(fig, row=1, col=1):
    fig.add_hline(y=50, line_dash="dash", line_color="#404650", line_width=1.5, row=row, col=col)
    fig.add_hrect(y0=50, y1=100, fillcolor="rgba(63,185,80,0.04)", line_width=0, row=row, col=col)
    fig.add_hrect(y0=0, y1=50, fillcolor="rgba(248,81,73,0.04)", line_width=0, row=row, col=col)

def line(fig, x, y, name, color, width=2, dash="solid", mode="lines"):
    fig.add_trace(go.Scatter(
        x=x, y=y.round(2) if hasattr(y, 'round') else y, name=name, mode=mode,
        line=dict(color=color, width=width, dash=dash),
        hovertemplate=f"<b>{name}</b>: %{{y:.2f}}<br>%{{x|%b %Y}}<extra></extra>",
    ))

# ─────────────────────────────────────────────
#  DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load():
    df = pd.read_excel("Final_Overall_Indices.xlsx", parse_dates=["Month"])
    df = df.rename(columns={"Unnamed: 16": "Male - Inflation Expectation"})
    df = df.sort_values("Month").reset_index(drop=True)
    df["Year"] = df["Month"].dt.year
    return df

df_all = load()

# ─────────────────────────────────────────────
#  SIDEBAR / NAVIGATION
# ─────────────────────────────────────────────
with st.sidebar:
    if os.path.exists("gallup.png"):
        st.image("gallup.png", use_container_width=True)
    else:
        st.markdown("<div style='text-align:center;padding:10px 0;'><div style='font-size:18px;font-weight:700;color:#388bfd;'>SBP × IBA</div><div style='font-size:11px;color:#8b949e;'>Consumer Confidence Survey</div></div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#21262d;margin:12px 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;font-weight:600;color:#8b949e;text-transform:uppercase;'>Navigation</div>", unsafe_allow_html=True)
    
    pages = ["Main Overview", "Overall Condition", "Current Condition", "Future Condition", "Inflation Expectation"]
    selected_page = st.radio("", pages, label_visibility="collapsed")

    st.markdown("<hr style='border-color:#21262d;margin:12px 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;font-weight:600;color:#8b949e;text-transform:uppercase;'>Time Filter</div>", unsafe_allow_html=True)
    
    preset = st.radio("Quick Preset", ["All data","Last 3 years","Last 1 year","2023 onwards"], label_visibility="collapsed")
    
    months_list = df_all["Month"].dt.to_period("M").astype(str).tolist()
    c1, c2 = st.columns(2)
    with c1: si = st.selectbox("From", range(len(months_list)), format_func=lambda i: months_list[i], index=0)
    with c2: ei = st.selectbox("To", range(len(months_list)), format_func=lambda i: months_list[i], index=len(months_list)-1)

    max_d = df_all["Month"].max()
    if preset == "Last 3 years": s_date = max_d - pd.DateOffset(years=3)
    elif preset == "Last 1 year": s_date = max_d - pd.DateOffset(years=1)
    elif preset == "2023 onwards": s_date = pd.Timestamp("2023-01-01")
    else: s_date = df_all["Month"].min()
    e_date = max_d

    if si > 0 or ei < len(months_list)-1:
        s_date = df_all["Month"].iloc[si]
        e_date = df_all["Month"].iloc[max(si, ei)]

# FILTER DATA
df = df_all[(df_all["Month"] >= pd.Timestamp(s_date)) & (df_all["Month"] <= pd.Timestamp(e_date))].copy()
if df.empty:
    st.error("No data for selected range — adjust the filters.")
    st.stop()

# ─────────────────────────────────────────────
#  MAIN DASHBOARD FUNCTION
# ─────────────────────────────────────────────
def render_main_dashboard(df):
    from_str = df["Month"].iloc[0].strftime("%b %Y")
    to_str   = df["Month"].iloc[-1].strftime("%b %Y")
    lat  = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else lat
    last_lbl = df["Month"].iloc[-1].strftime("%b %Y")

    st.markdown(f"""
    <div class='dash-header'>
        <h1>📊 SBP Consumer Confidence — Comprehensive Overview</h1>
        <p class='sub'>Diffusion Index (0–100) &nbsp;·&nbsp;
           <span style='color:#3fb950;font-weight:600;'>DI &gt; 50 = Optimism</span>
           &nbsp;·&nbsp;
           <span style='color:#f85149;font-weight:600;'>DI &lt; 50 = Pessimism</span>
        </p>
        <span class='badge'>Monthly · {from_str} – {to_str}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs ──
    def kpi_delta(new, old, invert=False):
        d = new - old
        if abs(d) < 0.005: return "→ unchanged", "flat"
        up = (d > 0 and not invert) or (d < 0 and invert)
        return f"{'▲' if d > 0 else '▼'} {abs(d):.2f} vs prev", "up" if up else "down"

    def sentiment(v):
        if pd.isna(v): return "N/A"
        if v >= 55: return "Strongly Optimistic"
        if v >= 50: return "Optimistic"
        if v >= 45: return "Slightly Pessimistic"
        return "Pessimistic"

    cci_d, cci_c = kpi_delta(lat["Consumer Confidence Index"], prev["Consumer Confidence Index"])
    cec_d, cec_c = kpi_delta(lat["Current Economic Conditions Index"], prev["Current Economic Conditions Index"])
    eec_d, eec_c = kpi_delta(lat["Expected Economic Conditions Index"], prev["Expected Economic Conditions Index"])
    ie_d,  ie_c  = kpi_delta(lat["Inflation Expectation"], prev["Inflation Expectation"], invert=True)

    st.markdown(f"""
    <div class='kpi-row'>
      <div class='kpi-card cci'><div class='kpi-label'>Consumer Confidence</div><div class='kpi-value'>{lat['Consumer Confidence Index']:.1f}</div><div class='kpi-delta {cci_c}'>{cci_d}</div><div class='kpi-note'>{sentiment(lat['Consumer Confidence Index'])} · {last_lbl}</div></div>
      <div class='kpi-card cec'><div class='kpi-label'>Current Conditions</div><div class='kpi-value'>{lat['Current Economic Conditions Index']:.1f}</div><div class='kpi-delta {cec_c}'>{cec_d}</div><div class='kpi-note'>How economy feels now</div></div>
      <div class='kpi-card eec'><div class='kpi-label'>Expected Conditions</div><div class='kpi-value'>{lat['Expected Economic Conditions Index']:.1f}</div><div class='kpi-delta {eec_c}'>{eec_d}</div><div class='kpi-note'>12-month ahead outlook</div></div>
      <div class='kpi-card ie'><div class='kpi-label'>Inflation Expectation</div><div class='kpi-value'>{lat['Inflation Expectation']:.1f}</div><div class='kpi-delta {ie_c}'>{ie_d}</div><div class='kpi-note'>Higher = more price fear</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # SECTION 1: MACRO TRENDS
    # ─────────────────────────────────────────────
    st.markdown("<div class='section-title'>1. Macro-Economic Trends</div>", unsafe_allow_html=True)
    
    # Chart 1: Multi-line Core Indices
    fig1 = go.Figure()
    line(fig1, df["Month"], df["Consumer Confidence Index"], "CCI (Overall Confidence)", C["cci"], 3)
    line(fig1, df["Month"], df["Current Economic Conditions Index"], "CEC (Current)", C["cec"], 2)
    line(fig1, df["Month"], df["Expected Economic Conditions Index"], "EEC (Expected)", C["eec"], 2, dash="dash")
    line(fig1, df["Month"], df["Inflation Expectation"], "IE (Inflation Fear)", C["ie"], 2)
    add_threshold(fig1)
    apply_layout(fig1, title="1.1 Core Indices History (Multi-Line)", height=450, yrange=[15,90])
    st.plotly_chart(fig1, use_container_width=True)

    c1, c2 = st.columns(2)
    # Chart 2: Dual Axis Area (CCI vs IE)
    with c1:
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df["Month"], y=df["Consumer Confidence Index"].round(2), name="CCI", line=dict(color=C["cci"], width=2.5), fill="tozeroy", fillcolor="rgba(56,139,253,0.1)"), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df["Month"], y=df["Inflation Expectation"].round(2), name="Inflation Expect.", line=dict(color=C["ie"], width=2, dash="dot")), secondary_y=True)
        apply_layout(fig2, title="1.2 Confidence vs Inflation Fear (Dual-Axis)", height=400)
        fig2.update_yaxes(title_text="CCI", range=[15,80], secondary_y=False)
        fig2.update_yaxes(title_text="Inflation Exp.", range=[40,105], showgrid=False, secondary_y=True)
        st.plotly_chart(fig2, use_container_width=True)

    # Chart 3: Gap Analysis (CEC vs EEC)
    with c2:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=df["Month"], y=df["Current Economic Conditions Index"].round(2), name="Current (CEC)", line=dict(color=C["cec"], width=2)))
        fig3.add_trace(go.Scatter(x=df["Month"], y=df["Expected Economic Conditions Index"].round(2), name="Expected (EEC)", line=dict(color=C["eec"], width=2), fill="tonexty", fillcolor="rgba(210,153,34,0.15)"))
        add_threshold(fig3)
        apply_layout(fig3, title="1.3 Current vs Expected Sentiment Gap (Filled Area)", height=400, yrange=[15,90])
        st.plotly_chart(fig3, use_container_width=True)


    # ─────────────────────────────────────────────
    # SECTION 2: LATEST DEMOGRAPHIC SNAPSHOT
    # ─────────────────────────────────────────────
    st.markdown(f"<div class='section-title'>2. Demographic Snapshot (Latest: {last_lbl})</div>", unsafe_allow_html=True)
    
    c3, c4 = st.columns(2)
    # Chart 4: Radar Chart (Rural vs Urban)
    with c3:
        cats = ['CCI (Confidence)', 'CEC (Current)', 'EEC (Expected)', 'IE (Inflation)']
        r_vals = [lat.get("Rural - Consumer Confidence Index", 0), lat.get("Rural - Current Economic Conditions Index", 0), lat.get("Rural - Expected Economic Conditions Index", 0), lat.get("Rural - Inflation Expectation", 0)]
        u_vals = [lat.get("Urban - Consumer Confidence Index", 0), lat.get("Urban - Current Economic Conditions Index", 0), lat.get("Urban - Expected Economic Conditions Index", 0), lat.get("Urban - Inflation Expectation", 0)]
        
        fig4 = go.Figure()
        fig4.add_trace(go.Scatterpolar(r=r_vals+[r_vals[0]], theta=cats+[cats[0]], fill='toself', name='Rural', line_color=C['rural'], fillcolor="rgba(56,139,253,0.3)"))
        fig4.add_trace(go.Scatterpolar(r=u_vals+[u_vals[0]], theta=cats+[cats[0]], fill='toself', name='Urban', line_color=C['urban'], fillcolor="rgba(210,153,34,0.3)"))
        apply_layout(fig4, title="2.1 Geographic Profile (Radar Plot)", height=400)
        fig4.update_layout(polar=dict(radialaxis=dict(visible=True, range=[20, 85], gridcolor="#30363d", linecolor="#30363d"), bgcolor="#0d1117"), showlegend=True)
        st.plotly_chart(fig4, use_container_width=True)

    # Chart 5: Side-by-Side Donuts (Gender)
    with c4:
        fig5 = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]], subplot_titles=['CCI', 'Inflation Exp.'])
        fig5.add_trace(go.Pie(labels=['Male', 'Female'], values=[lat.get("Male - Consumer Confidence Index", 1), lat.get("Female - Consumer Confidence Index", 1)], hole=.6, marker=dict(colors=[C["male"], C["female"]]), textinfo='label+percent', textposition='inside'), 1, 1)
        fig5.add_trace(go.Pie(labels=['Male', 'Female'], values=[lat.get("Male - Inflation Expectation", 1), lat.get("Female - Inflation Expectation", 1)], hole=.6, marker=dict(colors=[C["male"], C["female"]]), textinfo='label+percent', textposition='inside'), 1, 2)
        apply_layout(fig5, title="2.2 Gender Sentiment Share (Donut)", height=400)
        fig5.update_layout(showlegend=False, margin=dict(t=80, b=20, l=10, r=10)) # Adjust margins to fix title overlap
        for annotation in fig5['layout']['annotations']: annotation['font'] = dict(size=13, color='#c9d1d9')
        st.plotly_chart(fig5, use_container_width=True)

    # Chart 6: Grouped Bar (Education & Profession)
    c5, c6 = st.columns(2)
    with c5:
        ed_lbls = ['< Matric', 'Matric/Inter', 'Graduate+']
        ed_cci = [lat.get("Education less than matric - Consumer Confidence Index"), lat.get("Education matric or intermediate - Consumer Confidence Index"), lat.get("Education graduate or higher - Consumer Confidence Index")]
        ed_ie = [lat.get("Education less than matric - Inflation Expectation"), lat.get("Education matric or intermediate - Inflation Expectation"), lat.get("Education graduate or higher - Inflation Expectation")]
        
        fig6 = go.Figure(data=[
            go.Bar(name='CCI', x=ed_lbls, y=ed_cci, marker_color=C["cci"], text=[f"{v:.1f}" if pd.notna(v) else "" for v in ed_cci], textposition='auto'),
            go.Bar(name='Inflation (IE)', x=ed_lbls, y=ed_ie, marker_color=C["ie"], text=[f"{v:.1f}" if pd.notna(v) else "" for v in ed_ie], textposition='auto')
        ])
        apply_layout(fig6, title="2.3 Education Levels (Grouped Bar)", height=400)
        fig6.update_layout(barmode='group', uniformtext_minsize=10, uniformtext_mode='hide')
        st.plotly_chart(fig6, use_container_width=True)

    with c6:
        # Chart 7: Sorted Horizontal Bar (All Demographic CCI Ranking)
        snap = {
            "National": "Consumer Confidence Index", "Rural": "Rural - Consumer Confidence Index", "Urban": "Urban - Consumer Confidence Index",
            "Male": "Male - Consumer Confidence Index", "Female": "Female - Consumer Confidence Index",
            "Employees": "Profession - employees - Consumer Confidence Index", "Business Svc": "Profession - business (services) - Consumer Confidence Index",
            "Income >100K": "Between PKR 100,000 & PKR 200,000 - Consumer Confidence Index"
        }
        vals, names, colors = [], [], []
        for lbl, cn in snap.items():
            if cn in df.columns:
                v = df[cn].iloc[-1]
                if pd.notna(v):
                    vals.append(v)
                    names.append(lbl)
                    colors.append("#3fb950" if v >= 50 else "#f85149")
        
        # Sort values
        s = sorted(zip(vals, names, colors), key=lambda x: x[0])
        vals, names, colors = zip(*s) if s else ([],[],[])

        fig7 = go.Figure(go.Bar(
            x=list(vals), y=list(names), orientation="h",
            marker=dict(color=list(colors)),
            text=[f"{v:.1f}" for v in vals], textposition="inside", textfont=dict(color="#ffffff")
        ))
        apply_layout(fig7, title="2.4 Segment Ranking by CCI (Horizontal Bar)", height=400)
        fig7.update_layout(showlegend=False, margin=dict(l=100)) # Left margin for long names
        fig7.add_vline(x=50, line_dash="dash", line_color="#8b949e", line_width=1)
        st.plotly_chart(fig7, use_container_width=True)


    # ─────────────────────────────────────────────
    # SECTION 3: ADVANCED DISTRIBUTION & COMPARISONS
    # ─────────────────────────────────────────────
    st.markdown("<div class='section-title'>3. Deep Dive Analytics</div>", unsafe_allow_html=True)
    
    c7, c8 = st.columns(2)
    with c7:
        # Chart 8: Stacked Area (Income Trend)
        fig8 = go.Figure()
        inc_cols = [
            ("Below 55K", "Below PKR 55,000 - Consumer Confidence Index", "rgba(139,148,158,0.2)", C["y1"]),
            ("55K–100K", "Between PKR 55,000 & PKR 100,000 - Consumer Confidence Index", "rgba(63,185,80,0.2)", C["y2"]),
            ("100K–200K", "Between PKR 100,000 & PKR 200,000 - Consumer Confidence Index", "rgba(210,153,34,0.2)", C["y3"])
        ]
        for name, col, fillcolor, linecolor in inc_cols:
            if col in df.columns:
                fig8.add_trace(go.Scatter(x=df["Month"], y=df[col].round(2), name=name, mode='lines', fill='tozeroy', fillcolor=fillcolor, line=dict(color=linecolor, width=2)))
        apply_layout(fig8, title="3.1 Income Brackets Trend (Stacked Area)", height=400)
        st.plotly_chart(fig8, use_container_width=True)

    with c8:
        # Chart 9: Time-Series Bar (Gender Gap)
        if "Male - Consumer Confidence Index" in df.columns and "Female - Consumer Confidence Index" in df.columns:
            df["Gender Gap"] = df["Male - Consumer Confidence Index"] - df["Female - Consumer Confidence Index"]
            colors_gap = ["#3fb950" if val > 0 else "#f85149" for val in df["Gender Gap"]]
            fig9 = go.Figure(go.Bar(
                x=df["Month"], y=df["Gender Gap"].round(2),
                marker_color=colors_gap,
                hovertemplate="<b>Gap (Male - Female)</b>: %{y:+.2f}<br>%{x|%b %Y}<extra></extra>"
            ))
            apply_layout(fig9, title="3.2 Gender Gap Dynamics (Bar Diff)", height=400)
            fig9.update_layout(showlegend=False)
            st.plotly_chart(fig9, use_container_width=True)

    # Chart 10 & 11: Box Plot (Volatility) & Scatter Correlation
    c9, c10 = st.columns(2)
    with c9:
        # Chart 10: Box Plot of CCI by Year
        fig10 = go.Figure()
        fig10.add_trace(go.Box(x=df["Year"].astype(str), y=df["Consumer Confidence Index"], name="CCI Distribution", marker_color=C["cci"], boxpoints='all', jitter=0.3))
        apply_layout(fig10, title="3.3 CCI Volatility by Year (Box Plot)", height=400)
        fig10.update_layout(showlegend=False)
        st.plotly_chart(fig10, use_container_width=True)

    with c10:
        # Chart 11: Scatter Plot (CEC vs EEC for latest month across demographics)
        scatter_data = []
        for lbl, cec_col in {"National": "Current Economic Conditions Index", "Rural": "Rural - Current Economic Conditions Index", "Urban": "Urban - Current Economic Conditions Index", "Male": "Male - Current Economic Conditions Index", "Female": "Female - Current Economic Conditions Index"}.items():
            eec_col = cec_col.replace("Current", "Expected")
            if cec_col in lat and eec_col in lat:
                scatter_data.append({"Segment": lbl, "CEC": lat[cec_col], "EEC": lat[eec_col]})
        
        if scatter_data:
            sdf = pd.DataFrame(scatter_data).dropna()
            fig11 = px.scatter(sdf, x="CEC", y="EEC", text="Segment", color="Segment", size_max=15)
            # Add y=x reference line
            min_val = min(sdf["CEC"].min(), sdf["EEC"].min()) - 2
            max_val = max(sdf["CEC"].max(), sdf["EEC"].max()) + 2
            fig11.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val, max_val], mode="lines", name="y=x (Neutral Outlook)", line=dict(dash="dash", color="#8b949e")))
            
            apply_layout(fig11, title=f"3.4 Current vs Expected Correlation ({last_lbl})", height=400)
            fig11.update_traces(textposition='top center', marker=dict(size=12))
            fig11.update_layout(showlegend=False)
            st.plotly_chart(fig11, use_container_width=True)

    # ─────────────────────────────────────────────
    # SECTION 4: THE MATRIX
    # ─────────────────────────────────────────────
    st.markdown("<div class='section-title'>4. Complete Demographic Matrix</div>", unsafe_allow_html=True)
    
    # Chart 12: Heatmap
    hmap_cols = {
        "National": "Consumer Confidence Index", "Rural": "Rural - Consumer Confidence Index", "Urban": "Urban - Consumer Confidence Index",
        "Male": "Male - Consumer Confidence Index", "Female": "Female - Consumer Confidence Index",
        "Edu < Matric": "Education less than matric - Consumer Confidence Index", "Edu Matric/Inter": "Education matric or intermediate - Consumer Confidence Index", "Edu Graduate+": "Education graduate or higher - Consumer Confidence Index",
        "Prof Employees": "Profession - employees - Consumer Confidence Index", "Prof Services": "Profession - business (services) - Consumer Confidence Index", "Prof Industry": "Profession - business (industry) - Consumer Confidence Index",
        "Income <55K": "Below PKR 55,000 - Consumer Confidence Index", "Income 55–100K": "Between PKR 55,000 & PKR 100,000 - Consumer Confidence Index"
    }
    n_months = min(24, len(df))
    dh = df.tail(n_months)
    z_data, y_labels = [], []
    for lbl, cn in hmap_cols.items():
        if cn in dh.columns:
            z_data.append(dh[cn].round(1).tolist())
            y_labels.append(lbl)
    
    fig12 = go.Figure(go.Heatmap(
        z=z_data, x=dh["Month"].dt.strftime("%b %y").tolist(), y=y_labels,
        colorscale=[[0.0,"#7f1d1d"],[0.35,"#b91c1c"],[0.5,"#21262d"],[0.65,"#166534"],[1.0,"#14532d"]],
        zmid=50, zmin=20, zmax=80,
        text=[[f"{v:.1f}" if pd.notna(v) else "" for v in row] for row in z_data],
        texttemplate="%{text}", textfont=dict(size=9, color="rgba(255,255,255,0.7)"),
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}<extra></extra>",
        colorbar=dict(title=dict(text="CCI", font=dict(color="#8b949e")), thickness=14, tickvals=[20,35,50,65,80], tickfont=dict(color="#8b949e", size=10)),
    ))
    
    # Custom layout for Heatmap to ensure no clipping
    fig12.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d1117", 
        height=550, # Increased height
        margin=dict(l=140, r=20, t=40, b=60), # Large left margin for text
        title=dict(text="4.1 Consumer Confidence Index Heatmap (Last 24 Months)", font=dict(size=14, color="#ffffff"), x=0, xanchor="left")
    )
    fig12.update_xaxes(tickfont=dict(size=10), tickangle=-45, linecolor="#30363d")
    fig12.update_yaxes(tickfont=dict(size=11), linecolor="#30363d", autorange="reversed") # Reversed so National is on top
    st.plotly_chart(fig12, use_container_width=True)

    # ── FOOTER ──
    st.markdown("<hr style='border-color:#21262d;margin-top:32px;'>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#8b949e;font-size:12px;padding:10px 0 18px;'>📊 <b style='color:#c9d1d9;'>SBP Consumer Confidence Dashboard</b> · Data: State Bank of Pakistan</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  PAGE ROUTER (Logic to load views/ files)
# ─────────────────────────────────────────────
if selected_page == "Main Overview":
    render_main_dashboard(df)
else:
    safe_name = selected_page.replace(" ", "_")
    file_path = os.path.join("views", f"{safe_name}.py")
    
    if os.path.exists(file_path):
        spec = importlib.util.spec_from_file_location(safe_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "render"):
            module.render(df)
        else:
            st.error(f"Error: {file_path} must have a `render(df)` function to display.")
    else:
        st.markdown(f"""
        <div class='dev-box'>
            <div style="font-size: 50px; margin-bottom: 15px;">🚧</div>
            <h2>{selected_page} Module</h2>
            <p>This section is currently <b>Under Development</b>.<br>
            The dedicated analysis file (<code>views/{safe_name}.py</code>) has not been integrated yet.</p>
            <p style="margin-top:20px;"><i>Please navigate back to the <b>Main Overview</b> using the sidebar.</i></p>
        </div>
        """, unsafe_allow_html=True)