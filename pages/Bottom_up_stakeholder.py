import streamlit as st
import pandas as pd
import pickle
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from pyvis.network import Network

# Datei zum Speichern des Sitzungszustands
state_file = 'session_state.pkl'

# Funktion zum Laden des Sitzungszustands
def load_session_state():
    if os.path.exists(state_file):
        with open(state_file, 'rb') as f:
            return pickle.load(f)
    else:
        return {}

# Funktion zum Speichern des Sitzungszustands
def save_session_state(state):
    # Laden des aktuellen Zustands
    current_state = load_session_state()
    # Hinzufügen des neuen Zustands zum aktuellen Zustand
    combined_state = {**current_state, **state}
    # Speichern des kombinierten Zustands
    with open(state_file, 'wb') as f:
        pickle.dump(combined_state, f)

# Laden des Sitzungszustands aus der Datei
loaded_state = load_session_state()
st.session_state.update(loaded_state)


def stakeholder_punkte():
    if 'stakeholder_punkte_df' in st.session_state and not st.session_state.stakeholder_punkte_df.empty:
        # Change the order of columns
        st.session_state.stakeholder_punkte_df = st.session_state.stakeholder_punkte_df[['Platzierung', 'Thema', 'Unterthema', 'Unter-Unterthema', 'NumericalRating']]

        gb = GridOptionsBuilder.from_dataframe(st.session_state.stakeholder_punkte_df)
        gb.configure_pagination(paginationAutoPageSize=True, paginationPageSize=10)
        gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children", rowMultiSelectWithClick=True)
        gb.configure_side_bar()
        grid_options = gb.build()
        AgGrid(st.session_state.stakeholder_punkte_df, gridOptions=grid_options, enable_enterprise_modules=True, update_mode=GridUpdateMode.MODEL_CHANGED)

        # Button zum Löschen der Inhalte
        if st.button("Inhalte löschen"):
            # Entfernt den DataFrame aus dem session state
            if 'stakeholder_punkte_df' in st.session_state:
                del st.session_state['stakeholder_punkte_df']
                # Speichert den geänderten Zustand in der Datei
                save_session_state(st.session_state)
            st.experimental_rerun()  # Aktualisiert die Seite, um die Änderung widerzuspiegeln
    else:
        st.warning("Es wurden noch keine Inhalte im Excel-Upload hochgeladen. Bitte laden Sie eine Excel-Datei hoch.")

def excel_upload():
    """ Diese Funktion lädt Excel-Dateien hoch und erstellt Rankings basierend auf den Bewertungen. """
    def get_numerical_rating(value):
        ratings = {
            'Wesentlich': 3,
            'Eher Wesentlich': 2,
            'Eher nicht Wesentlich': 1,
            'Nicht Wesentlich': 0
        }
        return ratings.get(value, 0)

    def aggregate_rankings(df):
        """ Erzeugt eine aggregierte Rangliste basierend auf den Bewertungen. """
        df['NumericalRating'] = df['Bewertung'].apply(get_numerical_rating)
        df.fillna({'Thema': 'Unbekannt', 'Unterthema': 'Unbekannt', 'Unter-Unterthema': ''}, inplace=True)
        ranking = df.groupby(['Thema', 'Unterthema', 'Unter-Unterthema']).agg({'NumericalRating': 'sum'}).reset_index()
        ranking.sort_values(by='NumericalRating', ascending=False, inplace=True)
        ranking['Platzierung'] = ranking['NumericalRating'].rank(method='min', ascending=False).astype(int)
        return ranking[['Platzierung', 'Thema', 'Unterthema', 'Unter-Unterthema', 'NumericalRating']]

    uploaded_files = st.file_uploader("Excel-Dateien hochladen", accept_multiple_files=True, type=['xlsx'])
    if uploaded_files:
        df_list = [pd.read_excel(file, sheet_name=1, engine='openpyxl') for file in uploaded_files if file]
        combined_df = pd.concat(df_list)
        st.session_state.ranking_df = aggregate_rankings(combined_df)
        save_session_state({'ranking_df': st.session_state.ranking_df})
        st.write("Aktuelles Ranking basierend auf hochgeladenen Dateien:")
        gb = GridOptionsBuilder.from_dataframe(st.session_state.ranking_df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=15)
        gb.configure_side_bar()
        grid_options = gb.build()
        grid_options['defaultColDef'] = {'flex': 1}
        response = AgGrid(st.session_state.ranking_df, gridOptions=grid_options, enable_enterprise_modules=True, update_mode=GridUpdateMode.MODEL_CHANGED)
        st.session_state.grid_response = response
        save_session_state({'grid_response': st.session_state.grid_response})

        if st.button('Stakeholder Punkte übernehmen'):
            # Filter the data to keep only relevant columns
            relevant_columns = ['Thema', 'Unterthema', 'Unter-Unterthema', 'NumericalRating']
            new_df = st.session_state.ranking_df[relevant_columns]
            # Filter the rows to keep only those where 'NumericalRating' is greater than or equal to 1
            new_df = new_df[new_df['NumericalRating'] >= 1]

            if 'stakeholder_punkte_df' in st.session_state:
                # Merge the new dataframe with the existing one, adding the NumericalRating of identical entries
                st.session_state.stakeholder_punkte_df = pd.merge(st.session_state.stakeholder_punkte_df, new_df, on=['Thema', 'Unterthema', 'Unter-Unterthema'], how='outer')
                st.session_state.stakeholder_punkte_df['NumericalRating'] = st.session_state.stakeholder_punkte_df['NumericalRating_x'].add(st.session_state.stakeholder_punkte_df['NumericalRating_y'], fill_value=0)
                st.session_state.stakeholder_punkte_df.drop(columns=['NumericalRating_x', 'NumericalRating_y'], inplace=True)
            else:
                st.session_state.stakeholder_punkte_df = new_df

            # Create a new ranking based on NumericalRating
            st.session_state.stakeholder_punkte_df.sort_values(by='NumericalRating', ascending=False, inplace=True)
            st.session_state.stakeholder_punkte_df['Platzierung'] = st.session_state.stakeholder_punkte_df['NumericalRating'].rank(method='min', ascending=False).astype(int)

            save_session_state({'stakeholder_punkte_df': st.session_state.stakeholder_punkte_df})
            st.experimental_rerun()

def display_page():
    st.header("Stakeholder-Management")
    st.markdown("""
        Dieses Tool hilft Ihnen, Ihre Stakeholder effektiv zu verwalten und zu analysieren. Sie können relevante Informationen über verschiedene Stakeholdergruppen hinzufügen, bearbeiten und visualisieren. Die Daten helfen Ihnen, Strategien für den Umgang mit Ihren Stakeholdern zu entwickeln und zu priorisieren, basierend auf verschiedenen Kriterien wie Engagement-Level und Kommunikationshäufigkeit.
    """)
    tab1, tab2 = st.tabs(["Auswahl", "Stakeholder Nachhaltigkeitspunkte"])
    with tab1:
        excel_upload()
    with tab2:
        stakeholder_punkte()






