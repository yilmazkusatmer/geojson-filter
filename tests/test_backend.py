"""
Unit tests for GeoJSONProcessor backend logic

Tests all core functionality of the backend without UI dependencies.
"""

import pytest
import json
import io
from unittest.mock import MagicMock
import pandas as pd
import folium

# Import the class we want to test
from backend import GeoJSONProcessor


class TestGeoJSONProcessor:
    """Test suite for GeoJSONProcessor backend functionality"""
    
    def setup_method(self):
        """Setup a fresh processor for each test"""
        self.processor = GeoJSONProcessor()
        
        # Sample test data
        self.sample_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [8.5417, 47.3769]  # Zurich
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
                        "coordinates": [7.5886, 47.5596]  # Basel
                    },
                    "properties": {
                        "name": "Baloise Basel",
                        "type": "insurance", 
                        "city": "Basel"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [8.5, 47.3], [8.6, 47.3], [8.6, 47.4], [8.5, 47.4], [8.5, 47.3]
                        ]]
                    },
                    "properties": {
                        "name": "Zurich District", 
                        "type": "area",
                        "center": {
                            "type": "Point",
                            "coordinates": [8.55, 47.35]
                        }
                    }
                }
            ]
        }
    
    # === Loading and Validation Tests ===
    
    def test_load_geojson_valid_data(self):
        """Test loading valid GeoJSON data"""
        file_content = json.dumps(self.sample_geojson)
        mock_file = MagicMock()
        mock_file.read.return_value = file_content.encode('utf-8')
        
        result = self.processor.load_geojson(mock_file)
        assert result is True
        assert self.processor.data == self.sample_geojson
    
    def test_load_geojson_invalid_json(self):
        """Test loading invalid JSON"""
        mock_file = MagicMock()
        mock_file.read.return_value = b'invalid json content'
        
        with pytest.raises(ValueError, match="Ungültiges JSON-Format"):
            self.processor.load_geojson(mock_file)
    
    def test_load_geojson_missing_features(self):
        """Test loading GeoJSON without features"""
        invalid_geojson = {"type": "FeatureCollection"}
        file_content = json.dumps(invalid_geojson)
        mock_file = MagicMock()
        mock_file.read.return_value = file_content.encode('utf-8')
        
        with pytest.raises(ValueError, match="Keine 'features' gefunden"):
            self.processor.load_geojson(mock_file)
    
    # === Property Extraction Tests ===
    
    def test_extract_properties_success(self):
        """Test successful property extraction"""
        self.processor.data = self.sample_geojson
        df = self.processor.extract_properties()
        
        assert len(df) == 3
        assert list(df.columns) == ['name', 'type', 'city']
        assert df.iloc[0]['name'] == 'Helvetia Zurich'
        assert df.iloc[1]['name'] == 'Baloise Basel'
    
    def test_extract_properties_mixed_properties(self):
        """Test extraction with missing properties in some features"""
        mixed_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {"name": "Feature A", "category": "test"}
                },
                {
                    "type": "Feature", 
                    "geometry": {"type": "Point", "coordinates": [1, 1]},
                    "properties": {"name": "Feature B"}  # missing category
                }
            ]
        }
        
        self.processor.data = mixed_geojson
        df = self.processor.extract_properties()
        
        assert len(df) == 2
        assert 'name' in df.columns
        assert 'category' in df.columns
        assert pd.isna(df.iloc[1]['category'])  # Should be NaN for missing property
    
    # === Default Column Selection Tests ===
    
    def test_get_default_filter_column_name_exists(self):
        """Test default column when 'name' exists"""
        self.processor.data = self.sample_geojson
        df = self.processor.extract_properties()
        
        default_index = self.processor.get_default_filter_column()
        assert default_index == 0  # 'name' should be first column
    
    def test_get_default_filter_column_no_name(self):
        """Test default column when 'name' doesn't exist"""
        no_name_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {"id": "123", "category": "test"}
                }
            ]
        }
        
        self.processor.data = no_name_geojson
        df = self.processor.extract_properties()
        
        default_index = self.processor.get_default_filter_column()
        assert default_index == 0  # Should default to first column
    
    # === Filtering Tests ===
    
    def test_filter_data_with_pattern(self):
        """Test filtering with regex pattern"""
        self.processor.data = self.sample_geojson
        
        filtered_df, count = self.processor.filter_data("name", "Helvetia")
        
        assert count == 1
        assert len(filtered_df) == 1
        assert filtered_df.iloc[0]['name'] == 'Helvetia Zurich'
    
    def test_filter_data_case_insensitive(self):
        """Test case-insensitive filtering"""
        self.processor.data = self.sample_geojson
        
        filtered_df, count = self.processor.filter_data("name", "helvetia")
        
        assert count == 1
        assert filtered_df.iloc[0]['name'] == 'Helvetia Zurich'
    
    def test_filter_data_multiple_matches(self):
        """Test filtering with multiple matches"""
        self.processor.data = self.sample_geojson
        
        filtered_df, count = self.processor.filter_data("type", "insurance")
        
        assert count == 2
        assert len(filtered_df) == 2
    
    def test_filter_data_no_matches(self):
        """Test filtering with no matches"""
        self.processor.data = self.sample_geojson
        
        filtered_df, count = self.processor.filter_data("name", "NonExistent")
        
        assert count == 0
        assert len(filtered_df) == 0
    
    def test_filter_data_regex_pattern(self):
        """Test filtering with complex regex"""
        self.processor.data = self.sample_geojson
        
        filtered_df, count = self.processor.filter_data("name", "Helvetia|Baloise")
        
        assert count == 2
        assert len(filtered_df) == 2
    
    # === GeoJSON Creation Tests ===
    
    def test_create_filtered_geojson(self):
        """Test creating filtered GeoJSON"""
        self.processor.data = self.sample_geojson
        
        filtered_json = self.processor.create_filtered_geojson("name", "Helvetia")
        filtered_data = json.loads(filtered_json)
        
        assert filtered_data["type"] == "FeatureCollection"
        assert len(filtered_data["features"]) == 1
        assert filtered_data["features"][0]["properties"]["name"] == "Helvetia Zurich"
    
    def test_create_filtered_geojson_no_filter(self):
        """Test creating GeoJSON without filter"""
        self.processor.data = self.sample_geojson
        
        filtered_json = self.processor.create_filtered_geojson("name", "")
        filtered_data = json.loads(filtered_json)
        
        assert len(filtered_data["features"]) == 3  # All features
    
    # === Count Tests ===
    
    def test_get_feature_count(self):
        """Test getting total feature count"""
        self.processor.data = self.sample_geojson
        
        count = self.processor.get_feature_count()
        assert count == 3
    
    def test_get_filtered_feature_count(self):
        """Test getting filtered feature count"""
        filtered_json = json.dumps({
            "type": "FeatureCollection",
            "features": [self.sample_geojson["features"][0]]
        })
        
        count = self.processor.get_filtered_feature_count(filtered_json)
        assert count == 1
    
    # === Map Bounds Calculation Tests ===
    
    def test_calculate_map_bounds_points(self):
        """Test calculating bounds for point features"""
        self.processor.data = self.sample_geojson
        
        lat, lon = self.processor.calculate_map_bounds()
        
        # Should be average of Zurich and Basel coordinates
        expected_lat = (47.3769 + 47.5596 + 47.35) / 3
        expected_lon = (8.5417 + 7.5886 + 8.55) / 3
        
        assert abs(lat - expected_lat) < 0.01
        assert abs(lon - expected_lon) < 0.01
    
    def test_calculate_filtered_map_bounds(self):
        """Test calculating bounds for specific features"""
        features = [self.sample_geojson["features"][0]]  # Just Zurich
        
        lat, lon = self.processor.calculate_filtered_map_bounds(features)
        
        assert abs(lat - 47.3769) < 0.001
        assert abs(lon - 8.5417) < 0.001
    
    def test_calculate_map_bounds_empty_features(self):
        """Test bounds calculation with no features"""
        lat, lon = self.processor.calculate_filtered_map_bounds([])
        
        # Should return default Germany center
        assert lat == 51.1657
        assert lon == 10.4515
    
    # === Map Creation Tests ===
    
    def test_create_map_basic(self):
        """Test basic map creation"""
        self.processor.data = self.sample_geojson
        
        map_obj = self.processor.create_map()
        
        assert isinstance(map_obj, folium.Map)
        # Check if map has the expected location (approximately)
        assert abs(map_obj.location[0] - 47.4) < 0.2  # Rough center of test data
        assert abs(map_obj.location[1] - 8.2) < 0.5
    
    def test_create_map_with_filter(self):
        """Test map creation with filter"""
        self.processor.data = self.sample_geojson
        
        map_obj = self.processor.create_map("name", "Helvetia")
        
        assert isinstance(map_obj, folium.Map)
        # Should be centered on Zurich (Helvetia location)
        assert abs(map_obj.location[0] - 47.3769) < 0.1
        assert abs(map_obj.location[1] - 8.5417) < 0.1
    
    def test_create_focused_map_single_feature(self):
        """Test focused map for single feature"""
        self.processor.data = self.sample_geojson
        
        map_obj = self.processor.create_focused_map("Helvetia Zurich")
        
        assert isinstance(map_obj, folium.Map)
        assert map_obj.zoom_start == 16  # Should be high zoom for single feature
    
    def test_create_focused_map_multiple_features(self):
        """Test focused map for multiple features"""
        self.processor.data = self.sample_geojson
        
        map_obj = self.processor.create_focused_map(["Helvetia Zurich", "Baloise Basel"])
        
        assert isinstance(map_obj, folium.Map)
        # Should have lower zoom for multiple features
        assert map_obj.zoom_start < 16
    
    def test_create_focused_map_nonexistent_feature(self):
        """Test focused map for non-existent feature"""
        self.processor.data = self.sample_geojson
        
        map_obj = self.processor.create_focused_map("NonExistent Feature")
        
        assert isinstance(map_obj, folium.Map)
        # Should fallback to normal map
    
    # === Intelligent Zoom Tests ===
    
    def test_intelligent_zoom_single_feature(self):
        """Test zoom level calculation for single feature"""
        features = [self.sample_geojson["features"][0]]
        map_obj = self.processor.create_focused_map(["Helvetia Zurich"])
        
        assert map_obj.zoom_start == 16
    
    def test_intelligent_zoom_close_features(self):
        """Test zoom for close features"""
        # Create two very close features
        close_features = [
            "Helvetia Zurich",  # Same city
            "Zurich District"   # Same area  
        ]
        
        map_obj = self.processor.create_focused_map(close_features)
        
        # Should have high zoom for close features
        assert map_obj.zoom_start >= 12
    
    def test_intelligent_zoom_distant_features(self):
        """Test zoom for distant features"""
        distant_features = [
            "Helvetia Zurich",  # Zurich
            "Baloise Basel"     # Basel (different city)
        ]
        
        map_obj = self.processor.create_focused_map(distant_features)
        
        # Should have lower zoom for distant features  
        assert map_obj.zoom_start <= 12
    
    # === Coordinate Extraction Tests ===
    
    def test_extract_coords_recursive_polygon(self):
        """Test recursive coordinate extraction from polygon"""
        coords = [[8.5, 47.3], [8.6, 47.3], [8.6, 47.4], [8.5, 47.4], [8.5, 47.3]]
        lats, lons = [], []
        
        self.processor._extract_coords_recursive(coords, lats, lons)
        
        assert len(lats) == 5
        assert len(lons) == 5
        assert 47.3 in lats
        assert 8.5 in lons
    
    def test_extract_coords_recursive_nested(self):
        """Test recursive extraction from nested polygon structure"""
        nested_coords = [[[8.5, 47.3], [8.6, 47.3], [8.6, 47.4], [8.5, 47.4], [8.5, 47.3]]]
        lats, lons = [], []
        
        self.processor._extract_coords_recursive(nested_coords, lats, lons)
        
        assert len(lats) == 5
        assert len(lons) == 5
    
    # === Error Handling Tests ===
    
    def test_no_data_loaded(self):
        """Test behavior when no data is loaded"""
        # Don't load any data
        
        df = self.processor.extract_properties()
        assert df.empty
        
        count = self.processor.get_feature_count()
        assert count == 0
    
    def test_invalid_geometry_types(self):
        """Test handling of invalid or missing geometry"""
        invalid_geojson = {
            "type": "FeatureCollection", 
            "features": [
                {
                    "type": "Feature",
                    "geometry": None,  # Invalid geometry
                    "properties": {"name": "Invalid Feature"}
                }
            ]
        }
        
        self.processor.data = invalid_geojson
        
        # Should not crash
        map_obj = self.processor.create_map()
        assert isinstance(map_obj, folium.Map)
    
    # === Integration Tests ===
    
    def test_full_workflow(self):
        """Test complete workflow from load to export"""
        # Load data
        file_content = json.dumps(self.sample_geojson)
        mock_file = MagicMock()
        mock_file.read.return_value = file_content.encode('utf-8')
        
        success = self.processor.load_geojson(mock_file)
        assert success
        
        # Extract properties
        df = self.processor.extract_properties()
        assert len(df) > 0
        
        # Filter data
        filtered_df, count = self.processor.filter_data("type", "insurance")
        assert count == 2
        
        # Create map
        map_obj = self.processor.create_map("type", "insurance")
        assert isinstance(map_obj, folium.Map)
        
        # Export filtered data
        filtered_json = self.processor.create_filtered_geojson("type", "insurance")
        assert "FeatureCollection" in filtered_json
        
        # Verify export count
        export_count = self.processor.get_filtered_feature_count(filtered_json)
        assert export_count == 2 