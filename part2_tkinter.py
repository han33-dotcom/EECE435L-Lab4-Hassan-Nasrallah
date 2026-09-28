"""Part 2 - Tkinter GUI for the School Management System."""

from __future__ import annotations

import argparse
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from part1_oop import SchoolManager, ValidationError, build_demo_manager
from part4_database import SQLiteRepository


class SchoolManagementTkinter:
    """Coordinate the Tkinter interface for the school management system.

    The window exposes searchable student, instructor, and course views. User
    actions update the in-memory :class:`part1_oop.SchoolManager` and are then
    synchronized with :class:`part4_database.SQLiteRepository`.

    :param root: Top-level Tkinter window owned by the application.
    :type root: tkinter.Tk
    :param manager: Object model that stores the current school records.
    :type manager: part1_oop.SchoolManager
    :param database: SQLite database file used for persistent storage.
    :type database: str or pathlib.Path
    """

    def __init__(self, root: tk.Tk, manager: SchoolManager, database: str | Path) -> None:
        """Initialize the window, persistence layer, widgets, and visible data.

        :param root: Top-level Tkinter window.
        :type root: tkinter.Tk
        :param manager: School data to display and modify.
        :type manager: part1_oop.SchoolManager
        :param database: Path to the SQLite database.
        :type database: str or pathlib.Path
        :return: None.
        :rtype: None
        """
        self.root = root
        self.manager = manager
        self.repository = SQLiteRepository(database)
        self.selected: dict[str, str | None] = {"student": None, "instructor": None, "course": None}
        self.root.title("School Management System")
        self.root.geometry("1180x760")
        self.root.minsize(1000, 680)
        self.root.configure(bg="#EAF0F7")
        self._configure_style()
        self._build_ui()
        self.refresh_all()

    def _configure_style(self) -> None:
        """Apply the shared colors, typography, spacing, and widget themes.

        :return: None.
        :rtype: None
        """
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#F6F8FB")
        style.configure("Header.TFrame", background="#17365D")
        style.configure("Header.TLabel", background="#17365D", foreground="white", font=("Segoe UI Semibold", 22))
        style.configure("Subheader.TLabel", background="#17365D", foreground="#DCE7F5", font=("Segoe UI", 10))
        style.configure("TLabel", background="#F6F8FB", foreground="#26384C", font=("Segoe UI", 10))
        style.configure("TLabelframe", background="#F6F8FB", foreground="#17365D")
        style.configure("TLabelframe.Label", background="#F6F8FB", foreground="#17365D", font=("Segoe UI Semibold", 11))
        style.configure("TButton", font=("Segoe UI Semibold", 10), padding=(12, 7))
        style.configure("Accent.TButton", background="#2D6AA3", foreground="white")
        style.map("Accent.TButton", background=[("active", "#245986")])
        style.configure("Danger.TButton", background="#B44747", foreground="white")
        style.map("Danger.TButton", background=[("active", "#923939")])
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10), background="#DCE7F2", foreground="#17365D")
        style.configure("TNotebook", background="#EAF0F7", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI Semibold", 10), padding=(18, 10))

    def _build_ui(self) -> None:
        """Create the header, toolbar, tabbed views, and status area.

        :return: None.
        :rtype: None
        """
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(24, 18))
        header.pack(fill="x")
        ttk.Label(header, text="School Management System", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="Tkinter edition  |  Students, instructors, courses, and SQLite persistence", style="Subheader.TLabel").pack(anchor="w", pady=(3, 0))

        toolbar = ttk.Frame(self.root, padding=(20, 14))
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="Search").pack(side="left")
        self.search_var = tk.StringVar()
        search = ttk.Entry(toolbar, textvariable=self.search_var, width=34)
        search.pack(side="left", padx=(8, 12))
        search.bind("<KeyRelease>", lambda _event: self.refresh_all())
        ttk.Button(toolbar, text="Save JSON", command=self.save_json).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Load JSON", command=self.load_json).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Save to DB", command=self.save_database).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Load from DB", command=self.load_database).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Backup DB", command=self.backup_database).pack(side="left", padx=3)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 14))
        self.student_tab = ttk.Frame(self.notebook, padding=18)
        self.instructor_tab = ttk.Frame(self.notebook, padding=18)
        self.course_tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(self.student_tab, text="Students")
        self.notebook.add(self.instructor_tab, text="Instructors")
        self.notebook.add(self.course_tab, text="Courses")
        self._build_student_tab()
        self._build_instructor_tab()
        self._build_course_tab()

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status_var, padding=(20, 7)).pack(fill="x")

    @staticmethod
    def _field(parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> ttk.Entry:
        """Create a labeled entry field inside a grid-based form.

        :param parent: Frame that receives the label and entry widgets.
        :type parent: tkinter.ttk.Frame
        :param row: Grid row used by both widgets.
        :type row: int
        :param label: Text displayed beside the entry field.
        :type label: str
        :param variable: Tkinter variable bound to the entry value.
        :type variable: tkinter.StringVar
        :return: The created entry widget.
        :rtype: tkinter.ttk.Entry
        """
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        entry = ttk.Entry(parent, textvariable=variable, width=32)
        entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        return entry

    @staticmethod
    def _tree(parent: ttk.Frame, columns: tuple[str, ...], widths: tuple[int, ...]) -> ttk.Treeview:
        """Create a scrollable table with named columns and requested widths.

        :param parent: Frame that contains the table and its scrollbar.
        :type parent: tkinter.ttk.Frame
        :param columns: Column identifiers displayed as table headings.
        :type columns: tuple[str, ...]
        :param widths: Initial pixel width for every column.
        :type widths: tuple[int, ...]
        :return: Configured table widget.
        :rtype: tkinter.ttk.Treeview
        """
        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        for column, width in zip(columns, widths):
            tree.heading(column, text=column)
            tree.column(column, width=width, minwidth=80, anchor="w")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        return tree

    def _build_student_tab(self) -> None:
        """Build student editing, registration, and tabular display controls.

        :return: None.
        :rtype: None
        """
        self.student_tab.columnconfigure(1, weight=1)
        self.student_tab.rowconfigure(0, weight=1)
        form = ttk.LabelFrame(self.student_tab, text="Student details", padding=16)
        form.grid(row=0, column=0, sticky="nsw", padx=(0, 16))
        self.s_id, self.s_name, self.s_age, self.s_email = (tk.StringVar() for _ in range(4))
        self._field(form, 0, "Student ID", self.s_id)
        self._field(form, 1, "Name", self.s_name)
        self._field(form, 2, "Age", self.s_age)
        self._field(form, 3, "Email", self.s_email)
        ttk.Button(form, text="Add student", style="Accent.TButton", command=self.add_student).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(14, 4))
        ttk.Button(form, text="Update selected", command=self.update_student).grid(row=5, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Button(form, text="Delete selected", style="Danger.TButton", command=self.delete_student).grid(row=6, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Separator(form).grid(row=7, column=0, columnspan=2, sticky="ew", pady=14)
        ttk.Label(form, text="Register selected student in").grid(row=8, column=0, columnspan=2, sticky="w")
        self.student_course = ttk.Combobox(form, state="readonly", width=30)
        self.student_course.grid(row=9, column=0, columnspan=2, sticky="ew", pady=6)
        ttk.Button(form, text="Register course", command=self.register_student).grid(row=10, column=0, columnspan=2, sticky="ew")
        table_frame = ttk.Frame(self.student_tab)
        table_frame.grid(row=0, column=1, sticky="nsew")
        self.student_tree = self._tree(table_frame, ("ID", "Name", "Age", "Email", "Courses"), (100, 170, 55, 220, 210))
        self.student_tree.bind("<<TreeviewSelect>>", self.select_student)

    def _build_instructor_tab(self) -> None:
        """Build instructor editing, assignment, and display controls.

        :return: None.
        :rtype: None
        """
        self.instructor_tab.columnconfigure(1, weight=1)
        self.instructor_tab.rowconfigure(0, weight=1)
        form = ttk.LabelFrame(self.instructor_tab, text="Instructor details", padding=16)
        form.grid(row=0, column=0, sticky="nsw", padx=(0, 16))
        self.i_id, self.i_name, self.i_age, self.i_email = (tk.StringVar() for _ in range(4))
        self._field(form, 0, "Instructor ID", self.i_id)
        self._field(form, 1, "Name", self.i_name)
        self._field(form, 2, "Age", self.i_age)
        self._field(form, 3, "Email", self.i_email)
        ttk.Button(form, text="Add instructor", style="Accent.TButton", command=self.add_instructor).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(14, 4))
        ttk.Button(form, text="Update selected", command=self.update_instructor).grid(row=5, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Button(form, text="Delete selected", style="Danger.TButton", command=self.delete_instructor).grid(row=6, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Separator(form).grid(row=7, column=0, columnspan=2, sticky="ew", pady=14)
        ttk.Label(form, text="Assign selected instructor to").grid(row=8, column=0, columnspan=2, sticky="w")
        self.instructor_course = ttk.Combobox(form, state="readonly", width=30)
        self.instructor_course.grid(row=9, column=0, columnspan=2, sticky="ew", pady=6)
        ttk.Button(form, text="Assign course", command=self.assign_instructor).grid(row=10, column=0, columnspan=2, sticky="ew")
        table_frame = ttk.Frame(self.instructor_tab)
        table_frame.grid(row=0, column=1, sticky="nsew")
        self.instructor_tree = self._tree(table_frame, ("ID", "Name", "Age", "Email", "Courses"), (105, 180, 55, 220, 210))
        self.instructor_tree.bind("<<TreeviewSelect>>", self.select_instructor)

    def _build_course_tab(self) -> None:
        """Build course editing controls and the course summary table.

        :return: None.
        :rtype: None
        """
        self.course_tab.columnconfigure(1, weight=1)
        self.course_tab.rowconfigure(0, weight=1)
        form = ttk.LabelFrame(self.course_tab, text="Course details", padding=16)
        form.grid(row=0, column=0, sticky="nsw", padx=(0, 16))
        self.c_id, self.c_name = tk.StringVar(), tk.StringVar()
        self._field(form, 0, "Course ID", self.c_id)
        self._field(form, 1, "Course name", self.c_name)
        ttk.Button(form, text="Add course", style="Accent.TButton", command=self.add_course).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(14, 4))
        ttk.Button(form, text="Update selected", command=self.update_course).grid(row=3, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Button(form, text="Delete selected", style="Danger.TButton", command=self.delete_course).grid(row=4, column=0, columnspan=2, sticky="ew", pady=4)
        table_frame = ttk.Frame(self.course_tab)
        table_frame.grid(row=0, column=1, sticky="nsew")
        self.course_tree = self._tree(table_frame, ("ID", "Course", "Instructor", "Enrolled Students"), (125, 270, 210, 130))
        self.course_tree.bind("<<TreeviewSelect>>", self.select_course)

    def _run(self, operation, success: str) -> None:
        """Run a model operation and synchronize successful changes.

        Validation, conversion, and file-system errors are shown to the user in
        an error dialog. Successful operations refresh every table and update
        the status bar.

        :param operation: Zero-argument callable that performs the requested change.
        :type operation: collections.abc.Callable
        :param success: Status text displayed after successful completion.
        :type success: str
        :return: None.
        :rtype: None
        """
        try:
            operation()
            self.repository.sync_from_manager(self.manager)
            self.refresh_all()
            self.status_var.set(success)
        except (ValidationError, ValueError, OSError) as exc:
            messagebox.showerror("Cannot complete action", str(exc), parent=self.root)

    def add_student(self) -> None:
        """Add a student from the form values and persist the new record.

        :return: None.
        :rtype: None
        """
        self._run(lambda: self.manager.add_student(self.s_name.get(), self.s_age.get(), self.s_email.get(), self.s_id.get()), "Student added")

    def update_student(self) -> None:
        """Replace the selected student's details with the form values.

        :return: None.
        :rtype: None
        """
        self._run(lambda: self.manager.update_student(str(self.selected["student"] or ""), self.s_name.get(), self.s_age.get(), self.s_email.get(), self.s_id.get()), "Student updated")

    def delete_student(self) -> None:
        """Delete the selected student from the model and database.

        :return: None.
        :rtype: None
        """
        self._run(lambda: self.manager.delete_student(str(self.selected["student"] or "")), "Student deleted")

    def register_student(self) -> None:
        """Register the selected student in the course chosen by the user.

        :return: None.
        :rtype: None
        """
        course_id = self.student_course.get().split(" - ", 1)[0]
        self._run(lambda: self.manager.register_student(str(self.selected["student"] or ""), course_id), "Course registration saved")

    def add_instructor(self) -> None:
        """Add an instructor from the form values and persist the record.

        :return: None.
        :rtype: None
        """
        self._run(lambda: self.manager.add_instructor(self.i_name.get(), self.i_age.get(), self.i_email.get(), self.i_id.get()), "Instructor added")

    def update_instructor(self) -> None:
        """Replace the selected instructor's details with the form values.

        :return: None.
        :rtype: None
        """
        self._run(lambda: self.manager.update_instructor(str(self.selected["instructor"] or ""), self.i_name.get(), self.i_age.get(), self.i_email.get(), self.i_id.get()), "Instructor updated")

    def delete_instructor(self) -> None:
        """Delete the selected instructor from the model and database.

        :return: None.
        :rtype: None
        """
        self._run(lambda: self.manager.delete_instructor(str(self.selected["instructor"] or "")), "Instructor deleted")

    def assign_instructor(self) -> None:
        """Assign the selected instructor to the chosen course.

        :return: None.
        :rtype: None
        """
        course_id = self.instructor_course.get().split(" - ", 1)[0]
        self._run(lambda: self.manager.assign_instructor(str(self.selected["instructor"] or ""), course_id), "Instructor assignment saved")

    def add_course(self) -> None:
        """Add a course from the form values and persist the record.

        :return: None.
        :rtype: None
        """
        self._run(lambda: self.manager.add_course(self.c_id.get(), self.c_name.get()), "Course added")

    def update_course(self) -> None:
        """Replace the selected course identifier and name.

        :return: None.
        :rtype: None
        """
        self._run(lambda: self.manager.update_course(str(self.selected["course"] or ""), self.c_id.get(), self.c_name.get()), "Course updated")

    def delete_course(self) -> None:
        """Delete the selected course from the model and database.

        :return: None.
        :rtype: None
        """
        self._run(lambda: self.manager.delete_course(str(self.selected["course"] or "")), "Course deleted")

    def select_student(self, _event=None) -> None:
        """Load the selected student table row into the editing form.

        :param _event: Optional Tkinter selection event.
        :type _event: object, optional
        :return: None.
        :rtype: None
        """
        selection = self.student_tree.selection()
        if not selection:
            return
        values = self.student_tree.item(selection[0], "values")
        self.selected["student"] = values[0]
        for variable, value in zip((self.s_id, self.s_name, self.s_age, self.s_email), values[:4]):
            variable.set(value)

    def select_instructor(self, _event=None) -> None:
        """Load the selected instructor row into the editing form.

        :param _event: Optional Tkinter selection event.
        :type _event: object, optional
        :return: None.
        :rtype: None
        """
        selection = self.instructor_tree.selection()
        if not selection:
            return
        values = self.instructor_tree.item(selection[0], "values")
        self.selected["instructor"] = values[0]
        for variable, value in zip((self.i_id, self.i_name, self.i_age, self.i_email), values[:4]):
            variable.set(value)

    def select_course(self, _event=None) -> None:
        """Load the selected course row into the editing form.

        :param _event: Optional Tkinter selection event.
        :type _event: object, optional
        :return: None.
        :rtype: None
        """
        selection = self.course_tree.selection()
        if not selection:
            return
        values = self.course_tree.item(selection[0], "values")
        self.selected["course"] = values[0]
        self.c_id.set(values[0])
        self.c_name.set(values[1])

    def refresh_all(self) -> None:
        """Filter and repopulate all record tables and course selectors.

        The current search text is applied to students, instructors, and
        courses before their rows are redrawn.

        :return: None.
        :rtype: None
        """
        results = self.manager.search(self.search_var.get())
        for tree in (self.student_tree, self.instructor_tree, self.course_tree):
            tree.delete(*tree.get_children())
        for item in results["students"]:
            self.student_tree.insert("", "end", values=(item.student_id, item.name, item.age, item.email, ", ".join(c.course_id for c in item.registered_courses) or "None"))
        for item in results["instructors"]:
            self.instructor_tree.insert("", "end", values=(item.instructor_id, item.name, item.age, item.email, ", ".join(c.course_id for c in item.assigned_courses) or "None"))
        for item in results["courses"]:
            self.course_tree.insert("", "end", values=(item.course_id, item.course_name, item.instructor.name if item.instructor else "Unassigned", len(item.enrolled_students)))
        courses = [f"{c.course_id} - {c.course_name}" for c in self.manager.courses.values()]
        self.student_course["values"] = courses
        self.instructor_course["values"] = courses
        if courses and not self.student_course.get():
            self.student_course.current(0)
            self.instructor_course.current(0)

    def save_json(self) -> None:
        """Ask for a destination and export the current model as JSON.

        :return: None.
        :rtype: None
        """
        filename = filedialog.asksaveasfilename(parent=self.root, defaultextension=".json", filetypes=[("JSON", "*.json")])
        if filename:
            self.manager.save_json(filename)
            self.status_var.set(f"Saved {Path(filename).name}")

    def load_json(self) -> None:
        """Load a selected JSON file and synchronize it to SQLite.

        Invalid or inaccessible files are reported in an error dialog.

        :return: None.
        :rtype: None
        """
        filename = filedialog.askopenfilename(parent=self.root, filetypes=[("JSON", "*.json")])
        if filename:
            try:
                self.manager = SchoolManager.load_json(filename)
                self.repository.sync_from_manager(self.manager)
                self.refresh_all()
                self.status_var.set(f"Loaded {Path(filename).name}")
            except (ValidationError, ValueError, OSError) as exc:
                messagebox.showerror("Cannot load file", str(exc), parent=self.root)

    def save_database(self) -> None:
        """Write every current object-model record to SQLite.

        :return: None.
        :rtype: None
        """
        self.repository.sync_from_manager(self.manager)
        self.status_var.set("All records saved to SQLite")

    def load_database(self) -> None:
        """Replace the current model with records loaded from SQLite.

        :return: None.
        :rtype: None
        """
        self.manager = self.repository.load_manager()
        self.refresh_all()
        self.status_var.set("Records loaded from SQLite")

    def backup_database(self) -> None:
        """Ask for a destination and create a SQLite database backup.

        :return: None.
        :rtype: None
        """
        filename = filedialog.asksaveasfilename(parent=self.root, defaultextension=".db", filetypes=[("SQLite database", "*.db")])
        if filename:
            self.repository.sync_from_manager(self.manager)
            self.repository.backup(filename)
            self.status_var.set(f"Backup created: {Path(filename).name}")


def capture_window(root: tk.Tk, output: str | Path) -> None:
    """Capture the full desktop after bringing the application to the front.

    :param root: Application window that should be visible during capture.
    :type root: tkinter.Tk
    :param output: Destination image path.
    :type output: str or pathlib.Path
    :return: None.
    :rtype: None
    """
    from PIL import ImageGrab

    root.deiconify()
    root.lift()
    root.attributes("-topmost", True)
    root.focus_force()
    root.update_idletasks()
    ImageGrab.grab().save(output)
    root.after(250, root.destroy)


def main() -> None:
    """Parse command-line options and start the Tkinter event loop.

    :return: None.
    :rtype: None
    """
    parser = argparse.ArgumentParser(description="Tkinter School Management System")
    parser.add_argument("--database", default="school_management.db")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--screenshot")
    args = parser.parse_args()
    repository = SQLiteRepository(args.database)
    existing = repository.load_manager()
    manager = build_demo_manager() if args.demo or not (existing.students or existing.instructors or existing.courses) else existing
    repository.sync_from_manager(manager)
    root = tk.Tk()
    app = SchoolManagementTkinter(root, manager, args.database)
    if app.student_tree.get_children():
        first = app.student_tree.get_children()[0]
        app.student_tree.selection_set(first)
        app.student_tree.focus(first)
        app.select_student()
    if args.screenshot:
        Path(args.screenshot).parent.mkdir(parents=True, exist_ok=True)
        root.state("zoomed")
        root.after(1200, lambda: capture_window(root, args.screenshot))
    root.mainloop()


if __name__ == "__main__":
    main()
