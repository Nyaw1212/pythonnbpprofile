import tempfile
import unittest
from pathlib import Path

from src.db import connect, initialize
from src.personnel_service import PersonnelService


class PersonnelServiceTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.db"
        initialize(self.db_path)
        with connect(self.db_path) as connection:
            connection.executemany(
                """
                INSERT INTO personnel (
                    badge_number, rank, last_name, first_name, middle_name,
                    camp, office, classification, personnel_type, source_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("2", "CSSUPT", "GARCIA", "GARY", "A", "NBP", "OTS", "Commissioned", "CORRECTIONS OFFICER", 2),
                    ("7", "CCINSP", "BUTAWAN", "ROBERTO", None, "NBP", "ESCORT", None, "CORRECTIONS OFFICER", 1),
                    ("10", "CO1", "CHIAO", "ALVIN", None, "NBP", "CASO", None, "CORRECTIONS OFFICER", 4),
                    ("11", "CO1", "CANAO", "JUAN", None, "NBP", "CASO", None, "CORRECTIONS OFFICER", 3),
                ],
            )
        self.service = PersonnelService(self.db_path)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_search_by_name(self):
        result = self.service.search("garcia")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["badge_number"], "2")

    def test_filter_by_office(self):
        result = self.service.search(office="ESCORT")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["last_name"], "BUTAWAN")

    def test_get_profile(self):
        profile = self.service.get_profile("2")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["rank"], "CSSUPT")

    def test_multiline_search_preserves_term_order(self):
        result = self.service.search("CHIAO\nCANAO")
        self.assertEqual([row["last_name"] for row in result], ["CHIAO", "CANAO"])

    def test_default_search_preserves_sheet_order(self):
        result = self.service.search(limit=4)
        self.assertEqual(
            [row["badge_number"] for row in result],
            ["7", "2", "11", "10"],
        )


if __name__ == "__main__":
    unittest.main()
