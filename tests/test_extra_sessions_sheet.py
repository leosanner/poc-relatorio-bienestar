import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from utils.extra_sessions_sheet import (  # noqa: E402
    ExtraSessionsCatalogError,
    build_catalog_options_for_clinic,
    build_selected_session_price_lookup,
    load_extra_sessions_catalog,
    normalize_extra_sessions_records,
)


def build_sample_record(**overrides):
    base_record = {
        "nome tratamento": "Calatonia",
        "bienestar pix": "152",
        "bienestar cartao": "168",
        "vitaeflux pix": "152",
        "vitaeflux cartao": "168",
        "alecrim pix": "152",
        "alecrim cartao": "168",
    }
    base_record.update(overrides)
    return base_record


class ExtraSessionsSheetTests(unittest.TestCase):
    def test_normalize_records_accepts_header_variations(self):
        records = [
            {
                " Nome Tratamento ": " Calatonia ",
                "Bienestar PIX": "152,00",
                "Bienestar Cartao": "168,00",
                "VitaeFlux PIX": "152,00",
                "VitaeFlux Cartao": "168,00",
                "Alecrim PIX": "152,00",
                "Alecrim Cartao": "168,00",
            },
            {
                "nome tratamento": " ",
                "bienestar pix": "",
                "bienestar cartao": "",
                "vitaeflux pix": "",
                "vitaeflux cartao": "",
                "alecrim pix": "",
                "alecrim cartao": "",
            },
        ]

        catalog = normalize_extra_sessions_records(records, source_name="test")

        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog[0]["treatment_name"], "Calatonia")
        self.assertEqual(catalog[0]["prices"]["Bienestar"]["pix"], 152.0)

    def test_normalize_records_rejects_invalid_price(self):
        with self.assertRaises(ExtraSessionsCatalogError):
            normalize_extra_sessions_records(
                [build_sample_record(**{"bienestar pix": "abc"})],
                source_name="test",
            )

    def test_normalize_records_rejects_duplicate_names(self):
        with self.assertRaises(ExtraSessionsCatalogError):
            normalize_extra_sessions_records(
                [
                    build_sample_record(),
                    build_sample_record(**{"nome tratamento": " calatonia "}),
                ],
                source_name="test",
            )

    def test_load_catalog_uses_fallback_when_remote_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fallback_path = Path(temp_dir) / "fallback.json"
            fallback_path.write_text(
                json.dumps([build_sample_record()]),
                encoding="utf-8",
            )

            result = load_extra_sessions_catalog(
                spreadsheet_id="sheet-id",
                worksheet_name="tab-name",
                service_account_info={"client_email": "test@example.com"},
                fallback_path=fallback_path,
                remote_loader=lambda *_args: (_ for _ in ()).throw(RuntimeError("boom")),
            )

        self.assertEqual(result["source"], "fallback")
        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["catalog"][0]["treatment_name"], "Calatonia")

    def test_load_catalog_reports_unavailable_when_remote_and_fallback_fail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fallback_path = Path(temp_dir) / "fallback.json"
            fallback_path.write_text('{"invalid": true}', encoding="utf-8")

            result = load_extra_sessions_catalog(
                spreadsheet_id="sheet-id",
                worksheet_name="tab-name",
                service_account_info={"client_email": "test@example.com"},
                fallback_path=fallback_path,
                remote_loader=lambda *_args: (_ for _ in ()).throw(RuntimeError("boom")),
            )

        self.assertEqual(result["source"], "unavailable")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["catalog"], [])

    def test_build_catalog_options_and_selected_prices_for_clinic(self):
        catalog = normalize_extra_sessions_records(
            [
                build_sample_record(),
                build_sample_record(
                    **{
                        "nome tratamento": "Metaterapia",
                        "vitaeflux pix": "",
                        "vitaeflux cartao": "",
                    }
                ),
            ],
            source_name="test",
        )

        vitae_flux_options = build_catalog_options_for_clinic(catalog, "VitaeFlux")
        selected_prices = build_selected_session_price_lookup(
            catalog,
            "VitaeFlux",
            ["Calatonia", "Metaterapia"],
        )

        self.assertEqual([option["treatment_name"] for option in vitae_flux_options], ["Calatonia"])
        self.assertEqual(selected_prices, {"Calatonia": {"pix": 152.0, "cartao": 168.0}})


if __name__ == "__main__":
    unittest.main()
