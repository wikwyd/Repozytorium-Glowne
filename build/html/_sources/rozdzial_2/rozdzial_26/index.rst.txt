===========================
2.6. Partycjonowanie danych
===========================
**Autorzy**

1. Michał Bystrzak
2. Damian Dominiak

2.6.1 Wstęp i istota problemu
-----------------------------
W dobie systemów informatycznych przetwarzających gigabajty lub terabajty informacji (tzw. VLDB - Very Large Databases), tradycyjne podejście do składowania danych staje się wysoce niewydajne. Kiedy pojedyncza tabela rozrasta się do setek milionów rekordów, fizyczne ograniczenia sprzętowe oraz narzuty na zarządzanie indeksami powodują drastyczny spadek wydajności. Partycjonowanie to zaawansowana technika architektoniczna, polegająca na logicznym podziale jednej, ogromnej tabeli na mniejsze, odseparowane fizycznie fragmenty nazywane partycjami. Z perspektywy aplikacji docelowej oraz zapytań SQL, tabela wciąż prezentuje się i zachowuje jak spójna, pojedyncza relacja.

2.6.2 Cele stosowania partycjonowania danych
--------------------------------------------
Implementacja mechanizmu partycjonowania w systemach relacyjnych jest podyktowana chęcią rozwiązania konkretnych problemów wydajnościowych i administracyjnych. Główne cele to:

* **Zwiększenie wydajności zapytań (Query Performance):** Fundamentalnym celem jest eliminacja konieczności skanowania całej tabeli (Full Table Scan). Dzięki mechanizmowi *Partition Pruning* (odcinanie partycji), planista zapytań analizuje warunki zdefiniowane w klauzuli ``WHERE`` i kieruje odczyt wyłącznie do tych fizycznych plików, które mogą zawierać poszukiwane dane.
* **Optymalizacja procesów utrzymaniowych (Maintenance):** Olbrzymie tabele są trudne w utrzymaniu. Operacje takie jak ``VACUUM``, ``REINDEX`` czy odtwarzanie kopii zapasowych mogą blokować zasoby przez wiele godzin. Partycjonowanie pozwala na wykonywanie tych operacji selektywnie, tylko na tych partycjach, które uległy modyfikacji.
* **Zarządzanie cyklem życia danych (Data Lifecycle Management):** W przypadku danych historycznych (np. logów), najszybszą metodą ich usunięcia jest operacja ``DROP TABLE`` na starej partycji. Jest to operacja na metadanych, trwająca ułamki sekund, w przeciwieństwie do standardowego ``DELETE``, które w architekturze MVCC (Multi-Version Concurrency Control) generuje ogromne ilości "martwych krotek" (dead tuples) i obciąża dziennik transakcji (WAL).

2.6.3 Zastosowanie partycjonowania
----------------------------------
Technika ta nie jest uniwersalnym rozwiązaniem dla każdej bazy danych, lecz sprawdza się w specyficznych, wymagających scenariuszach:

* **Hurtownie danych (OLAP):** Systemy analityczne gromadzące dane historyczne. Partycjonowanie pozwala tam na błyskawiczne agregowanie danych (np. sumowanie przychodów z konkretnego miesiąca) bez wczytywania do pamięci RAM danych z całej dekady.
* **Systemy transakcyjne (OLTP) o wysokim przyroście:** Aplikacje rejestrujące logi systemowe, odczyty z czujników IoT, dane telemetryczne czy rejestry transakcji finansowych (Time-Series Data), gdzie każdego dnia przybywają miliony nowych wierszy.
* **Implementacja Storage Tiering:** Możliwość fizycznego rozdzielenia danych na różne nośniki. Najnowsze i najczęściej odpytywane partycje (Hot Data) umieszcza się na ultra-szybkich macierzach NVMe, podczas gdy starsze, rzadko używane partycje (Cold Data) przenosi się na tańsze wolumeny dyskowe (HDD), co znacząco optymalizuje koszty infrastruktury.

2.6.4 Zalety i wady partycjonowania
-----------------------------------
Jak każda technika optymalizacyjna, partycjonowanie stanowi kompromis inżynieryjny (Trade-off).

**Zalety:**

