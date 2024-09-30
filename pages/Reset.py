import streamlit as st
import os
import shutil
import zipfile
from io import BytesIO

# Define the file paths
STATE_FILE = 'SessionStates.pkl'
BACKUP_STATE_FILE = 'SessionStatesThemenESRS.pkl'
DEFAULT_STATE_FILE = 'Grundlagen.pkl'
DEFAULT_BACKUP_FILE = 'Grundlagen_Themen_ESRS.pkl'

# Function to reset the session state
def reset_session_state():
    st.session_state.clear()  # Clear all session state values

    # Check if 'SessionStates.pkl' and 'SessionStatesThemenESRS.pkl' exist, and overwrite them with the default files
    if os.path.exists(STATE_FILE) and os.path.exists(BACKUP_STATE_FILE):
        shutil.copy(DEFAULT_STATE_FILE, STATE_FILE)  # Overwrite 'SessionStates.pkl' with 'Grundlagen.pkl'
        shutil.copy(DEFAULT_BACKUP_FILE, BACKUP_STATE_FILE)  # Overwrite 'SessionStatesThemenESRS.pkl' with 'Grundlagen_Themen_ESRS.pkl'
        st.success("App wurde erfolgreich zurückgesetzt. Alle gespeicherten Inhalte wurden entfernt.")
    else:
        st.error("Die erforderlichen Pickle-Dateien 'SessionStates.pkl' und 'SessionStatesThemenESRS.pkl' fehlen. Bitte überprüfen Sie, ob die Dateien im verzeichnis vorliegen.")

# Function to simulate the modal dialog
def show_modal_dialog():
    with st.expander("⚠️ Bestätigen Sie Ihre Aktion", expanded=True):
        st.write("Sind Sie sicher, dass Sie alle gespeicherten Inhalte aus der App entfernen möchten?")

        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Ja"):
                reset_session_state()
                st.session_state.modal_open = False
        with col2:
            if st.button("Nein"):
                st.session_state.modal_open = False
                st.warning("Zurücksetzung abgebrochen.")

# Function to create a zip file for both pickle files and provide a download button
def download_pickle_files_as_zip():
    # Ensure both files exist before proceeding
    if os.path.exists(STATE_FILE) and os.path.exists(BACKUP_STATE_FILE):
        # Create an in-memory ZIP file
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.write(STATE_FILE)
            zf.write(BACKUP_STATE_FILE)
        
        # Ensure buffer is at the start before reading
        zip_buffer.seek(0)

        # Provide the download button for the zip file
        st.download_button(
            label="Download Pickle Files (ZIP)",
            data=zip_buffer,
            file_name="Speicherstände.zip",
            mime="application/zip"
        )
    else:
        st.warning("One or both of the required pickle files are missing. Please check that 'SessionStates.pkl' and 'SessionStatesThemenESRS.pkl' exist.")

# Display the settings page
def display_settings_page():
    if 'modal_open' not in st.session_state:
        st.session_state.modal_open = False

    if st.button('🔄 App neu starten'):
        st.session_state.modal_open = True  # Trigger modal on button press
    
    if st.session_state.modal_open:
        show_modal_dialog()  # Show the modal dialog if triggered
    
    # Add the download section for pickle files
    st.subheader("Speicherstände herunterladen")
    download_pickle_files_as_zip()

def display_page():
    st.subheader("Reset")
    st.write("Auf dieser Seite können Sie die App zurücksetzen und die Standardeinstellungen wiederherstellen.")
    display_settings_page()

