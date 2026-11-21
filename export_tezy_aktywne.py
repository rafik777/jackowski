#!/usr/bin/env python3
"""
Export a JSON subset of predictions from jackowski.db whose `horyzont_czasowy`
has already elapsed (`minal`) or is currently underway (`w_trakcie`) as of 2026-11-21.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "jackowski.db"
REF_DATE = "2026-11-21"
OUT_JSON = BASE_DIR / f"tezy_minione_i_w_trakcie_{REF_DATE}.json"

# Explicit classification for all fixed horyzont_czasowy strings as of 2026-11-21
EXACT_MINAL = {
    "11–16 czerwca 2026",
    "13 października 2026 (następny dzień)",
    "20 sierpnia – 20 września 2026",
    "2026 rok (przed sierpniem / wrześniem 2026)",
    "9–17 września 2026",
    "czerwiec 2026",
    "do jesieni 2026",
    "do końca czerwca 2026",
    "druga część lata 2026",
    "lato 2026",
    "lato 2026 (okres wielkich upałów)",
    "lato 2026 (po mistrzostwach świata w piłce nożnej)",
    "lato 2026 (w trakcie mistrzostw świata)",
    "lato 2026 (ze szczególnym wskazaniem na piątek 12 czerwca / noc z 12 na 13 czerwca)",
    "lipiec 2026",
    "mistrzostwa świata w piłce nożnej 2026",
    "najbliższe 3 dni (czerwiec 2026)",
    "najbliższe 5 dni (czerwiec 2026)",
    "ok. 28 sierpnia 2026",
    "po eskalacji w Iranie (lato 2026)",
    "początek lata 2026",
    "początek lipca 2026",
    "przed mistrzostwami świata w USA (2026)",
    "przyszły tydzień (środa)",  # wypowiedziane 2026-10-31 -> 2026-11-04
    "upalne dni (lato 2026)",
    "wrzesień 2026",
    "za około 40 dni (końcówka lipca 2026, ok. 25 lipca)",
}

EXACT_W_TRAKCIE = {
    "2026",
    "2026 rok",
    "2026–2028",
    "20–22 września 2026 / jesień 2026",
    "bardzo krótki okres czasu / niedługi czas",
    "do 2028",
    "do 2028 roku",
    "do 2031",
    "do 8 lat",
    "do końca 2026 roku",
    "do końca 2028",
    "do listopada 2026 / listopad 2026",
    "do późnej jesieni 2026",
    "druga połowa listopada 2026",
    "drugie półrocze 2026",
    "jesień 2026",
    "jesień 2026 (połowa października – listopad)",
    "jesień 2026 / nieokreślony",
    "jesień i zima 2026/2027",
    "jeszcze w 2026 roku",
    "kilka miesięcy",
    "koniec 2026",
    "koniec 2026 / przełom listopada i grudnia 2026",
    "koniec lata lub jesień 2026",
    "lada moment",
    "listopad 2026",
    "listopad 2026 / jesień i zima 2026/2027",
    "listopad 2026 lub listopad 2027",
    "listopad 2026 – marzec/kwiecień 2027",
    "najbliższe 10 lat",
    "najbliższe 10–15 dni; kulminacja w połowie listopada 2026",
    "najbliższe 5 lat (do 2031)",
    "najbliższe 8 miesięcy",
    "najbliższe dwa lata (do końca 2028)",
    "najbliższe kilka lat",
    "najbliższe kilka miesięcy (od czerwca 2026)",
    "najbliższe lata",
    "najbliższe lata / do 2031",
    "najbliższe miesiące",
    "najbliższe miesiące (przed końcem kadencji)",
    "od 11 września 2026",
    "od 22 września 2026",
    "od jesieni 2026",
    "od listopada 2026",
    "od połowy listopada / koniec 2026",
    "od połowy listopada 2026",
    "od połowy listopada 2026 do końca 2027",
    "od połowy listopada 2026 do kwietnia 2027",
    "od połowy listopada do końca 2026 roku",
    "od równonocy jesiennej (22–23 września 2026) / najbliższe dni",
    "od września / jesieni 2026",
    "około 20–22 listopada 2026",
    "październik / koniec 2026",
    "październik–grudzień 2026",
    "październik–listopad 2026",
    "połowa listopada 2026 – luty 2027",
    "połowa lub druga połowa listopada 2026",
    "przed 2028",
    "przed przełomem lutego i kwietnia",
    "przed zimą 2026/2027",
    "przełom jesieni i zimy 2026",
    "późna jesień (listopad) 2026",
    "za kilka tygodni",  # wypowiedziane 2026-10-31 -> połowa/koniec listopada 2026
}

# Short relative phrases: `minal` if spoken before 2026-09-21 (>2 months before 2026-11-21),
# otherwise `w_trakcie`
RELATIVE_SHORT = {
    "dosyć szybko",
    "najbliższa przyszłość",
    "najbliższe tygodnie",
    "najbliższy czas",
    "najbliższy okres",
    "niebawem",
    "niedługi czas",
    "niedługi okres czasu",
    "niedługo",
    "niedługo / najbliższy czas",
    "w niedługim czasie",
    "wkrótce",
}

EXACT_PRZYSZLY_LUB_WARUNKOWY = {
    "2027",
    "2027–2028 (do końca 2028)",
    "2028",
    "2029",
    "2031",
    "2070–2080",
    "co najmniej 6–8 lat",
    "dalsza przyszłość",
    "do krachu",
    "dużo wcześniej niż za 1000 lat",
    "grudzień 2026",
    "kilka tygodni podczas krachu",
    "koniec stycznia",
    "krótko przed Bożym Narodzeniem 2026",
    "krótko przed krachem",
    "krótko przed wielkim kryzysem ekonomicznym",
    "kwiecień 2027",
    "lato 2027",
    "marzec 2027",
    "marzec 2028",
    "od 2028",
    "od początku 2027 roku",
    "po krachu",
    "po przyszłych wyborach parlamentarnych",
    "po spotkaniu w Szwajcarii",
    "po wstrząsie giełdowym, przed krachem",
    "początek grudnia 2026",
    "przed szczegółowymi rozmowami USA–Iran",
    "przełom 2026 i 2027 roku",
    "przełom lutego i kwietnia",
    "przyszłe wybory parlamentarne",
    "przyszłe wybory parlamentarne i okres po nich",
    "rok do półtora roku po ogłoszeniu",
    "styczeń–luty 2027",
    "w ciągu najbliższych 50 lat (przed 2076)",
    "wcześniej niż za 50 lat",
    "wieloletni po krachu",
    "za 10 lat / przyszłość",
    "za 5 lat (do ok. 2031)",
    "za 50 lat (ok. 2076–2080)",
    "za ok. 5 lat (po powstaniu systemu)",
    "zima 2026/2027",
    "święta Bożego Narodzenia 2026",
}


def classify(horyzont: str, data_wypowiedzenia: str) -> str:
    if not horyzont or horyzont == "nieokreślony":
        return "nieokreslony"
    if horyzont in EXACT_MINAL:
        return "minal"
    if horyzont in EXACT_W_TRAKCIE:
        return "w_trakcie"
    if horyzont in RELATIVE_SHORT:
        return "minal" if data_wypowiedzenia < "2026-09-21" else "w_trakcie"
    if horyzont in EXACT_PRZYSZLY_LUB_WARUNKOWY:
        return "przyszly"
    raise ValueError(f"Unclassified horyzont_czasowy: {horyzont!r}")


def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT t.id, t.video_id, t.data_wypowiedzenia, t.horyzont_czasowy,
               t.teza, t.kategoria, t.timestamp_sek, t.cytat_zrodlowy,
               f.youtube_url, t.youtube_link_z_czasem
        FROM tezy t
        JOIN filmy f ON f.video_id = t.video_id
        ORDER BY t.data_wypowiedzenia DESC, t.video_id ASC, t.timestamp_sek ASC
        """
    ).fetchall()
    conn.close()

    selected = []
    counts = {"minal": 0, "w_trakcie": 0, "przyszly": 0, "nieokreslony": 0}
    for r in rows:
        status = classify(r["horyzont_czasowy"], r["data_wypowiedzenia"])
        counts[status] += 1
        if status in ("minal", "w_trakcie"):
            selected.append(
                {
                    "id": r["id"],
                    "status_horyzontu": status,
                    "data_wypowiedzenia": r["data_wypowiedzenia"],
                    "horyzont_czasowy": r["horyzont_czasowy"],
                    "teza": r["teza"],
                    "kategoria": r["kategoria"],
                    "youtube_url": r["youtube_url"],
                    "youtube_link_z_czasem": r["youtube_link_z_czasem"],
                    "cytat_zrodlowy": r["cytat_zrodlowy"],
                    "video_id": r["video_id"],
                }
            )

    doc = {
        "data_odniesienia": REF_DATE,
        "opis": "Podzbiór przepowiedni Krzysztofa Jackowskiego (Wizja na żywo 2026), których horyzont czasowy już minął (`minal`) lub trwa obecnie (`w_trakcie`) na dzień 2026-11-21.",
        "podsumowanie": {
            "lacznie_w_podzbiorze": len(selected),
            "minal": counts["minal"],
            "w_trakcie": counts["w_trakcie"],
            "wykluczone_przyszle_lub_warunkowe": counts["przyszly"],
            "wykluczone_nieokreslone": counts["nieokreslony"],
            "lacznie_w_bazie": len(rows),
        },
        "tezy": selected,
    }

    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote: {OUT_JSON}")
    print(json.dumps(doc["podsumowanie"], ensure_ascii=False, indent=2))
    print("\nSample `minal` (first 3):")
    for x in [s for s in selected if s["status_horyzontu"] == "minal"][:3]:
        print(f"  [{x['data_wypowiedzenia']} | {x['horyzont_czasowy']}] {x['teza'][:120]}")
    print("\nSample `w_trakcie` (first 3):")
    for x in [s for s in selected if s["status_horyzontu"] == "w_trakcie"][:3]:
        print(f"  [{x['data_wypowiedzenia']} | {x['horyzont_czasowy']}] {x['teza'][:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
