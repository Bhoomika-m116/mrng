import requests
import html
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English", "native": "English (Original)", "flag": "🇬🇧"},
    {"code": "hi", "name": "Hindi", "native": "हिन्दी (Hindi)", "flag": "🇮🇳"},
    {"code": "te", "name": "Telugu", "native": "తెలుగు (Telugu)", "flag": "🇮🇳"},
    {"code": "ta", "name": "Tamil", "native": "தமிழ் (Tamil)", "flag": "🇮🇳"},
    {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ (Kannada)", "flag": "🇮🇳"},
    {"code": "ml", "name": "Malayalam", "native": "മലയാളം (Malayalam)", "flag": "🇮🇳"},
    {"code": "bn", "name": "Bengali", "native": "বাংলা (Bengali)", "flag": "🇮🇳"},
    {"code": "mr", "name": "Marathi", "native": "मराठी (Marathi)", "flag": "🇮🇳"},
    {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી (Gujarati)", "flag": "🇮🇳"},
    {"code": "pa", "name": "Punjabi", "native": "ਪੰਜਾਬੀ (Punjabi)", "flag": "🇮🇳"},
    {"code": "ur", "name": "Urdu", "native": "اردو (Urdu)", "flag": "🇵🇰"},
    {"code": "es", "name": "Spanish", "native": "Español (Spanish)", "flag": "🇪🇸"},
    {"code": "fr", "name": "French", "native": "Français (French)", "flag": "🇫🇷"},
    {"code": "de", "name": "German", "native": "Deutsch (German)", "flag": "🇩🇪"},
    {"code": "ar", "name": "Arabic", "native": "العربية (Arabic)", "flag": "🇸🇦"},
    {"code": "zh-CN", "name": "Chinese", "native": "中文 (Chinese)", "flag": "🇨🇳"},
    {"code": "ja", "name": "Japanese", "native": "日本語 (Japanese)", "flag": "🇯🇵"},
    {"code": "ru", "name": "Russian", "native": "Русский (Russian)", "flag": "🇷🇺"},
    {"code": "pt", "name": "Portuguese", "native": "Português (Portuguese)", "flag": "🇵🇹"},
    {"code": "it", "name": "Italian", "native": "Italiano (Italian)", "flag": "🇮🇹"},
    {"code": "ko", "name": "Korean", "native": "한국어 (Korean)", "flag": "🇰🇷"},
    {"code": "tr", "name": "Turkish", "native": "Türkçe (Turkish)", "flag": "🇹🇷"},
    {"code": "id", "name": "Indonesian", "native": "Bahasa Indonesia", "flag": "🇮🇩"},
    {"code": "vi", "name": "Vietnamese", "native": "Tiếng Việt", "flag": "🇻🇳"},
]

# Language code alias mappings (e.g. zh -> zh-CN)
LANG_ALIASES = {
    "zh": "zh-CN",
    "cn": "zh-CN",
    "in": "hi"
}

_TRANSLATION_CACHE = {}

class MultilingualTranslator:
    def __init__(self):
        self.supported = SUPPORTED_LANGUAGES

    def get_supported_languages(self):
        return self.supported

    def get_lang_meta(self, lang_code):
        clean_code = LANG_ALIASES.get(lang_code.lower().strip(), lang_code.strip())
        for lang in self.supported:
            if lang["code"].lower() == clean_code.lower():
                return lang
        return {"code": lang_code, "name": lang_code.upper(), "native": lang_code.upper(), "flag": "🌐"}

    def translate_sentences(self, sentences, target_lang="en", source_lang="en"):
        """
        Translates a list of summary sentences to target native language using fast batching.
        """
        if not sentences:
            return []

        clean_target = LANG_ALIASES.get(target_lang.lower().strip(), target_lang.lower().strip())
        if clean_target == "en":
            return sentences

        # Filter out empty sentences but preserve indices
        non_empty = [(i, s.strip()) for i, s in enumerate(sentences) if s.strip()]
        if not non_empty:
            return sentences

        results = list(sentences)

        # Batch translation in one call using newline separators for blazing fast response (< 2 sec)
        joined_text = "\n\n".join([item[1] for item in non_empty])
        translated_blob = self.translate_text(joined_text, target_lang=clean_target, source_lang=source_lang)
        
        split_translated = [part.strip() for part in translated_blob.split("\n\n") if part.strip()]

        if len(split_translated) == len(non_empty):
            for idx, (orig_pos, _) in enumerate(non_empty):
                results[orig_pos] = split_translated[idx]
            return results

        # Fallback to parallel concurrent translation if batch splitting count differed
        with ThreadPoolExecutor(max_workers=min(len(non_empty), 6)) as executor:
            trans_list = list(executor.map(lambda item: self.translate_text(item[1], target_lang=clean_target, source_lang=source_lang), non_empty))

        for idx, (orig_pos, _) in enumerate(non_empty):
            if idx < len(trans_list) and trans_list[idx]:
                results[orig_pos] = trans_list[idx]

        return results

    def translate_text(self, text, target_lang="en", source_lang="en"):
        """
        Translates text to target native language using multi-provider fallback.
        Cached in-memory for instant 0ms retrieval on second access.
        """
        if not text or not text.strip():
            return ""

        target_lang = LANG_ALIASES.get(target_lang.lower().strip(), target_lang.lower().strip())
        source_lang = source_lang.lower().strip()

        if target_lang == "en" and source_lang == "en":
            return text

        cache_key = (hash(text), target_lang)
        if cache_key in _TRANSLATION_CACHE:
            return _TRANSLATION_CACHE[cache_key]

        translated = self._fetch_translation(text, target_lang, source_lang)
        _TRANSLATION_CACHE[cache_key] = translated
        return translated

    def _fetch_translation(self, text, target_lang, source_lang="en"):
        """
        Executes robust translation using MyMemory API with user-agent, fallback to deep_translator.
        """
        clean_text = text.strip()

        # If text is over 500 characters, chunk cleanly by paragraphs
        if len(clean_text) > 480:
            parts = [p.strip() for p in clean_text.split("\n\n") if p.strip()]
            if len(parts) > 1:
                translated_parts = [self._fetch_translation(p, target_lang, source_lang) for p in parts]
                return "\n\n".join(translated_parts)

        # Provider 1: MyMemory Translated API
        try:
            langpair = f"{source_lang}|{target_lang}"
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": clean_text,
                "langpair": langpair,
                "de": "legallens_practitioner@judicial.org" # Custom contact parameter lifts rate limit to 50,000 chars/day
            }
            resp = requests.get(url, params=params, timeout=7)
            if resp.status_code == 200:
                data = resp.json()
                if "responseData" in data and "translatedText" in data["responseData"]:
                    trans = data["responseData"]["translatedText"]
                    if trans and not trans.startswith("MYMEMORY WARNING"):
                        return html.unescape(trans)
        except Exception:
            pass

        # Provider 2: Deep-Translator fallback
        try:
            from deep_translator import GoogleTranslator
            dt_result = GoogleTranslator(source=source_lang, target=target_lang).translate(clean_text)
            if dt_result and dt_result.strip():
                return html.unescape(dt_result)
        except Exception:
            pass

        # Provider 3: Lingva translate mirror
        try:
            lingva_url = f"https://lingva.ml/api/v1/{source_lang}/{target_lang}/{urllib.parse.quote(clean_text)}"
            resp = requests.get(lingva_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "translation" in data and data["translation"]:
                    return html.unescape(data["translation"])
        except Exception:
            pass

        # Fallback to original text if offline
        return text
