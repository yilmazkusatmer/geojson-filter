import pytest
import pandas as pd
import streamlit as st
from unittest.mock import MagicMock, patch, mock_open
import json
import io

# Import the class we want to test
from frontend import StreamlitApp
from backend import GeoJSONProcessor


class TestStreamlitApp:
    """Test suite for StreamlitApp frontend functionality"""
    
    def setup_method(self):
        """Setup a fresh app for each test"""
        self.app = StreamlitApp()
        
        # Sample test data for UI testing
        self.sample_dataframe = pd.DataFrame({
            'name': ['Helvetia Zurich', 'Baloise Basel', 'AXA Geneva'],
            'type': ['insurance', 'insurance', 'insurance'],
            'city': ['Zurich', 'Basel', 'Geneva'],
            'employees': [1200, 800, 950]
        })
        
        self.sample_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [8.5417, 47.3769]
                    },
                    "properties": {
                        "name": "Helvetia Zurich",
                        "type": "insurance",
                        "city": "Zurich"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point", 
                        "coordinates": [7.5886, 47.5596]
                    },
                    "properties": {
                        "name": "Baloise Basel",
                        "type": "insurance",
                        "city": "Basel"
                    }
                }
            ]
        }
    
    # === Initialization Tests ===
    
    def test_app_initialization(self):
        """Test app initializes with GeoJSONProcessor"""
        assert isinstance(self.app.processor, GeoJSONProcessor)
        assert self.app.processor.data == {}
    
    @patch('streamlit.set_page_config')
    @patch('streamlit.title')
    @patch('streamlit.markdown')
    def test_setup_page(self, mock_markdown, mock_title, mock_page_config):
        """Test page setup configuration"""
        self.app.setup_page()
        
        mock_page_config.assert_called_once_with(
            page_title="GeoJSON Property Viewer & Filter", 
            layout="wide"
        )
        mock_title.assert_called_once_with("GeoJSON Property Viewer & Filter")
        mock_markdown.assert_called_once()
    
    # === File Upload Tests ===
    
    @patch('streamlit.file_uploader')
    def test_render_file_uploader(self, mock_uploader):
        """Test file uploader rendering"""
        mock_uploader.return_value = None
        
        result = self.app.render_file_uploader()
        
        mock_uploader.assert_called_once_with(
            "GeoJSON hochladen", 
            type=["json", "geojson"]
        )
        assert result is None
    
    # === Column Selection Tests ===
    
    @patch('streamlit.expander')
    @patch('streamlit.multiselect')
    def test_render_column_selector(self, mock_multiselect, mock_expander):
        """Test column selection interface"""
        mock_expander.return_value.__enter__ = MagicMock()
        mock_expander.return_value.__exit__ = MagicMock()
        mock_multiselect.return_value = ['name', 'type']
        
        result = self.app.render_column_selector(self.sample_dataframe)
        
        mock_expander.assert_called_once_with("Spalten auswählen")
        mock_multiselect.assert_called_once_with(
            "Welche Spalten sollen angezeigt werden?",
            ['name', 'type', 'city', 'employees'],
            default=['name', 'type', 'city', 'employees']
        )
        assert result == ['name', 'type']
    
    # === Filter Controls Tests ===
    
    @patch('streamlit.subheader')
    @patch('streamlit.selectbox')
    @patch('streamlit.text_input')
    def test_render_filter_controls(self, mock_text_input, mock_selectbox, mock_subheader):
        """Test filter controls rendering"""
        mock_selectbox.return_value = 'name'
        mock_text_input.return_value = 'Helvetia'
        
        name_col, pattern = self.app.render_filter_controls(self.sample_dataframe, 0)
        
        mock_subheader.assert_called_once_with("Filtern")
        mock_selectbox.assert_called_once_with(
            "Spalte, auf die gefiltert werden soll",
            ['name', 'type', 'city', 'employees'],
            index=0
        )
        mock_text_input.assert_called_once_with("Regex‑Muster (z.B. 'Helvetia')", "")
        
        assert name_col == 'name'
        assert pattern == 'Helvetia'
    
    # === Results Preview Tests ===
    
    @patch('streamlit.write')
    @patch('streamlit.subheader')
    @patch('streamlit.dataframe')
    def test_render_results_preview_basic_table(self, mock_dataframe, mock_subheader, mock_write):
        """Test basic results preview without selection functionality"""
        filtered_df = self.sample_dataframe.iloc[:2]  # First 2 rows
        chosen_cols = ['type', 'city']  # No 'name' column selected
        
        mock_dataframe.return_value = MagicMock()
        
        result = self.app.render_results_preview(
            filtered_df, chosen_cols, 2, 3, True
        )
        
        mock_write.assert_called_with("🎯 **Gefilterte Features:** 2 / 3")
        mock_subheader.assert_called_with("Preview der Ergebnisse")
        mock_dataframe.assert_called_once()
        assert result is None
    
    @patch('streamlit.write')
    @patch('streamlit.subheader')
    @patch('streamlit.info')
    @patch('streamlit.dataframe')
    @patch('streamlit.success')
    @patch('streamlit.button')
    def test_render_results_preview_with_selection(self, mock_button, mock_success, 
                                                  mock_dataframe, mock_info, 
                                                  mock_subheader, mock_write):
        """Test results preview with multi-row selection"""
        filtered_df = self.sample_dataframe.iloc[:2]
        chosen_cols = ['name', 'type', 'city']  # Include 'name' for selection
        
        # Mock dataframe selection event
        mock_event = MagicMock()
        mock_event.selection.rows = [0, 1]  # Two rows selected
        mock_dataframe.return_value = mock_event
        mock_button.return_value = False
        
        # Mock session state
        with patch.dict('streamlit.session_state', {}, clear=True):
            result = self.app.render_results_preview(
                filtered_df, chosen_cols, 2, 3, True
            )
        
        mock_info.assert_called_with(
            "💡 **Tipp:** Wähle eine oder mehrere Zeilen aus der Tabelle - die Karte passt sich automatisch an!"
        )
        mock_success.assert_called_with(
            "🎯 **2 Features ausgewählt:** Helvetia Zurich, Baloise Basel"
        )
        mock_button.assert_called_with(
            "🎯 Fokussieren", 
            key="zoom_to_selected", 
            type="primary"
        )
    
    @patch('streamlit.write')
    @patch('streamlit.subheader')
    @patch('streamlit.info')
    @patch('streamlit.dataframe')
    @patch('streamlit.success')
    @patch('streamlit.button')
    @patch('streamlit.rerun')
    def test_render_results_preview_button_click(self, mock_rerun, mock_button, 
                                                mock_success, mock_dataframe, 
                                                mock_info, mock_subheader, mock_write):
        """Test focus button click functionality"""
        filtered_df = self.sample_dataframe.iloc[:1]
        chosen_cols = ['name', 'type']
        
        # Mock single row selection
        mock_event = MagicMock()
        mock_event.selection.rows = [0]
        mock_dataframe.return_value = mock_event
        mock_button.return_value = True  # Button clicked
        
        with patch.dict('streamlit.session_state', {}, clear=True):
            self.app.render_results_preview(
                filtered_df, chosen_cols, 1, 3, True
            )
            
            # Check if session state was set correctly
            assert st.session_state.selected_row_name == ['Helvetia Zurich']
            assert st.session_state.show_map is True
        
        mock_rerun.assert_called_once()
    
    @patch('streamlit.warning')
    def test_render_results_preview_empty_dataframe(self, mock_warning):
        """Test results preview with empty dataframe"""
        empty_df = pd.DataFrame()
        
        result = self.app.render_results_preview(
            empty_df, [], 0, 3, True
        )
        
        mock_warning.assert_called_with("⚠️ Keine Ergebnisse für diesen Filter gefunden.")
        assert result is None
    
    # === Map Section Tests ===
    
    @patch('streamlit.subheader')
    @patch('streamlit.checkbox')
    def test_render_map_section_checkbox_off(self, mock_checkbox, mock_subheader):
        """Test map section when checkbox is unchecked"""
        mock_checkbox.return_value = False
        
        with patch.dict('streamlit.session_state', {'show_map': False}, clear=True):
            self.app.render_map_section("name", "Helvetia")
        
        mock_subheader.assert_called_with("🗺️ Kartenansicht")
        mock_checkbox.assert_called_once()
    
    @patch('streamlit.subheader')
    @patch('streamlit.checkbox')
    @patch('streamlit.spinner')
    @patch('streamlit_folium.st_folium')
    @patch('streamlit.info')
    def test_render_map_section_normal_map(self, mock_info, mock_st_folium, 
                                          mock_spinner, mock_checkbox, mock_subheader):
        """Test map section showing normal filtered map"""
        mock_checkbox.return_value = True
        mock_spinner.return_value.__enter__ = MagicMock()
        mock_spinner.return_value.__exit__ = MagicMock()
        
        # Setup processor with test data
        self.app.processor.data = self.sample_geojson
        
        with patch.dict('streamlit.session_state', 
                       {'show_map': True, 'selected_row_name': None}, 
                       clear=True):
            self.app.render_map_section("type", "insurance")
        
        mock_st_folium.assert_called_once()
        mock_info.assert_called_with("📊 **2 von 2 Features** werden angezeigt")
    
    @patch('streamlit.subheader')
    @patch('streamlit.checkbox')
    @patch('streamlit.spinner')
    @patch('streamlit_folium.st_folium')
    @patch('streamlit.info')
    @patch('streamlit.button')
    def test_render_map_section_focused_map(self, mock_button, mock_info, 
                                           mock_st_folium, mock_spinner, 
                                           mock_checkbox, mock_subheader):
        """Test map section showing focused map"""
        mock_checkbox.return_value = True
        mock_spinner.return_value.__enter__ = MagicMock()
        mock_spinner.return_value.__exit__ = MagicMock()
        mock_button.return_value = False
        
        # Setup processor with test data
        self.app.processor.data = self.sample_geojson
        
        with patch.dict('streamlit.session_state', 
                       {'show_map': True, 'selected_row_name': ['Helvetia Zurich']}, 
                       clear=True):
            self.app.render_map_section("name", "")
        
        mock_st_folium.assert_called_once()
        mock_info.assert_called_with("🎯 **Fokus auf:** Helvetia Zurich")
        mock_button.assert_called_with(
            "🔄 Zurück zur Übersicht", 
            key="back_to_overview"
        )
    
    @patch('streamlit.subheader')
    @patch('streamlit.checkbox')
    @patch('streamlit.spinner')
    @patch('streamlit_folium.st_folium')
    @patch('streamlit.info')
    @patch('streamlit.button')
    def test_render_map_section_multiple_features(self, mock_button, mock_info, 
                                                 mock_st_folium, mock_spinner, 
                                                 mock_checkbox, mock_subheader):
        """Test map section with multiple focused features"""
        mock_checkbox.return_value = True
        mock_spinner.return_value.__enter__ = MagicMock()
        mock_spinner.return_value.__exit__ = MagicMock()
        mock_button.return_value = False
        
        # Setup processor with test data
        self.app.processor.data = self.sample_geojson
        
        with patch.dict('streamlit.session_state', 
                       {'show_map': True, 'selected_row_name': ['Helvetia Zurich', 'Baloise Basel']}, 
                       clear=True):
            self.app.render_map_section("name", "")
        
        mock_st_folium.assert_called_once()
        mock_info.assert_called_with("🎯 **Fokus auf 2 Features:** Helvetia Zurich, Baloise Basel")
    
    @patch('streamlit.subheader')
    @patch('streamlit.checkbox')
    @patch('streamlit.spinner')
    @patch('streamlit.error')
    @patch('streamlit.info')
    def test_render_map_section_error_handling(self, mock_info_tip, mock_error, 
                                              mock_spinner, mock_checkbox, mock_subheader):
        """Test map section error handling"""
        mock_checkbox.return_value = True
        mock_spinner.return_value.__enter__ = MagicMock()
        mock_spinner.return_value.__exit__ = MagicMock()
        
        # Force an error by not setting up processor data
        with patch.dict('streamlit.session_state', {'show_map': True}, clear=True):
            with patch.object(self.app.processor, 'create_map', side_effect=Exception("Test error")):
                self.app.render_map_section("name", "")
        
        mock_error.assert_called_with("❌ Fehler beim Erstellen der Karte: Test error")
        mock_info_tip.assert_called_with("💡 **Tipp:** Versuche es mit einer anderen GeoJSON-Datei.")
    
    @patch('streamlit.subheader')
    @patch('streamlit.checkbox')
    @patch('streamlit.spinner')
    @patch('streamlit.button')
    @patch('streamlit.rerun')
    def test_render_map_section_back_button(self, mock_rerun, mock_button, 
                                           mock_spinner, mock_checkbox, mock_subheader):
        """Test back to overview button functionality"""
        mock_checkbox.return_value = True
        mock_spinner.return_value.__enter__ = MagicMock()
        mock_spinner.return_value.__exit__ = MagicMock()
        mock_button.return_value = True  # Back button clicked
        
        # Setup processor with test data
        self.app.processor.data = self.sample_geojson
        
        with patch.dict('streamlit.session_state', 
                       {'show_map': True, 'selected_row_name': ['Helvetia Zurich']}, 
                       clear=True):
            self.app.render_map_section("name", "")
            
            # Check if session state was reset
            assert st.session_state.selected_row_name is None
            assert st.session_state.selected_features == []
        
        mock_rerun.assert_called_once()
    
    # === Download Section Tests ===
    
    @patch('streamlit.subheader')
    @patch('streamlit.download_button')
    def test_render_download_section_basic(self, mock_download_button, mock_subheader):
        """Test basic download section without selection"""
        filtered_json = '{"type": "FeatureCollection", "features": []}'
        
        with patch.dict('streamlit.session_state', {}, clear=True):
            self.app.render_download_section(filtered_json, 5)
        
        mock_subheader.assert_called_with("📥 Download")
        mock_download_button.assert_called_with(
            "🎯 Gefiltertes GeoJSON herunterladen",
            data=filtered_json,
            file_name="filtered.geojson",
            mime="application/geo+json",
            help="Lädt alle 5 gefilterten Features herunter (nicht nur ausgewählte)"
        )
    
    @patch('streamlit.subheader')
    @patch('streamlit.info')
    @patch('streamlit.download_button')
    def test_render_download_section_with_selection(self, mock_download_button, 
                                                   mock_info, mock_subheader):
        """Test download section with selected features"""
        filtered_json = '{"type": "FeatureCollection", "features": []}'
        
        with patch.dict('streamlit.session_state', 
                       {'selected_features': ['Feature 1', 'Feature 2']}, 
                       clear=True):
            self.app.render_download_section(filtered_json, 10)
        
        mock_info.assert_called_with(
            "💡 **Hinweis:** Download enthält alle 10 gefilterten Features, nicht nur die 2 ausgewählten."
        )
        mock_download_button.assert_called_with(
            "🎯 Gefiltertes GeoJSON herunterladen",
            data=filtered_json,
            file_name="filtered.geojson",
            mime="application/geo+json",
            help="Lädt alle 10 gefilterten Features herunter (nicht nur ausgewählte)"
        )
    
    # === Session State Management Tests ===
    
    def test_session_state_initialization(self):
        """Test session state variables are properly initialized"""
        # Test different initialization scenarios
        filtered_df = self.sample_dataframe.iloc[:1]
        chosen_cols = ['name', 'type']
        
        with patch('streamlit.dataframe') as mock_dataframe:
            with patch('streamlit.write'), patch('streamlit.subheader'), patch('streamlit.info'):
                mock_event = MagicMock()
                mock_event.selection.rows = []
                mock_dataframe.return_value = mock_event
                
                with patch.dict('streamlit.session_state', {}, clear=True):
                    self.app.render_results_preview(
                        filtered_df, chosen_cols, 1, 3, False
                    )
                    
                    # Check initialization
                    assert 'selected_features' in st.session_state
                    assert 'selected_row_name' in st.session_state
                    assert st.session_state.selected_features == []
    
    def test_session_state_persistence(self):
        """Test session state persists through reruns"""
        with patch.dict('streamlit.session_state', 
                       {'show_map': True, 'selected_features': ['Test Feature']}, 
                       clear=True):
            
            # Simulate map section call
            with patch('streamlit.checkbox') as mock_checkbox:
                mock_checkbox.return_value = True
                with patch('streamlit.subheader'), patch('streamlit.spinner'):
                    with patch('streamlit_folium.st_folium'), patch('streamlit.info'):
                        self.app.render_map_section("name", "")
                
                # Session state should persist
                assert st.session_state.show_map is True
                assert st.session_state.selected_features == ['Test Feature']
    
    # === Integration Tests ===
    
    @patch('streamlit.set_page_config')
    @patch('streamlit.title')
    @patch('streamlit.markdown')
    @patch('streamlit.file_uploader')
    @patch('streamlit.write')
    @patch('streamlit.error')
    def test_run_no_file_uploaded(self, mock_error, mock_write, mock_uploader, 
                                 mock_markdown, mock_title, mock_page_config):
        """Test run method when no file is uploaded"""
        mock_uploader.return_value = None
        
        self.app.run()
        
        mock_uploader.assert_called_once()
        # Should not call other methods without file
        mock_write.assert_not_called()
    
    @patch('streamlit.set_page_config')
    @patch('streamlit.title') 
    @patch('streamlit.markdown')
    @patch('streamlit.file_uploader')
    @patch('streamlit.write')
    @patch('streamlit.error')
    @patch('streamlit.stop')
    def test_run_invalid_file(self, mock_stop, mock_error, mock_write, 
                             mock_uploader, mock_markdown, mock_title, mock_page_config):
        """Test run method with invalid file"""
        # Mock invalid file
        mock_file = MagicMock()
        mock_file.read.return_value = b'invalid json'
        mock_uploader.return_value = mock_file
        
        with patch.object(self.app.processor, 'load_geojson', 
                         side_effect=ValueError("Invalid JSON")):
            self.app.run()
        
        mock_error.assert_called_with("Invalid JSON")
        mock_stop.assert_called_once()
    
    @patch('streamlit.set_page_config')
    @patch('streamlit.title')
    @patch('streamlit.markdown') 
    @patch('streamlit.file_uploader')
    @patch('streamlit.write')
    @patch('streamlit.expander')
    @patch('streamlit.multiselect')
    @patch('streamlit.subheader')
    @patch('streamlit.selectbox')
    @patch('streamlit.text_input')
    @patch('streamlit.dataframe')
    @patch('streamlit.checkbox')
    @patch('streamlit.download_button')
    def test_run_successful_workflow(self, mock_download, mock_checkbox, 
                                    mock_dataframe, mock_text_input, mock_selectbox,
                                    mock_subheader, mock_multiselect, mock_expander,
                                    mock_write, mock_uploader, mock_markdown, 
                                    mock_title, mock_page_config):
        """Test successful complete workflow"""
        # Mock valid file
        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps(self.sample_geojson).encode('utf-8')
        mock_uploader.return_value = mock_file
        
        # Mock UI components
        mock_expander.return_value.__enter__ = MagicMock()
        mock_expander.return_value.__exit__ = MagicMock()
        mock_multiselect.return_value = ['name', 'type']
        mock_selectbox.return_value = 'name'
        mock_text_input.return_value = 'Helvetia'
        mock_dataframe.return_value = MagicMock()
        mock_dataframe.return_value.selection.rows = []
        mock_checkbox.return_value = False
        
        with patch.dict('streamlit.session_state', {}, clear=True):
            self.app.run()
        
        # Verify key components were called
        mock_uploader.assert_called_once()
        mock_multiselect.assert_called_once()
        mock_selectbox.assert_called_once()
        mock_text_input.assert_called_once()
        mock_download.assert_called_once()
    
    # === Error Handling Tests ===
    
    def test_error_handling_in_map_creation(self):
        """Test error handling during map creation"""
        with patch('streamlit.checkbox', return_value=True):
            with patch('streamlit.subheader'), patch('streamlit.spinner'):
                with patch('streamlit.error') as mock_error:
                    with patch('streamlit.info') as mock_info_tip:
                        with patch.object(self.app.processor, 'create_map', 
                                         side_effect=Exception("Map creation failed")):
                            with patch.dict('streamlit.session_state', {'show_map': True}, clear=True):
                                self.app.render_map_section("name", "")
                
                mock_error.assert_called_with("❌ Fehler beim Erstellen der Karte: Map creation failed")
                mock_info_tip.assert_called_with("💡 **Tipp:** Versuche es mit einer anderen GeoJSON-Datei.")
    
    def test_feature_selection_edge_cases(self):
        """Test feature selection with edge cases"""
        # Test with empty selection
        filtered_df = self.sample_dataframe
        chosen_cols = ['name', 'type']
        
        with patch('streamlit.dataframe') as mock_dataframe:
            with patch('streamlit.write'), patch('streamlit.subheader'), patch('streamlit.info'):
                mock_event = MagicMock()
                mock_event.selection.rows = []  # No selection
                mock_dataframe.return_value = mock_event
                
                with patch.dict('streamlit.session_state', 
                               {'selected_features': ['Previous Selection']}, 
                               clear=True):
                    self.app.render_results_preview(
                        filtered_df, chosen_cols, 4, 4, False
                    )
                    
                    # Should reset selection
                    assert st.session_state.selected_features == []
                    assert st.session_state.selected_row_name is None 