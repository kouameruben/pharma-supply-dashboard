"""
app.py — Pharma Supply Chain Dashboard
Author: Kouamé Ruben
Stack: Streamlit + Plotly
Launch: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Pharma Supply Chain Dashboard",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load Data ──
@st.cache_data
def load_data():
    base = Path("data/processed")
    data = {}
    for f in ["pharma_enriched", "district_monthly", "product_monthly",
              "global_kpis", "category_kpis", "forecast_results", "alerts"]:
        path = base / f"{f}.parquet"
        if path.exists():
            data[f] = pd.read_parquet(path)
    return data

data = load_data()

if not data:
    st.error("⚠️ No data found. Run the pipeline first: `python python/pipeline.py`")
    st.stop()

df = data.get("pharma_enriched", pd.DataFrame())
kpis = data.get("global_kpis", pd.DataFrame())
forecasts = data.get("forecast_results", pd.DataFrame())
alerts = data.get("alerts", pd.DataFrame())

if len(df) > 0:
    df["month"] = pd.to_datetime(df["month"])

# ── Sidebar Filters ──
st.sidebar.image("https://img.shields.io/badge/💊_Pharma_Supply-Chain_Analytics-blue?style=for-the-badge", width=280)
st.sidebar.markdown("---")

if len(df) > 0:
    selected_districts = st.sidebar.multiselect(
        "🏥 Districts", df["name"].unique().tolist(),
        default=df["name"].unique().tolist()[:5]
    )
    selected_categories = st.sidebar.multiselect(
        "💊 Catégories", df["category"].unique().tolist(),
        default=df["category"].unique().tolist()
    )
    date_range = st.sidebar.date_input(
        "📅 Période",
        value=(df["month"].min(), df["month"].max()),
        min_value=df["month"].min(),
        max_value=df["month"].max()
    )
    
    # Filter
    mask = (
        df["name"].isin(selected_districts) &
        df["category"].isin(selected_categories) &
        (df["month"] >= pd.Timestamp(date_range[0])) &
        (df["month"] <= pd.Timestamp(date_range[1] if len(date_range) > 1 else date_range[0]))
    )
    filtered = df[mask]
else:
    filtered = df

# ══════════════════════════════════════════
# TAB NAVIGATION
# ══════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["📊 Overview", "🤖 Forecast", "🚨 Alerts"])

# ── TAB 1: OVERVIEW ──
with tab1:
    st.markdown("## 📊 Supply Chain Overview")
    
    if len(kpis) > 0:
        k = kpis.iloc[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📦 Consommation", f"{k.get('total_consumption', 0):,.0f}", 
                   f"{k.get('consumption_mom_change', 0):+.1%} MoM")
        c2.metric("💰 Valeur (FCFA)", f"{k.get('total_value_fcfa', 0)/1e6:,.1f}M")
        c3.metric("✅ Fill Rate", f"{k.get('overall_fill_rate', 0):.1%}")
        c4.metric("🔴 Stockout Rate", f"{k.get('overall_stockout_rate', 0):.1%}",
                   f"{k.get('stockout_mom_change', 0):+.1%}", delta_color="inverse")
        c5.metric("⚠️ Ruptures critiques", f"{k.get('critical_stockouts', 0)}")
    
    st.markdown("---")
    
    if len(filtered) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Évolution de la consommation")
            monthly_trend = filtered.groupby("month").agg(
                consumption=("consumption", "sum"),
                stockout_rate=("stockout", "mean")
            ).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=monthly_trend["month"], y=monthly_trend["consumption"],
                                      mode="lines+markers", name="Consommation",
                                      line=dict(color="#0EA5E9", width=2)))
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20),
                              template="plotly_white",
                              yaxis_title="Unités", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🏥 Stockout par district")
            dist_stockout = filtered.groupby("name")["stockout"].mean().reset_index()
            dist_stockout.columns = ["District", "Taux de rupture"]
            dist_stockout = dist_stockout.sort_values("Taux de rupture", ascending=True)
            
            fig2 = px.bar(dist_stockout, x="Taux de rupture", y="District", orientation="h",
                          color="Taux de rupture", color_continuous_scale=["#10B981", "#F59E0B", "#EF4444"])
            fig2.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20),
                               template="plotly_white", showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Category breakdown
        st.markdown("### 💊 Répartition par catégorie")
        cat_data = filtered.groupby("category").agg(
            total=("consumption", "sum"),
            value=("consumption_value", "sum"),
            stockout_rate=("stockout", "mean")
        ).reset_index().sort_values("value", ascending=False)
        
        col3, col4 = st.columns(2)
        with col3:
            fig3 = px.pie(cat_data, values="value", names="category",
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig3.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig3, use_container_width=True)
        
        with col4:
            fig4 = px.bar(cat_data, x="category", y="stockout_rate",
                          color="stockout_rate", color_continuous_scale=["#10B981", "#EF4444"])
            fig4.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20),
                               template="plotly_white", yaxis_title="Taux de rupture",
                               xaxis_title="", showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)

# ── TAB 2: FORECAST ──
with tab2:
    st.markdown("## 🤖 Prévision de la demande (ML)")
    
    if len(forecasts) > 0:
        avg_mape = forecasts["mape_model"].mean()
        avg_naive = forecasts["mape_naive"].mean()
        improvement = 1 - avg_mape / avg_naive
        
        c1, c2, c3 = st.columns(3)
        c1.metric("🎯 MAPE Modèle", f"{avg_mape:.1%}")
        c2.metric("📊 MAPE Naïf", f"{avg_naive:.1%}")
        c3.metric("📈 Amélioration", f"{improvement:.0%}")
        
        st.markdown("---")
        st.markdown("### Accuracy par produit")
        
        fig_fc = go.Figure()
        fig_fc.add_trace(go.Bar(x=forecasts["product_name"], y=forecasts["mape_naive"],
                                 name="Baseline (naïf)", marker_color="#94A3B8"))
        fig_fc.add_trace(go.Bar(x=forecasts["product_name"], y=forecasts["mape_model"],
                                 name="ML Model", marker_color="#0EA5E9"))
        fig_fc.update_layout(barmode="group", height=400, template="plotly_white",
                              yaxis_title="MAPE", xaxis_title="",
                              margin=dict(l=20, r=20, t=30, b=80))
        st.plotly_chart(fig_fc, use_container_width=True)
        
        st.markdown("### Détails des prévisions")
        st.dataframe(forecasts.style.format({
            "mape_model": "{:.1%}", "mape_naive": "{:.1%}", "improvement": "{:.0%}",
            "next_month_forecast": "{:,.0f}"
        }), use_container_width=True)
    else:
        st.info("Exécutez le pipeline pour générer les prévisions.")

# ── TAB 3: ALERTS ──
with tab3:
    st.markdown("## 🚨 Alertes & Recommandations")
    
    if len(alerts) > 0:
        high = len(alerts[alerts["risk_level"] == "High"])
        medium = len(alerts[alerts["risk_level"] == "Medium"])
        vital_high = len(alerts[(alerts["risk_level"] == "High") & (alerts["criticality"] == "Vital")])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Risque élevé", high)
        c2.metric("🟡 Risque moyen", medium)
        c3.metric("⚠️ Médicaments vitaux à risque", vital_high)
        
        st.markdown("---")
        
        # Filter by risk level
        risk_filter = st.selectbox("Filtrer par niveau de risque",
                                    ["Tous", "High", "Medium"])
        
        display = alerts if risk_filter == "Tous" else alerts[alerts["risk_level"] == risk_filter]
        
        # Color-coded table
        def color_risk(val):
            if val == "High": return "background-color: #FEE2E2; color: #991B1B"
            if val == "Medium": return "background-color: #FEF3C7; color: #92400E"
            return ""
        
        st.dataframe(
            display.style.applymap(color_risk, subset=["risk_level"]),
            use_container_width=True, height=500
        )
        
        # Top critical alerts
        st.markdown("### ⚠️ Actions immédiates recommandées")
        critical = alerts[(alerts["risk_level"] == "High") & (alerts["criticality"] == "Vital")].head(10)
        for _, row in critical.iterrows():
            st.warning(
                f"**{row['product_name']}** — {row['district_name']} | "
                f"Stock: {row['current_stock']:,.0f} | "
                f"Jours restants: {row['days_of_stock']:.0f} | "
                f"Commander: **{row['recommended_order']:,.0f} unités**"
            )
    else:
        st.info("Exécutez le pipeline pour générer les alertes.")

# ── Footer ──
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 12px;'>"
    "Pharma Supply Chain Dashboard — Kouamé Ruben | "
    "<a href='https://github.com/kouameruben'>GitHub</a> | "
    "<a href='https://linkedin.com/in/kouameruben'>LinkedIn</a>"
    "</div>", unsafe_allow_html=True
)
