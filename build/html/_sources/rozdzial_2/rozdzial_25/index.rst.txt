==================================
Wydajność, skalowanie i replikacja
==================================

:Autorzy:
    1. Olaf Chomicki
    2. Konrad Machowski
    3. Wiktor Wydrzyński

Wydajność, skalowanie i replikacja
==================================

Współczesne systemy bazodanowe muszą sprostać wymaganiom związanym z wykładniczym przyrostem wolumenu danych oraz stale rosnącą liczbą jednoczesnych użytkowników. W tym kontekście kluczowe staje się zrozumienie trzech fundamentalnych pojęć: wydajności, skalowania i replikacji. Wydajność odnosi się do szybkości przetwarzania pojedynczych transakcji i zapytań przy optymalnym wykorzystaniu dostępnych zasobów. 

Gdy optymalizacja kodu przestaje wystarczać, konieczne staje się skalowanie – pionowe (zwiększanie mocy pojedynczego serwera) lub poziome (rozpraszanie obciążenia na wiele maszyn). Replikacja z kolei stanowi most łączący skalowanie odczytów z zapewnieniem wysokiej dostępności i odporności systemu na awarie sprzętowe.

Kontrola i buforowanie połączeń z bazą danych
=============================================

Nawiązywanie nowego połączenia z bazą danych jest operacją niezwykle kosztowną procesorowo i czasowo, ponieważ wymaga uwierzytelnienia użytkownika, alokacji pamięci oraz ustanowienia sesji sieciowej. W systemach o dużym natężeniu ruchu brak kontroli nad liczbą połączeń prowadzi do szybkiego wyczerpania zasobów serwera. 

Rozwiązaniem tego problemu jest buforowanie połączeń (Connection Pooling). Mechanizm ten polega na utrzymywaniu stałej puli otwartych, gotowych do użycia połączeń, które są wielokrotnie współdzielone przez aplikację. Narzędzia takie jak PgBouncer (dla PostgreSQL) czy wbudowane pule w serwerach aplikacji drastycznie zmniejszają narzut overhead, stabilizując czas reakcji bazy danych pod dużym obciążeniem.

Przykład konfiguracji PgBouncer (fragment pliku ``pgbouncer.ini``):

.. code-block:: ini

   [databases]
   moja_baza = host=127.0.0.1 port=5432 dbname=produkcja

   [pgbouncer]
   listen_port = 6432
   listen_addr = *
   auth_type = md5
   auth_file = /etc/pgbouncer/userlist.txt
   pool_mode = transaction
   max_client_conn = 1000
   default_pool_size = 20

INDEX i CLUSTER
===============

Indeksowanie to podstawowa technika optymalizacji zapytań o charakterze odczytowym. Instrukcja ``INDEX`` tworzy pomocniczą strukturę danych (najczęściej w formie B-drzewa), która pozwala silnikowi bazy danych na błyskawiczne odnalezienie żądanych wierszy bez konieczności kosztownego przeszukiwania całej tabeli (Full Table Scan). 

Z kolei polecenie ``CLUSTER`` idzie o krok dalej – fizycznie reorganizuje strukturę danych na dysku w taki sposób, aby kolejność wierszy w tabeli dokładnie odpowiadała kolejności indeksu. Powoduje to, że powiązane rekordy są składowane obok siebie w tych samych blokach pamięci, co radykalnie przyspiesza zapytania zakresowe (Range Queries).

Przykład użycia poleceń w PostgreSQL:

.. code-block:: sql

   -- 1. Tworzenie standardowego indeksu B-drzewa na kolumnie data_zamowienia
   CREATE INDEX idx_zamowienia_data ON zamowienia (data_zamowienia);

   -- 2. Fizyczne przemieszczenie danych na dysku według kolejności indeksu
   CLUSTER zamowienia USING idx_zamowienia_data;

Rola i zastosowanie replikacji
==============================

