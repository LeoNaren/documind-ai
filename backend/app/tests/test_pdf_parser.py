from app.services import pdf_parser


def test_extract_pdf_chunks(monkeypatch, tmp_path):
    class FakePage:
        def extract_text(self):
            return "PDF text. " * 30

    class FakeReader:
        def __init__(self, path):
            self.pages = [FakePage()]

    monkeypatch.setattr(pdf_parser, "PdfReader", FakeReader)

    chunks = pdf_parser.extract_pdf_chunks(tmp_path / "demo.pdf")

    assert chunks[0].source_type == "pdf"
    assert chunks[0].page_number == 1

