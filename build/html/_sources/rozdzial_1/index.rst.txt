================================
Wstęp do sprawozdania oraz linki
================================

:Autorzy:
    1. Olaf Chomicki
    2. Konrad Machowski
    3. Wiktor Wydrzyński

Wstęp
=====

Niniejszy dokument stanowi techniczną dokumentację laboratorium z przedmiotu Bazy Danych. Celem projektu była transformacja wiedzy teoretycznej w praktyczne kompetencje inżynierskie, obejmujące projektowanie, wdrażanie oraz administrację systemami relacyjnymi. Opracowanie opisuje pełen cykl wdrożeniowy oprogramowania: od analizy wymagań i modelowania (pojęciowego i logicznego), przez fizyczną implementację w środowiskach PostgreSQL i SQLite, aż po automatyzację procesów masowego zasilania struktur bazodanowych (ETL).

Wykaz repozytoriów (Linki)
==========================

Stosując standardy inżynierii oprogramowania, architekturę projektu podzielono na odrębne repozytoria w rozproszonym systemie kontroli wersji Git. Taka dekompozycja gwarantuje utrzymanie czystości architektury, separację warstwy dokumentacyjnej od kodu operacyjnego oraz ułatwia audyt zmian.

Główne repozytorium sprawozdania (Dokumentacja Sphinx)
------------------------------------------------------
Centralny węzeł dokumentacyjny projektu. Zawiera logikę sprawozdania zapisaną w formacie reStructuredText oraz pełną konfigurację środowiska kompilatora Sphinx (w tym pliki ``conf.py`` oraz ``Makefile``).

* **Link:** https://github.com/wikwyd/Repozytorium-Glowne.git

Repozytorium z plikami projektowymi
-----------------------------------
Baza kodu deweloperskiego. Przechowuje skrypty strukturalne DDL dostosowane do dialektów PostgreSQL i SQLite, wygenerowany plik wbudowanej bazy danych oraz płaskie zbiory danych (CSV) wykorzystane do zautomatyzowanego populowania tabel.

* **Link:** https://github.com/wikwyd/pliki.git

Repozytoria reszty grupy (Submoduły)
------------------------------------
Poniższa sekcja zawiera wykaz repozytoriów, w których zespoły opracowywały dedykowane tematy specjalistyczne. Aby zapewnić spójność ostatecznego dokumentu, repozytoria te zostały zintegrowane z głównym projektem jako submoduły (submodules) i stanowią treść Rozdziału 2.

* **Grupa 1 (rozdzial_1):** https://github.com/karaskamil/Sprzet-dla-bazy-danych.git
* **Grupa 2 (rozdzial_2):** https://github.com/Youarecheck/Bazy_Danych_Tematyczne_Repo_MK.git
* **Grupa 3 (rozdzial_3):** https://github.com/pawlos1337/Bazy-danych-temat.git
* **Grupa 4 (rozdzial_4):** https://github.com/OskarProgrammer/monitorowanie_i_diagnostyka.git
* **Grupa 5 (rozdzial_5):** https://github.com/KMachoK/Tematyczne.git
* **Grupa 6 (rozdzial_6):** https://github.com/domino0472/Partycjonowani-Danych
* **Grupa 7 (rozdzial_7):** https://github.com/oski486/BazyDanych-Subject.git
* **Grupa 8 (rozdzial_8):** https://github.com/Koko9077/Kopie-zapasowe-i-odzyskiwanie-danych.git