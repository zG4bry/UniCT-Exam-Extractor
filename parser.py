"""CLI per parsing dei PDF degli esami e salvataggio nel DB SQLite."""
import argparse

from exam_services import ExamPdfParser, ExamRepository, PdfFetcher

DEFAULT_URL_REGOLARI = (
    "https://web.dmi.unict.it/sites/default/files/ESAMI%202025-26_v6.pdf"
)
DEFAULT_URL_FUORI_CORSO = (
    "https://web.dmi.unict.it/sites/default/files/ESAMI%20Fuori%20Corso%202025-26.pdf"
)


class ExamImportPipeline:
    """Orchestration del flusso import PDF -> parsing -> salvataggio DB."""

    def __init__(
        self,
        db_path: str,
        regolari_pdf_path: str,
        fuori_corso_pdf_path: str,
        regolari_url: str = DEFAULT_URL_REGOLARI,
        fuori_corso_url: str = DEFAULT_URL_FUORI_CORSO,
    ) -> None:
        self.db_path = db_path
        self.regolari_pdf_path = regolari_pdf_path
        self.fuori_corso_pdf_path = fuori_corso_pdf_path
        self.regolari_url = regolari_url
        self.fuori_corso_url = fuori_corso_url
        self.parser = ExamPdfParser()
        self.repository = ExamRepository(db_path)

    def run(self, allow_download: bool, reset_db: bool) -> int:
        """Esegue l'import completo e ritorna il numero di record salvati."""
        regolari_pdf = PdfFetcher.ensure_pdf(
            self.regolari_url, self.regolari_pdf_path, allow_download=allow_download
        )
        fuori_corso_pdf = PdfFetcher.ensure_pdf(
            self.fuori_corso_url,
            self.fuori_corso_pdf_path,
            allow_download=allow_download,
        )

        print("Elaborazione esami regolari...")
        regular_exams = self.parser.parse_regular(regolari_pdf)
        print(f"Trovati {len(regular_exams)} appelli ordinari.")

        print("Elaborazione esami fuori corso...")
        out_of_course_exams = self.parser.parse_out_of_course(fuori_corso_pdf)
        print(f"Trovati {len(out_of_course_exams)} appelli fuori corso.")

        all_exams = regular_exams + out_of_course_exams
        self.repository.init_schema(clear_existing=reset_db)
        inserted = self.repository.save_exams(all_exams)
        print(
            f"Completato con successo! Salvati {inserted} appelli unici in '{self.db_path}'."
        )
        return inserted


def build_arg_parser() -> argparse.ArgumentParser:
    """Costruisce il parser argomenti CLI."""
    cli = argparse.ArgumentParser(description="Importa appelli esami da PDF in SQLite")
    cli.add_argument("--db", default="esami.db", help="Percorso file database SQLite")
    cli.add_argument(
        "--regolari-pdf",
        default="esami_regolari.pdf",
        help="Percorso PDF esami regolari",
    )
    cli.add_argument(
        "--fuori-corso-pdf",
        default="esami_fuori_corso.pdf",
        help="Percorso PDF esami fuori corso",
    )
    cli.add_argument(
        "--no-download",
        action="store_true",
        help="Non scarica i PDF: usa solo quelli locali",
    )
    cli.add_argument(
        "--no-reset",
        action="store_true",
        help="Non svuota la tabella prima del salvataggio",
    )
    return cli


def main() -> None:
    """Entrypoint CLI."""
    args = build_arg_parser().parse_args()
    pipeline = ExamImportPipeline(
        db_path=args.db,
        regolari_pdf_path=args.regolari_pdf,
        fuori_corso_pdf_path=args.fuori_corso_pdf,
    )
    pipeline.run(allow_download=not args.no_download, reset_db=not args.no_reset)


if __name__ == "__main__":
    main()