Replikacja polega na permanentnym kopiowaniu i synchronizowaniu danych z głównego węzła bazy danych (Primary/Master) na węzły pomocnicze (Replica/Slave). Jej rola w architekturze systemów IT jest wieloaspektowa. Po pierwsze, gwarantuje wysoką dostępność (High Availability) – w przypadku fizycznej awarii Mastera, jedna z replik może automatycznie przejąć jego funkcje (proces Failover). 

Po drugie, umożliwia skalowanie odczytów (Read Scalability). Przekierowanie operacji modyfikujących (INSERT, UPDATE) do węzła głównego, a operacji odczytu oraz generowania ciężkich raportów na repliki pozwala na znaczne odciążenie głównego serwera.

Oprogramowanie i zaimplementowane mechanizmy replikacji
=======================================================

Mechanizmy replikacji mogą być realizowane na poziomie silnika bazy danych lub za pomocą zewnętrznego oprogramowania. Wyróżnia się dwa główne podejścia pod kątem transmisji danych: replikację opartą na logu (WAL - Write-Ahead Logging) oraz replikację logiczną. Ze względu na synchronizację, proces ten może przebiegać synchronicznie lub asynchronicznie.

Przykład konfiguracji replikacji logicznej (wbudowanej w PostgreSQL):

.. code-block:: sql

   -- KROK 1: Uruchomienie na węźle głównym (Primary) - zdefiniowanie publikacji
   CREATE PUBLICATION pub_dane_sprzedazy FOR TABLE zamowienia, klienci;

   -- KROK 2: Uruchomienie na węźle pomocniczym (Replica) - subskrypcja danych
   CREATE SUBSCRIPTION sub_dane_sprzedazy 
   CONNECTION 'host=192.168.1.50 port=5432 dbname=produkcja user=repl_user password=secret' 
   PUBLICATION pub_dane_sprzedazy;

Limity systemu oraz ograniczanie dostępu użytkowników
=====================================================

Bezpieczeństwo i stabilność bazy danych wymagają rygorystycznego zarządzania limitami systemowymi oraz uprawnieniami. Zbyt duża swoboda przyznana użytkownikom lub procesom aplikacyjnym może doprowadzić do celowego bądź przypadkowego unieruchomienia systemu.

Przykład nakładania restrykcji i limitów zasobów w PostgreSQL:

.. code-block:: sql

   -- 1. Ograniczenie maksymalnej liczby jednoczesnych połączeń dla danej roli
   ALTER ROLE rola_analityk CONNECTION LIMIT 5;

   -- 2. Ustawienie maksymalnego czasu wykonywania pojedynczego zapytania (np. 30 sekund)
   ALTER ROLE rola_analityk SET statement_timeout = '30s';

   -- 3. Nadanie uprawnień wyłącznie do odczytu danych w wybranym schemacie
   REVOKE ALL ON ALL TABLES IN SCHEMA public FROM rola_analityk;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO rola_analityk;

Testy wydajności sprzętu na poziomie systemu operacyjnego
=========================================================

Przed wdrożeniem produkcyjnym bazy danych kluczowe jest przeprowadzenie niezależnych testów wydajnościowych podzespołów sprzętowych (Benchmarków) bezpośrednio na poziomie systemu operacyjnego, aby wykluczyć błędy konfiguracyjne środowiska.

Przykłady poleceń diagnostycznych i testowych w systemie Linux:

.. code-block:: bash

   # 1. Test wydajności procesora (CPU) za pomocą sysbench
   sysbench cpu --cpu-max-prime=20000 run

   # 2. Test przepustowości i alokacji pamięci RAM
   sysbench memory --memory-block-size=1M --memory-total-size=10G run

   # 3. Zaawansowany test wydajności dysku (IOPS i opóźnienia) narzędziem fio
   # Symulacja losowego odczytu/zapisu (Random R/W) specyficznego dla baz danych
   fio --name=test_bazy --ioengine=libaio --rw=randrw --bs=4k \
       --size=2G --numjobs=2 --runtime=30 --time_based \
       --filename=/var/lib/postgresql/test_io.file --group_reporting
