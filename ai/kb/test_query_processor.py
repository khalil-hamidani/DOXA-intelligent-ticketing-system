from query_processor import QueryProcessor

qp = QueryProcessor()

query = "Combien de projets puis-je créer avec mon plan ?"
print("Original:", query)

cleaned = qp.clean(query)
print("Cleaned:", cleaned)

keywords = qp.keywords(cleaned)
print("Keywords:", keywords)

augmented = qp.augment(query)
print("Augmented:", augmented)
