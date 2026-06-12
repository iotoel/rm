def search_raw(raw_data, query: str):
    query = query.lower().strip()
    results = []
    seen = set()

    for section in raw_data.get("sections", []):
        section_title = section.get("title", "")

        for topic in section.get("topics", []):
            topic_title = topic.get("title", "")

            key = (section_title, topic_title)
            if key in seen:
                continue

            topic_text = topic_title.lower()
            section_text = section_title.lower()

            # ❗ STRICTER MATCH (wichtig!)
            matched = False

            if query in topic_text:
                matched = True

            # optional: section match nur wenn topic auch leicht passt
            elif query in section_text and query in topic_text:
                matched = True

            # fallback: nur wenn wirklich Inhalt passt
            else:
                haystack = str(topic).lower()
                if query in haystack:
                    matched = True

            if matched:
                seen.add(key)
                results.append({
                    "section": section_title,
                    "topic": topic_title,
                    "data": topic   # 👈 WICHTIG: FULL DATA
                })

    return results