"""Servizi OOP per parsing PDF, persistenza SQLite ed export calendario."""

import re
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pdfplumber
import requests


@dataclass(frozen=True, slots=True)
class ExamRecord:
    """Rappresenta un singolo appello d'esame."""

    materia: str
    data_esame: date
    tipo: str

    @property
    def data_iso(self) -> str:
        """Restituisce la data nel formato ISO usato nel DB."""
        return self.data_esame.isoformat()


class ItalianDateParser:
    """Utility per convertire date italiane in oggetti datetime/date."""

    MONTHS = {
        "GEN": 1,
        "FEB": 2,
        "MAR": 3,
        "APR": 4,
        "MAG": 5,
        "GIU": 6,
        "LUG": 7,
        "AGO": 8,
        "SET": 9,
        "OTT": 10,
        "NOV": 11,
        "DIC": 12,
        "GENNAIO": 1,
        "FEBBRAIO": 2,
        "MARZO": 3,
        "APRILE": 4,
        "MAGGIO": 5,
        "GIUGNO": 6,
        "LUGLIO": 7,
        "AGOSTO": 8,
        "SETTEMBRE": 9,
        "OTTOBRE": 10,
        "NOVEMBRE": 11,
        "DICEMBRE": 12,
    }

    @classmethod
    def parse_day_list(cls, day_str: str, month: int, year: int) -> list[date]:
        """Estrae una lista di date da stringhe tipo '1, 21' o '2 e 22'."""
        result: list[date] = []
        for day_text in re.findall(r"\d+", day_str):
            try:
                result.append(date(year, month, int(day_text)))
            except ValueError:
                continue
        return result

    @classmethod
    def parse_full_date(cls, raw_text: str) -> date | None:
        """Parsa stringhe tipo '30 ottobre 2025'."""
        match = re.search(r"(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})", raw_text)
        if not match:
            return None

        day = int(match.group(1))
        month_name = match.group(2).upper()
        year = int(match.group(3))
        month = cls.MONTHS.get(month_name[:3])
        if month is None:
            return None

        try:
            return date(year, month, day)
        except ValueError:
            return None


class ExamPdfParser:
    """Parser dei PDF per esami ordinari e fuori corso."""

    def parse_regular(self, pdf_path: str) -> list[ExamRecord]:
        """Legge il PDF degli appelli ordinari."""
        exams: list[ExamRecord] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or not table[0]:
                        continue
                    header = [str(cell).replace("\n", " ").strip() for cell in table[0]]
                    if len(header) < 2 or "INSEGNAMENTO" in header[0].upper():
                        continue

                    month_columns: dict[int, tuple[int, int]] = {}
                    for idx, col_name in enumerate(header[1:], start=1):
                        match = re.search(r"([A-Za-z]+)\s*(\d{4})", col_name)
                        if not match:
                            continue
                        month_name = match.group(1).upper()
                        year = int(match.group(2))
                        month = ItalianDateParser.MONTHS.get(month_name[:3])
                        if month is not None:
                            month_columns[idx] = (month, year)

                    for row in table[1:]:
                        if not row or not row[0]:
                            continue
                        materia = str(row[0]).replace("\n", " ").strip()
                        materia_upper = materia.upper()
                        if (
                            not materia
                            or "AULA" in materia_upper
                            or "PRIMO ANNO" in materia_upper
                            or "SECONDO ANNO" in materia_upper
                        ):
                            continue

                        for idx, (month, year) in month_columns.items():
                            if idx >= len(row) or not row[idx]:
                                continue
                            day_text = str(row[idx]).replace("\n", " ")
                            for day in ItalianDateParser.parse_day_list(
                                day_text, month, year
                            ):
                                exams.append(
                                    ExamRecord(
                                        materia=materia,
                                        data_esame=day,
                                        tipo="Ordinario",
                                    )
                                )
        return exams

    def parse_out_of_course(self, pdf_path: str) -> list[ExamRecord]:
        """Legge il PDF degli appelli fuori corso."""
        exams: list[ExamRecord] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or not table[0]:
                        continue
                    header = [str(cell).replace("\n", " ").strip().upper() for cell in table[0]]
                    if "INSEGNAMENTO" not in header:
                        continue

                    for row in table[1:]:
                        if not row or not row[0]:
                            continue
                        materia = str(row[0]).replace("\n", " ").strip()
                        materia_upper = materia.upper()
                        if (
                            not materia
                            or "ANNO" in materia_upper
                            or "CORSO DI LAUREA" in materia_upper
                        ):
                            continue

                        for cell in row[1:]:
                            if not cell:
                                continue
                            parsed = ItalianDateParser.parse_full_date(
                                str(cell).replace("\n", " ").strip()
                            )
                            if parsed is None:
                                continue
                            exams.append(
                                ExamRecord(
                                    materia=materia,
                                    data_esame=parsed,
                                    tipo="Fuori Corso",
                                )
                            )
        return exams


