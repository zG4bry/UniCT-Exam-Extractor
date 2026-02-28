"""CLI OOP per consultazione appelli da SQLite e export in formato iCalendar."""

from __future__ import annotations

import argparse
import sys

from exam_services import CalendarExporter, ExamRepository


class ExamManagerCLI:
    """Interfaccia utente per listing, ricerca e export ICS."""

    def __init__(self, db_path: str = "esami.db") -> None:
        self.repository = ExamRepository(db_path)

    @staticmethod
    def _print_rows(rows: list[tuple[int, str, str, str]], title: str) -> None:
        print(f"\n{title}")
        print(f"\n{'ID':<4} | {'Data':<12} | {'Tipo':<15} | {'Materia'}")
        print("-" * 80)
        for exam_id, materia, data_esame, tipo in rows:
            print(f"{exam_id:<4} | {data_esame:<12} | {tipo:<15} | {materia}")
        print(f"\nTotale esami trovati: {len(rows)}")

    def show_all(self) -> None:
        """Mostra tutti gli esami presenti nel DB."""
        rows = self.repository.list_exams()
        self._print_rows(rows, "Elenco completo appelli")

    def search_subject(self, subject: str) -> None:
        """Cerca esami per materia."""
        rows = self.repository.search_exams(subject)
        if not rows:
            print(f"\nNessun esame trovato per '{subject}'.")
            return
        self._print_rows(rows, f"Risultati per materia: {subject}")

    def export_ics(self, subject_filter: str | None, output_file: str) -> None:
        """Esporta gli esami filtrati (o tutti) in un file .ics."""
        exams = self.repository.fetch_for_calendar(subject_filter)
        if not exams:
            print("Nessun esame da esportare.")
            return

        exported = CalendarExporter.export(exams, output_file=output_file)
        print(f"\nEsportati {exported} appelli nel file '{output_file}'.")
        print("Puoi importarlo in Google Calendar, Apple Calendar o altri client.")


def build_arg_parser() -> argparse.ArgumentParser:
    """Configura gli argomenti CLI."""
    cli = argparse.ArgumentParser(description="UniCT Exam Extractor (DMI) - Gestore Appelli")
    cli.add_argument("--db", default="esami.db", help="Percorso file database SQLite")
    cli.add_argument("--lista", action="store_true", help="Mostra tutti gli appelli")
    cli.add_argument(
        "--cerca",
        type=str,
        metavar="MATERIA",
        help="Cerca appelli per una specifica materia",
    )
    cli.add_argument(
        "--ics",
        action="store_true",
        help="Esporta gli appelli in un file calendario (.ics)",
    )
    cli.add_argument(
        "--output",
        type=str,
        default="esami.ics",
        help="Nome file .ics di output (default: esami.ics)",
    )
    return cli


def main() -> None:
    """Entrypoint CLI."""
    parser = build_arg_parser()
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    manager = ExamManagerCLI(db_path=args.db)

    if args.lista:
        manager.show_all()
    elif args.cerca:
        manager.search_subject(args.cerca)

    if args.ics:
        manager.export_ics(subject_filter=args.cerca, output_file=args.output)


if __name__ == "__main__":
    main()
