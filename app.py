import warnings
 
import numpy as np
import pandas as pd
import plotly.express as px
import statsmodels.formula.api as smf
import streamlit as st
 
warnings.filterwarnings("ignore")
 
st.set_page_config(page_title="Dampak MBG - Regresi Panel", page_icon="🍽️", layout="wide")
 
LABEL = {
    "stunting_pct": "Prevalensi stunting (%)",
    "kemiskinan_pct": "Tingkat kemiskinan (%)",
    "pengangguran_muda_pct": "Pengangguran muda (%)",
    "mbg_per_kapita_ribu": "Anggaran MBG per kapita (Rp ribu)",
    "pdrb_per_kapita_juta": "PDRB per kapita (Rp juta)",
    "akses_internet_pct": "Akses internet (%)",
    "upah_minimum_juta": "Upah minimum (Rp juta)",
}
DEP_OPTIONS = ["stunting_pct", "kemiskinan_pct", "pengangguran_muda_pct"]
INDEP_OPTIONS = ["mbg_per_kapita_ribu", "pdrb_per_kapita_juta", "akses_internet_pct", "upah_minimum_juta"]
 
 
@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv("data_panel.csv")
 
 
df = load_data()
 
# ------------------------------------------------------------------ header
st.title("🍽️ Dampak Program Makan Bergizi Gratis (MBG) terhadap Indikator Sosial-Ekonomi")
st.caption(
    "Analisis regresi data panel 34 provinsi, 2019-2025. "
    "⚠️ Dataset ini SIMULASI untuk latihan/demo, bukan data resmi BPS/Kemenkes. "
    "Ganti data_panel.csv dengan data asli sebelum dipakai untuk kesimpulan."
)
 
# ------------------------------------------------------------------ sidebar
st.sidebar.header("Pengaturan model")
y_var = st.sidebar.selectbox("Variabel dependen (Y)", DEP_OPTIONS, format_func=LABEL.get)
x_vars = st.sidebar.multiselect(
    "Variabel independen (X)", INDEP_OPTIONS, default=INDEP_OPTIONS, format_func=LABEL.get
)
model_type = st.sidebar.radio(
    "Spesifikasi model",
    ["Pooled OLS", "Fixed Effect (provinsi)", "Two-way Fixed Effect (provinsi + tahun)"],
    index=1,
)
cluster = st.sidebar.checkbox("Standard error cluster per provinsi", value=True)
tahun_min, tahun_max = st.sidebar.slider("Rentang tahun", 2019, 2025, (2019, 2025))
 
data = df[(df["tahun"] >= tahun_min) & (df["tahun"] <= tahun_max)].copy()
 
tab1, tab2, tab3, tab4 = st.tabs(["📈 Tren", "🧮 Regresi", "🗺️ Antar provinsi", "📄 Data"])
 
# ------------------------------------------------------------------ tab 1
with tab1:
    c1, c2, c3 = st.columns(3)
    last = data[data["tahun"] == data["tahun"].max()]
    first = data[data["tahun"] == data["tahun"].min()]
    for col, v in zip((c1, c2, c3), DEP_OPTIONS):
        delta = last[v].mean() - first[v].mean()
        col.metric(LABEL[v], f"{last[v].mean():.2f}", f"{delta:+.2f} sejak {data['tahun'].min()}",
                   delta_color="inverse")
 
    nas = data.groupby("tahun")[DEP_OPTIONS + ["mbg_per_kapita_ribu"]].mean().reset_index()
    fig = px.line(nas, x="tahun", y=y_var, markers=True,
                  title=f"Rata-rata nasional: {LABEL[y_var]}", labels=LABEL)
    if tahun_max >= 2025:
        fig.add_vline(x=2025, line_dash="dash", annotation_text="MBG mulai")
    st.plotly_chart(fig, width="stretch")
 
    pilih = st.multiselect("Bandingkan provinsi", sorted(df["provinsi"].unique()),
                           default=["DKI Jakarta", "Jawa Barat", "Nusa Tenggara Timur", "Papua"])
    if pilih:
        fig2 = px.line(data[data["provinsi"].isin(pilih)], x="tahun", y=y_var,
                       color="provinsi", markers=True, labels=LABEL)
        st.plotly_chart(fig2, width="stretch")
 
