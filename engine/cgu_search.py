def search_cgu(cgu, query: str):
    q = query.lower().strip().split()

    results = []

    for unit in cgu.get("units", []):
        topic = unit.get("topic", "").lower()
        section = unit.get("section", "").lower()

        # 🔍 Match-Bedingung: alle Query-Wörter müssen irgendwo vorkommen
        text = f"{topic} {section}"

        if all(word in text for word in q):
            results.append(unit)

    return results