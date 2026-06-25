========================
Zapytania do bazy danych
========================

.. toctree::
   :maxdepth: 2
   :caption: Spis treści:

Wprowadzenie
============

W ramach piątego rozdziału zaimplementowano moduł analityczny w języku Python, służący do interakcji ze strukturami relacyjnej bazy danych. Przygotowane zapytania SQL realizują złożone scenariusze biznesowe wypożyczalni samochodów, wykorzystując zaawansowane mechanizmy silnika bazy danych. 

Zgodnie z dobrymi praktykami inżynierii oprogramowania, kwerendy zhermetyzowano w postaci funkcji przyjmujących aktywny wskaźnik połączenia (obiekt ``conn``), co pozwala na bezpośrednie użycie kodu zarówno w środowiskach produkcyjnych, jak i w notatnikach JupyterLab (JupyterHub).

Zaawansowane mechanizmy zapytań SQL
===================================

Aby system w pełni odpowiadał na potrzeby analityczne, w kodzie Pythona wdrożono pełne spektrum operacji na relacjach, w tym selekcję z operacjami wierszowymi, agregacje wielowierszowe, algebrę zbiorów, złączenia asymetryczne oraz podzapytania skalarne. Poniżej omówiono zaimplementowaną logikę bazodanową.

Selekcja danych i funkcje wierszowe
-----------------------------------
Pierwsze z zapytań wykorzystuje klauzulę ``WHERE`` do filtrowania rekordów po statusie transakcji oraz implementuje wierszowe operacje arytmetyczne na typach dat (natywnie zwracające typ ``integer`` w PostgreSQL).

.. py:function:: pobierz_czas_wypozyczen(conn)
   :noindex:

   Pobiera wykaz zakończonych wypożyczeń wraz z dynamicznie obliczanym czasem ich trwania.

   :param conn: Aktywny obiekt połączenia z bazą danych (np. psycopg).
   :return: Lista krotek: (ID wypożyczenia, złączona nazwa auta, wyliczona liczba dni).

   **Opis techniczny:** Zapytanie realizuje operację arytmetyczną ``(w.data_do - w.data_od)`` bezpośrednio na warstwie bazy danych dla rekordów ze statusem 'Zakonczone'. Dodatkowo, operator ``||`` pozwala na wierszową konkatenację atrybutów marki i modelu do jednej, płaskiej kolumny.

Funkcje agregujące i grupowanie
-------------------------------
Do generowania metryk biznesowych wykorzystano funkcje agregujące, operujące na zgrupowanych wierszach dla poszczególnych osi wymiarów.

.. py:function:: raport_przychodow_kategorii(conn)
   :noindex:

   Generuje zsumowany raport estymowanych przychodów dla klasyfikacji pojazdów.

   :param conn: Aktywny obiekt połączenia z bazą danych.
   :return: Lista krotek: (Nazwa kategorii, liczba wypożyczeń, łączny przychód).

   **Opis techniczny:** Kwerenda implementuje wielokrotne złączenie wewnętrzne (``INNER JOIN``) celem utworzenia widoku o płaskiej hierarchii. Wynik jest grupowany po nazwie kategorii (``GROUP BY k.nazwa``), a przychód estymowany z wykorzystaniem matematycznego wyrażenia wewnątrz funkcji grupującej ``SUM()``.

Połączenia asymetryczne (LEFT JOIN)
-----------------------------------
W relacyjnych systemach analitycznych niezbędne bywa zachowanie informacji o encjach sierocych (nieposiadających powiązań w tabelach zależnych).

.. py:function:: sprawdz_historie_aut(conn)
   :noindex:

   Zwraca pełny wykaz pojazdów we flocie, identyfikując jednostki z brakiem historii operacyjnej.

   :param conn: Aktywny obiekt połączenia z bazą danych.
   :return: Lista krotek z danymi pojazdu oraz opcjonalną datą wypożyczenia.

   **Opis techniczny:** Zastosowanie klauzuli ``LEFT JOIN`` między tabelą główną (samochody) a zależną (wypożyczenia) gwarantuje, że pojazdy niespełniające warunku złączenia zostaną zwrócone w relacji wynikowej z wartością ``NULL`` w miejscu atrybutów tabeli podrzędnej.

Operatory zbiorowe (Różnica)
----------------------------
Część logiki oparto o matematyczną algebrę relacyjną zamiast tradycyjnych złączeń warunkowych, co ułatwia zarządzanie inwentarzem w czasie rzeczywistym.

.. py:function:: dostepne_samochody(conn)
   :noindex:

   Zwraca zbiór identyfikatorów pojazdów aktualnie dostępnych fizycznie na placu.

   :param conn: Aktywny obiekt połączenia z bazą danych.
   :return: Lista krotek identyfikujących dostępne samochody.

   **Opis techniczny:** W zapytaniu użyto operatora różnicy zbiorów ``EXCEPT``. System zaciąga nadzbiór wszystkich zarejestrowanych aut, a następnie odejmuje od niego podzbiór generowany przez kwerendę wskazującą pojazdy mające w tabeli transakcyjnej status 'W trakcie'.

Zagnieżdżone podzapytania (Subqueries)
--------------------------------------
Logikę najdroższego zasobu odseparowano strukturalnie, wstrzykując zapytanie podrzędne bezpośrednio do predykatu kwerendy nadrzędnej.

.. py:function:: klienci_najdrozszych_aut(conn)
   :noindex:

   Wyciąga dane kontaktowe klientów korzystających z najdroższego segmentu floty.

   :param conn: Aktywny obiekt połączenia z bazą danych.
   :return: Zbiór krotek (imię, nazwisko, email, telefon).

   **Opis techniczny:** Rdzeniem zapytania jest dynamiczne podzapytanie w klauzuli ``WHERE`` określające maksymalną stawkę bazową: ``(SELECT id_kategorii FROM kategorie ORDER BY cena_za_dzien DESC LIMIT 1)``. Zapewnia to odporność aplikacji na zmiany cenifikatora w tabeli kategorii.

Implementacja skryptowa
=======================

Wyżej zdefiniowane funkcje zostały spakietowane w postaci odizolowanego modułu Pythona, gotowego do wykonania lub podpięcia jako biblioteka analityczna w głównym kodzie aplikacji. 

.. code-block:: python

    import psycopg
    import sqlite3

    def sprawdz_historie_aut(conn):
        cursor = conn.cursor()
        query = """
            SELECT 
                s.marka, 
                s.model, 
                s.nr_rejestracyjny, 
                w.data_od
            FROM samochody s
            LEFT JOIN wypozyczenia w ON s.id_samochodu = w.id_samochodu;
        """
        cursor.execute(query)
        wyniki = cursor.fetchall()
        cursor.close()
        return wyniki
