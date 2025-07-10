"""
Backend Logic for GeoJSON Processing

This module contains the GeoJSONProcessor class which handles all data processing,
filtering, and manipulation operations for GeoJSON files.
"""

import json
import re
from typing import Dict, List, Any, Tuple

import pandas as pd


class GeoJSONProcessor:
    """Backend logic for processing GeoJSON data"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.prop_df: pd.DataFrame = pd.DataFrame()
    
    def load_geojson(self, uploaded_file) -> bool:
        """Load and validate GeoJSON data"""
        try:
            self.data = json.load(uploaded_file)
        except Exception as e:
            raise ValueError(f"Die Datei konnte nicht gelesen werden: {e}")
        
        if "features" not in self.data or not isinstance(self.data["features"], list):
            raise ValueError("Die Datei enthält keine gültigen GeoJSON‑Features.")
        
        return True
    
    def extract_properties(self) -> pd.DataFrame:
        """Extract properties from GeoJSON features into DataFrame"""
        self.prop_df = pd.DataFrame([f.get("properties", {}) for f in self.data["features"]])
        
        if self.prop_df.empty:
            raise ValueError("Keine Eigenschaften gefunden – nichts darzustellen.")
        
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