* Spektakularny wzrost wydajności operacji odczytu, o ile zapytanie wykorzystuje klucz partycjonowania.
* Optymalne wykorzystanie pamięci operacyjnej (RAM) – indeksy dla poszczególnych partycji są znacznie mniejsze i z większym prawdopodobieństwem zmieszczą się w całości w pamięci podręcznej (Cache).
* Możliwość bezinwazyjnego odłączania i dołączania gigabajtów danych niemal w czasie rzeczywistym.

**Wady:**

* Zwiększony narzut (overhead) na planistę zapytań. Przy bardzo dużej liczbie partycji (np. tysiące fragmentów), czas samego planowania zapytania przez silnik bazy może być dłuższy niż czas jego wykonania.
* Ograniczenia strukturalne: w wielu systemach DBMS (w tym w PostgreSQL) globalne klucze główne (Primary Keys) i ograniczenia unikalności (UNIQUE) muszą z założenia zawierać w sobie kolumnę będącą kluczem partycjonowania, co bywa trudne do pogodzenia z logiką biznesową aplikacji.
* Spadek wydajności w przypadku zapytań omijących klucz partycjonowania – silnik musi wówczas odpytać każdą fizyczną partycję z osobna.

2.6.5 Implementacja partycjonowania w PostgreSQL
------------------------------------------------
Począwszy od wersji 10, PostgreSQL oferuje natywne wsparcie dla partycjonowania deklaratywnego. Eliminuje to konieczność ręcznego pisania skomplikowanych wyzwalaczy czy reguł (rules). Silnik obsługuje trzy główne strategie przydziału danych:

* **Zakresowe (RANGE):** Dane są dzielone na podstawie ciągłych przedziałów wartości. Najczęściej wykorzystywanym kluczem są typy daty i czasu (np. jedna partycja dla ``2025-01-01`` do ``2025-01-31``) lub sekwencje numeryczne.
* **Listowe (LIST):** Dane są dystrybuowane na podstawie konkretnych, dyskretnych wartości zdefiniowanych w tablicy. Metoda ta idealnie sprawdza się w przypadku podziału na kategorie biznesowe, takie jak "Status_Zlecenia" (osobna partycja dla wartości ``Zakończone``, ``W trakcie``) lub regiony geograficzne.
* **Haszujące (HASH):** Wiersze są rozdzielane na zadaną liczbę partycji (modułów) z wykorzystaniem zaawansowanej, matematycznej funkcji skrótu. Strategia ta nie służy przyspieszaniu zapytań zakresowych, lecz idealnie równomiernemu rozłożeniu ciężaru I/O podczas masowych operacji wstawiania (INSERT) w systemach wielodyskowych.

2.6.6 Ograniczenia i obejście w środowisku SQLite
-------------------------------------------------
W przeciwieństwie do potężnych, serwerowych silników RDBMS takich jak PostgreSQL, lekka i plikowa biblioteka SQLite **nie posiada** natywnego mechanizmu partycjonowania deklaratywnego. Wynika to z jej osadzonej (embedded) architektury.

Niemniej jednak, efekt partycjonowania w SQLite można emulować za pomocą programistycznego podejścia warstwowego:
1. **Podział fizyczny:** Utworzenie wielu mniejszych, niezależnych tabel (np. ``zlecenia_2025``, ``zlecenia_2026``).
2. **Warstwa logiczna:** Stworzenie wspólnego widoku (``VIEW``), który scala wszystkie te tabele z wykorzystaniem operatora ``UNION ALL``. Umożliwia to wykonywanie zapytań ``SELECT`` na jednej strukturze.
3. **Zarządzanie modyfikacjami:** Obsługa instrukcji DML (``INSERT``, ``UPDATE``, ``DELETE``) wymaga zdefiniowania na widoku zestawu wyzwalaczy (``TRIGGERS INSTEAD OF``). Wyzwalacze te muszą przechwytywać dane w locie, analizować klucz (np. datę) i dynamicznie przekierowywać operację do odpowiedniej fizycznej pod-tabeli. 

Choć to rozwiązanie jest funkcjonalne, należy pamiętać, że w SQLite każdorazowe uruchamianie wyzwalaczy generuje zauważalny narzut wydajnościowy w porównaniu do natywnego mechanizmu w PostgreSQL.