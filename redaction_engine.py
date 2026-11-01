import re


class RedactionEngine:

    def __init__(self, settings):
        self.update_settings(settings)

    def update_settings(self, settings):
        custom_words = settings.get("custom_words", [])

        # Make sure custom_words is always a list
        if isinstance(custom_words, str):
            custom_words = [custom_words]

        self.custom_words = custom_words

        self.replacement = settings.get(
            "replacement",
            "[REDACTED]"
        )

        self.detectors = settings.get(
            "detectors",
            {}
        )

    def redact(self, text):
        if not text:
            return text, 0

        result = text
        count = 0

        # Custom words
        result, matches = self._redact_custom_words(result)
        count += matches

        # Built-in detectors
        if self.detectors.get("jwt", False):
            result, matches = self._redact_jwt(result)
            count += matches

        if self.detectors.get("api_keys", False):
            result, matches = self._redact_api_keys(result)
            count += matches

        if self.detectors.get("email", False):
            result, matches = self._redact_email(result)
            count += matches

        if self.detectors.get("phone", False):
            result, matches = self._redact_phone(result)
            count += matches

        if self.detectors.get("ipv4", False):
            result, matches = self._redact_ipv4(result)
            count += matches

        return result, count

    def _redact_custom_words(self, text):
        count = 0

        # Match longer custom words first
        for word in sorted(
            self.custom_words,
            key=len,
            reverse=True
        ):
            if not isinstance(word, str):
                continue

            word = word.strip()

            if not word:
                continue

            # Literal substring matching, case-insensitive.
            # No word boundaries are used intentionally.
            pattern = re.escape(word)

            text, replacements = re.subn(
                pattern,
                self.replacement,
                text,
                flags=re.IGNORECASE
            )

            count += replacements

        return text, count

    def _redact_jwt(self, text):
        pattern = re.compile(
            r"\beyJ[a-zA-Z0-9_-]+\."
            r"[a-zA-Z0-9_-]+\."
            r"[a-zA-Z0-9_-]+\b"
        )

        return pattern.subn(
            self.replacement,
            text
        )

    def _redact_api_keys(self, text):
        patterns = [
            r"\bsk-[a-zA-Z0-9_-]{20,}\b",
            r"\bAKIA[0-9A-Z]{16}\b",
            r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"
        ]

        count = 0

        for pattern_text in patterns:
            pattern = re.compile(pattern_text)

            text, matches = pattern.subn(
                self.replacement,
                text
            )

            count += matches

        return text, count

    def _redact_email(self, text):
        pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\."
            r"[A-Za-z]{2,}\b"
        )

        return pattern.subn(
            self.replacement,
            text
        )

    def _redact_phone(self, text):
        pattern = re.compile(
            r"(?<!\d)"
            r"(?:\+91[\s-]?)?"
            r"[6-9]\d{9}"
            r"(?!\d)"
        )

        return pattern.subn(
            self.replacement,
            text
        )

    def _redact_ipv4(self, text):
        pattern = re.compile(
            r"\b"
            r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"
            r"(?:\."
            r"(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}"
            r"\b"
        )

        return pattern.subn(
            self.replacement,
            text
        )