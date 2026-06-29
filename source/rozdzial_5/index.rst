============================================
Zapytania do bazy danych (SQLite PostgreSQL)
============================================

.. toctree::
   :maxdepth: 2
   :caption: Spis treści:

:Autorzy:
    1. Olaf Chomicki
    2. Konrad Machowski
    3. Wiktor Wydrzyński

Wprowadzenie
============

W ramach piątego rozdziału zaimplementowano moduł analityczny w języku Python, służący do interakcji ze strukturami relacyjnej bazy danych. Ze względu na zróżnicowane środowisko wdrożeniowe, przygotowano osobne pule zapytań dedykowane dla silnika **SQLite** (wykorzystywanego lokalnie/testowo) oraz **PostgreSQL** (środowisko produkcyjne). 

Zgodnie z dobrymi praktykami inżynierii oprogramowania, kwerendy zhermetyzowano w postaci funkcji przyjmujących aktywny wskaźnik połączenia (obiekt ``conn``), co pozwala na bezpośrednie użycie kodu w aplikacjach oraz notatnikach Jupyter.

Część 1: Zapytania w dialekcie SQLite
=====================================

Poniższe 5 zapytań zostało zoptymalizowanych pod kątem lekkiego silnika SQLite, wykorzystując jego natywne funkcje przetwarzania dat i agregacji tekstowej.

Arytmetyka dat w SQLite (julianday)
-----------------------------------
.. py:function:: sqlite_pobierz_czas_wypozyczen(conn)
   :noindex:

   Pobiera wykaz zakończonych wypożyczeń z obliczonym czasem ich trwania.

   :param conn: Obiekt połączenia (sqlite3).
   :return: Lista krotek: (ID, złączona nazwa auta, liczba dni).

   **Opis techniczny:** Ponieważ SQLite nie posiada natywnego typu daty, wykorzystano funkcję ``julianday()`` do konwersji ciągów tekstowych na wartości zmiennoprzecinkowe reprezentujące dni, a następnie użyto rzutowania ``CAST(... AS INTEGER)``.

Agregacja i złączenia wewnętrzne (INNER JOIN)
---------------------------------------------
.. py:function:: sqlite_raport_przychodow_kategorii(conn)
   :noindex:

   Generuje zsumowany raport estymowanych przychodów dla klasyfikacji pojazdów.

   :param conn: Obiekt połączenia (sqlite3).
   :return: Lista krotek: (Nazwa kategorii, łączny przychód).

   **Opis techniczny:** Kwerenda implementuje złączenie ``INNER JOIN`` łącząc tabele kategorii, samochodów i transakcji, grupując wyniki funkcją ``SUM()`` po nazwie kategorii.

Połączenia asymetryczne (LEFT JOIN)
-----------------------------------
.. py:function:: sqlite_sprawdz_historie_aut(conn)
   :noindex:

   Zwraca pełny wykaz pojazdów, identyfikując te bez historii wypożyczeń.

   :param conn: Obiekt połączenia (sqlite3).
   :return: Lista krotek (Marka, Model, Data wypożyczenia lub NULL).

   **Opis techniczny:** Zastosowanie klauzuli ``LEFT JOIN`` gwarantuje, że pojazdy niespełniające warunku złączenia zostaną zwrócone w relacji wynikowej z wartością ``NULL``.

Operatory zbiorowe (EXCEPT)
---------------------------
.. py:function:: sqlite_dostepne_samochody(conn)
   :noindex:

   Zwraca zbiór identyfikatorów aut aktualnie dostępnych na placu.

   :param conn: Obiekt połączenia (sqlite3).
   :return: Lista krotek z ID pojazdów.

   **Opis techniczny:** Wykorzystano operator różnicy zbiorów ``EXCEPT``. System zaciąga nadzbiór wszystkich aut i odejmuje podzbiór aut o statusie 'W trakcie'.

Agregacja tekstowa (GROUP_CONCAT)
---------------------------------
.. py:function:: sqlite_wyposazenie_floty(conn)
   :noindex:

   Agreguje listę wyposażenia dodatkowego dla każdego samochodu w jeden ciąg znaków.

   :param conn: Obiekt połączenia (sqlite3).
   :return: Lista krotek (ID pojazdu, połączona lista wyposażenia).

   **Opis techniczny:** Użyto specyficznej dla SQLite funkcji ``GROUP_CONCAT()``, która spłaszcza relację jeden-do-wielu do pojedynczej kolumny tekstowej oddzielonej przecinkami.


Część 2: Zaawansowane zapytania PostgreSQL
==========================================

