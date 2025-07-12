"""
Translation Manager for GeoJSON Viewer Application

This module provides translation capabilities with English as the default language.
"""

import json
import os
import streamlit as st
from typing import Dict, Any


class TranslationManager:
    """Manages translations for the GeoJSON Viewer application"""
    
    def __init__(self, default_language: str = "en"):
        """Initialize translation manager with default language (English)"""
        self.default_language = default_language
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()
        
        # Initialize session state for language if not exists
        if "app_language" not in st.session_state:
            st.session_state.app_language = default_language
    
    def load_translations(self):
        """Load all translation files from the translations directory"""
        translations_dir = "translations"
        
        if not os.path.exists(translations_dir):
            # Create empty translations if directory doesn't exist
            self.translations = {
                "en": {},
                "de": {}
            }
            return
        
        # Load English translations
        en_file = os.path.join(translations_dir, "translations_en.json")
        if os.path.exists(en_file):
            with open(en_file, 'r', encoding='utf-8') as f:
                self.translations["en"] = json.load(f)
        
        # Load German translations
        de_file = os.path.join(translations_dir, "translations_de.json")
        if os.path.exists(de_file):
            with open(de_file, 'r', encoding='utf-8') as f:
                self.translations["de"] = json.load(f)
    
    def get_current_language(self) -> str:
        """Get the current selected language"""
        return st.session_state.get("app_language", self.default_language)
    
    def set_language(self, language_code: str):
        """Set the current language"""
        if language_code in self.translations:
            st.session_state.app_language = language_code
    
    def get_text(self, key: str, **kwargs) -> str:
        """Get translated text for the given key in the current language"""
        current_lang = self.get_current_language()
        
        # Try to get text in current language
        if current_lang in self.translations:
            text = self.translations[current_lang].get(key)
            if text:
                # Format text with provided kwargs
                try:
                    return text.format(**kwargs)
                except (KeyError, ValueError):
                    return text
        
        # Fallback to default language
        if self.default_language in self.translations:
            text = self.translations[self.default_language].get(key)
            if text:
                try:
                    return text.format(**kwargs)
                except (KeyError, ValueError):
                    return text
        
        # Ultimate fallback - return the key itself
        return key
    
    def render_language_selector(self):
        """Render the language selector in the sidebar"""
        st.sidebar.markdown("---")
        
        # Language options
        language_options = {
            "en": "🇺🇸 English",
            "de": "🇩🇪 Deutsch"
        }
        
        current_lang = self.get_current_language()
        
        # Create selectbox for language selection
        selected_lang = st.sidebar.selectbox(
            self.get_text("language_selector"),
            options=list(language_options.keys()),
            format_func=lambda x: language_options[x],
            index=0 if current_lang == "en" else 1,
            key="language_selectbox"
        )
        
        # Update language if changed
        if selected_lang != current_lang:
            self.set_language(selected_lang)
            st.rerun()
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages with their display names"""
        return {
            "en": "English",
            "de": "Deutsch"
        } 