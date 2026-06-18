================================================
Kontrola i konserwacja
================================================

:Autorzy:
    1. Paweł Łoćwin
    2. Paweł Łosowski

Wprowadzenie i planowanie konserwacji
=====================================
Współczesne systemy relacyjnych baz danych to wysoce skomplikowane środowiska, które wymagają ciągłego i proaktywnego nadzoru. Aby zagwarantować wysoką dostępność i niezawodność, niezbędne jest rygorystyczne planowanie procesów konserwacyjnych, które opiera się na odpowiedzi na trzy kluczowe pytania:

* **Kiedy?** Operacje inwazyjne (np. pełna przebudowa tabel i indeksów) powinny być planowane w tzw. oknach serwisowych, czyli w godzinach najniższego obciążenia systemu (zwykle w nocy lub w weekendy). Lżejsze prace konserwacyjne mogą odbywać się w tle.
* **W jakim zakresie?** Należy precyzyjnie określić, czy konserwacji wymaga cała instancja, pojedyncza baza danych, czy tylko wytypowane, najszybciej rosnące tabele. Skupienie się na najbardziej obciążonych obszarach oszczędza zasoby sprzętowe.
* **Jak?** Konserwacja powinna być maksymalnie zautomatyzowana (np. z wykorzystaniem systemowego demona CRON lub rozszerzenia `pg_cron`). Ręczne interwencje administratora powinny być zarezerwowane wyłącznie dla sytuacji awaryjnych i niestandardowych problemów wydajnościowych.

Zarządzanie stanem serwera i sesjami
====================================
Podstawą kontroli nad środowiskiem bazodanowym jest zarządzanie cyklem życia samej usługi. Uruchamianie, zatrzymywanie i restartowanie serwera bazy danych realizuje się najczęściej za pośrednictwem menedżera usług systemu operacyjnego (np. polecenia `systemctl start/stop/restart postgresql`) lub za pomocą dedykowanego narzędzia wiersza poleceń `pg_ctl`.

Podczas wdrażania krytycznych aktualizacji lub w sytuacjach awaryjnych, konieczne jest sprawne zarządzanie ruchem użytkowników:

* **Zapobieganie nowym połączeniom:** Administrator może tymczasowo zablokować możliwość logowania się do konkretnej bazy danych poprzez zmianę jej metadanych. Pozwala to na "odcięcie" aplikacji bez wyłączania całego serwera.
* **Ograniczanie i rozłączanie użytkowników:** Istniejące, aktywne sesje, które np. zawiesiły się lub blokują ważne operacje, można siłowo przerwać, zwalniając tym samym zablokowane zasoby.

.. code-block:: sql

    -- Zapobieganie nawiązywaniu nowych połączeń do bazy danych
    ALTER DATABASE biblioteka_db ALLOW_CONNECTIONS = false;

    -- Siłowe rozłączenie wszystkich aktywnych użytkowników (poza aktualną sesją)
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = 'biblioteka_db' AND pid <> pg_backend_pid();

Proces Vacuum
=============
Architektura PostgreSQL opiera się na mechanizmie MVCC (Multi-Version Concurrency Control). Oznacza to, że instrukcje aktualizacji (UPDATE) i usuwania (DELETE) nie niszczą fizycznie starych danych, lecz tworzą tzw. "martwe krotki" (dead tuples). Do zarządzania nimi służy proces czyszczenia:

* **VACUUM:** Standardowa operacja zwalniająca miejsce po martwych wierszach, czyniąca je dostępnymi dla nowych danych. Nie zmniejsza ona fizycznego rozmiaru pliku na dysku i nie blokuje możliwości jednoczesnego odczytu i zapisu tabeli.
* **VACUUM FULL:** Inwazyjna i ciężka operacja, która fizycznie przebudowuje tabelę, faktycznie zmniejszając jej rozmiar i zwracając wolne miejsce do systemu operacyjnego. Wymaga ekskluzywnej blokady (lock), całkowicie odcinając aplikację od modyfikowanej tabeli na czas trwania procesu.
* **AUTOVACUUM:** Zautomatyzowany proces działający w tle, który regularnie monitoruje poziom zmian w tabelach i samoczynnie wyzwala standardowy Vacuum, zapobiegając niekontrolowanemu puchnięciu bazy danych (table bloat).

Zarządzanie transakcjami i schematy (SCHEMA)
============================================
Kolejnym aspektem administracji jest dbanie o logiczną strukturę bazy oraz spójność operacji.

**SCHEMA (Schematy)** to wirtualne przestrzenie nazw (przypominające katalogi w systemie operacyjnym), służące do logicznego grupowania tabel, widoków i funkcji. Ich główne zastosowania to:
* Izolacja danych różnych mikrousług lub aplikacji wewnątrz jednej wspólnej bazy danych.
* Implementacja architektury wielodostępowej (multi-tenant), gdzie każdy klient aplikacji obsługiwany jest w dedykowanym, oddzielnym schemacie.
* Ułatwione i zbiorcze zarządzanie uprawnieniami dostępu.

**Zarządzanie transakcjami** to proces kontrolowania instrukcji (BEGIN, COMMIT, ROLLBACK) w taki sposób, aby zachować zgodność z regułami ACID. Administrator musi zwracać szczególną uwagę na zapobieganie tzw. długim transakcjom (long-running transactions). Otwarta i porzucona transakcja powstrzymuje proces Vacuum przed usuwaniem martwych krotek, co prowadzi do drastycznego spadku wydajności całej bazy.

.. code-block:: sql

    -- Przykład logiki transakcyjnej z wykorzystaniem konkretnego schematu
    BEGIN;
    INSERT INTO finanse.historia (kwota, opis) VALUES (200, 'Opłata serwisowa');
    UPDATE finanse.konta SET saldo = saldo - 200 WHERE id_klienta = 5;
    COMMIT;

Zarządzanie indeksami
=====================
Indeksy są fundamentalne dla wydajnego wyszukiwania danych, jednak ich utrzymanie kosztuje — spowalniają one modyfikacje danych (DML) i konsumują miejsce na dysku. 

Prawidłowe zarządzanie indeksami polega na stałym monitorowaniu ich wykorzystania. Należy identyfikować i usuwać indeksy, które nie są wykorzystywane przez planistę zapytań (tzw. unused indexes). Dodatkowo, podobnie jak tabele, indeksy ulegają fragmentacji. Z tego powodu administrator powinien regularnie planować operację **REINDEX**, która od nowa buduje strukturę drzewa indeksu, przywracając mu optymalny rozmiar i maksymalną wydajność. W systemach o wysokiej dostępności stosuje się przebudowę w trybie `CONCURRENTLY`, która nie przerywa pracy aplikacji.

Podsumowanie
============
Prawidłowa kontrola i konserwacja środowiska bazodanowego to wielowymiarowy proces, wymagający głębokiego zrozumienia zarówno architektury logicznej, jak i fizycznej serwera. 

Stabilność i wydajność systemu zależy w równej mierze od prawidłowego zarządzania stanem usługi i połączeniami, dogłębnego planowania okien serwisowych, jak i proaktywnego zarządzania mechanizmem Vacuum i transakcjami. Wykorzystanie schematów do strukturyzacji danych oraz regularne dbanie o kondycję indeksów pozwala na zbudowanie środowiska, które będzie skalowalne, przewidywalne i odporne na awarie w trudnych, produkcyjnych warunkach.

:Autorzy:
    1. Paweł Łoćwin
    2. Paweł Łosowski
