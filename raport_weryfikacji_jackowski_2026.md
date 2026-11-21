# Raport weryfikacji przepowiedni Krzysztofa Jackowskiego („Wizja na żywo”, 2026)

**Data odniesienia weryfikacji:** `2026-11-21`  
**Zakres analizowanego korpusu:** 69 filmów „Wizja na żywo” z `archiwumwizji.pl` (`2026-05-28` – `2026-11-20`), z czego 68 posiada pobraną transkrypcję (1 film prywatny), 67 zawiera przepowiednie — łącznie **653 wyodrębnione tezy prognostyczne**.  
**Zweryfikowany podzbiór:** wszystkie **62 przepowiednie**, których horyzont czasowy minął przed `2026-11-21`.

Pliki źródłowe i wynikowe:
- Pełna weryfikacja 62 tez (JSON): [weryfikacja_tez_minionych_2026-11-21.json](file:///home/rafal/projekty/jackowski/weryfikacja_tez_minionych_2026-11-21.json)
- Pełna weryfikacja 62 tez (CSV): [weryfikacja_tez_minionych_2026-11-21.csv](file:///home/rafal/projekty/jackowski/weryfikacja_tez_minionych_2026-11-21.csv)
- Baza SQLite (filmy + transkrypcje + 653 tezy): [jackowski.db](file:///home/rafal/projekty/jackowski/jackowski.db)

---

## 1. Wyniki weryfikacji 62 minionych przepowiedni

| Werdykt | Liczba | Udział |
| :--- | ---: | ---: |
| **Potwierdzona** | **4** | **6,5%** |
| **Częściowo potwierdzona** | **18** | **29,0%** |
| **Niepotwierdzona** | **33** | **53,2%** |
| **Nieweryfikowalna (zbyt ogólna)** | **7** | **11,3%** |
| **Razem** | **62** | **100,0%** |

### Kluczowe rozbicie: co się dzieje, gdy przepowiednia jest naprawdę konkretna?
Wśród 62 zweryfikowanych tez **11 miało wysoką konkretność** (konkretna data/okno kilku dni, konkretny podmiot i falsyfikowalne zdarzenie):
- **Potwierdzone:** **0 / 11 (0,0%)**
- **Częściowo potwierdzone:** **2 / 11 (18,2%)**
- **Niepotwierdzone:** **9 / 11 (81,8%)** — m.in.:
  - wielkie uderzenie USA i Izraela na Iran dokładnie między 9 a 17 września 2026 (`ID=490`),
  - zamach bombowy ok. 25 lipca 2026 po 40 dniach spokoju (`ID=569`),
  - zmasowany atak Iranu na Izrael w ciągu 5 dni od 11 czerwca (`ID=577`),
  - tajfuny nad Czechami, Słowacją, Węgrami, Rumunią i okolicami Rzeszowa latem 2026 (`ID=571`),
  - wielki wyż i stabilna ładna pogoda 20 sierpnia – 20 września 2026 (`ID=446`),
  - głośne wydarzenia wokół Trybunału Konstytucyjnego w konkretną środę 4 listopada (`ID=82`).

### A jakie były 4 „potwierdzone” tezy?
Żadna z 4 potwierdzonych tez nie miała cech nieprawdopodobnego, ponadnaturalnego trafienia:
1. **`ID=437` (`2026-07-24`, niska konkretność):** *„W najbliższym okresie czasu nie dojdzie do blokady internetu.”* — prognoza zachowania status quo („nic się nie wydarzy”).
2. **`ID=615` (`2026-06-05`, średnia konkretność):** *„W czerwcu zarówno w Tunezji, jak i w Egipcie będzie bezpiecznie.”* — kolejna prognoza status quo (brak zamachów w kurortach w jednym miesiącu).
3. **`ID=475` (`2026-07-14`, średnia konkretność, ekstrapolacja newsów):** *„Bitcoin nie powróci do swoich wcześniejszych szczytowych poziomów cenowych przynajmniej w najbliższym czasie.”* — w dniu wypowiedzi BTC kosztował ~63 tys. USD przy historycznym szczycie ~126 tys. USD (październik 2025); prognoza, że nie wzrośnie szybko o +100% w trakcie bessy, to zwykła ekstrapolacja rynkowa.
4. **`ID=641` (`2026-05-28`, średnia konkretność, ekstrapolacja newsów):** *„W czerwcu wznowione zostaną okazjonalne działania wojenne przeciwko Iranowi wraz z irańskimi atakami odwetowymi, lecz bez zmasowanego ataku i bez lądowej interwencji USA oraz Izraela.”* — wojna USA/Izraela z Iranem trwała już od lutego 2026, a w maju obowiązywał kruchy rozejm przerywany starciami; scenariusz „ograniczonych starć bez inwazji lądowej” odpowiadał konsensusowi analityków geopolitycznych z końca maja.

---

## 2. Konkretność i podatność na dopasowanie (62 tezy)

| Parametr | Wysoka | Średnia | Niska |
| :--- | ---: | ---: | ---: |
| **Konkretność / falsyfikowalność tezy** | 11 (17,7%) | 37 (59,7%) | 14 (22,6%) |
| **Podatność na dopasowanie *post factum*** | 29 (46,8%) | 20 (32,3%) | 13 (21,0%) |

- **79,0% (49 / 62)** zweryfikowanych tez zostało zakwalifikowanych jako **ekstrapolacja bieżących newsów** (tematów już obecnych w mediach w dniu nagrania).
- **79,0% (49 / 62)** ma wysoką lub średnią podatność na dopasowanie *post factum* do rozmaitych zdarzeń.

---

## 3. Powtarzalność motywów w całym korpusie (653 tezy / 67 filmów)

Przepowiednie Jackowskiego nie są zróżnicowanym zbiorem niezależnych wglądów — opierają się na kilkunastu stałych, powtarzanych co kilka dni kliszach katastroficznych:

| Motyw | Liczba tez (z 653) | Liczba filmów (z 67) | Udział filmów |
| :--- | ---: | ---: | ---: |
| Wojna / ataki zbrojne / rakiety / eskalacja | 185 | 61 | **91%** |
| Rosja / Putin / Ukraina / Białoruś | 158 | 53 | **79%** |
| Iran / Izrael / Bliski Wschód | 126 | 47 | **70%** |
| Prowokacja / granica / ewakuacja / stan wyjątkowy / drony / fałszywa flaga | 78 | 43 | **64%** |
| Polska polityka / zamach stanu / rząd / Tusk / Nawrocki / wybory | 72 | 41 | **61%** |
| Krach finansowy / kryzys / banki / dolar / giełda / kryptowaluty | 104 | 40 | **60%** |
| Zamieszki / protesty / panika / chaos społeczny | 45 | 30 | **45%** |
| Skażenie / broń jądrowa / promieniowanie | 34 | 25 | **37%** |
| Nowa pandemia / zaraza / epidemia | 27 | 18 | **27%** |
| Katastrofy / pogoda / upały / tajfuny / powodzie | 16 | 13 | **19%** |
| Cyberatak / awaria internetu / blackout / brak prądu | 13 | 10 | **15%** |
| AI / kontrola cyfrowa / inwigilacja | 7 | 6 | **9%** |

Dodatkowo aż **366 z 653 tez (56,1%)** w ogóle **nie zawiera żadnego horyzontu czasowego** (`nieokreślony`), co czyni je z definicji niefalsyfikowalnymi — nigdy nie można wykazać, że się nie sprawdziły.

---

## 4. Mechanizmy psychologiczne, poznawcze, statystyczne i językowe

W analizowanym korpusie wyraźnie dominuje zestaw klasycznych mechanizmów znanych z psychologii poznawczej i analizy wróżbiarstwa (*cold reading* / pseudoprognozowanie):

| Mechanizm wykryty w 62 minionych tezach | Wystąpienia | Udział |
| :--- | ---: | ---: |
| Ekstrapolacja bieżących newsów | 49 | **79,0%** |
| Asekuracja językowa (*hedging*) | 44 | **71,0%** |
| Katastrofizm eskalacyjny | 42 | **67,7%** |
| Podatność na dopasowanie *post factum* | 26 | **41,9%** |
| Brak konkretnego miejsca lub podmiotu | 26 | **41,9%** |
| Ogólnikowość / efekt Barnuma | 20 | **32,3%** |
| Brak falsyfikowalności | 12 | **19,4%** |
| Ruchoma bramka / wielokrotne powtarzanie | 4 | **6,5%** |

### Na czym polegają najważniejsze z tych mechanizmów w praktyce?
1. **Ekstrapolacja bieżących wiadomości (79%):** Większość „wizji” dotyczy kryzysów, o których media mówią już tego samego dnia (wojna z Iranem, wojna w Ukrainie, spory wokół TK/rządu/prezydenta, sytuacja na granicy wschodniej, spadki na Bitcoinie). Jeśli w trwającym konflikcie dojdzie do kolejnego incydentu, łatwo przypisać sobie trafienie.
2. **Strzelanie śrutem (*shotgunning*) i efekt strzelca wyborowego z Teksasu (*Texas sharpshooter fallacy*):** Produkowanie ~10 katastroficznych tez w każdym odcinku (653 tezy w niecałe 6 miesięcy) i powtarzanie tych samych wątków w 60–90% nagrań gwarantuje statystycznie, że przy wystarczającej liczbie incydentów na świecie *coś* zbiegnie się tematycznie (np. rutynowy komunikat GIS, fałszywy alarm bombowy, lokalny incydent graniczny). Później eksponuje się wyłącznie „trafienia” (*cherry-picking*), a setki nietrafionych tez giną w szumie.
3. **Asekuracja językowa (*hedging*):** Wypowiedzi są nasycone sformułowaniami amortyzującymi porażkę: *„mam poczucie”*, *„coś koło tego”*, *„może podlegam sugestii”*, *„nie traktujcie tego dosłownie”*, *„chyba w Polsce”*, *„coś dziwnego”*. Gdy prognoza nie działa, autor zawsze ma furtkę wyjścia.
4. **Ruchoma bramka (*moving the goalposts*) i brak dat:** 56% wszystkich tez nie ma żadnej daty, a te z datami są wielokrotnie przesuwane w kolejnych odcinkach (np. wielkie uderzenie na Iran / wielki krach / ewakuacja rejonów Polski zapowiadane kolejno na czerwiec, lipiec, wrzesień, połowę listopada, koniec roku, 2027, 2028).
5. **Efekt Barnuma / ogólnikowość:** Zamiast konkretnych nazw, miejsc i liczb pojawiają się etykiety takie jak *„jakiś duży urząd”*, *„pewne państwo”*, *„bardzo znany polityk”*, *„coś bardzo ważnego, o czym będzie głośno”*. W dowolnym tygodniu na świecie zawsze dzieje się coś, co odbiorca może pod taką etykietę podłożyć (efekt potwierdzenia).
6. **Katastrofizm i błąd negatywności (*negativity bias*):** Dominacja lękowych scenariuszy (wojna, skażenie, krach, zamach stanu, pandemia) silnie angażuje emocjonalnie i napędza oglądalność YouTube (algorytmiczna premia za emocje i poczucie zagrożenia), a jednocześnie sprawia, że odbiorcy zapamiętują groźne obrazy i łączą je z każdą niepokojącą wiadomością.

---

## 5. Wniosek końcowy: czy dane pozwalają uznać Krzysztofa Jackowskiego za prawdziwego jasnowidza?

**Nie — zebrane dane empiryczne jednoznacznie temu przeczą.**
- **0% trafień (0/11)** wśród tez o wysokiej konkretności i falsyfikowalności.
- **53,2% (33/62)** jednoznacznie niepotwierdzonych tez oraz **11,3% (7/62)** zbyt ogólnych do weryfikacji.
- Zaledwie **6,5% (4/62)** tez potwierdzonych — z czego **3 to trywialne prognozy status quo / trwającej bessy**, a **1 to bezpośrednia ekstrapolacja już trwającego konfliktu zbrojnego**.
- Skuteczność jest **niższa niż poziom zwykłego komentatora polityczno-ekonomicznego** korzystającego z prasy codziennej i nie wykazuje żadnego statystycznego sygnału zdolności paranormalnych.

To, co sprawia wrażenie „trafności” u części odbiorców, jest w pełni wyjaśnialne przez kombinację: **dużej objętości powtarzanych prognoz (653 tezy w pół roku), braku dat (56%), ekstrapolacji bieżących newsów (79%), asekuracji językowej (71%) oraz dopasowywania ogólnych haseł do późniejszych zdarzeń**.
