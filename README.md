# UniCT Exam Extractor (DMI)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**UniCT Exam Extractor** è uno strumento in Python progettato per gli studenti del **Dipartimento di Matematica e Informatica (DMI)** dell'Università di Catania. 

Lo script automatizza l'estrazione delle date degli appelli d'esame dai PDF ufficiali pubblicati dal portale (attualmente ottimizzato per i corsi di **Informatica**), li organizza in un database SQLite locale e permette di esportarli in formato `.ics` per integrarli istantaneamente nei propri calendari digitali.

---

## ✨ Funzionalità

*   **⚡ Estrazione Mirata**: Parsing specializzato per i PDF degli appelli (Ordinari e Fuori Corso) del DMI Catania (Area Informatica).
*   **💾 Database SQLite**: Archiviazione locale in `esami.db`, permettendo ricerche e filtri istantanei senza dover rielaborare i PDF.
*   **🔍 Ricerca Intelligente via CLI**:
    *   Interfaccia a riga di comando semplice e intuitiva.
    *   Ricerca per materia con supporto parziale (es. "Programmazione").
    *   Visualizzazione date ottimizzata in formato italiano `GG-MM-YYYY`.
*   **📅 Sync Calendario (.ics)**: Esportazione in formato iCalendar universale, compatibile con Google Calendar, Apple Calendar e Outlook.

---

## 🛠️ Architettura e Struttura File

Il progetto è strutturato in moduli indipendenti per separare la logica di estrazione dalla visualizzazione:

| File / Modulo            | Descrizione                                                                                                                                     |
| :----------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------- |
| **`exam_services.py`**   | Logica core: interazione con SQLite (`ExamRepository`), parsing date e generazione `.ics` (`CalendarExporter`).                               |
| **`gestore_esami.py`**   | Interfaccia CLI utente. Permette di consultare il database e gestire le esportazioni.                                                         |
| **`parser.py`**         | Motore di ingestion. Utilizza `pdfplumber` per estrarre i dati dai PDF e popolarli nel database.                                             |

---

## 🚀 Requisiti e Installazione

Il progetto richiede **Python 3.10+**.

### 1. Setup Locale
```bash
git clone https://github.com/tuo-username/unict-exam-extractor.git
cd unict-exam-extractor
```

### 2. Ambiente Virtuale & Dipendenze
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 💻 Guida all'uso

### Fase 1: Ingestione dei dati
Posiziona i PDF degli appelli nella cartella principale (es. `esami_regolari.pdf` e `esami_fuori_corso.pdf`) ed esegui il parsing:
```bash
python3 parser.py
```

### Fase 2: Consultazione
Una volta popolato il database, usa `gestore_esami.py`:

**Elenco completo:**
```bash
python3 gestore_esami.py --lista
```

**Ricerca per materia:**
```bash
python3 gestore_esami.py --cerca "Architettura"
```

### Fase 3: Esportazione ICS
Per portare gli esami sul tuo smartphone o PC:
```bash
# Esporta tutti gli appelli
python3 gestore_esami.py --ics

# Esporta solo una materia specifica
python3 gestore_esami.py --cerca "Analisi" --ics --output "analisi.ics"
```

---


## 📝 Licenza

Distribuito sotto la Licenza MIT. 
© 2026 - UniCT Exam Extractor Team
