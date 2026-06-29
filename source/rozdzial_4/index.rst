=========================================
Implementacja bazy danych i import danych 
=========================================

.. toctree::
   :maxdepth: 2
   :caption: Spis treści:

:Autorzy:
    1. Olaf Chomicki
    2. Konrad Machowski
    3. Wiktor Wydrzyński

Wprowadzenie
============
W ramach czwartego rozdziału zrealizowano dwa kluczowe etapy prac wdrożeniowych: utworzenie struktur tabelarycznych zdefiniowanych w modelu fizycznym oraz wdrożenie zoptymalizowanych mechanizmów importu danych testowych. Prace przeprowadzono w sposób równoległy dla środowiska lokalnego opartego na silniku SQLite oraz serwerowego wykorzystującego system PostgreSQL.

Definicja i inicjalizacja struktur danych
==============================================

Pierwszym etapem wdrażania systemu bazodanowego było przeniesienie założeń modelu fizycznego do wytypowanych systemów zarządzania bazami danych (DBMS). Proces ten wymagał adaptacji skryptów DDL (Data Definition Language) do specyficznych dialektów SQL obsługiwanych przez wybrane środowiska.

W przypadku **PostgreSQL**, definicje tabel utworzono wykorzystując zaawansowane typy danych (np. ``NUMERIC``) oraz współczesne metody autoinkrementacji kluczy głównych poprzez klauzulę ``GENERATED ALWAYS AS IDENTITY``. Poniżej przedstawiono implementację dla kluczowych tabel, ilustrującą nałożone więzy integralności (unikalność i kontrolę dat):

.. code-block:: sql

    -- Fragment definicji kluczowych tabel (PostgreSQL)
    CREATE TABLE Klienci (
        ID_Klienta INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        Imie VARCHAR(50) NOT NULL,
        Nazwisko VARCHAR(100) NOT NULL,
        PESEL VARCHAR(11) UNIQUE NOT NULL,
        Nr_Prawa_Jazdy VARCHAR(20) UNIQUE
    );

    CREATE TABLE Wypozyczenia (
        ID_Wypozyczenia INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        ID_Klienta INT NOT NULL,
        Data_Od DATE NOT NULL,
        Data_Do DATE NOT NULL,
        CONSTRAINT fk_klient FOREIGN KEY (ID_Klienta) REFERENCES Klienci(ID_Klienta),
        CONSTRAINT sprawdz_daty CHECK (Data_Do >= Data_Od)
    );

W środowisku **SQLite**, będącym lekką bazą wbudowaną, wykorzystano uproszczone mapowanie typów (``INTEGER``, ``TEXT``). Proces inicjalizacji wymagał wywołania procedury aktywującej wsparcie dla więzów referencyjnych za pomocą dyrektywy ``PRAGMA foreign_keys = ON;``, co zostało zaprezentowane na poniższym fragmencie kodu implementującego tabele z kluczem obcym:

.. code-block:: sql

    -- Fragment definicji kluczowych tabel (SQLite)
    PRAGMA foreign_keys = ON;

    CREATE TABLE Klienci (
        ID_Klienta INTEGER PRIMARY KEY,
        Imie TEXT NOT NULL,
        Nazwisko TEXT NOT NULL,
        PESEL TEXT UNIQUE NOT NULL
    );

    CREATE TABLE Wypozyczenia (
        ID_Wypozyczenia INTEGER PRIMARY KEY,
        ID_Klienta INTEGER,
        Data_Od TEXT NOT NULL,
        Data_Do TEXT NOT NULL,
        FOREIGN KEY (ID_Klienta) REFERENCES Klienci(ID_Klienta)
    );

Zasilenie bazy danymi demonstracyjnymi
===========================================

Na etapie testowania architektury modelu fizycznego, puste relacje zostały zasilone małym zbiorem danych demonstracyjnych wykorzystując klasyczne polecenia DML z rodziny ``INSERT``. Procedura ta miała na celu weryfikację poprawności działania nałożonych ograniczeń integralnościowych – na przykład weryfikację unikalności numerów PESEL i numerów rejestracyjnych pojazdów oraz zgodność typów asocjacyjnych.

Koncepcja mechanizmów masowego importu (ETL)
=================================================

Dla zasymulowania warunków produkcyjnych i obciążenia systemów większym wolumenem rekordów, utworzono standaryzowany plik formatu CSV reprezentujący logikę płaskich rekordów z informacjami o potencjalnych klientach.

Zarówno dla SQLite, jak i PostgreSQL, pierwszym krokiem w środowisku języka Python było odczytanie płaskiego pliku i przeniesienie go do ustrukturyzowanej, iterowalnej pamięci RAM (np. w postaci listy list):

.. code-block:: python

    import csv

    # Wczytywanie danych z pliku CSV do struktury iterowalnej
    with open('klienci.csv', 'r', encoding='utf-8') as plik_csv:
        reader = csv.reader(plik_csv)
        next(reader) # Pominięcie wiersza z nagłówkami
        dane_z_csv = [row for row in reader]

Mając przygotowaną strukturę w pamięci aplikacji, przystąpiono do operacji ładowania danych, przyjmując strategie adekwatne do natury silników bazodanowych.

Mechanizm COPY w PostgreSQL
---------------------------
Ze względu na architekturę klient-serwer, przesyłanie tysięcy pojedynczych zapytań ``INSERT`` wiąże się z ogromnym kosztem operacyjnym ze względu na opóźnienia sieciowe oraz narzut parsowania po stronie serwera. Wdrożono zatem natywną dla PostgreSQL instrukcję ``COPY`` obsługującą strumieniowanie wejścia (``STDIN``):

.. code-block:: python

    # Właściwy proces wsadowego importu do bazy PostgreSQL
    # (Zakładając aktywne połączenie psycopg2/psycopg3 pod zmienną conn_pg)
    
    with conn_pg.cursor() as cursor_pg:
        # Zastosowanie strumieniowania binarnego wprost do pamięci buforowej Postgresa
        with cursor_pg.copy(
            "COPY Klienci (Imie, Nazwisko, PESEL, Nr_Prawa_Jazdy, Telefon, Email) FROM STDIN"
        ) as copy_operation:
            for row in dane_z_csv:
                copy_operation.write_row(row)
                
    conn_pg.commit()

Takie podejście buduje ciągły potok danych bezpośrednio do pliku tabeli, omijając standardową kontrolę transakcyjną planisty (query planner) dla każdego pojedynczego wiersza z osobna, co jest referencyjnym wzorcem w środowiskach inżynierii danych.

Mechanizm Batch Insert w SQLite
-------------------------------
W silniku SQLite wykorzystano z kolei grupowanie instrukcji poprzez metodę ``executemany()`` dostępną w sterowniku języka Python. Ponieważ cała baza jest jednoplikowa, wykonanie całego wsadu w obrębie jednej otwartej i zatwierdzonej tylko raz na końcu transakcji redukuje obciążenie I/O systemu plików do minimum.
