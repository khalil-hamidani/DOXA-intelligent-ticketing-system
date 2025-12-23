import re

class QueryProcessor:

    def clean(self, query: str) -> str:
        query = query.lower().strip()
        query = re.sub(r"[^\w\s]", "", query)
        return query

    def keywords(self, query: str):
        stopwords = {
            "le", "la", "les", "de", "des", "du",
            "un", "une", "et", "ou", "pour",
            "comment", "quoi", "est", "sont"
        }
        words = query.split()
        return [w for w in words if w not in stopwords and len(w) > 2]

    def augment(self, query: str) -> str:
        cleaned = self.clean(query)
        keywords = self.keywords(cleaned)
        return " ".join(keywords)