Kolejne 5 zapytań wykorzystuje potężne mechanizmy analityczne wbudowane w silnik PostgreSQL, niedostępne w prostszych bazach danych.

Zaawansowana agregacja tekstowa (STRING_AGG)
--------------------------------------------
.. py:function:: pg_lista_klientow_aut(conn)
   :noindex:

   Generuje dla każdego auta czytelną listę wszystkich klientów, którzy go wypożyczyli.

   :param conn: Obiekt połączenia (psycopg).
   :return: Lista krotek (Auto, lista klientów).

   **Opis techniczny:** Wykorzystano potężną funkcję ``STRING_AGG()``, która w przeciwieństwie do rozwiązań z SQLite pozwala na użycie własnego separatora oraz zagnieżdżonego sortowania klauzulą ``ORDER BY`` wewnątrz agregacji.

Selektywna agregacja (Klauzula FILTER)
--------------------------------------
.. py:function:: pg_analiza_przychodow_selektywna(conn)
   :noindex:

   Zwraca sumę przychodów podzieloną na opłacone i zaległe w jednym zapytaniu.

   :param conn: Obiekt połączenia (psycopg).
   :return: Lista krotek (Kategoria, suma opłaconych, suma zaległych).

   **Opis techniczny:** Użyto klauzuli ``FILTER (WHERE ...)`` podpiętej pod funkcję agregującą, co pozwala na warunkowe sumowanie kolumn (tzw. pivotowanie) bez konieczności pisania skomplikowanych instrukcji ``CASE WHEN``.

Funkcje okna (Window Functions)
-------------------------------
.. py:function:: pg_ranking_klientow(conn)
   :noindex:

   Tworzy ranking najlepszych klientów na podstawie generowanych przychodów.

   :param conn: Obiekt połączenia (psycopg).
   :return: Lista krotek (Imię, Nazwisko, Przychód, Pozycja w rankingu).

   **Opis techniczny:** Zapytanie korzysta z zaawansowanej funkcji analitycznej (okna) ``RANK() OVER (ORDER BY SUM(kwota) DESC)``, przypisując każdemu klientowi pozycję w rankingu całkowicie na poziomie silnika bazy.

Natywna arytmetyka interwałów dat (INTERVAL)
--------------------------------------------
.. py:function:: pg_pobierz_sredni_czas_wypozyczen(conn)
   :noindex:

   Oblicza średni czas wypożyczenia dla poszczególnych marek samochodów.

   :param conn: Obiekt połączenia (psycopg).
   :return: Lista krotek (Marka, średni czas w dniach).

   **Opis techniczny:** Postgres natywnie obsługuje typ ``INTERVAL``. Wykorzystano odjęcie od siebie typów ``DATE`` i przepuszczenie wyniku przez agregat ``AVG()``, a następnie zaokrąglenie do pełnych dni funkcją ``EXTRACT(DAY FROM ...)``.

Wyrażenia tablicowe (CTE - WITH)
--------------------------------
.. py:function:: pg_klienci_najdrozszych_aut(conn)
   :noindex:

   Wyszukuje klientów korzystających z najdroższego segmentu aut wykorzystując CTE.

   :param conn: Obiekt połączenia (psycopg).
   :return: Zbiór krotek (imię, nazwisko, email, telefon).

   **Opis techniczny:** Logikę predykatu odseparowano za pomocą klauzuli ``WITH`` (Common Table Expressions). Utworzono tymczasowy widok szukający najwyższej ceny, który następnie dołączono do głównego zapytania. Zwiększa to znacząco czytelność złożonego kodu SQL.

Implementacja skryptowa
=======================

Wszystkie wyżej opisane kwerendy zaimplementowano w języku Python. Funkcje prefiksowane są odpowiednio nazwami ``sqlite_`` oraz ``pg_``.

