import json

def explain_cgu(results):
    """
    results = Output von search_cgu()
    Erwartet: Liste von Units aus cgu_builder
    """

    explanation = {}

    for r in results:
        section = r.get("section", "Unknown section")
        topic = r.get("topic", "Unknown topic")
        data = r.get("data", {})

        if section not in explanation:
            explanation[section] = []

        explanation[section].append({
            "topic": topic,
            "data": data
        })

    return explanation


def print_explanation(explanation):
    print("\n" + "=" * 60)
    print("📘 ERKLÄRUNG")
    print("=" * 60 + "\n")

    for section, items in explanation.items():
        print(f"\n🧩 {section}")
        print("-" * 60)

        for item in items:
            topic = item.get("topic", "")
            data = item.get("data", {})

            print(f"\n▶ {topic}\n")

            # ─────────────────────────────
            # 1. NOTES (alle Varianten)
            # ─────────────────────────────
            for key in ["notes", "note", "notes2"]:
                if key in data:
                    val = data[key]
                    if isinstance(val, list):
                        print("💡 Hinweise:")
                        for n in val:
                            print(f"  - {n}")
                    else:
                        print(f"💡 Hinweis: {val}")

            # ─────────────────────────────
            # 2. TABLES (alle Keys automatisch)
            # ─────────────────────────────
            for key, value in data.items():
                if isinstance(value, dict):
                    if "columns" in value and "rows" in value:
                        print(f"\n📊 Tabelle ({key}):")
                        print(" | ".join(value["columns"]))
                        print("-" * 60)
                        for row in value["rows"]:
                            print(" | ".join(row))

            # ─────────────────────────────
            # 3. LISTEN / EXAMPLES / ENTRIES
            # ─────────────────────────────
            for key, value in data.items():
                if isinstance(value, list) and key not in ["rows"]:
                    # entries / examples / etc.
                    if all(isinstance(x, dict) for x in value):
                        print(f"\n📌 {key}:")
                        for item2 in value:
                            print(" - " + " | ".join(str(v) for v in item2.values()))
                    else:
                        print(f"\n📌 {key}:")
                        for x in value:
                            print(f" - {x}")

            print("\n" + "-" * 60)