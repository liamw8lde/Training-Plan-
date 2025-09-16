
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tennis Winter-Training", layout="wide")

st.title("🎾 Trainingsplan – Viewer")

@st.cache_data
def load_data(file):
    if hasattr(file, "read"):
        # Uploaded file (BytesIO)
        return pd.read_csv(file, dtype=str, sep=",").pipe(_postprocess)
    else:
        # Path-like
        return pd.read_csv(file, dtype=str, sep=",").pipe(_postprocess)

def _postprocess(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure expected columns
    expected = ["Datum", "Tag", "Slot", "Typ", "Spieler"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"Fehlende Spalten: {', '.join(missing)}. Erwartet: {expected}")
    # Strip whitespace
    for c in expected:
        df[c] = df[c].astype(str).str.strip()
    # Parse dates (dayfirst safe)
    df["Datum_dt"] = pd.to_datetime(df["Datum"], errors="coerce", dayfirst=True, utc=False)
    # ISO week/year
    iso = df["Datum_dt"].dt.isocalendar()
    df["Jahr"] = iso["year"]
    df["Woche"] = iso["week"]
    # Extract start time from Slot like 'D20:00-120 PLA'
    t1 = df["Slot"].str.extract(r"[ED](\d{2}):(\d{2})")
    time = t1[0].fillna("00") + ":" + t1[1].fillna("00")
    df["Startzeit"] = pd.to_datetime(time, format="%H:%M", errors="coerce").dt.time
    # Players list
    df["Spieler_list"] = (
        df["Spieler"]
        .astype(str)
        .str.split(",")
        .apply(lambda xs: [x.strip() for x in xs if str(x).strip() != ""])
    )
    # Exploded for player filtering
    df_exp = df.explode("Spieler_list").rename(columns={"Spieler_list": "Spieler_Name"})
    return df, df_exp

# Data source: uploader OR default file path
default_path = "/mnt/data/Datum,Tag,Slot,Typ,Spieler.csv"
st.sidebar.header("📄 Datenquelle")
uploaded = st.sidebar.file_uploader("CSV hochladen (Spalten: Datum, Tag, Slot, Typ, Spieler)", type=["csv"])
use_default = st.sidebar.checkbox("Beispieldatei verwenden", value=not bool(uploaded))

try:
    if uploaded is not None and not use_default:
        df, df_exp = load_data(uploaded)
        source_label = "Hochgeladene Datei"
    else:
        df, df_exp = load_data(default_path)
        source_label = "Standarddatei"
except Exception as e:
    st.error(f"Fehler beim Laden der Daten: {e}")
    st.stop()

st.sidebar.success(f"Quelle: {source_label}")

tab1, tab2 = st.tabs(["📆 Wochenübersicht", "🧍 Spieler-Matches"])

with tab1:
    st.subheader("📆 Wochenübersicht")
    weeks = (
        df.dropna(subset=["Datum_dt"])
          .assign(WeekKey=lambda x: x["Jahr"].astype(str) + "-W" + x["Woche"].astype(str).str.zfill(2))
          .sort_values(["Jahr","Woche","Datum_dt"])
    )
    available_weeks = weeks["WeekKey"].unique().tolist()
    if not available_weeks:
        st.warning("Keine gültigen Wochen gefunden.")
    else:
        selected_week = st.selectbox("Woche wählen (ISO)", options=available_weeks, index=0)
        sel_year = int(selected_week.split("-W")[0])
        sel_week = int(selected_week.split("-W")[1])
        wk = df[(df["Jahr"] == sel_year) & (df["Woche"] == sel_week)].copy()
        wk = wk.sort_values(["Datum_dt", "Startzeit", "Slot"])
        st.caption(f"Zeilen: {len(wk)}")
        st.dataframe(
            wk[["Datum", "Tag", "Slot", "Typ", "Spieler"]],
            use_container_width=True,
            hide_index=True
        )
        by_day = (
            wk.groupby(["Datum","Tag","Typ"], dropna=False)
              .size()
              .reset_index(name="Anzahl Matches")
              .sort_values(["Datum","Typ"])
        )
        with st.expander("Tages-Zusammenfassung"):
            st.dataframe(by_day, use_container_width=True, hide_index=True)
        csv = wk[["Datum","Tag","Slot","Typ","Spieler"]].to_csv(index=False)
        st.download_button("⬇️ Woche als CSV", data=csv, file_name=f"spielplan_{selected_week}.csv", mime="text/csv")

with tab2:
    st.subheader("🧍 Spieler-Matches")
    players = sorted([p for p in df_exp["Spieler_Name"].dropna().unique().tolist() if str(p).strip()])
    if not players:
        st.warning("Keine Spieler gefunden.")
    else:
        sel_players = st.multiselect("Spieler wählen", options=players, max_selections=5)
        if sel_players:
            pf = df_exp[df_exp["Spieler_Name"].isin(sel_players)].copy()
            pf = pf.sort_values(["Datum_dt", "Startzeit", "Slot"])
            cols = st.columns(min(len(sel_players), 5))
            for i, p in enumerate(sel_players):
                cnt = (pf["Spieler_Name"] == p).sum()
                cols[i].metric(p, f"{cnt} Matches")
            st.dataframe(pf[["Spieler_Name","Datum","Tag","Slot","Typ","Spieler"]], use_container_width=True, hide_index=True)
            csv2 = pf[["Spieler_Name","Datum","Tag","Slot","Typ","Spieler"]].to_csv(index=False)
            st.download_button("⬇️ Auswahl als CSV", data=csv2, file_name="spieler_matches.csv", mime="text/csv")
        else:
            st.info("Bitte Spieler auswählen, um ihre Matches zu sehen.")
