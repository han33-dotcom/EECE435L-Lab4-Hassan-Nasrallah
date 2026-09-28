"""Part 3 - PyQt5 GUI for the School Management System."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from part1_oop import SchoolManager, ValidationError, build_demo_manager
from part4_database import SQLiteRepository

try:
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QColor, QFont
    from PyQt5.QtWidgets import (
        QApplication,
        QComboBox,
        QFileDialog,
        QFormLayout,
        QFrame,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False


if QT_AVAILABLE:

    class SchoolManagementPyQt(QMainWindow):
        def __init__(self, manager: SchoolManager, database: str | Path) -> None:
            super().__init__()
            self.manager = manager
            self.repository = SQLiteRepository(database)
            self.selected: dict[str, str | None] = {"student": None, "instructor": None, "course": None}
            self.setWindowTitle("School Management System")
            self.resize(1240, 790)
            self.setMinimumSize(1040, 690)
            self._apply_styles()
            self._build_ui()
            self.refresh_all()

        def _apply_styles(self) -> None:
            self.setStyleSheet(
                """
                QMainWindow { background: #eaf0f7; }
                QFrame#header { background: #17365d; border-radius: 0px; }
                QLabel#title { color: white; font: 600 24px 'Segoe UI'; }
                QLabel#subtitle { color: #dce7f5; font: 10pt 'Segoe UI'; }
                QLabel { color: #26384c; font: 10pt 'Segoe UI'; }
                QTabWidget::pane { background: #f7f9fc; border: 1px solid #cbd6e2; }
                QTabBar::tab { background: #dce7f2; color: #17365d; padding: 11px 22px; font: 600 10pt 'Segoe UI'; }
                QTabBar::tab:selected { background: #ffffff; border-top: 3px solid #2d6aa3; }
                QLineEdit, QComboBox { background: white; border: 1px solid #b8c7d8; border-radius: 4px; padding: 7px; min-height: 20px; }
                QPushButton { background: #e3eaf2; color: #17365d; border: 1px solid #bac8d8; border-radius: 4px; padding: 8px 12px; font: 600 9.5pt 'Segoe UI'; }
                QPushButton:hover { background: #d4e0ed; }
                QPushButton#primary { background: #2d6aa3; color: white; border-color: #2d6aa3; }
                QPushButton#primary:hover { background: #245986; }
                QPushButton#danger { background: #b44747; color: white; border-color: #b44747; }
                QTableWidget { background: white; alternate-background-color: #f4f7fb; gridline-color: #d7e0ea; selection-background-color: #c7def3; selection-color: #17365d; }
                QHeaderView::section { background: #dce7f2; color: #17365d; padding: 8px; border: 0; border-right: 1px solid #c5d1df; font: 600 9.5pt 'Segoe UI'; }
                """
            )

        def _build_ui(self) -> None:
            central = QWidget()
            outer = QVBoxLayout(central)
            outer.setContentsMargins(0, 0, 0, 12)
            outer.setSpacing(0)

            header = QFrame(objectName="header")
            header_layout = QVBoxLayout(header)
            header_layout.setContentsMargins(26, 17, 26, 17)
            title = QLabel("School Management System", objectName="title")
            subtitle = QLabel("PyQt5 edition  |  Complete record management, search, CSV export, and SQLite backup", objectName="subtitle")
            header_layout.addWidget(title)
            header_layout.addWidget(subtitle)
            outer.addWidget(header)

            toolbar = QHBoxLayout()
            toolbar.setContentsMargins(22, 14, 22, 14)
            toolbar.addWidget(QLabel("Search"))
            self.search = QLineEdit()
            self.search.setPlaceholderText("Name, ID, email, or course")
            self.search.setMaximumWidth(330)
            self.search.textChanged.connect(self.refresh_all)
            toolbar.addWidget(self.search)
            for text, callback in (
                ("Save JSON", self.save_json),
                ("Load JSON", self.load_json),
                ("Save to DB", self.save_database),
                ("Load from DB", self.load_database),
                ("Export CSV", self.export_csv),
                ("Backup DB", self.backup_database),
            ):
                button = QPushButton(text)
                button.clicked.connect(callback)
                toolbar.addWidget(button)
            toolbar.addStretch()
            outer.addLayout(toolbar)

            self.tabs = QTabWidget()
            self.tabs.setContentsMargins(20, 0, 20, 0)
            self.tabs.addTab(self._student_tab(), "Students")
            self.tabs.addTab(self._instructor_tab(), "Instructors")
            self.tabs.addTab(self._course_tab(), "Courses")
            outer.addWidget(self.tabs, 1)
            self.status = QLabel("Ready")
            self.status.setContentsMargins(24, 8, 24, 0)
            outer.addWidget(self.status)
            self.setCentralWidget(central)

        @staticmethod
        def _input() -> QLineEdit:
            return QLineEdit()

        @staticmethod
        def _button(text: str, callback, role: str = "") -> QPushButton:
            button = QPushButton(text)
            if role:
                button.setObjectName(role)
            button.clicked.connect(callback)
            return button

        @staticmethod
        def _table(headers: list[str]) -> QTableWidget:
            table = QTableWidget(0, len(headers))
            table.setHorizontalHeaderLabels(headers)
            table.setAlternatingRowColors(True)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setSelectionMode(QTableWidget.SingleSelection)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.verticalHeader().setVisible(False)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            table.horizontalHeader().setStretchLastSection(True)
            return table

        def _tab_layout(self, form_widget: QWidget, table: QTableWidget) -> QWidget:
            tab = QWidget()
            layout = QHBoxLayout(tab)
            layout.setContentsMargins(18, 18, 18, 18)
            layout.setSpacing(18)
            form_widget.setMaximumWidth(360)
            layout.addWidget(form_widget)
            layout.addWidget(table, 1)
            return tab

        def _student_tab(self) -> QWidget:
            form_widget = QFrame()
            form = QFormLayout(form_widget)
            form.setSpacing(11)
            self.s_id, self.s_name, self.s_age, self.s_email = (self._input() for _ in range(4))
            for label, field in (("Student ID", self.s_id), ("Name", self.s_name), ("Age", self.s_age), ("Email", self.s_email)):
                form.addRow(label, field)
            form.addRow(self._button("Add student", self.add_student, "primary"))
            form.addRow(self._button("Update selected", self.update_student))
            form.addRow(self._button("Delete selected", self.delete_student, "danger"))
            form.addRow(QLabel("Register selected student in"))
            self.student_course = QComboBox()
            form.addRow(self.student_course)
            form.addRow(self._button("Register course", self.register_student))
            self.student_table = self._table(["ID", "Name", "Age", "Email", "Courses"])
            for column, width in enumerate((100, 165, 60, 245, 175)):
                self.student_table.setColumnWidth(column, width)
            self.student_table.itemSelectionChanged.connect(self.select_student)
            return self._tab_layout(form_widget, self.student_table)

        def _instructor_tab(self) -> QWidget:
            form_widget = QFrame()
            form = QFormLayout(form_widget)
            form.setSpacing(11)
            self.i_id, self.i_name, self.i_age, self.i_email = (self._input() for _ in range(4))
            for label, field in (("Instructor ID", self.i_id), ("Name", self.i_name), ("Age", self.i_age), ("Email", self.i_email)):
                form.addRow(label, field)
            form.addRow(self._button("Add instructor", self.add_instructor, "primary"))
            form.addRow(self._button("Update selected", self.update_instructor))
            form.addRow(self._button("Delete selected", self.delete_instructor, "danger"))
            form.addRow(QLabel("Assign selected instructor to"))
            self.instructor_course = QComboBox()
            form.addRow(self.instructor_course)
            form.addRow(self._button("Assign course", self.assign_instructor))
            self.instructor_table = self._table(["ID", "Name", "Age", "Email", "Courses"])
            for column, width in enumerate((105, 175, 60, 245, 175)):
                self.instructor_table.setColumnWidth(column, width)
            self.instructor_table.itemSelectionChanged.connect(self.select_instructor)
            return self._tab_layout(form_widget, self.instructor_table)

        def _course_tab(self) -> QWidget:
            form_widget = QFrame()
            form = QFormLayout(form_widget)
            form.setSpacing(11)
            self.c_id, self.c_name = self._input(), self._input()
            form.addRow("Course ID", self.c_id)
            form.addRow("Course name", self.c_name)
            form.addRow(self._button("Add course", self.add_course, "primary"))
            form.addRow(self._button("Update selected", self.update_course))
            form.addRow(self._button("Delete selected", self.delete_course, "danger"))
            self.course_table = self._table(["ID", "Course", "Instructor", "Enrolled Students"])
            for column, width in enumerate((125, 285, 220, 150)):
                self.course_table.setColumnWidth(column, width)
            self.course_table.itemSelectionChanged.connect(self.select_course)
            return self._tab_layout(form_widget, self.course_table)

        def _run(self, operation, success: str) -> None:
            try:
                operation()
                self.repository.sync_from_manager(self.manager)
                self.refresh_all()
                self.status.setText(success)
            except (ValidationError, ValueError, OSError) as exc:
                QMessageBox.critical(self, "Cannot complete action", str(exc))

        def add_student(self) -> None:
            self._run(lambda: self.manager.add_student(self.s_name.text(), self.s_age.text(), self.s_email.text(), self.s_id.text()), "Student added")

        def update_student(self) -> None:
            self._run(lambda: self.manager.update_student(str(self.selected["student"] or ""), self.s_name.text(), self.s_age.text(), self.s_email.text(), self.s_id.text()), "Student updated")

        def delete_student(self) -> None:
            self._run(lambda: self.manager.delete_student(str(self.selected["student"] or "")), "Student deleted")

        def register_student(self) -> None:
            course_id = self.student_course.currentData()
            self._run(lambda: self.manager.register_student(str(self.selected["student"] or ""), str(course_id or "")), "Course registration saved")

        def add_instructor(self) -> None:
            self._run(lambda: self.manager.add_instructor(self.i_name.text(), self.i_age.text(), self.i_email.text(), self.i_id.text()), "Instructor added")

        def update_instructor(self) -> None:
            self._run(lambda: self.manager.update_instructor(str(self.selected["instructor"] or ""), self.i_name.text(), self.i_age.text(), self.i_email.text(), self.i_id.text()), "Instructor updated")

        def delete_instructor(self) -> None:
            self._run(lambda: self.manager.delete_instructor(str(self.selected["instructor"] or "")), "Instructor deleted")

        def assign_instructor(self) -> None:
            course_id = self.instructor_course.currentData()
            self._run(lambda: self.manager.assign_instructor(str(self.selected["instructor"] or ""), str(course_id or "")), "Instructor assignment saved")

        def add_course(self) -> None:
            self._run(lambda: self.manager.add_course(self.c_id.text(), self.c_name.text()), "Course added")

        def update_course(self) -> None:
            self._run(lambda: self.manager.update_course(str(self.selected["course"] or ""), self.c_id.text(), self.c_name.text()), "Course updated")

        def delete_course(self) -> None:
            self._run(lambda: self.manager.delete_course(str(self.selected["course"] or "")), "Course deleted")

        def select_student(self) -> None:
            row = self.student_table.currentRow()
            if row < 0:
                return
            values = [self.student_table.item(row, col).text() for col in range(4)]
            self.selected["student"] = values[0]
            for field, value in zip((self.s_id, self.s_name, self.s_age, self.s_email), values):
                field.setText(value)
                field.setCursorPosition(0)

        def select_instructor(self) -> None:
            row = self.instructor_table.currentRow()
            if row < 0:
                return
            values = [self.instructor_table.item(row, col).text() for col in range(4)]
            self.selected["instructor"] = values[0]
            for field, value in zip((self.i_id, self.i_name, self.i_age, self.i_email), values):
                field.setText(value)
                field.setCursorPosition(0)

        def select_course(self) -> None:
            row = self.course_table.currentRow()
            if row < 0:
                return
            self.selected["course"] = self.course_table.item(row, 0).text()
            self.c_id.setText(self.course_table.item(row, 0).text())
            self.c_name.setText(self.course_table.item(row, 1).text())

        @staticmethod
        def _set_rows(table: QTableWidget, rows: list[list[object]]) -> None:
            table.setRowCount(len(rows))
            for row_index, values in enumerate(rows):
                for column_index, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    if row_index % 2 == 1:
                        item.setBackground(QColor("#f4f7fb"))
                    table.setItem(row_index, column_index, item)
            table.resizeRowsToContents()

        def refresh_all(self) -> None:
            results = self.manager.search(self.search.text())
            self._set_rows(self.student_table, [[x.student_id, x.name, x.age, x.email, ", ".join(c.course_id for c in x.registered_courses) or "None"] for x in results["students"]])
            self._set_rows(self.instructor_table, [[x.instructor_id, x.name, x.age, x.email, ", ".join(c.course_id for c in x.assigned_courses) or "None"] for x in results["instructors"]])
            self._set_rows(self.course_table, [[x.course_id, x.course_name, x.instructor.name if x.instructor else "Unassigned", len(x.enrolled_students)] for x in results["courses"]])
            current_student = self.student_course.currentData()
            current_instructor = self.instructor_course.currentData()
            for combo in (self.student_course, self.instructor_course):
                combo.clear()
                for course in self.manager.courses.values():
                    combo.addItem(f"{course.course_id} - {course.course_name}", course.course_id)
            for combo, value in ((self.student_course, current_student), (self.instructor_course, current_instructor)):
                index = combo.findData(value)
                if index >= 0:
                    combo.setCurrentIndex(index)

        def save_json(self) -> None:
            filename, _ = QFileDialog.getSaveFileName(self, "Save JSON", "school_data.json", "JSON (*.json)")
            if filename:
                self.manager.save_json(filename)
                self.status.setText(f"Saved {Path(filename).name}")

        def load_json(self) -> None:
            filename, _ = QFileDialog.getOpenFileName(self, "Load JSON", "", "JSON (*.json)")
            if filename:
                self._run(lambda: self._replace_manager(SchoolManager.load_json(filename)), f"Loaded {Path(filename).name}")

        def _replace_manager(self, manager: SchoolManager) -> None:
            self.manager = manager

        def save_database(self) -> None:
            self.repository.sync_from_manager(self.manager)
            self.status.setText("All records saved to SQLite")

        def load_database(self) -> None:
            self.manager = self.repository.load_manager()
            self.refresh_all()
            self.status.setText("Records loaded from SQLite")

        def export_csv(self) -> None:
            filename, _ = QFileDialog.getSaveFileName(self, "Export CSV", "school_records.csv", "CSV (*.csv)")
            if filename:
                self.manager.export_csv(filename)
                self.status.setText(f"Exported {Path(filename).name}")

        def backup_database(self) -> None:
            filename, _ = QFileDialog.getSaveFileName(self, "Backup database", "school_management_backup.db", "SQLite database (*.db)")
            if filename:
                self.repository.sync_from_manager(self.manager)
                self.repository.backup(filename)
                self.status.setText(f"Backup created: {Path(filename).name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="PyQt5 School Management System")
    parser.add_argument("--database", default="school_management.db")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--screenshot")
    args = parser.parse_args()
    if not QT_AVAILABLE:
        raise SystemExit("PyQt5 is not installed. Run: python -m pip install -r requirements.txt")
    repository = SQLiteRepository(args.database)
    existing = repository.load_manager()
    manager = build_demo_manager() if args.demo or not (existing.students or existing.instructors or existing.courses) else existing
    repository.sync_from_manager(manager)
    application = QApplication(sys.argv)
    application.setFont(QFont("Segoe UI", 10))
    window = SchoolManagementPyQt(manager, args.database)
    window.showMaximized() if args.screenshot else window.show()
    if window.student_table.rowCount():
        window.student_table.selectRow(0)
    if args.screenshot:
        output = Path(args.screenshot)
        output.parent.mkdir(parents=True, exist_ok=True)

        def capture() -> None:
            application.primaryScreen().grabWindow(0).save(str(output))
            application.quit()

        QTimer.singleShot(1200, capture)
    sys.exit(application.exec_())


if __name__ == "__main__":
    main()
