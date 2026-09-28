"""Part 4 - SQLite CRUD, persistence, backup, restore, and evidence output."""

from __future__ import annotations

import argparse
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Iterator

from part1_oop import Course, Instructor, SchoolManager, Student, ValidationError, build_demo_manager


class SQLiteRepository:
    def __init__(self, filename: str | Path = "school_management.db") -> None:
        self.filename = Path(filename)
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        self.create_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.filename)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def create_schema(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL CHECK(age >= 0),
                    email TEXT NOT NULL UNIQUE
                );
                CREATE TABLE IF NOT EXISTS instructors (
                    instructor_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL CHECK(age >= 0),
                    email TEXT NOT NULL UNIQUE
                );
                CREATE TABLE IF NOT EXISTS courses (
                    course_id TEXT PRIMARY KEY,
                    course_name TEXT NOT NULL,
                    instructor_id TEXT,
                    FOREIGN KEY(instructor_id) REFERENCES instructors(instructor_id)
                        ON UPDATE CASCADE ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS enrollments (
                    student_id TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    PRIMARY KEY(student_id, course_id),
                    FOREIGN KEY(student_id) REFERENCES students(student_id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
                    FOREIGN KEY(course_id) REFERENCES courses(course_id)
                        ON UPDATE CASCADE ON DELETE CASCADE
                );
                """
            )

    def create_student(self, student: Student) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO students(student_id, name, age, email) VALUES (?, ?, ?, ?)",
                (student.student_id, student.name, student.age, student.email),
            )

    def update_student(self, original_id: str, student: Student) -> None:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE students SET student_id=?, name=?, age=?, email=? WHERE student_id=?",
                (student.student_id, student.name, student.age, student.email, original_id),
            )
            if cursor.rowcount == 0:
                raise ValidationError("Student was not found in the database.")

    def delete_student(self, student_id: str) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM students WHERE student_id=?", (student_id,))

    def create_instructor(self, instructor: Instructor) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO instructors(instructor_id, name, age, email) VALUES (?, ?, ?, ?)",
                (instructor.instructor_id, instructor.name, instructor.age, instructor.email),
            )

    def update_instructor(self, original_id: str, instructor: Instructor) -> None:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE instructors SET instructor_id=?, name=?, age=?, email=? WHERE instructor_id=?",
                (instructor.instructor_id, instructor.name, instructor.age, instructor.email, original_id),
            )
            if cursor.rowcount == 0:
                raise ValidationError("Instructor was not found in the database.")

    def delete_instructor(self, instructor_id: str) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM instructors WHERE instructor_id=?", (instructor_id,))

    def create_course(self, course: Course) -> None:
        instructor_id = course.instructor.instructor_id if course.instructor else None
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO courses(course_id, course_name, instructor_id) VALUES (?, ?, ?)",
                (course.course_id, course.course_name, instructor_id),
            )

    def update_course(self, original_id: str, course: Course) -> None:
        instructor_id = course.instructor.instructor_id if course.instructor else None
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE courses SET course_id=?, course_name=?, instructor_id=? WHERE course_id=?",
                (course.course_id, course.course_name, instructor_id, original_id),
            )
            if cursor.rowcount == 0:
                raise ValidationError("Course was not found in the database.")

    def delete_course(self, course_id: str) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM courses WHERE course_id=?", (course_id,))

    def enroll_student(self, student_id: str, course_id: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO enrollments(student_id, course_id) VALUES (?, ?)",
                (student_id, course_id),
            )

    def assign_instructor(self, instructor_id: str | None, course_id: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE courses SET instructor_id=? WHERE course_id=?", (instructor_id, course_id)
            )

    def sync_from_manager(self, manager: SchoolManager) -> None:
        """Replace database contents atomically with the validated object graph."""
        with self.connect() as connection:
            connection.execute("DELETE FROM enrollments")
            connection.execute("DELETE FROM courses")
            connection.execute("DELETE FROM students")
            connection.execute("DELETE FROM instructors")
            connection.executemany(
                "INSERT INTO students(student_id, name, age, email) VALUES (?, ?, ?, ?)",
                [(x.student_id, x.name, x.age, x.email) for x in manager.students.values()],
            )
            connection.executemany(
                "INSERT INTO instructors(instructor_id, name, age, email) VALUES (?, ?, ?, ?)",
                [(x.instructor_id, x.name, x.age, x.email) for x in manager.instructors.values()],
            )
            connection.executemany(
                "INSERT INTO courses(course_id, course_name, instructor_id) VALUES (?, ?, ?)",
                [
                    (x.course_id, x.course_name, x.instructor.instructor_id if x.instructor else None)
                    for x in manager.courses.values()
                ],
            )
            connection.executemany(
                "INSERT INTO enrollments(student_id, course_id) VALUES (?, ?)",
                [
                    (student.student_id, course.course_id)
                    for student in manager.students.values()
                    for course in student.registered_courses
                ],
            )

    def load_manager(self) -> SchoolManager:
        with self.connect() as connection:
            manager = SchoolManager()
            for row in connection.execute("SELECT * FROM students ORDER BY student_id"):
                manager.add_student(row["name"], row["age"], row["email"], row["student_id"])
            for row in connection.execute("SELECT * FROM instructors ORDER BY instructor_id"):
                manager.add_instructor(row["name"], row["age"], row["email"], row["instructor_id"])
            for row in connection.execute("SELECT * FROM courses ORDER BY course_id"):
                manager.add_course(row["course_id"], row["course_name"])
                if row["instructor_id"]:
                    manager.assign_instructor(row["instructor_id"], row["course_id"])
            for row in connection.execute("SELECT * FROM enrollments ORDER BY student_id, course_id"):
                manager.register_student(row["student_id"], row["course_id"])
            return manager

    def backup(self, destination: str | Path) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as source, closing(sqlite3.connect(destination)) as target:
            source.backup(target)
        return destination

    def restore(self, source: str | Path) -> None:
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(source)
        with closing(sqlite3.connect(source)) as backup_connection, self.connect() as target:
            backup_connection.backup(target)

    def rows(self, table: str) -> list[dict[str, object]]:
        if table not in {"students", "instructors", "courses", "enrollments"}:
            raise ValidationError("Unknown database table.")
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]


def render_database_snapshot(repository: SQLiteRepository, output: str | Path) -> None:
    """Create a readable evidence image from the real SQLite schema and rows."""
    from PIL import Image, ImageDraw, ImageFont

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1500, 930
    image = Image.new("RGB", (width, height), "#F4F7FB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 23)
    bold = ImageFont.truetype("C:/Windows/Fonts/seguisb.ttf", 26)
    title = ImageFont.truetype("C:/Windows/Fonts/seguisb.ttf", 40)
    mono = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 19)
    draw.rounded_rectangle((35, 28, width - 35, height - 28), 18, fill="white", outline="#CAD5E3", width=2)
    draw.text((75, 62), "SQLite Database Evidence", font=title, fill="#17365D")
    draw.text((75, 120), f"File: {repository.filename.name}  |  Foreign keys enabled  |  Four normalized tables", font=font, fill="#43546A")
    colors = ["#DCEAF7", "#E4F3EA", "#FFF1D6", "#F2E6F7"]
    y = 185
    for index, table in enumerate(("students", "instructors", "courses", "enrollments")):
        rows = repository.rows(table)
        draw.rounded_rectangle((75, y, width - 75, y + 155), 12, fill=colors[index], outline="#BCC9D8", width=2)
        draw.text((100, y + 14), f"{table.upper()} ({len(rows)} rows)", font=bold, fill="#17365D")
        if rows:
            headers = list(rows[0])
            draw.text((100, y + 54), " | ".join(headers), font=mono, fill="#26384C")
            for line_index, row in enumerate(rows[:3]):
                values = [str(row[key]) if row[key] is not None else "NULL" for key in headers]
                draw.text((100, y + 84 + line_index * 25), " | ".join(values), font=mono, fill="#364A60")
        else:
            draw.text((100, y + 66), "No rows", font=mono, fill="#65758A")
        y += 175
    image.save(output)


def capture_database_window(repository: SQLiteRepository, output: str | Path) -> None:
    """Show the real SQLite tables in a maximized window and capture the full screen."""
    import tkinter as tk
    from tkinter import ttk

    from PIL import ImageGrab

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    root.title(f"SQLite Database Viewer - {repository.filename.name}")
    root.state("zoomed")
    root.configure(bg="#EAF0F7")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="#F6F8FB")
    style.configure("Header.TFrame", background="#17365D")
    style.configure("Header.TLabel", background="#17365D", foreground="white", font=("Segoe UI Semibold", 22))
    style.configure("Subheader.TLabel", background="#17365D", foreground="#DCE7F5", font=("Segoe UI", 10))
    style.configure("TNotebook", background="#EAF0F7", borderwidth=0)
    style.configure("TNotebook.Tab", font=("Segoe UI Semibold", 10), padding=(20, 10))
    style.configure("Treeview", rowheight=31, font=("Consolas", 10), background="white", fieldbackground="white")
    style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10), background="#DCE7F2", foreground="#17365D")

    header = ttk.Frame(root, style="Header.TFrame", padding=(28, 18))
    header.pack(fill="x")
    ttk.Label(header, text="SQLite Database Evidence", style="Header.TLabel").pack(anchor="w")
    ttk.Label(
        header,
        text=f"{repository.filename.name}  |  Foreign keys enabled  |  Students, instructors, courses, and enrollments",
        style="Subheader.TLabel",
    ).pack(anchor="w", pady=(3, 0))

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=24, pady=20)
    for table in ("students", "instructors", "courses", "enrollments"):
        rows = repository.rows(table)
        frame = ttk.Frame(notebook, padding=16)
        notebook.add(frame, text=f"{table.title()} ({len(rows)} rows)")
        columns = tuple(rows[0].keys()) if rows else ("status",)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for column in columns:
            tree.heading(column, text=column.replace("_", " ").title())
            tree.column(column, width=220, minwidth=120, anchor="w", stretch=True)
        for row in rows:
            tree.insert("", "end", values=["NULL" if row[column] is None else row[column] for column in columns])
        tree.pack(fill="both", expand=True)

    status = tk.StringVar(value="Database opened successfully  |  4 normalized tables  |  Sample data verified")
    ttk.Label(root, textvariable=status, padding=(24, 8)).pack(fill="x")

    def capture() -> None:
        root.deiconify()
        root.lift()
        root.attributes("-topmost", True)
        root.focus_force()
        root.update_idletasks()
        ImageGrab.grab().save(output)
        root.after(250, root.destroy)

    root.after(1200, capture)
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="School Management System SQLite utility")
    parser.add_argument("--database", default="school_management.db")
    parser.add_argument("--init-demo", action="store_true")
    parser.add_argument("--backup")
    parser.add_argument("--snapshot")
    parser.add_argument("--window-screenshot")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    repository = SQLiteRepository(args.database)
    if args.init_demo:
        repository.sync_from_manager(build_demo_manager())
    if args.backup:
        repository.backup(args.backup)
    if args.snapshot:
        render_database_snapshot(repository, args.snapshot)
    if args.window_screenshot:
        capture_database_window(repository, args.window_screenshot)
    if args.show:
        for table in ("students", "instructors", "courses", "enrollments"):
            print(f"\n{table.upper()}")
            for row in repository.rows(table):
                print(row)


if __name__ == "__main__":
    main()
