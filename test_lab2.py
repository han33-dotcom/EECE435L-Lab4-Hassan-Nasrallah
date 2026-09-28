"""Automated checks for OOP validation, serialization, relationships, and SQLite."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from part1_oop import SchoolManager, ValidationError, build_demo_manager
from part4_database import SQLiteRepository


class SchoolManagementTests(unittest.TestCase):
    def test_validation_rejects_invalid_data(self) -> None:
        manager = SchoolManager()
        with self.assertRaises(ValidationError):
            manager.add_student("Invalid Age", -1, "valid@example.edu", "S1")
        with self.assertRaises(ValidationError):
            manager.add_student("Invalid Email", 20, "not-an-email", "S1")

    def test_polymorphism_and_relationships(self) -> None:
        manager = build_demo_manager()
        student = manager.students["S1001"]
        instructor = manager.instructors["I2001"]
        self.assertIn("student S1001", student.introduce())
        self.assertIn("instructor I2001", instructor.introduce())
        self.assertIn(student, manager.courses["EECE435"].enrolled_students)
        self.assertIs(manager.courses["EECE435"].instructor, instructor)

    def test_json_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            filename = Path(temporary) / "school.json"
            original = build_demo_manager()
            original.save_json(filename)
            loaded = SchoolManager.load_json(filename)
            self.assertEqual(original.to_dict(), loaded.to_dict())

    def test_database_round_trip_backup_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "school.db"
            backup = Path(temporary) / "backup.db"
            repository = SQLiteRepository(database)
            repository.sync_from_manager(build_demo_manager())
            loaded = repository.load_manager()
            self.assertEqual(2, len(loaded.students))
            self.assertEqual(3, len(loaded.courses))
            repository.backup(backup)
            repository.delete_student("S1001")
            self.assertEqual(1, len(repository.rows("students")))
            repository.restore(backup)
            self.assertEqual(2, len(repository.rows("students")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
