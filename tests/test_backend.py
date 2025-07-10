"""
Unit tests for GeoJSONProcessor backend logic

Tests all core functionality of the backend without UI dependencies.
"""

import json
import pytest
import pandas as pd
from io import StringIO
from unittest.mock import mock_open, patch

from backend import GeoJSONProcessor


class TestGeoJSONProcessor:
    """Test suite for GeoJSONProcessor class"""
    
    @pytest.fixture
    def processor(self):
        """Create a fresh GeoJSONProcessor instance for each test"""
        return GeoJSONProcessor()
    
    @pytest.fixture
    def valid_geojson_file(self):
        """Load valid test GeoJSON data"""
        with open('tests/fixtures/test_data.json', 'r') as f:
            data = json.load(f)
        return StringIO(json.dumps(data))
    
    @pytest.fixture
    def invalid_geojson_file(self):
        """Load invalid test GeoJSON data"""
        with open('tests/fixtures/invalid_data.json', 'r') as f:
            data = json.load(f)
        return StringIO(json.dumps(data))
    
    @pytest.fixture
    def empty_properties_file(self):
        """Create GeoJSON with empty properties"""
        data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {"type": "Point", "coordinates": [0, 0]}
                }
            ]
        }
        return StringIO(json.dumps(data))

    def test_initialization(self, processor):
        """Test processor initializes with empty state"""
        assert processor.data == {}
        assert processor.prop_df.empty

    def test_load_valid_geojson(self, processor, valid_geojson_file):
        """Test loading valid GeoJSON data"""
        result = processor.load_geojson(valid_geojson_file)
        
        assert result is True
        assert "features" in processor.data
        assert len(processor.data["features"]) == 3
        assert processor.data["type"] == "FeatureCollection"

    def test_load_invalid_geojson_missing_features(self, processor, invalid_geojson_file):
        """Test loading GeoJSON without features array raises ValueError"""
        with pytest.raises(ValueError, match="keine gültigen GeoJSON‑Features"):
            processor.load_geojson(invalid_geojson_file)

    def test_load_invalid_json(self, processor):
        """Test loading malformed JSON raises ValueError"""
        invalid_json = StringIO('{"invalid": json}')
        
        with pytest.raises(ValueError, match="konnte nicht gelesen werden"):
            processor.load_geojson(invalid_json)

    def test_extract_properties_success(self, processor, valid_geojson_file):
        """Test extracting properties from valid GeoJSON"""
        processor.load_geojson(valid_geojson_file)
        result_df = processor.extract_properties()
        
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 3
        assert "name" in result_df.columns
        assert "company" in result_df.columns
        assert "city" in result_df.columns
        
        # Test specific values
        assert result_df.iloc[0]["name"] == "Helvetia Location"
        assert result_df.iloc[1]["company"] == "Baloise Group"

    def test_extract_properties_empty(self, processor, empty_properties_file):
        """Test extracting from GeoJSON with empty properties raises ValueError"""
        processor.load_geojson(empty_properties_file)
        
        with pytest.raises(ValueError, match="Keine Eigenschaften gefunden"):
            processor.extract_properties()

    def test_get_default_filter_column_with_name(self, processor, valid_geojson_file):
        """Test default filter column when 'name' exists"""
        processor.load_geojson(valid_geojson_file)
        processor.extract_properties()
        
        default_index = processor.get_default_filter_column()
        assert default_index == processor.prop_df.columns.get_loc("name")

    def test_get_default_filter_column_without_name(self, processor):
        """Test default filter column when 'name' doesn't exist"""
        # Create data without 'name' column
        processor.prop_df = pd.DataFrame({
            "company": ["Test Corp"],
            "city": ["Basel"]
        })
        
        default_index = processor.get_default_filter_column()
        assert default_index == 0

    def test_filter_data_with_pattern(self, processor, valid_geojson_file):
        """Test filtering data with regex pattern"""
        processor.load_geojson(valid_geojson_file)
        processor.extract_properties()
        
        filtered_df, count = processor.filter_data("company", "Helvetia")
        
        assert count == 1
        assert len(filtered_df) == 1
        assert filtered_df.iloc[0]["name"] == "Helvetia Location"

    def test_filter_data_case_insensitive(self, processor, valid_geojson_file):
        """Test filtering is case insensitive"""
        processor.load_geojson(valid_geojson_file)
        processor.extract_properties()
        
        filtered_df, count = processor.filter_data("company", "helvetia")
        
        assert count == 1
        assert filtered_df.iloc[0]["company"] == "Helvetia Insurance"

    def test_filter_data_regex_pattern(self, processor, valid_geojson_file):
        """Test filtering with regex pattern"""
        processor.load_geojson(valid_geojson_file)
        processor.extract_properties()
        
        # Filter for companies ending with "Group" or "Insurance"
        filtered_df, count = processor.filter_data("company", "(Group|Insurance)$")
        
        assert count == 2
        companies = filtered_df["company"].tolist()
        assert "Helvetia Insurance" in companies
        assert "Baloise Group" in companies

    def test_filter_data_empty_pattern(self, processor, valid_geojson_file):
        """Test filtering with empty pattern returns all data"""
        processor.load_geojson(valid_geojson_file)
        processor.extract_properties()
        
        filtered_df, count = processor.filter_data("name", "")
        
        assert count == 3
        assert len(filtered_df) == 3

    def test_filter_data_no_matches(self, processor, valid_geojson_file):
        """Test filtering with pattern that matches nothing"""
        processor.load_geojson(valid_geojson_file)
        processor.extract_properties()
        
        filtered_df, count = processor.filter_data("name", "NonExistent")
        
        assert count == 0
        assert len(filtered_df) == 0

    def test_filter_data_null_values(self, processor, valid_geojson_file):
        """Test filtering handles null values gracefully"""
        processor.load_geojson(valid_geojson_file)
        processor.extract_properties()
        
        # Filter on employees column which has null value
        filtered_df, count = processor.filter_data("employees", "200")
        
        assert count == 1
        assert filtered_df.iloc[0]["name"] == "Baloise Office"

    def test_create_filtered_geojson_with_pattern(self, processor, valid_geojson_file):
        """Test creating filtered GeoJSON with pattern"""
        processor.load_geojson(valid_geojson_file)
        processor.extract_properties()
        
        result_json = processor.create_filtered_geojson("company", "Helvetia")
        result_data = json.loads(result_json)
        
        assert result_data["type"] == "FeatureCollection"
        assert len(result_data["features"]) == 1
        assert result_data["features"][0]["properties"]["name"] == "Helvetia Location"

    def test_create_filtered_geojson_empty_pattern(self, processor, valid_geojson_file):
        """Test creating GeoJSON with empty pattern returns all features"""
        processor.load_geojson(valid_geojson_file)
        processor.extract_properties()
        
        result_json = processor.create_filtered_geojson("name", "")
        result_data = json.loads(result_json)
        
        assert len(result_data["features"]) == 3

    def test_create_filtered_geojson_no_matches(self, processor, valid_geojson_file):
        """Test creating GeoJSON with no matching pattern"""
        processor.load_geojson(valid_geojson_file)
        processor.extract_properties()
        
        result_json = processor.create_filtered_geojson("name", "NonExistent")
        result_data = json.loads(result_json)
        
        assert len(result_data["features"]) == 0

    def test_get_feature_count(self, processor, valid_geojson_file):
        """Test getting total feature count"""
        processor.load_geojson(valid_geojson_file)
        
        count = processor.get_feature_count()
        assert count == 3

    def test_get_feature_count_empty(self, processor):
        """Test getting feature count with no data"""
        count = processor.get_feature_count()
        assert count == 0

    def test_get_filtered_feature_count(self, processor, valid_geojson_file):
        """Test getting filtered feature count"""
        processor.load_geojson(valid_geojson_file)
        processor.extract_properties()
        
        filtered_json = processor.create_filtered_geojson("company", "Helvetia")
        count = processor.get_filtered_feature_count(filtered_json)
        
        assert count == 1

    def test_workflow_integration(self, processor, valid_geojson_file):
        """Test complete workflow integration"""
        # Load data
        processor.load_geojson(valid_geojson_file)
        
        # Extract properties
        prop_df = processor.extract_properties()
        assert not prop_df.empty
        
        # Get default column
        default_col = processor.get_default_filter_column()
        column_name = prop_df.columns[default_col]
        assert column_name == "name"
        
        # Filter data
        filtered_df, count = processor.filter_data(column_name, "Helvetia")
        assert count == 1
        
        # Create filtered GeoJSON
        filtered_json = processor.create_filtered_geojson(column_name, "Helvetia")
        filtered_data = json.loads(filtered_json)
        assert len(filtered_data["features"]) == 1
        
        # Verify feature count
        feature_count = processor.get_filtered_feature_count(filtered_json)
        assert feature_count == 1


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_missing_properties_in_feature(self):
        """Test handling features without properties"""
        processor = GeoJSONProcessor()
        data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]}
                    # Missing properties
                }
            ]
        }
        
        file_obj = StringIO(json.dumps(data))
        processor.load_geojson(file_obj)
        
        with pytest.raises(ValueError, match="Keine Eigenschaften gefunden"):
            processor.extract_properties()

    def test_filter_nonexistent_column(self):
        """Test filtering on non-existent column"""
        processor = GeoJSONProcessor()
        processor.prop_df = pd.DataFrame({"name": ["Test"]})
        
        # Should not raise error, just return empty results
        filtered_df, count = processor.filter_data("nonexistent", "pattern")
        assert count == 0
        assert len(filtered_df) == 0 