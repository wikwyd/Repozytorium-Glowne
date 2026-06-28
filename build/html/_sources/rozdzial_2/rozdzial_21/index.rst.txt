======================================================
Sprzęt dla bazy danych
======================================================

:Autorzy:
    1. Wiktor Głogowski
    2. Olga Grześkowiak
    3. Kamil Karaś


Wstęp
=====

Współczesne systemy zarządzania bazami danych (DBMS) stanowią fundament operacyjny większości przedsiębiorstw. Efektywność ich działania zależy bezpośrednio od synergii pomiędzy warstwą oprogramowania a architekturą sprzętową, na której są one uruchamiane. Bazy danych wykazują unikalne, skrajnie wysokie wymagania względem podsystemów wejścia/wyjścia (I/O), procesora, pamięci operacyjnej oraz niezawodności zasilania.

W zależności od profilu obciążenia systemu, infrastrukturę sprzętową klasyfikuje się pod dwa główne typy zadań:

* **OLTP (Online Transaction Processing):** Systemy transakcyjne charakteryzujące się ogromną liczbą jednoczesnych, krótkich operacji zapisu i odczytu (np. systemy bankowe, sklepy internetowe). Kluczowym parametrem jest tu minimalne opóźnienie oraz wysoka liczba operacji wejścia/wyjścia na sekundę (IOPS).
* **OLAP (Online Analytical Processing):** Hurtownie danych i systemy analityczne realizujące długie, złożone zapytania, które agregują miliony rekordów. Tutaj priorytetem jest przepustowość sekwencyjna oraz masowa wielordzeniowość procesorów.

Poniższy rozdział opisuje architekturę fizyczną bazy danych oraz wytyczne w sprawie doboru komponentów.

Procesor (CPU)
==============

Wybór procesora dla serwera bazodanowego determinowany jest nie tylko surową wydajnością obliczeniową, ale również architekturą pamięci podręcznej, topologią połączeń międzygniazdowych oraz modelami licencjonowania oprogramowania.

Wydajność Jednowątkowa vs Wielordzeniowość
------------------------------------------

Decyzja o wyborze modelu procesora zależy od struktury zapytań generowanych przez aplikację:

1. **Taktowanie Zegara:** W środowiskach OLTP, gdzie transakcje często wykonują się sekwencyjnie lub są blokowane przez zamki i zatrzaski, wyższe taktowanie rdzenia (np. 3.6 GHz - 4.0 GHz) przynosi lepsze rezultaty niż ekstremalna liczba rdzeni o niskim taktowaniu. Szybka realizacja pojedynczego wątku skraca czas trwania blokad.
2. **Skalowanie Wielordzeniowe:** W systemach OLAP silniki baz danych potrafią dzielić jedno zapytanie na wiele wątków. W tym przypadku procesory posiadające 64, 96 lub więcej rdzeni fizycznych (np. AMD EPYC, Intel Xeon Scalable) pozwalają na równoległe skanowanie indeksów i tabel, drastycznie przyspieszając operacje analityczne.

**Wpływ Licencjonowania na Wybór CPU:** Wiodący producenci oprogramowania bazodanowego (np. Microsoft SQL Server Enterprise, Oracle) stosują model licencjonowania per-core. Koszt licencji na jeden rdzeń wielokrotnie przewyższa koszt zakupu samego sprzętu. Z tego powodu ekonomicznie i wydajnościowo uzasadniony jest wybór procesorów o mniejszej liczbie rdzeni, ale o maksymalnym dostępnym taktowaniu bazowym i zaawansowanej architekturze cache.

Topologia NUMA (Non-Uniform Memory Access)
------------------------------------------

Wieloprocesorowe serwery (np. architektury dwu- lub czterogniazdowe) dzielą zasoby na tzw. węzły NUMA. Każdy procesor posiada swój zintegrowany kontroler pamięci i bezpośredni dostęp do fizycznie najbliższych banków RAM (pamięć lokalna).

* **Dostęp Lokalny:** Charakteryzuje się minimalnymi opóźnieniami i maksymalnym pasmem przenoszenia.
* **Dostęp Zdalny:** Jeśli procesor osadzony w gnieździe 0 potrzebuje danych znajdujących się w banku pamięci przypisanym do gniazda 1, transakcja musi odbyć się za pośrednictwem magistrali międzyprocesorowej (Intel UPI lub AMD Infinity Fabric). Generuje to narzut opóźnienia zwany *NUMA penalty*.

Niewłaściwa alokacja wątków przez system operacyjny może prowadzić do ciągłego przemieszczania danych między węzłami (*NUMA bouncing*), co drastycznie obniża wydajność bazy danych. Wymagane jest stosowanie silników bazodanowych w pełni wspierających i optymalizujących architekturę NUMA (*NUMA-aware*).

