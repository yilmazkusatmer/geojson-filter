"""
Backend Logic for GeoJSON Processing

This module contains the GeoJSONProcessor class which handles all data processing,
filtering, and manipulation operations for GeoJSON files.
"""

import json
import re
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd
import folium
from translation_manager import TranslationManager


class GeoJSONProcessor:
    """Backend logic for processing GeoJSON data"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.prop_df: pd.DataFrame = pd.DataFrame()
        self.translator = TranslationManager(default_language="en")
    
    def load_geojson(self, uploaded_file) -> bool:
        """Load and validate GeoJSON data"""
        try:
            self.data = json.load(uploaded_file)
        except Exception as e:
            raise ValueError(self.translator.get_text("file_read_error", error=str(e)))
        
        if "features" not in self.data or not isinstance(self.data["features"], list):
            raise ValueError(self.translator.get_text("invalid_geojson"))
        
        return True
    
    def extract_properties(self) -> pd.DataFrame:
        """Extract properties from GeoJSON features into DataFrame"""
        self.prop_df = pd.DataFrame([f.get("properties", {}) for f in self.data["features"]])
        
        if self.prop_df.empty:
            raise ValueError(self.translator.get_text("no_properties_found"))
        
        return self.prop_df
    
    def get_default_filter_column(self) -> int:
        """Get default column index for filtering (prefer 'name' if exists)"""
        if "name" in self.prop_df.columns:
            return self.prop_df.columns.get_loc("name")
        return 0
    
    def filter_data(self, column: str, pattern: str) -> Tuple[pd.DataFrame, int]:
        """Filter data based on regex pattern"""
        if not pattern:
            return self.prop_df, len(self.prop_df)
        
        # Handle non-existent columns gracefully
        if column not in self.prop_df.columns:
            empty_df = self.prop_df.iloc[0:0]  # Empty DataFrame with same structure
            return empty_df, 0
        
        mask = self.prop_df[column].astype(str).str.contains(
            pattern, flags=re.IGNORECASE, regex=True, na=False
        )
        filtered_df = self.prop_df[mask]
        return filtered_df, len(filtered_df)
    
    def create_filtered_geojson(self, column: str, pattern: str) -> str:
        """Create filtered GeoJSON as JSON string"""
        filtered_geojson = self.data.copy()
        
        if pattern:
            filtered_geojson["features"] = [
                feat for feat in self.data["features"]
                if re.search(pattern, str(feat.get("properties", {}).get(column, "")), re.IGNORECASE)
            ]
        
        return json.dumps(filtered_geojson, ensure_ascii=False, indent=2)
    
    def get_feature_count(self) -> int:
        """Get total number of features"""
        return len(self.data.get("features", []))
    
    def get_filtered_feature_count(self, filtered_json: str) -> int:
        """Get count of features in filtered GeoJSON"""
        return len(json.loads(filtered_json)["features"])
    
    def calculate_map_bounds(self) -> Tuple[float, float]:
        """Calculate center coordinates for map based on all features"""
        return self.calculate_filtered_map_bounds(self.data.get("features", []))
    
    def calculate_filtered_map_bounds(self, features: List[Dict[str, Any]]) -> Tuple[float, float]:
        """Calculate center coordinates for map based on specific features"""
        lats, lons = [], []
        
        for feature in features:
            geometry = feature.get("geometry", {})
            if geometry.get("type") == "Point":
                coords = geometry.get("coordinates", [])
                if len(coords) >= 2:
                    lons.append(coords[0])
                    lats.append(coords[1])
            elif geometry.get("type") in ["Polygon", "MultiPolygon"]:
                # Extract all coordinates from polygon/multipolygon
                coords = geometry.get("coordinates", [])
                self._extract_coords_recursive(coords, lats, lons)
                
                # Also use center point if available for better centering
                properties = feature.get("properties", {})
                center_data = properties.get("center", {})
                if center_data.get("type") == "Point":
                    center_coords = center_data.get("coordinates", [])
                    if len(center_coords) >= 2:
                        lons.append(center_coords[0])
                        lats.append(center_coords[1])
        
        if not lats or not lons:
            # Default to Germany center if no coordinates found
            return 51.1657, 10.4515
        
        return sum(lats) / len(lats), sum(lons) / len(lons)
    
    def _extract_coords_recursive(self, coords, lats, lons):
        """Recursively extract coordinates from nested structures"""
        if isinstance(coords, list) and len(coords) > 0:
            if isinstance(coords[0], (int, float)):
                # This is a coordinate pair [lon, lat]
                if len(coords) >= 2:
                    lons.append(coords[0])
                    lats.append(coords[1])
            else:
                # This is a nested structure, recurse
                for item in coords:
                    self._extract_coords_recursive(item, lats, lons)
    
    def _calculate_intelligent_zoom(self, features: List[Dict[str, Any]]) -> int:
        """Calculate intelligent zoom level based on geographic extent and feature characteristics"""
        if not features:
            return 10  # Default zoom for no features
        
        feature_count = len(features)
        
        # Extract all coordinates from features
        lats, lons = [], []
        has_large_polygons = False
        
        for feature in features:
            geometry = feature.get("geometry", {})
            geom_type = geometry.get("type", "")
            
            if geom_type == "Point":
                coords = geometry.get("coordinates", [])
                if len(coords) >= 2:
                    lons.append(coords[0])
                    lats.append(coords[1])
            elif geom_type in ["Polygon", "MultiPolygon"]:
                # Extract all polygon coordinates
                self._extract_coords_recursive(geometry.get("coordinates", []), lats, lons)
                
                # Check if this is a large polygon (like a state/country)
                if lats and lons:
                    temp_lat_range = max(lats) - min(lats) if len(lats) > 1 else 0
                    temp_lon_range = max(lons) - min(lons) if len(lons) > 1 else 0
                    if temp_lat_range > 0.5 or temp_lon_range > 0.5:  # Large polygon detected
                        has_large_polygons = True
                
                # Also use center point if available for better centering
                properties = feature.get("properties", {})
                center_data = properties.get("center", {})
                if center_data.get("type") == "Point":
                    center_coords = center_data.get("coordinates", [])
                    if len(center_coords) >= 2:
                        lons.append(center_coords[0])
                        lats.append(center_coords[1])
        
        # Calculate geographic spread
        if not lats or not lons:
            return 10  # Default zoom if no coordinates
        
        lat_range = max(lats) - min(lats) if len(lats) > 1 else 0
        lon_range = max(lons) - min(lons) if len(lons) > 1 else 0
        max_range = max(lat_range, lon_range)
        
        # Intelligent zoom algorithm considering:
        # 1. Feature count
        # 2. Geographic spread
        # 3. Presence of large polygons (states, countries, etc.)
        
        if has_large_polygons:
            # Special handling for large polygons like states/countries
            if feature_count == 1:
                if max_range > 5.0:  # Very large polygon (country-sized)
                    return 5
                elif max_range > 2.0:  # Large polygon (state-sized)
                    return 7
                elif max_range > 1.0:  # Medium polygon (region-sized)
                    return 8
                else:  # Small polygon (city-sized)
                    return 10
            else:
                # Multiple large polygons - zoom out more
                return max(4, 7 - feature_count // 2)
        
        # Standard zoom logic for points and small polygons
        if feature_count == 1:
            if max_range < 0.001:  # Very small area
                return 16
            elif max_range < 0.01:  # Small area
                return 14
            elif max_range < 0.1:  # Medium area
                return 12
            else:  # Large area
                return 10
        elif feature_count <= 3:
            if max_range < 0.01:  # Very close features
                return 14
            elif max_range < 0.1:  # Close features
                return 12
            elif max_range < 0.5:  # Medium spread
                return 10
            else:  # Large spread
                return 8
        elif feature_count <= 10:
            if max_range < 0.1:  # Close features
                return 11
            elif max_range < 1.0:  # Medium spread
                return 9
            else:  # Large spread
                return 7
        elif feature_count <= 50:
            if max_range < 0.5:  # Close features
                return 9
            elif max_range < 2.0:  # Medium spread
                return 7
            else:  # Large spread
                return 5
        else:
            # Many features - wide overview
            return max(4, 8 - feature_count // 20)
    
    def create_map(self, column: str = "", pattern: str = "") -> folium.Map:
        """Create a Folium map with GeoJSON features"""
        # Determine which features to show first
        features_to_show = self.data.get("features", [])
        
        if pattern and column:
            # Filter features based on pattern
            features_to_show = [
                feat for feat in features_to_show
                if re.search(pattern, str(feat.get("properties", {}).get(column, "")), re.IGNORECASE)
            ]
        
        # Calculate center based on FILTERED features, not all features
        center_lat, center_lon = self.calculate_filtered_map_bounds(features_to_show)
        
        # Calculate intelligent zoom based on geographic extent AND feature count
        zoom_level = self._calculate_intelligent_zoom(features_to_show)
        
        # Create base map with intelligent zoom level
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_level,
            tiles='OpenStreetMap'
        )
        
        # Add features to map
        for feature in features_to_show:
            self._add_feature_to_map(m, feature)
        
        return m
    
    def create_focused_map(self, feature_names, column: str = "name") -> folium.Map:
        """Create a map focused on specific feature(s) by name - supports single string or list"""
        # Handle both single feature and multiple features
        if isinstance(feature_names, str):
            feature_names = [feature_names]
        elif not isinstance(feature_names, list):
            # Fallback to normal map if invalid input
            return self.create_map()
        
        # Find the target features
        target_features = []
        for feature in self.data.get("features", []):
            properties = feature.get("properties", {})
            feature_name = properties.get(column, "")
            if feature_name in feature_names:
                target_features.append(feature)
        
        if not target_features:
            # Fallback to normal map if no features found
            return self.create_map()
        
        # Calculate center coordinates for ALL selected features
        center_lat, center_lon = self.calculate_filtered_map_bounds(target_features)
        
        # Calculate intelligent zoom based on geographic extent AND feature count
        zoom_level = self._calculate_intelligent_zoom(target_features)
        
        # Create map with intelligent zoom
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_level,
            tiles='OpenStreetMap'
        )
        
        # Add all selected features with highlight
        for feature in target_features:
            self._add_feature_to_map(m, feature, highlight=True)
        
        return m
    
    def _add_feature_to_map(self, m: folium.Map, feature: Dict[str, Any], highlight: bool = False):
        """Add a single GeoJSON feature to the map"""
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        

        
        # Create popup text from properties
        popup_text = "<br>".join([
            f"<b>{key}:</b> {value}" 
            for key, value in properties.items() 
            if value is not None and value != ""
        ])
        
        if popup_text == "":
            popup_text = "No properties available"
        
        if geometry.get("type") == "Point":
            coords = geometry.get("coordinates", [])
            if len(coords) >= 2:
                lat, lon = coords[1], coords[0]  # lat, lon
                
                # Choose colors based on highlight
                if highlight:
                    color, fill_color, radius = 'orange', 'yellow', 20
                else:
                    color, fill_color, radius = 'darkred', 'red', 15
                
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=radius,
                    popup=folium.Popup(popup_text, max_width=300),
                    color=color,
                    fillColor=fill_color,
                    fillOpacity=0.9,
                    weight=4
                ).add_to(m)
        
        elif geometry.get("type") in ["Polygon", "MultiPolygon"]:
            # Choose colors based on highlight
            if highlight:
                fill_color, border_color, weight, opacity = '#ffff00', '#ff8800', 6, 1.0
            else:
                fill_color, border_color, weight, opacity = '#ff4444', '#cc0000', 5, 0.9
            
            # Use folium.GeoJson for polygon geometries with high visibility
            folium.GeoJson(
                feature,
                popup=folium.Popup(popup_text, max_width=300),
                style_function=lambda x: {
                    'fillColor': fill_color,
                    'color': border_color,
                    'weight': weight,
                    'fillOpacity': opacity,
                    'opacity': 1.0
                }
            ).add_to(m)
            
            # Also add center point for better visibility of small polygons
            center_data = properties.get("center", {})
            if center_data.get("type") == "Point":
                center_coords = center_data.get("coordinates", [])
                if len(center_coords) >= 2:
                    center_lat, center_lon = center_coords[1], center_coords[0]
                    folium.CircleMarker(
                        location=[center_lat, center_lon],
                        radius=8,
                        popup=folium.Popup(popup_text, max_width=300),
                        color='darkred',
                        fillColor='yellow',
                        fillOpacity=1.0,
                        weight=2
                    ).add_to(m) 