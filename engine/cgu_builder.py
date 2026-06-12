import hashlib

def make_id(*parts):
    return hashlib.md5("::".join(parts).encode("utf-8")).hexdigest()


def build_cgu(raw):
    units = []

    for section in raw.get("sections", []):
        section_title = section.get("title", "")
        section_id = section.get("id", "")

        for topic in section.get("topics", []):
            topic_title = topic.get("title", "")

            unit_id = make_id(section_id, topic_title)

            units.append({
                "id": unit_id,
                "section": section_title,
                "topic": topic_title,
                "data": topic
            })

    return {"units": units}