.. code-block:: python

    import psycopg
    import sqlite3

    # ==========================================
    # ZAPYTANIA SQLITE
    # ==========================================

    def sqlite_pobierz_czas_wypozyczen(conn):
        cursor = conn.cursor()
        query = """
            SELECT w.id_wypozyczenia, 
                   s.marka || ' ' || s.model AS auto,
                   CAST(julianday(w.data_do) - julianday(w.data_od) AS INTEGER) AS dni
            FROM wypozyczenia w
            JOIN samochody s ON w.id_samochodu = s.id_samochodu
            WHERE w.status = 'Zakonczone';
        """
        cursor.execute(query)
        return cursor.fetchall()

    def sqlite_raport_przychodow_kategorii(conn):
        cursor = conn.cursor()
        query = """
            SELECT k.nazwa, SUM(k.cena_za_dzien * CAST(julianday(w.data_do) - julianday(w.data_od) AS INTEGER))
            FROM kategorie k
            INNER JOIN samochody s ON k.id_kategorii = s.id_kategorii
            INNER JOIN wypozyczenia w ON s.id_samochodu = w.id_samochodu
            GROUP BY k.nazwa;
        """
        cursor.execute(query)
        return cursor.fetchall()

    def sqlite_sprawdz_historie_aut(conn):
        cursor = conn.cursor()
        query = """
            SELECT s.marka, s.model, w.data_od
            FROM samochody s
            LEFT JOIN wypozyczenia w ON s.id_samochodu = w.id_samochodu;
        """
        cursor.execute(query)
        return cursor.fetchall()

    def sqlite_dostepne_samochody(conn):
        cursor = conn.cursor()
        query = """
            SELECT id_samochodu FROM samochody
            EXCEPT
            SELECT id_samochodu FROM wypozyczenia WHERE status = 'W trakcie';
        """
        cursor.execute(query)
        return cursor.fetchall()

    def sqlite_wyposazenie_floty(conn):
        cursor = conn.cursor()
        query = """
            SELECT s.id_samochodu, GROUP_CONCAT(w.nazwa_wyposazenia, ', ')
            FROM samochody s
            LEFT JOIN wyposazenie_aut wa ON s.id_samochodu = wa.id_samochodu
            LEFT JOIN wyposazenie w ON wa.id_wyposazenia = w.id_wyposazenia
            GROUP BY s.id_samochodu;
        """
        cursor.execute(query)
        return cursor.fetchall()

    # ==========================================
    # ZAPYTANIA POSTGRESQL
    # ==========================================

    def pg_lista_klientow_aut(conn):
        cursor = conn.cursor()
        query = """
            SELECT s.nr_rejestracyjny, 
                   STRING_AGG(kl.imie || ' ' || kl.nazwisko, ', ' ORDER BY w.data_od DESC) as klienci
            FROM samochody s
            JOIN wypozyczenia w ON s.id_samochodu = w.id_samochodu
            JOIN klienci kl ON w.id_klienta = kl.id_klienta
            GROUP BY s.nr_rejestracyjny;
        """
        cursor.execute(query)
        return cursor.fetchall()

    def pg_analiza_przychodow_selektywna(conn):
        cursor = conn.cursor()
        query = """
            SELECT k.nazwa,
                   SUM(w.kwota_calkowita) FILTER (WHERE w.status_platnosci = 'Oplacone') as oplacone,
                   SUM(w.kwota_calkowita) FILTER (WHERE w.status_platnosci = 'Zalegle') as zalegle
            FROM kategorie k
            JOIN samochody s ON k.id_kategorii = s.id_kategorii
            JOIN wypozyczenia w ON s.id_samochodu = w.id_samochodu
            GROUP BY k.nazwa;
        """
        cursor.execute(query)
        return cursor.fetchall()

    def pg_ranking_klientow(conn):
        cursor = conn.cursor()
        query = """
            SELECT kl.imie, kl.nazwisko, SUM(w.kwota_calkowita) as suma_wydatkow,
                   RANK() OVER (ORDER BY SUM(w.kwota_calkowita) DESC) as pozycja_w_rankingu
            FROM klienci kl
            JOIN wypozyczenia w ON kl.id_klienta = w.id_klienta
            GROUP BY kl.id_klienta, kl.imie, kl.nazwisko;
        """
        cursor.execute(query)
        return cursor.fetchall()

    def pg_pobierz_sredni_czas_wypozyczen(conn):
        cursor = conn.cursor()
        query = """
            SELECT s.marka, 
                   EXTRACT(DAY FROM AVG(w.data_do - w.data_od)) as sredni_czas_dni
            FROM wypozyczenia w
            JOIN samochody s ON w.id_samochodu = s.id_samochodu
            WHERE w.status = 'Zakonczone'
            GROUP BY s.marka;
        """
        cursor.execute(query)
        return cursor.fetchall()

    def pg_klienci_najdrozszych_aut(conn):
        cursor = conn.cursor()
        query = """
            WITH NajdrozszaKategoria AS (
                SELECT id_kategorii FROM kategorie ORDER BY cena_za_dzien DESC LIMIT 1
            )
            SELECT DISTINCT kl.imie, kl.nazwisko, kl.email, kl.telefon
            FROM klienci kl
            JOIN wypozyczenia w ON kl.id_klienta = w.id_klienta
            JOIN samochody s ON w.id_samochodu = s.id_samochodu
            WHERE s.id_kategorii = (SELECT id_kategorii FROM NajdrozszaKategoria);
        """
        cursor.execute(query)
        return cursor.fetchall()
