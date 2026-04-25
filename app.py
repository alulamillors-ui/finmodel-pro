import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="FinModel Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0f1117; }
    [data-testid="stSidebar"] * { color: #e0e0e0 !important; }
    .metric-card {
        background: #1e2130;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid;
        margin-bottom: 8px;
    }
    .metric-card.green { border-color: #1D9E75; }
    .metric-card.blue  { border-color: #378ADD; }
    .metric-card.amber { border-color: #EF9F27; }
    .metric-card.red   { border-color: #D85A30; }
    .metric-label { font-size: 12px; color: #888; margin-bottom: 4px; }
    .metric-value { font-size: 24px; font-weight: 600; color: #fff; }
    .metric-sub   { font-size: 11px; color: #666; margin-top: 2px; }
    .section-header {
        font-size: 13px; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.08em;
        color: #888; margin: 1.5rem 0 0.5rem;
    }
    .stTabs [data-baseweb="tab"] { font-weight: 500; }
    div[data-testid="stMetricValue"] > div { font-size: 22px !important; }
</style>
""", unsafe_allow_html=True)


def fmt_ar(n):
    if abs(n) >= 1e9:
        return f"{n/1e9:.2f} Mrd Ar"
    elif abs(n) >= 1e6:
        return f"{n/1e6:.2f} M Ar"
    elif abs(n) >= 1e3:
        return f"{n/1e3:.1f} k Ar"
    return f"{n:.0f} Ar"


def metric_card(label, value, sub="", color="green"):
    st.markdown(f"""
    <div class="metric-card {color}">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")

    module = st.radio("Module", ["📊 Budget & Prévisions", "💰 Analyse DCF"], label_visibility="collapsed")

    st.markdown("---")

    if "Budget" in module:
        st.markdown("### Revenus & Coûts")
        rev0       = st.number_input("CA initial (Ar)",       value=500_000_000, step=10_000_000, format="%d")
        growth_pct = st.number_input("Croissance CA (%/an)",  value=12.0, step=0.5)
        var_pct    = st.number_input("Coûts variables (% CA)", value=35.0, step=1.0, min_value=0.0, max_value=99.0)
        fixed_cost = st.number_input("Charges fixes (Ar)",    value=150_000_000, step=5_000_000, format="%d")
        tax_pct    = st.number_input("Taux d'impôt (%)",      value=20.0, step=1.0)
        years_b    = st.slider("Années de projection",        min_value=2, max_value=10, value=5)

        st.markdown("### Amortissements")
        invest     = st.number_input("Investissement initial (Ar)", value=200_000_000, step=10_000_000, format="%d")
        invest_life = st.slider("Durée d'amortissement (ans)",      min_value=2, max_value=20, value=10)
        amort_method = st.selectbox("Méthode", ["Linéaire", "Dégressif (double taux)"])
        add_invest_yr = st.number_input("Investissement annuel supp. (Ar)", value=20_000_000, step=5_000_000, format="%d")

        st.markdown("### Scénario")
        scenario = st.selectbox("Scénario", ["Base", "Optimiste (+30%)", "Pessimiste (−25%)"])

    else:
        st.markdown("### Flux de trésorerie")
        fcf1       = st.number_input("FCF Année 1 (Ar)",          value=80_000_000, step=5_000_000, format="%d")
        fcf_growth = st.number_input("Croissance FCF (%/an)",      value=10.0, step=0.5)
        wacc       = st.number_input("WACC (%)",                   value=12.0, step=0.5)
        tgr        = st.number_input("Taux croissance terminal (%)", value=3.0, step=0.5)
        years_d    = st.slider("Années de projection",             min_value=3, max_value=10, value=5)
        debt       = st.number_input("Dette nette (Ar)",           value=50_000_000, step=5_000_000, format="%d")

        st.markdown("### Amortissements (EBITDA → FCF)")
        invest_d    = st.number_input("Investissement initial (Ar)", value=200_000_000, step=10_000_000, format="%d")
        invest_life_d = st.slider("Durée d'amortissement (ans)",     min_value=2, max_value=20, value=10)
        amort_method_d = st.selectbox("Méthode", ["Linéaire", "Dégressif (double taux)"])
        capex_pct   = st.number_input("Capex annuel (% CA)",         value=5.0, step=0.5)
        nwc_pct     = st.number_input("Variation BFR (% croissance CA)", value=10.0, step=1.0)
        rev0_d      = st.number_input("CA Année 1 (Ar, pour BFR/Capex)", value=500_000_000, step=10_000_000, format="%d")
        growth_pct_d = st.number_input("Croissance CA (%/an)",        value=12.0, step=0.5)


# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("# 📊 FinModel Pro")
st.markdown("Modélisation financière — Prévisions budgétaires · Amortissements · DCF")
st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# MODULE BUDGET
# ══════════════════════════════════════════════════════════════════════════════
if "Budget" in module:

    mult = {"Base": 1.0, "Optimiste (+30%)": 1.30, "Pessimiste (−25%)": 0.75}[scenario]

    def amort_schedule(cost, life, method, n_years):
        """Retourne la liste des dotations annuelles."""
        if method == "Linéaire":
            annual = cost / life
            return [annual if y < life else 0 for y in range(n_years)]
        else:  # Dégressif double taux
            rate = 2 / life
            book = cost
            schedule = []
            for y in range(n_years):
                if y >= life:
                    schedule.append(0)
                else:
                    da = book * rate
                    book -= da
                    schedule.append(da)
            return schedule

    rows = []
    amort_init = amort_schedule(invest, invest_life, amort_method, years_b)

    for y in range(1, years_b + 1):
        rev = rev0 * mult * (1 + growth_pct/100) ** y
        var_cost = rev * (var_pct / 100)
        total_cost = fixed_cost + var_cost

        # Amortissement initial + supplémentaire (on suppose add_invest_yr dès an 1)
        da_init = amort_init[y-1]
        da_add  = amort_schedule(add_invest_yr * y, invest_life, amort_method, years_b)[y-1]
        da_total = da_init + da_add

        ebitda = rev - total_cost
        ebit   = ebitda - da_total
        ebt    = ebit
        tax    = max(0, ebt * (tax_pct / 100))
        net    = ebt - tax
        margin = net / rev * 100

        rows.append({
            "Année": f"An {y}",
            "Chiffre d'affaires": rev,
            "Coûts variables": var_cost,
            "Charges fixes": fixed_cost,
            "EBITDA": ebitda,
            "Amortissements": da_total,
            "EBIT": ebit,
            "Impôt": tax,
            "Résultat net": net,
            "Marge nette (%)": margin,
        })

    df = pd.DataFrame(rows)

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("CA final", fmt_ar(df["Chiffre d'affaires"].iloc[-1]),
                    f"Scénario : {scenario}", "green")
    with col2:
        rn = df["Résultat net"].iloc[-1]
        metric_card("Résultat net final", fmt_ar(rn),
                    f"{df['Marge nette (%)'].iloc[-1]:.1f}% marge", "blue" if rn >= 0 else "red")
    with col3:
        metric_card("EBITDA final", fmt_ar(df["EBITDA"].iloc[-1]),
                    f"An {years_b}", "amber")
    with col4:
        total_da = df["Amortissements"].sum()
        metric_card("Total amortissements", fmt_ar(total_da),
                    f"Méthode : {amort_method}", "green")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📈 Graphiques", "📋 Tableau détaillé", "📉 Amortissements"])

    with tab1:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        years_labels = df["Année"].tolist()

        fig.add_trace(go.Bar(name="Chiffre d'affaires", x=years_labels,
                             y=df["Chiffre d'affaires"], marker_color="#1D9E75", opacity=0.85), secondary_y=False)
        fig.add_trace(go.Bar(name="EBITDA", x=years_labels,
                             y=df["EBITDA"], marker_color="#EF9F27", opacity=0.85), secondary_y=False)
        fig.add_trace(go.Bar(name="Amortissements", x=years_labels,
                             y=df["Amortissements"], marker_color="#888", opacity=0.7), secondary_y=False)
        fig.add_trace(go.Scatter(name="Résultat net", x=years_labels,
                                 y=df["Résultat net"], mode="lines+markers",
                                 line=dict(color="#378ADD", width=2.5, dash="dot"),
                                 marker=dict(size=7)), secondary_y=False)
        fig.add_trace(go.Scatter(name="Marge nette (%)", x=years_labels,
                                 y=df["Marge nette (%)"], mode="lines+markers",
                                 line=dict(color="#D85A30", width=2),
                                 marker=dict(size=6)), secondary_y=True)

        fig.update_layout(
            barmode="group", template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.08),
            height=420, margin=dict(t=40, b=20, l=0, r=0),
            yaxis_title="Montant (Ar)", yaxis2_title="Marge nette (%)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        display_df = df.copy()
        for col in ["Chiffre d'affaires","Coûts variables","Charges fixes","EBITDA",
                    "Amortissements","EBIT","Impôt","Résultat net"]:
            display_df[col] = display_df[col].apply(fmt_ar)
        display_df["Marge nette (%)"] = display_df["Marge nette (%)"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_df.set_index("Année"), use_container_width=True)
        csv = df.to_csv(index=False).encode()
        st.download_button("⬇️ Télécharger CSV", csv, "budget_previsionnel.csv", "text/csv")

    with tab3:
        da_df = pd.DataFrame({
            "Année": [f"An {y}" for y in range(1, years_b+1)],
            "Amort. initial (Ar)": [fmt_ar(v) for v in amort_init[:years_b]],
            "Amort. supplémentaire (Ar)": [fmt_ar(da_total - da_init)
                                           for da_total, da_init in zip(df["Amortissements"], amort_init[:years_b])],
            "Total dotation (Ar)": [fmt_ar(v) for v in df["Amortissements"]],
        })

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Amort. initial", x=da_df["Année"],
                              y=df["Amortissements"] - [d - ai for d, ai in zip(df["Amortissements"], amort_init[:years_b])],
                              marker_color="#7F77DD"))
        fig2.add_trace(go.Bar(name="Amort. supplémentaire", x=da_df["Année"],
                              y=[d - ai for d, ai in zip(df["Amortissements"], amort_init[:years_b])],
                              marker_color="#AFA9EC"))
        fig2.update_layout(
            barmode="stack", template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=300, margin=dict(t=20, b=20, l=0, r=0),
            yaxis_title="Dotation (Ar)"
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(da_df.set_index("Année"), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# MODULE DCF
# ══════════════════════════════════════════════════════════════════════════════
else:
    w = wacc / 100
    g = tgr  / 100
    fg = fcf_growth / 100
    gca = growth_pct_d / 100

    def amort_dcf(cost, life, method, n):
        if method == "Linéaire":
            return [cost / life if y < life else 0 for y in range(n)]
        else:
            rate, book, out = 2/life, cost, []
            for y in range(n):
                if y >= life: out.append(0)
                else:
                    da = book * rate; book -= da; out.append(da)
            return out

    amort_vals = amort_dcf(invest_d, invest_life_d, amort_method_d, years_d)

    rows_d = []
    for y in range(1, years_d + 1):
        rev_y  = rev0_d * (1 + gca) ** y
        capex  = rev_y * (capex_pct / 100)
        delta_nwc = rev_y * gca * (nwc_pct / 100)
        da     = amort_vals[y-1]
        fcf_raw = fcf1 * (1 + fg) ** (y-1)
        # FCF ajusté = FCF brut + DA - Capex - ΔBFR
        fcf_adj = fcf_raw + da - capex - delta_nwc
        pv = fcf_adj / (1 + w) ** y
        rows_d.append({
            "Année": f"An {y}",
            "FCF brut": fcf_raw,
            "Amortissements": da,
            "Capex": capex,
            "ΔBFR": delta_nwc,
            "FCF ajusté": fcf_adj,
            "Facteur actualisation": 1/(1+w)**y,
            "PV du FCF": pv,
        })

    df_d = pd.DataFrame(rows_d)
    sum_pv = df_d["PV du FCF"].sum()
    last_fcf_adj = df_d["FCF ajusté"].iloc[-1]
    tv = last_fcf_adj * (1 + g) / (w - g)
    pv_tv = tv / (1 + w) ** years_d
    ev = sum_pv + pv_tv
    equity = ev - debt
    tv_pct = pv_tv / ev * 100

    # Analyse de sensibilité WACC × TGR
    waccs = [w - 0.02, w - 0.01, w, w + 0.01, w + 0.02]
    tgrs  = [g - 0.01, g, g + 0.01, g + 0.02]
    sens_data = []
    for ww in waccs:
        row_s = []
        for tt in tgrs:
            if ww <= tt:
                row_s.append(None)
                continue
            tv_s = last_fcf_adj * (1 + tt) / (ww - tt)
            pv_tv_s = tv_s / (1 + ww) ** years_d
            sum_pv_s = sum(df_d["FCF ajusté"].iloc[y-1] / (1+ww)**y for y in range(1, years_d+1))
            ev_s = sum_pv_s + pv_tv_s
            row_s.append(round(ev_s / 1e6, 1))
        sens_data.append(row_s)

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Valeur d'entreprise (EV)", fmt_ar(ev), f"WACC {wacc:.1f}%", "green")
    with col2:
        metric_card("Valeur capitaux propres", fmt_ar(equity), "EV − Dette nette", "blue")
    with col3:
        metric_card("Valeur terminale (PV)", fmt_ar(pv_tv), f"{tv_pct:.0f}% de la valeur totale", "amber")
    with col4:
        metric_card("Σ PV des FCF ajustés", fmt_ar(sum_pv), f"Sur {years_d} ans", "green")

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Graphiques", "📋 Tableau FCF", "🔥 Sensibilité WACC×TGR", "📉 Amortissements"])

    with tab1:
        fig = make_subplots(rows=1, cols=2,
                            subplot_titles=("FCF brut vs FCF ajusté vs PV", "Décomposition de la valeur"))

        labels = df_d["Année"].tolist()
        fig.add_trace(go.Bar(name="FCF brut",    x=labels, y=df_d["FCF brut"],    marker_color="#7F77DD"), row=1, col=1)
        fig.add_trace(go.Bar(name="FCF ajusté",  x=labels, y=df_d["FCF ajusté"],  marker_color="#1D9E75"), row=1, col=1)
        fig.add_trace(go.Scatter(name="PV FCF",  x=labels, y=df_d["PV du FCF"],
                                 mode="lines+markers", line=dict(color="#378ADD", width=2.5, dash="dot"),
                                 marker=dict(size=7)), row=1, col=1)

        fig.add_trace(go.Pie(
            labels=["PV FCF (phase explicite)", "Valeur terminale actualisée"],
            values=[sum_pv, pv_tv],
            hole=0.55,
            marker_colors=["#1D9E75", "#EF9F27"],
            textinfo="label+percent"
        ), row=1, col=2)

        fig.update_layout(
            template="plotly_dark", barmode="group",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=400, margin=dict(t=50, b=20, l=0, r=0),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        df_disp = df_d.copy()
        for col in ["FCF brut","Amortissements","Capex","ΔBFR","FCF ajusté","PV du FCF"]:
            df_disp[col] = df_disp[col].apply(fmt_ar)
        df_disp["Facteur actualisation"] = df_disp["Facteur actualisation"].apply(lambda x: f"{x:.4f}")
        st.dataframe(df_disp.set_index("Année"), use_container_width=True)
        csv_d = df_d.to_csv(index=False).encode()
        st.download_button("⬇️ Télécharger CSV", csv_d, "analyse_dcf.csv", "text/csv")

    with tab3:
        st.markdown("**Valeur d'entreprise (M Ar) selon WACC et taux de croissance terminal**")
        wacc_labels = [f"WACC {ww*100:.1f}%" for ww in waccs]
        tgr_labels  = [f"TGR {tt*100:.1f}%" for tt in tgrs]
        sens_arr = np.array([[v if v is not None else np.nan for v in r] for r in sens_data])

        fig_h = go.Figure(go.Heatmap(
            z=sens_arr, x=tgr_labels, y=wacc_labels,
            colorscale="RdYlGn", text=sens_arr,
            texttemplate="%{text:.0f} M",
            hoverongaps=False,
        ))
        # Highlight current cell
        cur_ww_idx = 2
        cur_tt_idx = 1
        fig_h.add_shape(type="rect",
            x0=cur_tt_idx-0.5, x1=cur_tt_idx+0.5,
            y0=cur_ww_idx-0.5, y1=cur_ww_idx+0.5,
            line=dict(color="white", width=2)
        )
        fig_h.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=280, margin=dict(t=20, b=20, l=0, r=0),
            xaxis_title="Taux de croissance terminal", yaxis_title="WACC"
        )
        st.plotly_chart(fig_h, use_container_width=True)
        st.caption("Le cadre blanc indique le scénario central. En M Ar.")

    with tab4:
        fig_da = go.Figure()
        fig_da.add_trace(go.Bar(name="Amortissements", x=df_d["Année"],
                                y=df_d["Amortissements"], marker_color="#7F77DD"))
        fig_da.add_trace(go.Bar(name="Capex", x=df_d["Année"],
                                y=df_d["Capex"], marker_color="#D85A30"))
        fig_da.update_layout(
            barmode="group", template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=280, margin=dict(t=20, b=20, l=0, r=0),
            yaxis_title="Montant (Ar)"
        )
        st.plotly_chart(fig_da, use_container_width=True)

        da_disp = df_d[["Année","Amortissements","Capex"]].copy()
        da_disp["Amortissements"] = da_disp["Amortissements"].apply(fmt_ar)
        da_disp["Capex"] = da_disp["Capex"].apply(fmt_ar)
        da_disp["DA − Capex"] = (df_d["Amortissements"] - df_d["Capex"]).apply(fmt_ar)
        st.dataframe(da_disp.set_index("Année"), use_container_width=True)

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#555;font-size:12px;'>FinModel Pro — Prototype IA · Modélisation financière</p>",
    unsafe_allow_html=True
)
