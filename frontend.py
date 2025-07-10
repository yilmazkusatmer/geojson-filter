"""
Frontend UI Logic for GeoJSON Viewer

This module contains the StreamlitApp class which handles all user interface
components, rendering, and user interactions for the GeoJSON filtering application.
"""

from typing import List, Tuple

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from backend import GeoJSONProcessor


class StreamlitApp:
    """Frontend UI logic for Streamlit app"""
    
    def __init__(self):
        self.processor = GeoJSONProcessor()
        self.setup_page()
    
    def setup_page(self):
        """Configure Streamlit page"""
        st.set_page_config(page_title="GeoJSON Property Viewer & Filter", layout="wide")
        st.title("GeoJSON Property Viewer & Filter")
        st.markdown(
            """
            Laden Sie eine **GeoJSON**‑Datei hoch ➜ sehen Sie alle *properties* ➜ filtern Sie per **Regex**
            und laden Sie das gefilterte GeoJSON wieder herunter.
            """
        )
    
    def render_file_uploader(self):
        """Render file upload interface"""
        return st.file_uploader("GeoJSON hochladen", type=["json", "geojson"])
    
    def render_column_selector(self, prop_df: pd.DataFrame) -> List[str]:
        """Render column selection interface"""
        with st.expander("Spalten auswählen"):
            return st.multiselect(
                "Welche Spalten sollen angezeigt werden?",
                prop_df.columns.tolist(),
                default=prop_df.columns.tolist(),
            )
    
    def render_filter_controls(self, prop_df: pd.DataFrame, default_index: int) -> Tuple[str, str]:
        """Render filter control interface"""
        st.subheader("Filtern")
        
        name_col = st.selectbox(
            "Spalte, auf die gefiltert werden soll", 
            prop_df.columns, 
            index=default_index
        )
        pattern = st.text_input("Regex‑Muster (z.B. 'Helvetia')", "")
        
        return name_col, pattern
    
    def render_results_preview(self, filtered_df: pd.DataFrame, chosen_cols: List[str], 
                             filtered_count: int, total_count: int, has_pattern: bool) -> str:
        """Render filtered results preview and return selected feature name if clicked"""
        # Display count
        if has_pattern:
            st.write(f"🎯 **Gefilterte Features:** {filtered_count} / {total_count}")
        else:
            st.write(f"📊 **Alle Features:** {total_count}")
        
        # Display table
        st.subheader("Preview der Ergebnisse")
        selected_feature = None
        
        if not filtered_df.empty:
            # Check if 'name' column exists for click functionality
            if 'name' in filtered_df.columns and 'name' in chosen_cols:
                st.info("💡 **Tipp:** Wähle eine oder mehrere Zeilen aus der Tabelle - die Karte passt sich automatisch an!")
                
                # Create clickable table with multi-row selection
                event = st.dataframe(
                    filtered_df[chosen_cols].reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True,
                    selection_mode="multi-row",
                    on_select="rerun",
                    key="feature_table"
                )
                
                # Initialize session state if needed
                if "selected_features" not in st.session_state:
                    st.session_state.selected_features = []
                
                # Check if rows were selected
                if event.selection.rows:
                    selected_features = []
                    for row_idx in event.selection.rows:
                        if row_idx < len(filtered_df):
                            selected_row = filtered_df.iloc[row_idx]
                            feature_name = selected_row.get('name', f'Feature {row_idx+1}')
                            selected_features.append(feature_name)
                    
                    # Update session state with selected features
                    st.session_state.selected_features = selected_features
                    
                    # Show selected features info
                    if len(selected_features) == 1:
                        st.success(f"🎯 **Ausgewählt:** {selected_features[0]}")
                    else:
                        st.success(f"🎯 **{len(selected_features)} Features ausgewählt:** {', '.join(selected_features[:3])}{'...' if len(selected_features) > 3 else ''}")
                    
                    # Auto-zoom to selected features  
                    if st.button("🎯 Fokussieren", key="zoom_to_selected", type="primary"):
                        # Set selected features for map focusing and auto-enable map
                        st.session_state.selected_row_name = selected_features
                        st.session_state.show_map = True  # Auto-enable map when zooming
                        st.rerun()
                else:
                    # No rows selected - reset selection
                    if st.session_state.get("selected_features"):
                        st.session_state.selected_features = []
                        st.session_state.selected_row_name = None
                
                # Initialize single feature selection state if needed
                if "selected_row_name" not in st.session_state:
                    st.session_state.selected_row_name = None
            else:
                # Regular table without click functionality
                st.dataframe(filtered_df[chosen_cols], use_container_width=True)
        else:
            st.warning("⚠️ Keine Ergebnisse für diesen Filter gefunden.")
        
        return selected_feature or st.session_state.get("selected_row_name")
    
    def render_map_section(self, name_col: str, pattern: str, selected_feature: str = None):
        """Render interactive map visualization"""
        st.subheader("🗺️ Kartenansicht")
        
        # Initialize map visibility in session state
        if "show_map" not in st.session_state:
            st.session_state.show_map = False
            
        # Use session state for checkbox to persist through reruns
        show_map = st.checkbox("Karte anzeigen", value=st.session_state.show_map, key="map_visibility")
        st.session_state.show_map = show_map
        
        if show_map:
            with st.spinner("Lade Karte..."):
                try:
                    # Check if specific features are selected for focus
                    if st.session_state.get("selected_row_name"):
                        folium_map = self.processor.create_focused_map(st.session_state.selected_row_name, name_col)
                        
                        # Show info about focused features
                        selected_features = st.session_state.selected_row_name
                        if isinstance(selected_features, list):
                            if len(selected_features) == 1:
                                st.info(f"🎯 **Fokus auf:** {selected_features[0]}")
                            else:
                                st.info(f"🎯 **Fokus auf {len(selected_features)} Features:** {', '.join(selected_features[:2])}{'...' if len(selected_features) > 2 else ''}")
                        else:
                            st.info(f"🎯 **Fokus auf:** {selected_features}")
                        
                        # Add button to return to overview
                        if st.button("🔄 Zurück zur Übersicht", key="back_to_overview"):
                            st.session_state.selected_row_name = None
                            st.session_state.selected_features = []
                            st.rerun()
                    else:
                        # Show normal filtered map
                        folium_map = self.processor.create_map(name_col, pattern)
                        
                        # Show feature count info
                        if pattern and name_col:
                            import re
                            filtered_count = len([
                                feat for feat in self.processor.data.get("features", [])
                                if re.search(pattern, str(feat.get("properties", {}).get(name_col, "")), re.IGNORECASE)
                            ])
                            st.info(f"📊 **{filtered_count} von {self.processor.get_feature_count()} Features** werden angezeigt")
                        else:
                            st.info(f"📊 **Alle {self.processor.get_feature_count()} Features** werden angezeigt")
                    
                    st_folium(folium_map, width=700, height=500)
                except Exception as e:
                    st.error(f"❌ Fehler beim Erstellen der Karte: {str(e)}")
                    st.info("💡 **Tipp:** Versuche es mit einer anderen GeoJSON-Datei.")
    
    def render_download_section(self, filtered_json: str, feature_count: int):
        """Render download interface"""
        st.subheader("📥 Download")
        
        # Show clear info about what gets downloaded
        if st.session_state.get("selected_features"):
            selected_count = len(st.session_state.selected_features)
            st.info(f"💡 **Hinweis:** Download enthält alle {feature_count} gefilterten Features, nicht nur die {selected_count} ausgewählten.")
        
        st.download_button(
            "🎯 Gefiltertes GeoJSON herunterladen",
            data=filtered_json,
            file_name="filtered.geojson",
            mime="application/geo+json",
            help=f"Lädt alle {feature_count} gefilterten Features herunter (nicht nur ausgewählte)"
        )
    
    def run(self):
        """Main application logic"""
        uploaded_file = self.render_file_uploader()
        
        if uploaded_file is not None:
            try:
                # Load and process data
                self.processor.load_geojson(uploaded_file)
                prop_df = self.processor.extract_properties()
                
                st.write(f"**Anzahl Features:** {self.processor.get_feature_count()}")
                
                # UI Controls
                chosen_cols = self.render_column_selector(prop_df)
                default_index = self.processor.get_default_filter_column()
                name_col, pattern = self.render_filter_controls(prop_df, default_index)
                
                # Process filtering
                filtered_df, filtered_count = self.processor.filter_data(name_col, pattern)
                
                # Render results and get selected feature
                selected_feature = self.render_results_preview(
                    filtered_df, chosen_cols, filtered_count, 
                    self.processor.get_feature_count(), bool(pattern)
                )
                
                # Map visualization
                self.render_map_section(name_col, pattern, selected_feature)
                
                # Download section
                filtered_json = self.processor.create_filtered_geojson(name_col, pattern)
                feature_count = self.processor.get_filtered_feature_count(filtered_json)
                self.render_download_section(filtered_json, feature_count)
                
            except ValueError as e:
                st.error(str(e))
                st.stop() 