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
                    camp, office, classification, personnel_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("2", "CSSUPT", "GARCIA", "GARY", "A", "NBP", "OTS", "Commissioned", "CORRECTIONS OFFICER"),
                    ("7", "CCINSP", "BUTAWAN", "ROBERTO", None, "NBP", "ESCORT", None, "CORRECTIONS OFFICER"),
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


if __name__ == "__main__":
    unittest.main()