class PdfFetcher:
    """Gestisce il download dei PDF con fallback ai file locali."""

    @staticmethod
    def ensure_pdf(source_url: str, destination: str, allow_download: bool) -> str:
        """Assicura la presenza del PDF, scaricandolo se richiesto."""
        destination_path = Path(destination)
        if allow_download:
            try:
                response = requests.get(source_url, timeout=30)
                response.raise_for_status()
                destination_path.write_bytes(response.content)
                print(f"Scaricato: {source_url} -> {destination}")
            except requests.RequestException as exc:
                if destination_path.exists():
                    print(
                        f"Download fallito ({exc}). Uso il file locale esistente: {destination}"
                    )
                else:
                    raise RuntimeError(
                        f"Impossibile scaricare {source_url} e file locale assente: {destination}"
                    ) from exc
        elif not destination_path.exists():
            raise FileNotFoundError(
                f"File PDF non trovato: {destination}. "
                "Rimuovi --no-download o indica un file valido."
            )
        return str(destination_path)


class ExamRepository:
    """Repository SQLite per lettura/scrittura appelli."""

    def __init__(self, db_path: str = "esami.db") -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def init_schema(self, clear_existing: bool = False) -> None:
        """Inizializza schema tabella."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS appelli (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    materia TEXT NOT NULL,
                    data_esame TEXT NOT NULL,
                    tipo TEXT NOT NULL
                    UNIQUE(materia, data_esame, tipo)
                )
                """
            )
            if clear_existing:
                cursor.execute("DELETE FROM appelli")
            conn.commit()

    def save_exams(self, exams: list[ExamRecord]) -> int:
        """Salva gli appelli evitando duplicati."""
        if not exams:
            return 0
        unique = sorted(
            {(exam.materia, exam.data_iso, exam.tipo) for exam in exams},
            key=lambda row: (row[1], row[0], row[2]),
        )
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT OR IGNORE INTO appelli (materia, data_esame, tipo)
                VALUES (?, ?, ?)
                """,
                unique,
            )
            conn.commit()
        return len(unique)

    def list_exams(self) -> list[tuple[int, str, str, str]]:
        """Restituisce tutti gli esami ordinati per data formato GG-MM-YYYY nell'output."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, materia, strftime('%d-%m-%Y', data_esame) as data_esame, tipo
                FROM appelli
                ORDER BY appelli.data_esame, materia
                """
            )
            return cursor.fetchall()

    def search_exams(self, materia_filter: str) -> list[tuple[int, str, str, str]]:
        """Restituisce gli esami filtrati per materia con data in GG-MM-YYYY."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, materia, strftime('%d-%m-%Y', data_esame) as data_esame, tipo
                FROM appelli
                WHERE materia LIKE ?
                ORDER BY appelli.data_esame, materia
                """,
                (f"%{materia_filter}%",),
            )
            return cursor.fetchall()

    def fetch_for_calendar(self, materia_filter: str | None = None) -> list[ExamRecord]:
        """Recupera gli appelli in formato ExamRecord."""
        with self._connect() as conn:
            cursor = conn.cursor()
            if materia_filter:
                cursor.execute(
                    """
                    SELECT materia, data_esame, tipo
                    FROM appelli
                    WHERE materia LIKE ?
                    ORDER BY data_esame, materia
                    """,
                    (f"%{materia_filter}%",),
                )
            else:
                cursor.execute(
                    """
                    SELECT materia, data_esame, tipo
                    FROM appelli
                    ORDER BY data_esame, materia
                    """
                )
            rows = cursor.fetchall()

        parsed: list[ExamRecord] = []
        for materia, data_esame, tipo in rows:
            parsed.append(
                ExamRecord(
                    materia=materia,
                    data_esame=datetime.strptime(data_esame, "%Y-%m-%d").date(),
                    tipo=tipo,
                )
            )
        return parsed


class CalendarExporter:
    """Esporta gli esami in formato iCalendar."""

    @staticmethod
    def export(exams: list[ExamRecord], output_file: str) -> int:
        """Scrive il file .ics e ritorna il numero di eventi esportati."""
        from icalendar import Calendar, Event

        cal = Calendar()
        cal.add("prodid", "-//UniCT Exam Extractor (DMI)//")
        cal.add("version", "2.0")

        for exam in exams:
            event = Event()
            event.add("summary", f"Esame: {exam.materia} ({exam.tipo})")
            event.add("dtstart", exam.data_esame)
            event.add("description", f"Appello di {exam.materia} ({exam.tipo})")
            cal.add_component(event)

        Path(output_file).write_bytes(cal.to_ical())
        return len(exams)
