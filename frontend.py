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
from translation_manager import TranslationManager


class StreamlitApp:
    """Frontend UI logic for Streamlit app"""
    
    def __init__(self):
        self.processor = GeoJSONProcessor()
        self.translator = TranslationManager(default_language="en")
        self.setup_page()
    
    def setup_page(self):
        """Configure Streamlit page"""
        st.set_page_config(page_title=self.translator.get_text("app_title"), layout="wide")
        st.title(self.translator.get_text("app_title"))
        st.markdown(self.translator.get_text("description"))
    
    def render_file_uploader(self):
        """Render file upload interface"""
        return st.file_uploader(self.translator.get_text("file_upload"), type=["json", "geojson"])
    
    def render_column_selector(self, prop_df: pd.DataFrame) -> List[str]:
        """Render column selection interface"""
        with st.expander(self.translator.get_text("column_selector")):
            return st.multiselect(
                self.translator.get_text("column_selector_help"),
                prop_df.columns.tolist(),
                default=prop_df.columns.tolist(),
            )
    
    def render_filter_controls(self, prop_df: pd.DataFrame, default_index: int) -> Tuple[str, str]:
        """Render filter control interface"""
        st.subheader(self.translator.get_text("filter_section"))
        
        name_col = st.selectbox(
            self.translator.get_text("filter_column"), 
            prop_df.columns, 
            index=default_index
        )
        
        # Get dynamic example from actual data
        example_value = self._get_example_value(prop_df, name_col)
        pattern_placeholder = self.translator.get_text("filter_pattern", example=example_value)
        
        pattern = st.text_input(pattern_placeholder, "")
        
        return name_col, pattern
    
    def render_results_preview(self, filtered_df: pd.DataFrame, chosen_cols: List[str], 
                             filtered_count: int, total_count: int, has_pattern: bool) -> str:
        """Render filtered results preview and return selected feature name if clicked"""
        # Display count
        if has_pattern:
            st.write(self.translator.get_text("filtered_features", filtered=filtered_count, total=total_count))
        else:
            st.write(self.translator.get_text("all_features", total=total_count))
        
        # Display table
        st.subheader(self.translator.get_text("results_preview"))
        selected_feature = None
        
        if not filtered_df.empty:
            # Check if 'name' column exists for click functionality
            if 'name' in filtered_df.columns and 'name' in chosen_cols:
                st.info(self.translator.get_text("selection_tip"))
                
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
                        st.success(self.translator.get_text("selected_single", name=selected_features[0]))
                    else:
                        names = ', '.join(selected_features[:3]) + ('...' if len(selected_features) > 3 else '')
                        st.success(self.translator.get_text("selected_multiple", count=len(selected_features), names=names))
                    
                    # Auto-zoom to selected features  
                    if st.button(self.translator.get_text("focus_button"), key="zoom_to_selected", type="primary"):
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
            st.warning(self.translator.get_text("no_results"))
        
        return selected_feature or st.session_state.get("selected_row_name")
    
    def _get_example_value(self, prop_df: pd.DataFrame, column: str) -> str:
        """Get a dynamic example value from the actual data for the selected column"""
        if column not in prop_df.columns or prop_df.empty:
            return "example"
        
        # Get the first non-null, non-empty value from the column
        column_data = prop_df[column].dropna()
        if not column_data.empty:
            # Get first value and convert to string
            first_value = str(column_data.iloc[0])
            if first_value and first_value.strip():
                # If it's a long value, truncate it
                if len(first_value) > 20:
                    return first_value[:17] + "..."
                return first_value
        
        return "example"
    
    def render_map_section(self, name_col: str, pattern: str, selected_feature: str = None):
        """Render interactive map visualization"""
        st.subheader(self.translator.get_text("map_section"))
        
        # Initialize map visibility in session state
        if "show_map" not in st.session_state:
            st.session_state.show_map = False
            
        # Use session state for checkbox to persist through reruns
        show_map = st.checkbox(self.translator.get_text("show_map"), value=st.session_state.show_map, key="map_visibility")
        st.session_state.show_map = show_map
        
        if show_map:
            with st.spinner(self.translator.get_text("loading_map")):
                try:
                    # Check if specific features are selected for focus
                    if st.session_state.get("selected_row_name"):
                        folium_map = self.processor.create_focused_map(st.session_state.selected_row_name, name_col)
                        
                        # Show info about focused features
                        selected_features = st.session_state.selected_row_name
                        if isinstance(selected_features, list):
                            if len(selected_features) == 1:
                                st.info(self.translator.get_text("map_focus", name=selected_features[0]))
                            else:
                                names = ', '.join(selected_features[:2]) + ('...' if len(selected_features) > 2 else '')
                                st.info(self.translator.get_text("map_focus_multiple", count=len(selected_features), names=names))
                        else:
                            st.info(self.translator.get_text("map_focus", name=selected_features))
                        
                        # Add button to return to overview
                        if st.button(self.translator.get_text("back_to_overview"), key="back_to_overview"):
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
                            st.info(self.translator.get_text("features_displayed", filtered=filtered_count, total=self.processor.get_feature_count()))
                        else:
                            st.info(self.translator.get_text("all_features_displayed", total=self.processor.get_feature_count()))
                    
                    st_folium(folium_map, width=700, height=500)
                except Exception as e:
                    st.error(self.translator.get_text("map_error", error=str(e)))
                    st.info(self.translator.get_text("map_error_tip"))
    
    def render_download_section(self, filtered_json: str, feature_count: int):
        """Render download interface"""
        st.subheader(self.translator.get_text("download_section"))
        
        # Show clear info about what gets downloaded
        if st.session_state.get("selected_features"):
            selected_count = len(st.session_state.selected_features)
            st.info(self.translator.get_text("download_info", total=feature_count, selected=selected_count))
        
        st.download_button(
            self.translator.get_text("download_button"),
            data=filtered_json,
            file_name="filtered.geojson",
            mime="application/geo+json",
            help=self.translator.get_text("download_help", count=feature_count)
        )
    
    def run(self):
        """Main application logic"""
        # Render language selector in sidebar
        self.translator.render_language_selector()
        
        uploaded_file = self.render_file_uploader()
        
        if uploaded_file is not None:
            try:
                # Load and process data
                self.processor.load_geojson(uploaded_file)
                prop_df = self.processor.extract_properties()
                
                st.write(f"**{self.translator.get_text('feature_count')}:** {self.processor.get_feature_count()}")
                
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