from engine.loader import load_raw, load_cgu
from engine.raw_search import search_raw
from engine.cgu_search import search_cgu
from engine.cgu_explain import explain_cgu, print_explanation


def explain(query):
    raw = load_raw()
    cgu = load_cgu()

    raw_results = search_raw(raw, query)
    cgu_results = search_cgu(cgu, query)

    explanation = explain_cgu(cgu_results)
    print_explanation(explanation)


if __name__ == "__main__":
    q = input("Frage: ")
    explain(q)