# ------------------------------------------------------------------ tab 2
with tab2:
    if not x_vars:
        st.warning("Pilih minimal satu variabel independen.")
    else:
        rhs = " + ".join(x_vars)
        if model_type.startswith("Fixed"):
            rhs += " + C(provinsi)"
        elif model_type.startswith("Two-way"):
            rhs += " + C(provinsi) + C(tahun)"
        formula = f"{y_var} ~ {rhs}"
 
        if cluster:
            groups = pd.factorize(data["provinsi"])[0]
            res = smf.ols(formula, data=data).fit(cov_type="cluster", cov_kwds={"groups": groups})
        else:
            res = smf.ols(formula, data=data).fit()
 
        st.subheader("Hasil estimasi")
        st.code(f"Formula: {formula}", language="text")
 
        coef = pd.DataFrame({
            "Variabel": [LABEL.get(i, i) for i in res.params.index],
            "Koefisien": res.params.values,
            "Std. Error": res.bse.values,
            "t": res.tvalues.values,
            "p-value": res.pvalues.values,
        })
        # sembunyikan dummy FE agar tabel ringkas
        mask = ~coef["Variabel"].str.startswith("C(")
        coef_show = coef[mask].copy()
        coef_show["Sig."] = coef_show["p-value"].apply(
            lambda p: "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else "")
        st.dataframe(coef_show.style.format(
            {"Koefisien": "{:.4f}", "Std. Error": "{:.4f}", "t": "{:.2f}", "p-value": "{:.4f}"}),
            width="stretch", hide_index=True)
 
        m1, m2, m3 = st.columns(3)
        m1.metric("R²", f"{res.rsquared:.3f}")
        m2.metric("Adj. R²", f"{res.rsquared_adj:.3f}")
        m3.metric("N observasi", int(res.nobs))
 
        if "mbg_per_kapita_ribu" in x_vars:
            b = res.params["mbg_per_kapita_ribu"]
            p = res.pvalues["mbg_per_kapita_ribu"]
            arah = "menurunkan" if b < 0 else "menaikkan"
            sig = "signifikan" if p < 0.05 else "tidak signifikan"
            st.info(
                f"**Interpretasi:** setiap tambahan Rp 100 ribu anggaran MBG per kapita "
                f"berasosiasi dengan {arah} {LABEL[y_var].lower()} sebesar **{abs(b)*100:.3f} poin** "
                f"(ceteris paribus; {sig} pada α=5%, p={p:.4f}). "
                f"Ini asosiasi statistik pada data simulasi, bukan bukti kausal."
            )
 
        with st.expander("Ringkasan lengkap statsmodels"):
            st.text(str(res.summary()))
 
        # diagnostik
        st.subheader("Diagnostik residual")
        d = data.assign(fitted=res.fittedvalues, resid=res.resid)
        fig3 = px.scatter(d, x="fitted", y="resid", hover_data=["provinsi", "tahun"],
                          title="Residual vs fitted")
        fig3.add_hline(y=0, line_dash="dash")
        st.plotly_chart(fig3, width="stretch")
 
        # korelasi
        st.subheader("Matriks korelasi")
        corr = data[[y_var] + x_vars].corr().rename(index=LABEL, columns=LABEL)
        st.plotly_chart(px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                                  zmin=-1, zmax=1), width="stretch")
 
# ------------------------------------------------------------------ tab 3
with tab3:
    th = st.selectbox("Tahun", sorted(data["tahun"].unique(), reverse=True))
    sub = data[data["tahun"] == th].sort_values(y_var, ascending=False)
    st.plotly_chart(px.bar(sub, x="provinsi", y=y_var, color=y_var,
                           color_continuous_scale="Reds", labels=LABEL,
                           title=f"{LABEL[y_var]} per provinsi, {th}"),
                    width="stretch")
    st.plotly_chart(px.scatter(sub, x="mbg_per_kapita_ribu", y=y_var, size="pdrb_per_kapita_juta",
                               hover_name="provinsi", trendline="ols", labels=LABEL,
                               title=f"MBG vs {LABEL[y_var]} ({th})"),
                    width="stretch")
 
# ------------------------------------------------------------------ tab 4
with tab4:
    st.dataframe(data, width="stretch", hide_index=True)
    st.download_button("Unduh CSV", data.to_csv(index=False).encode(), "data_panel_filtered.csv", "text/csv")
 
