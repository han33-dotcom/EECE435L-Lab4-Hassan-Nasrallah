"""Part 1 - Object-oriented model for the School Management System."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")


class ValidationError(ValueError):
    """Raised when data violates a School Management System rule."""


def _required(value: str, label: str) -> str:
    clean = str(value).strip()
    if not clean:
        raise ValidationError(f"{label} is required.")
    return clean


def _valid_age(value: int | str) -> int:
    try:
        age = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Age must be a whole number.") from exc
    if age < 0:
        raise ValidationError("Age cannot be negative.")
    return age


def _valid_email(value: str) -> str:
    email = str(value).strip()
    if not EMAIL_PATTERN.fullmatch(email):
        raise ValidationError("Enter a valid email address.")
    return email


@dataclass
class Person:
    """Base class demonstrating encapsulation through validated properties."""

    name: str
    age: int
    _email: str

    def __post_init__(self) -> None:
        self.name = _required(self.name, "Name")
        self.age = _valid_age(self.age)
        self._email = _valid_email(self._email)

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        self._email = _valid_email(value)

    def introduce(self) -> str:
        return f"My name is {self.name}, and I am {self.age} years old."


@dataclass
class Student(Person):
    student_id: str
    registered_courses: list[Course] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.student_id = _required(self.student_id, "Student ID")

    def introduce(self) -> str:
        return f"{super().introduce()} I am student {self.student_id}."

    def register_course(self, course: Course) -> None:
        if course not in self.registered_courses:
            self.registered_courses.append(course)
        if self not in course.enrolled_students:
            course.enrolled_students.append(self)


@dataclass
class Instructor(Person):
    instructor_id: str
    assigned_courses: list[Course] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.instructor_id = _required(self.instructor_id, "Instructor ID")

    def introduce(self) -> str:
        return f"{super().introduce()} I am instructor {self.instructor_id}."

    def assign_course(self, course: Course) -> None:
        if course.instructor is not None and course in course.instructor.assigned_courses:
            course.instructor.assigned_courses.remove(course)
        course.instructor = self
        if course not in self.assigned_courses:
            self.assigned_courses.append(course)


@dataclass
class Course:
    course_id: str
    course_name: str
    instructor: Instructor | None = field(default=None, repr=False)
    enrolled_students: list[Student] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self.course_id = _required(self.course_id, "Course ID")
        self.course_name = _required(self.course_name, "Course name")

    def add_student(self, student: Student) -> None:
        student.register_course(self)


class SchoolManager:
    """Coordinates objects, relationships, search, and serialization."""

    def __init__(self) -> None:
        self.students: dict[str, Student] = {}
        self.instructors: dict[str, Instructor] = {}
        self.courses: dict[str, Course] = {}

    @staticmethod
    def _ensure_unique(identifier: str, records: dict[str, Any], label: str) -> None:
        if identifier in records:
            raise ValidationError(f"{label} '{identifier}' already exists.")

    def add_student(self, name: str, age: int | str, email: str, student_id: str) -> Student:
        student = Student(name, age, email, student_id)
        self._ensure_unique(student.student_id, self.students, "Student ID")
        self.students[student.student_id] = student
        return student

    def add_instructor(self, name: str, age: int | str, email: str, instructor_id: str) -> Instructor:
        instructor = Instructor(name, age, email, instructor_id)
        self._ensure_unique(instructor.instructor_id, self.instructors, "Instructor ID")
        self.instructors[instructor.instructor_id] = instructor
        return instructor

    def add_course(self, course_id: str, course_name: str) -> Course:
        course = Course(course_id, course_name)
        self._ensure_unique(course.course_id, self.courses, "Course ID")
        self.courses[course.course_id] = course
        return course

    def register_student(self, student_id: str, course_id: str) -> None:
        try:
            student = self.students[student_id]
            course = self.courses[course_id]
        except KeyError as exc:
            raise ValidationError("Choose an existing student and course.") from exc
        student.register_course(course)

    def assign_instructor(self, instructor_id: str, course_id: str) -> None:
        try:
            instructor = self.instructors[instructor_id]
            course = self.courses[course_id]
        except KeyError as exc:
            raise ValidationError("Choose an existing instructor and course.") from exc
        instructor.assign_course(course)

    def update_student(self, original_id: str, name: str, age: int | str, email: str, student_id: str) -> None:
        if original_id not in self.students:
            raise ValidationError("Select a student to update.")
        updated = Student(name, age, email, student_id)
        if student_id != original_id:
            self._ensure_unique(student_id, self.students, "Student ID")
        current = self.students.pop(original_id)
        current.name, current.age, current.email, current.student_id = updated.name, updated.age, updated.email, updated.student_id
        self.students[student_id] = current

    def update_instructor(self, original_id: str, name: str, age: int | str, email: str, instructor_id: str) -> None:
        if original_id not in self.instructors:
            raise ValidationError("Select an instructor to update.")
        updated = Instructor(name, age, email, instructor_id)
        if instructor_id != original_id:
            self._ensure_unique(instructor_id, self.instructors, "Instructor ID")
        current = self.instructors.pop(original_id)
        current.name, current.age, current.email, current.instructor_id = updated.name, updated.age, updated.email, updated.instructor_id
        self.instructors[instructor_id] = current

    def update_course(self, original_id: str, course_id: str, course_name: str) -> None:
        if original_id not in self.courses:
            raise ValidationError("Select a course to update.")
        updated = Course(course_id, course_name)
        if course_id != original_id:
            self._ensure_unique(course_id, self.courses, "Course ID")
        current = self.courses.pop(original_id)
        current.course_id, current.course_name = updated.course_id, updated.course_name
        self.courses[course_id] = current

    def delete_student(self, student_id: str) -> None:
        student = self.students.pop(student_id, None)
        if student is None:
            raise ValidationError("Select a student to delete.")
        for course in list(student.registered_courses):
            if student in course.enrolled_students:
                course.enrolled_students.remove(student)

    def delete_instructor(self, instructor_id: str) -> None:
        instructor = self.instructors.pop(instructor_id, None)
        if instructor is None:
            raise ValidationError("Select an instructor to delete.")
        for course in list(instructor.assigned_courses):
            course.instructor = None

    def delete_course(self, course_id: str) -> None:
        course = self.courses.pop(course_id, None)
        if course is None:
            raise ValidationError("Select a course to delete.")
        if course.instructor and course in course.instructor.assigned_courses:
            course.instructor.assigned_courses.remove(course)
        for student in list(course.enrolled_students):
            if course in student.registered_courses:
                student.registered_courses.remove(course)

    def search(self, query: str) -> dict[str, list[Any]]:
        needle = query.strip().casefold()
        if not needle:
            return {
                "students": list(self.students.values()),
                "instructors": list(self.instructors.values()),
                "courses": list(self.courses.values()),
            }

        def contains(*values: object) -> bool:
            return any(needle in str(value).casefold() for value in values)

        students = [
            item for item in self.students.values()
            if contains(item.student_id, item.name, item.email, *(course.course_name for course in item.registered_courses))
        ]
        instructors = [
            item for item in self.instructors.values()
            if contains(item.instructor_id, item.name, item.email, *(course.course_name for course in item.assigned_courses))
        ]
        courses = [
            item for item in self.courses.values()
            if contains(item.course_id, item.course_name, item.instructor.name if item.instructor else "")
        ]
        return {"students": students, "instructors": instructors, "courses": courses}

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "students": [
                {
                    "student_id": item.student_id,
                    "name": item.name,
                    "age": item.age,
                    "email": item.email,
                    "registered_courses": [course.course_id for course in item.registered_courses],
                }
                for item in self.students.values()
            ],
            "instructors": [
                {
                    "instructor_id": item.instructor_id,
                    "name": item.name,
                    "age": item.age,
                    "email": item.email,
                    "assigned_courses": [course.course_id for course in item.assigned_courses],
                }
                for item in self.instructors.values()
            ],
            "courses": [
                {
                    "course_id": item.course_id,
                    "course_name": item.course_name,
                    "instructor_id": item.instructor.instructor_id if item.instructor else None,
                    "enrolled_students": [student.student_id for student in item.enrolled_students],
                }
                for item in self.courses.values()
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SchoolManager:
        manager = cls()
        for row in data.get("students", []):
            manager.add_student(row["name"], row["age"], row["email"], row["student_id"])
        for row in data.get("instructors", []):
            manager.add_instructor(row["name"], row["age"], row["email"], row["instructor_id"])
        for row in data.get("courses", []):
            manager.add_course(row["course_id"], row["course_name"])
        for row in data.get("courses", []):
            if row.get("instructor_id"):
                manager.assign_instructor(row["instructor_id"], row["course_id"])
            for student_id in row.get("enrolled_students", []):
                manager.register_student(student_id, row["course_id"])
        return manager

    def save_json(self, filename: str | Path) -> None:
        Path(filename).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load_json(cls, filename: str | Path) -> SchoolManager:
        return cls.from_dict(json.loads(Path(filename).read_text(encoding="utf-8")))

    def export_csv(self, filename: str | Path) -> None:
        with Path(filename).open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Record Type", "ID", "Name", "Age", "Email", "Courses/Instructor"])
            for student in self.students.values():
                writer.writerow(["Student", student.student_id, student.name, student.age, student.email,
                                 "; ".join(course.course_id for course in student.registered_courses)])
            for instructor in self.instructors.values():
                writer.writerow(["Instructor", instructor.instructor_id, instructor.name, instructor.age,
                                 instructor.email, "; ".join(course.course_id for course in instructor.assigned_courses)])
            for course in self.courses.values():
                writer.writerow(["Course", course.course_id, course.course_name, "", "",
                                 course.instructor.instructor_id if course.instructor else "Unassigned"])


def build_demo_manager() -> SchoolManager:
    manager = SchoolManager()
    manager.add_course("EECE435", "Software Tools Laboratory")
    manager.add_course("EECE321", "Database Systems")
    manager.add_course("EECE340", "Computer Networks")
    manager.add_student("Lina Haddad", 21, "lina.haddad@example.edu", "S1001")
    manager.add_student("Omar Khalil", 22, "omar.khalil@example.edu", "S1002")
    manager.add_instructor("Dr. Maya Nassar", 41, "maya.nassar@example.edu", "I2001")
    manager.add_instructor("Dr. Karim Saleh", 45, "karim.saleh@example.edu", "I2002")
    manager.register_student("S1001", "EECE435")
    manager.register_student("S1001", "EECE321")
    manager.register_student("S1002", "EECE435")
    manager.assign_instructor("I2001", "EECE435")
    manager.assign_instructor("I2002", "EECE321")
    return manager


if __name__ == "__main__":
    demo = build_demo_manager()
    for group, records in demo.search("").items():
        print(f"{group.title()}: {len(records)}")
        for record in records:
            print(" -", record)
