import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def render(df):
    st.markdown("<div style='font-size:24px; font-weight:700; color:#ffffff; margin-bottom:10px;'>📊 Overall Condition (CCI)</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#8b949e; margin-bottom:30px;'>Comprehensive breakdown of the Consumer Confidence Index across all demographics.</div>", unsafe_allow_html=True)

    if df.empty:
        st.warning("No data available for the selected date range.")
        return

    # Helper for consistent, non-overlapping layouts
    def apply_layout(fig, title):
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d1117",
            font=dict(family="Inter,sans-serif", color="#c9d1d9", size=12),
            margin=dict(l=50, r=30, t=60, b=80), # Large margins to prevent overlap
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
            xaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
            yaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
            title=dict(text=title, font=dict(size=18, color="#ffffff"), x=0.01, y=0.95),
            height=450
        )
        fig.add_hline(y=50, line_dash="dash", line_color="#404650", line_width=1.5)

    base_idx = "Consumer Confidence Index"
    
    # 1. National Trend
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df["Month"], y=df[base_idx].round(2), mode='lines+markers', name="National CCI", line=dict(color="#388bfd", width=3)))
    apply_layout(fig1, "1. National Overall Condition Trend")
    st.plotly_chart(fig1, use_container_width=True)

    # 2. 6-Month Rolling Average
    fig2 = go.Figure()
    rolling = df[base_idx].rolling(6, min_periods=1).mean()
    fig2.add_trace(go.Scatter(x=df["Month"], y=df[base_idx].round(2), mode='lines', name="Raw Data", line=dict(color="rgba(56,139,253,0.3)", width=1)))
    fig2.add_trace(go.Scatter(x=df["Month"], y=rolling.round(2), mode='lines', name="6-Month Moving Average", line=dict(color="#bc8cff", width=3)))
    apply_layout(fig2, "2. Volatility Smoothing: 6-Month Rolling Average")
    st.plotly_chart(fig2, use_container_width=True)

    # 3. Annual Averages
    df['Year'] = df['Month'].dt.year
    yearly = df.groupby('Year')[base_idx].mean().reset_index()
    fig3 = go.Figure(go.Bar(x=yearly['Year'].astype(str), y=yearly[base_idx].round(2), marker_color=["#3fb950" if v>=50 else "#f85149" for v in yearly[base_idx]], text=yearly[base_idx].round(1), textposition='auto'))
    apply_layout(fig3, "3. Yearly Average Overall Condition")
    st.plotly_chart(fig3, use_container_width=True)

    # 4. Rural vs Urban
    fig4 = go.Figure()
    if "Rural - " + base_idx in df.columns: fig4.add_trace(go.Scatter(x=df["Month"], y=df["Rural - " + base_idx].round(2), name="Rural", line=dict(color="#388bfd", width=2)))
    if "Urban - " + base_idx in df.columns: fig4.add_trace(go.Scatter(x=df["Month"], y=df["Urban - " + base_idx].round(2), name="Urban", line=dict(color="#d29922", width=2)))
    apply_layout(fig4, "4. Geographic Divide: Rural vs Urban")
    st.plotly_chart(fig4, use_container_width=True)

    # 5. Gender
    fig5 = go.Figure()
    if "Male - " + base_idx in df.columns: fig5.add_trace(go.Scatter(x=df["Month"], y=df["Male - " + base_idx].round(2), name="Male", line=dict(color="#79c0ff", width=2)))
    if "Female - " + base_idx in df.columns: fig5.add_trace(go.Scatter(x=df["Month"], y=df["Female - " + base_idx].round(2), name="Female", line=dict(color="#bc8cff", width=2)))
    apply_layout(fig5, "5. Gender Sentiment Comparison")
    st.plotly_chart(fig5, use_container_width=True)

    # 6. Education Levels
    fig6 = go.Figure()
    for col, name, color in [("Education less than matric - ", "< Matric", "#3fb950"), ("Education matric or intermediate - ", "Matric/Inter", "#d29922"), ("Education graduate or higher - ", "Graduate+", "#388bfd")]:
        full_col = col + base_idx
        if full_col in df.columns: fig6.add_trace(go.Scatter(x=df["Month"], y=df[full_col].round(2), name=name, line=dict(color=color, width=2)))
    apply_layout(fig6, "6. Overall Condition by Education Level")
    st.plotly_chart(fig6, use_container_width=True)

    # 7. Profession Breakdowns
    fig7 = go.Figure()
    for col, name in [("Profession - employees - ", "Employees"), ("Profession - business (services) - ", "Business (Services)"), ("Profession - business (industry) - ", "Business (Industry)"), ("Profession - business (agriculture) - ", "Business (Agriculture)")]:
        full_col = col + base_idx
        if full_col in df.columns: fig7.add_trace(go.Scatter(x=df["Month"], y=df[full_col].round(2), name=name, mode='lines'))
    apply_layout(fig7, "7. Profession Cohort Trends")
    st.plotly_chart(fig7, use_container_width=True)

    # 8. Income Brackets
    fig8 = go.Figure()
    for col, name in [("Below PKR 55,000 - ", "Below 55K"), ("Between PKR 55,000 & PKR 100,000 - ", "55K-100K"), ("Between PKR 100,000 & PKR 200,000 - ", "100K-200K")]:
        full_col = col + base_idx
        if full_col in df.columns: fig8.add_trace(go.Scatter(x=df["Month"], y=df[full_col].round(2), name=name, fill='tozeroy'))
    apply_layout(fig8, "8. Income Brackets (Filled Area)")
    st.plotly_chart(fig8, use_container_width=True)

    # 9. High Income (Sparse Data)
    fig9 = go.Figure()
    c200 = "PKR 200,000 and Above - " + base_idx
    if c200 in df.columns:
        d200 = df.dropna(subset=[c200])
        fig9.add_trace(go.Scatter(x=d200["Month"], y=d200[c200].round(2), mode='markers+lines', name="> PKR 200K", marker=dict(size=10, symbol='diamond')))
    apply_layout(fig9, "9. High Income Bracket (> PKR 200K) Data Points")
    st.plotly_chart(fig9, use_container_width=True)

    # 10. Box Plot Distributions
    fig10 = go.Figure(go.Box(x=df['Year'].astype(str), y=df[base_idx], boxpoints='all', marker_color="#388bfd", name="Monthly variance"))
    apply_layout(fig10, "10. Monthly Volatility Distribution per Year")
    st.plotly_chart(fig10, use_container_width=True)

    # 11. Latest Snapshot Ranking
    lat = df.iloc[-1]
    lbls, vals = [], []
    for c in df.columns:
        if base_idx in c and c != base_idx and pd.notna(lat.get(c)):
            lbls.append(c.replace(" - " + base_idx, ""))
            vals.append(lat[c])
    
    if vals:
        s = sorted(zip(vals, lbls))
        s_vals, s_lbls = zip(*s)
        fig11 = go.Figure(go.Bar(x=s_vals, y=s_lbls, orientation='h', marker_color=["#3fb950" if v>=50 else "#f85149" for v in s_vals], text=[f"{v:.1f}" for v in s_vals], textposition='inside'))
        apply_layout(fig11, f"11. Segment Ranking Snapshot ({df['Month'].iloc[-1].strftime('%b %Y')})")
        fig11.update_layout(margin=dict(l=150, r=20, t=60, b=40)) # Extra left margin for long labels
        st.plotly_chart(fig11, use_container_width=True)