Znaczenie Pamięci Podręcznej (Cache L3)
---------------------------------------

Struktury danych w relacyjnych bazach (drzewa B+, tabele stron) sprawiają, że procesor wykonuje ogromną liczbę operacji skoków i wyszukiwań wskaźników. Powoduje to częste chybienia pamięci podręcznej, zmuszając procesor do czekania na dane z RAM-u. Procesory wyposażone w powiększoną pamięć podręczną poziomu trzeciego (L3), takie jak układy z technologią 3D V-Cache, pozwalają na zatrzymanie krytycznych struktur indeksowych wewnątrz struktur procesora, generując ogromne zyski wydajnościowe.

Pamięć RAM
==========

Pamięć operacyjna RAM decyduje o tym, jak duża część bazy danych może być przetwarzana bezpośrednio w super-szybkiej pamięci półprzewodnikowej, bez konieczności odwoływania się do podsystemu dyskowego.

Mechanizm Buforowania Danych
----------------------------

Podstawową jednostką wymiany danych między dyskiem a pamięcią w bazach danych jest strona (zazwyczaj o rozmiarze 8 KB). Silnik bazy danych alokuje obszar pamięci RAM nazywany **Buffer Pool** (w MS SQL Server) lub **Shared Buffers** (w PostgreSQL).

* **Odczyty z Pamięci (Logical Reads):** Jeśli żądana strona danych znajduje się już w RAM, odczyt następuje natychmiastowo (rzędu nanosekund).
* **Odczyty z Dysku (Physical Reads):** W przypadku braku strony w buforze, wątek bazy danych zostaje zawieszony do czasu fizycznego załadowania strony z pamięci masowej, co zwiększa czas odpowiedzi o rzędy wielkości.

Docelowym stanem konfiguracyjnym dla systemów produkcyjnych jest posiadanie takiej ilości pamięci RAM, która pozwala na bezproblemowe przetrzymywanie w całości tzw. hot data set, czyli najczęściej modyfikowanych i odpytywanych danych wraz z ich indeksami.

Wymóg Technologii ECC (Error-Correcting Code)
--------------------------------------------------------

W serwerach bazodanowych niedopuszczalne jest stosowanie pamięci bez obsługi korekcji błędów (non-ECC). Pamięci **ECC** posiadają dodatkowe układy scalone pozwalające na wykrywanie i automatyczną korekcję błędów jednobitowych oraz wykrywanie błędów wielobitowych.

Wystąpienie zjawiska *bit-flip* (samorzutnej zmiany wartości bitu w pamięci RAM pod wpływem np. tła radiacyjnego lub zakłóceń elektromagnetycznych) w systemie bez ECC niesie katastrofalne skutki dla baz danych:
   
* **Cicha korupcja danych:** Błędna wartość może zostać zapisana z bufora pamięci wprost na dysk, powodując trwałe i niezauważalne zniszczenie struktury tabeli lub błędne zapisy księgowe.
* **Uszkodzenie stron indeksowych:** Powoduje błędy integralności i uniemożliwia poprawne wykonywanie zapytań SQL.
* **Awaria krytyczna:** W przypadku naruszenia pamięci jądra systemu operacyjnego lub krytycznego procesu bazy danych dochodzi do natychmiastowego zatrzymania serwera (Kernel Panic / BSOD).

Parametry Wydajnościowe: Przepustowość i Opóźnienia
---------------------------------------------------

Współczesne standardy serwerowe opierają się na pamięciach DDR5, oferujących zaawansowaną architekturę wielokanałową (np. 8 lub 12 kanałów pamięci na jedno gniazdo CPU). Wysoka przepustowość (wyrażana w MT/s) przyspiesza operacje sortowania w pamięci, tworzenie tabel tymczasowych oraz operacje złączania typu *Hash Join*, które są na porządku dziennym w systemach analitycznych.

Pamięć Masowa
============================

Podsystem pamięci masowej bezpośrednio determinuje ostateczną trwałość danych (cecha *Durability* z paradygmatu ACID) oraz jest najczęstszym wąskim gardłem systemu informatycznego z uwagi na mechaniczne lub interfejsowe ograniczenia prędkości.

Klasyfikacja Nośników i Ich Przydatność
---------------------------------------

Współczesna inżynieria bazodanowa całkowicie odchodzi od talerzowych dysków magnetycznych HDD w środowiskach produkcyjnych na rzecz pamięci półprzewodnikowych Flash.

