import streamlit as st
import pandas as pd
import plotly.express as px
import json

# Configuration
st.set_page_config(page_title="Sting – Simulateur de mission", layout="wide")

# 🎨 Couleur boutons
st.markdown("""
    <style>
        .stButton>button {
            background-color: #003ea5;
            color: white;
            border-radius: 8px;
            padding: 0.5em 1em;
        }
    </style>
""", unsafe_allow_html=True)

# 🐝 Titre
st.title("🐝 Sting – Planifiez vos missions comme un pro")
st.caption("Un simulateur visuel pour assembler, ajuster et analyser vos tâches logistiques")

# 🧱 Briques disponibles
briques_disponibles = [
    {"Nom": "Contrat direct", "Temps": 15, "Catégorie": "contractualisation"},
    {"Nom": "Portail", "Temps": 5, "Catégorie": "contractualisation"},
    {"Nom": "Prise en charge véhicule", "Temps": 30, "Catégorie": "collecte"},
    {"Nom": "Dépose véhicule", "Temps": 25, "Catégorie": "collecte"},
    {"Nom": "Départ en journée", "Temps": 20, "Catégorie": "collecte"},
    {"Nom": "Ouvrir la mission", "Temps": 10, "Catégorie": "collecte"},
    {"Nom": "Collecte alimentaire froid", "Temps": 45, "Catégorie": "collecte"},
    {"Nom": "Contrôle sans manipulations", "Temps": 35, "Catégorie": "controle"},
    {"Nom": "Livraison température positif", "Temps": 40, "Catégorie": "livraison"},
]
df_disponibles = pd.DataFrame(briques_disponibles)

# 🧠 Session
if "briques_mission" not in st.session_state:
    st.session_state.briques_mission = pd.DataFrame(columns=["Nom", "Temps", "Catégorie"])

# ---
## Fonction pour la boîte de dialogue (Dialog)

@st.dialog("Choisir une brique à ajouter")
def ajouter_brique_dialogue():
    selected_brique = st.selectbox("Briques disponibles", df_disponibles["Nom"])
    
    # On ajoute une vérification pour éviter d'ajouter la même brique plusieurs fois
    if selected_brique in st.session_state.briques_mission["Nom"].values:
        st.warning("Cette brique est déjà présente.")
        if st.button("Fermer"):
            st.rerun()
    else:
        if st.button("Ajouter la brique"):
            brique = df_disponibles[df_disponibles["Nom"] == selected_brique].iloc[0]
            st.session_state.briques_mission = pd.concat(
                [st.session_state.briques_mission, pd.DataFrame([brique])], ignore_index=True
            )
            st.success(f"Brique ajoutée : {selected_brique}")
            # st.rerun() est utilisé ici pour fermer le dialogue et rafraîchir l'application
            st.rerun()

# ---

# 🖼️ Layout principal
col1, col2 = st.columns([1, 2])

# ============================
# 🧩 GAUCHE = AJOUT + LISTE
# ============================
with col1:
    st.subheader("📋 Briques dans la mission")

    # Le bouton appelle la fonction de dialogue
    if st.button("➕ Ajouter une brique"):
        ajouter_brique_dialogue()

    if st.session_state.briques_mission.empty:
        st.info("Aucune brique dans la mission.")
    else:
        updated_rows = []
        for i, row in st.session_state.briques_mission.iterrows():
            with st.expander(f"🧱 {row['Nom']}", expanded=True):
                colA, colB = st.columns([3, 1])
                with colA:
                    new_time = st.number_input(
                        f"Temps (min) pour « {row['Nom']} »", min_value=1,
                        value=int(row["Temps"]), step=1, key=f"temps_{i}"
                    )
                with colB:
                    if st.button("❌ Supprimer", key=f"suppr_{i}"):
                        st.session_state.briques_mission.drop(i, inplace=True)
                        st.session_state.briques_mission.reset_index(drop=True, inplace=True)
                        st.rerun()

                updated_rows.append((i, new_time))

        for i, new_time in updated_rows:
            st.session_state.briques_mission.at[i, "Temps"] = new_time

# ============================
# 📊 DROITE = ANALYSE
# ============================
with col2:
    st.subheader("📊 Résultats et analyses")

    if st.session_state.briques_mission.empty:
        st.info("Ajoutez des briques pour afficher les résultats.")
    else:
        # Nettoyage
        st.session_state.briques_mission["Temps"] = pd.to_numeric(
            st.session_state.briques_mission["Temps"], errors="coerce"
        ).fillna(0).astype(int)

        total = st.session_state.briques_mission["Temps"].sum()
        st.success(f"🕒 Temps total estimé : **{total} minutes**")

        grouped = st.session_state.briques_mission.groupby("Catégorie")["Temps"].sum().reset_index()

        fig = px.bar(
            grouped,
            x="Catégorie", y="Temps",
            color="Catégorie",
            title="Répartition du temps par catégorie",
            color_discrete_sequence=["#003ea5", "#ffcb05", "#e8b900", "#999999"]
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================
# 📁 SIDEBAR = IMPORT/EXPORT
# ============================
st.sidebar.header("📁 Import / Export")

# Export
st.sidebar.subheader("💾 Exporter la mission")

csv = st.session_state.briques_mission.to_csv(index=False).encode("utf-8")
st.sidebar.download_button("⬇️ Télécharger CSV", csv, file_name="mission_sting.csv", mime="text/csv")

json_data = st.session_state.briques_mission.to_dict(orient="records")
json_str = json.dumps(json_data, indent=2)
st.sidebar.download_button("⬇️ Télécharger JSON", json_str, file_name="mission_sting.json", mime="application/json")

# Import
st.sidebar.subheader("📥 Importer une mission")
uploaded = st.sidebar.file_uploader("Choisir un fichier", type=["csv", "json"])

if uploaded:
    try:
        if uploaded.name.endswith(".csv"):
            df = pd.read_csv(uploaded)
        elif uploaded.name.endswith(".json"):
            df = pd.DataFrame(json.load(uploaded))

        if {"Nom", "Temps", "Catégorie"}.issubset(df.columns):
            st.session_state.briques_mission = df
            st.sidebar.success("✅ Mission importée avec succès.")
        else:
            st.sidebar.error("❌ Colonnes manquantes dans le fichier.")
    except Exception as e:
        st.sidebar.error(f"Erreur à l’import : {e}")