* **Dyski HDD (SAS 10K/15K):** Ze względu na ograniczenia mechaniczne oferują zaledwie kilkaset IOPS i wysokie opóźnienia (>5 ms). Ich zastosowanie ogranicza się obecnie wyłącznie do składowania archiwalnych kopii zapasowych (backups).
* **Dyski SSD (SATA/SAS Enterprise):** Zapewniają stabilną wydajność na poziomie do 90 000 IOPS dla odczytu, jednak ograniczeniem staje się interfejs SATA (6 Gb/s) lub SAS-3 (12 Gb/s).
* **Nośniki NVMe (PCIe Gen4/Gen5):** Komunikują się bezpośrednio z procesorem poprzez magistralę PCI Express, eliminując narzut protokołów SCSI/ATA. Osiągają wydajność przekraczającą 1 000 000 IOPS oraz redukują opóźnienia do wartości mikrosekundowych (<50 µs), stając się bezdyskusyjnym standardem dla baz danych.

Fizyczna Separacja Architektury Plików
--------------------------------------

Poprawna konfiguracja pamięci masowej wymaga rozdzielenia różnych typów aktywności wejścia/wyjścia na odseparowane fizycznie wolumeny dyskowe:

1. **Dziennik Transakcji:** Każda operacja modyfikacji danych (INSERT, UPDATE, DELETE) musi zostać najpierw sekwencyjnie zapisana w dzienniku transakcji, zanim baza potwierdzi jej pomyślne wykonanie. Ruch ten ma charakter niemal wyłącznie sekwencyjnego zapisu o krytycznym znaczeniu dla opóźnienia aplikacji. Dziennik transakcji powinien znajdować się na najszybszych dedykowanych nośnikach o minimalnym opóźnieniu zapisu.
2. **Pliki Danych:** Przechowują właściwe tabele i indeksy. Ruch na tych plikach ma charakter wysoce losowy (zarówno odczyty, jak i zapisy wywoływane przez proces *Checkpoint*, który zrzuca zmodyfikowane strony z RAM na dysk). Wymagają macierzy zoptymalizowanej pod kątem wysokiej liczby losowych IOPS.
3. **Baza Tymczasowa (TempDB / Swapping Space):** Wykorzystywana przez silnik bazy do przechowywania obiektów tymczasowych, wyników pośrednich podzapytań oraz sortowania. Generuje bardzo intensywny, mieszany ruch. Umieszcza się ją na ultra-szybkich dyskach o wysokiej wytrzymałości.

Żywotność i Wytrzymałość Zapisu (DWPD)
--------------------------------------

Bazy danych nieustannie modyfikują i nadpisują sektory. Z tego powodu stosowanie dysków klasy konsumenckiej grozi ich błyskawicznym zużyciem. Przy doborze nośników kluczowym parametrem jest **DWPD** (*Drive Writes Per Day*) – wskaźnik określający, ile razy dziennie można zapisać całą pojemność dysku przez okres gwarancyjny (zazwyczaj 5 lat). Do baz danych wymagane są nośniki klasy *Enterprise Mixed-Use* lub *Write-Intensive* o współczynniku DWPD wynoszącym minimum 3-5.

Kontrolery i Interfejsy Pamięci
===============================

Kontrolery realizują zadania pośrednictwa, zarządzania macierzami nadmiarowymi (RAID) oraz gwarantują integralność zapisu.

Sprzętowy RAID vs Software-Defined Storage
------------------------------------------

Przez lata standardem były sprzętowe kontrolery RAID (*Hardware RAID*) wyposażone we własny procesor i pamięć cache. Odciążają one procesor główny serwera z obliczeń sum kontrolnych (szczególnie parzystości w RAID 5/6).

W przypadku nowoczesnych pamięci NVMe sprzętowe kontrolery starszego typu stawały się wąskim gardłem, blokując bezpośredni dostęp do linii PCIe. Współcześnie odchodzi się od nich na rzecz:

* **Bezpośredniego podłączenia NVMe (Direct Attached PCIe)** i zarządzania programowego na poziomie zaawansowanych systemów plików (np. ZFS) lub warstw logicznych OS (np. Linux mdadm / LVM).
* Modernistycznych, dedykowanych sprzętowych kontrolerów NVMe RAID klasy Enterprise, zdolnych do natywnego przetwarzania protokołu NVMe z pełną prędkością magistrali PCIe Gen5.

**Pamięć Podtrzymywana Bateryjnie (BBU/FBWC):**
W przypadku korzystania ze sprzętowego kontrolera RAID z włączoną pamięcią podręczną zapisu (*Write-Back Cache*), **bezwzględnym warunkiem bezpieczeństwa** jest obecność modułu **BBU** (*Battery Backup Unit*) lub **FBWC** (*Flash-Backed Write Cache*). W razie awarii zasilania serwera, moduł ten podtrzymuje dane w pamięci cache kontrolera (lub przepisuje je do dedykowanej pamięci flash), zapobiegając utracie nieutrwalonych transakcji i uszkodzeniu struktury macierzy.

Wybór Poziomu RAID pod Kątem Baz Danych
---------------------------------------

* **RAID 10 (Striped Mirror):** Rekomendowany układ dla większości systemów bazodanowych. Łączy zalety wydajnościowe paskowania (RAID 0) i bezpieczeństwa lustrzanego (RAID 1). Zapewnia doskonałą wydajność losowego zapisu, ponieważ nie generuje tzw. narzutu parzystości (*write penalty*).
* **RAID 5 / RAID 6:** Zapewniają lepsze wykorzystanie przestrzeni dyskowej, ale każda operacja zapisu wymaga odczytu danych, obliczenia nowej parzystości i ponownego zapisu (*kara za zapis*). Są **wysoce niewskazane dla baz transakcyjnych OLTP**. Mogą być stosowane jedynie w hurtowniach danych (OLAP), gdzie operacje zapisu są sekwencyjne i rzadkie (procesy ETL).

Zasilanie i Niezawodność
========================

Podsystem zasilania w infrastrukturze bazodanowej traktowany jest jako integralny element ochrony integralności logicznej danych, a nie tylko komponent ciągłości działania.

Nadmiarowość Zasilaczy i Niezależne Linie Zasilające
----------------------------------------------------

Serwer bazodanowy musi posiadać zasilacze nadmiarowe typu *Hot-Swap* (z możliwością wymiany podczas pracy) w konfiguracji minimum **N+1** lub optymalnie **2N** (Full Redundancy). 

Zasilacze muszą być podpięte do fizycznie odseparowanych źródeł zasilania:

* **Zasilacz A:** Podłączony do Linii zasilającej A oraz dedykowanego modułu UPS A.
* **Zasilacz B:** Podłączony do Linii zasilającej B oraz dedykowanego modułu UPS B.

Taka topologia gwarantuje, że awaria jednego zasilacza, uszkodzenie kabla lub całkowity zanik napięcia na jednej z linii energetycznych nie spowoduje wyłączenia serwera.

Infrastruktura UPS i Agregaty Prądotwórcze
------------------------------------------

Wszelkie systemy serwerowe DBMS muszą współpracować z zasilaczami awaryjnymi UPS działającymi w topologii *Online* (podwójne przetwarzanie). Zapewniają one idealną sinusoidę napięcia, eliminują przepięcia i gwarantują czas podtrzymania niezbędny do automatycznego uruchomienia spalinowych agregatów prądotwórczych o odpowiedniej mocy.

Zapobieganie Zjawisku "Torn Writes"
-----------------------------------

Zjawisko *Torn Write* (rozbity/częściowy zapis) występuje, gdy system operacyjny przesyła do zapisu stronę danych (np. 8 KB), a w trakcie fizycznego zapisu na komórkę pamięci Flash dochodzi do nagłego odcięcia zasilania. W efekcie na dysku ląduje np. tylko 4 KB danych, co powoduje bezpowrotne uszkodzenie struktury tej strony i błąd sumy kontrolnej przy próbie kolejnego uruchomienia bazy danych.

Poza mechanizmami programowymi (takimi jak *Doublewrite Buffer* w silniku InnoDB/MySQL), na poziomie sprzętowym stosuje się technologię **PLP (Power Loss Protection)**. Dyski klasy Enterprise posiadają wbudowane banki kondensatorów tantalowych. W momencie wykrycia spadku napięcia, energia z kondensatorów pozwala na podtrzymanie pracy kontrolera dysku przez czas wymagany do bezpiecznego opróżnienia pamięci podręcznej RAM dysku i utrwalenia wszystkich danych w nieulotnych komórkach pamięci NAND Flash.


Podsumowanie
============

Dobór sprzętu dla systemów zarządzania bazami danych musi być ściśle dopasowany do profilu obciążenia, z wyraźnym podziałem na transakcyjne środowiska OLTP oraz analityczne systemy OLAP. Wybór procesora stanowi kompromis pomiędzy taktowaniem a wielordzeniowością ze względu na koszty licencyjne, podczas gdy w przypadku pamięci operacyjnej absolutnym wymogiem jest zastosowanie technologii ECC chroniącej przed cichą korupcją danych. W obszarze pamięci masowej standardem stały się nośniki półprzewodnikowe NVMe o wysokiej wytrzymałości (DWPD), które ze względów wydajnościowych wymagają fizycznej separacji wolumenów dla dzienników transakcji i plików danych. Do zabezpieczenia pracy dysków rekomenduje się użycie konfiguracji RAID 10 w połączeniu z nowoczesnymi kontrolerami sprzętowymi lub rozwiązaniami programowymi. Całość infrastruktury musi być kategorycznie chroniona przed awariami poprzez nadmiarowe zasilacze w konfiguracji 2N, systemy UPS w topologii Online oraz dyski wyposażone w sprzętową ochronę PLP eliminującą zjawisko uszkodzonych zapisów.
