"""Read-only compatibility checks for a private MyBible module corpus.

These tests are deliberately standalone: the application data layer does not
exist yet. Once ``sola.data`` lands, the discovery and query helpers here should
be replaced by the real module registry while keeping the same coverage.
"""

from __future__ import annotations

import os
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_ROOT = REPO_ROOT / "private_modules"

MODULE_SUFFIXES = (
    ".dictionary",
    ".commentaries",
    ".subheadings",
    ".crossreferences",
    ".plan",
    ".devotions",
    ".bundle",
)

# These are not modules: they hold generated indexes, runtime data, or user data.
EXCLUDED_DIRS = {".git", ".pytest_cache", "__pycache__", "user", "runtime"}


def is_runtime_artifact(path: Path) -> bool:
    """Return True for generated files that must never be treated as modules."""
    name = path.name
    lower = name.lower()
    return (
        name.startswith("-")
        or lower == "referencedata.sqlite3"
        or lower.endswith(".search")
        or lower.endswith(".new")
        or lower.endswith("-journal")
        or lower.endswith("-wal")
        or lower.endswith("-shm")
        or lower.endswith(".cache.sqlite3")
    )


def module_kind(path: Path) -> str:
    """Classify a module by its longest known suffix."""
    lower = path.name.lower()
    if lower.endswith(".bundle.zip"):
        return "bundle"
    if not lower.endswith(".sqlite3"):
        raise ValueError(f"not a SQLite module: {path.name}")
    stem = lower[: -len(".sqlite3")]
    for suffix in sorted(MODULE_SUFFIXES, key=len, reverse=True):
        if stem.endswith(suffix):
            return suffix[1:]
    return "bible"


def discover_module_files(root: Path) -> list[Path]:
    """Find real module files below *root*, skipping runtime/user data."""
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in EXCLUDED_DIRS and not name.startswith(".")
        )
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            lower = filename.lower()
            if not (lower.endswith(".sqlite3") or lower.endswith(".bundle.zip")):
                continue
            if is_runtime_artifact(path):
                continue
            found.append(path)
    return found


def direct_module_files(root: Path) -> list[Path]:
    """Return only real module files directly in *root*."""
    found: list[Path] = []
    for path in sorted(root.iterdir()):
        if not path.is_file():
            continue
        lower = path.name.lower()
        if not (lower.endswith(".sqlite3") or lower.endswith(".bundle.zip")):
            continue
        if is_runtime_artifact(path):
            continue
        found.append(path)
    return found


def find_corpus_root() -> Path | None:
    """Resolve the corpus from SOLA_TEST_MODULES or a single private_modules clone."""
    configured = os.environ.get("SOLA_TEST_MODULES")
    if configured:
        root = Path(configured).expanduser().resolve()
        if not root.is_dir():
            raise pytest.UsageError(f"SOLA_TEST_MODULES does not exist: {root}")
        return root

    if not PRIVATE_ROOT.is_dir():
        return None
    if direct_module_files(PRIVATE_ROOT):
        return PRIVATE_ROOT

    candidates = [
        child
        for child in sorted(PRIVATE_ROOT.iterdir())
        if child.is_dir()
        and not child.name.startswith(".")
        and discover_module_files(child)
    ]
    if len(candidates) > 1:
        names = ", ".join(child.name for child in candidates)
        raise pytest.UsageError(
            "Multiple private module repositories found under private_modules/: "
            f"{names}. Set SOLA_TEST_MODULES to the one to test."
        )
    return candidates[0] if candidates else None


CORPUS_ROOT = find_corpus_root()
MODULE_PATHS = discover_module_files(CORPUS_ROOT) if CORPUS_ROOT else []
MODULE_IDS = (
    [str(path.relative_to(CORPUS_ROOT)) for path in MODULE_PATHS]
    if CORPUS_ROOT
    else []
)


def open_read_only(path: Path) -> sqlite3.Connection:
    """Open a module through a read-only SQLite URI.

    ``Path.as_uri()`` percent-encodes spaces, apostrophes, plus signs, and
    non-ASCII characters, which matters for this corpus.
    """
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    return connection


def table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0].lower()
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }


def column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    return {
        row[1].lower()
        for row in connection.execute(f'PRAGMA table_info("{table}")')
    }


def require(condition: object, path: Path, message: str) -> None:
    if not condition:
        raise AssertionError(f"{path.name}: {message}")


def validate_module(path: Path) -> str:
    """Validate INFO plus the required tables and a sample query for one module."""
    kind = module_kind(path)
    if kind == "bundle":
        # Bundle archives are not SQLite modules; import/listing is post-1.0.
        return kind

    with closing(open_read_only(path)) as connection:
        tables = table_names(connection)
        require("info" in tables, path, "missing INFO table")

        info = {
            str(name).lower(): value
            for name, value in connection.execute("SELECT name, value FROM info")
        }
        require(
            str(info.get("description") or "").strip(),
            path,
            "INFO.description is empty",
        )

        if kind == "bible":
            require("verses" in tables, path, "missing VERSES table")
            require(
                {"books", "books_all"} & tables,
                path,
                "missing BOOKS and BOOKS_ALL tables",
            )
            require(
                {"book_number", "chapter", "verse", "text"}
                <= column_names(connection, "verses"),
                path,
                "VERSES is missing required columns",
            )
            connection.execute(
                "SELECT book_number, chapter, verse, text FROM verses LIMIT 1"
            ).fetchone()

        elif kind == "dictionary":
            if "dictionary" in tables:
                require(
                    {"topic", "definition"}
                    <= column_names(connection, "dictionary"),
                    path,
                    "DICTIONARY is missing required columns",
                )
                connection.execute(
                    "SELECT topic, definition FROM dictionary LIMIT 1"
                ).fetchone()
            elif "words" in tables:
                require(
                    {"variation", "standard_form"}
                    <= column_names(connection, "words"),
                    path,
                    "WORDS is missing required columns",
                )
                connection.execute(
                    "SELECT variation, standard_form FROM words LIMIT 1"
                ).fetchone()
            else:
                require(False, path, "missing DICTIONARY and WORDS tables")

        elif kind == "commentaries":
            require("commentaries" in tables, path, "missing COMMENTARIES table")
            require(
                {
                    "book_number",
                    "chapter_number_from",
                    "verse_number_from",
                    "text",
                }
                <= column_names(connection, "commentaries"),
                path,
                "COMMENTARIES is missing required columns",
            )
            connection.execute("SELECT * FROM commentaries LIMIT 1").fetchone()

        elif kind == "subheadings":
            require("subheadings" in tables, path, "missing SUBHEADINGS table")
            columns = column_names(connection, "subheadings")
            require(
                {"book_number", "chapter", "verse"} <= columns,
                path,
                "SUBHEADINGS is missing required columns",
            )
            require(
                bool({"subheading", "text"} & columns),
                path,
                "SUBHEADINGS has no text column",
            )
            connection.execute("SELECT * FROM subheadings LIMIT 1").fetchone()

        elif kind == "crossreferences":
            require(
                "cross_references" in tables,
                path,
                "missing CROSS_REFERENCES table",
            )
            require(
                {
                    "book",
                    "chapter",
                    "verse",
                    "book_to",
                    "chapter_to",
                    "verse_to_start",
                }
                <= column_names(connection, "cross_references"),
                path,
                "CROSS_REFERENCES is missing required columns",
            )
            connection.execute(
                "SELECT * FROM cross_references LIMIT 1"
            ).fetchone()

        elif kind == "plan":
            require("reading_plan" in tables, path, "missing READING_PLAN table")
            require(
                {"day", "book_number", "start_chapter", "end_chapter"}
                <= column_names(connection, "reading_plan"),
                path,
                "READING_PLAN is missing required columns",
            )
            connection.execute("SELECT * FROM reading_plan LIMIT 1").fetchone()

        elif kind == "devotions":
            require("devotions" in tables, path, "missing DEVOTIONS table")
            require(
                {"day", "devotion"} <= column_names(connection, "devotions"),
                path,
                "DEVOTIONS is missing required columns",
            )
            connection.execute("SELECT * FROM devotions LIMIT 1").fetchone()

        else:  # pragma: no cover - module_kind only returns known kinds
            raise AssertionError(f"{path.name}: unsupported module kind {kind!r}")

    return kind


def test_private_corpus_is_available() -> None:
    if CORPUS_ROOT is None:
        pytest.skip(
            "No private module corpus found. Clone a corpus into "
            "private_modules/<repo> or set SOLA_TEST_MODULES."
        )
    assert MODULE_PATHS, f"No modules found under {CORPUS_ROOT}"


def test_corpus_inventory() -> None:
    if not MODULE_PATHS:
        pytest.skip("No private module corpus available")
    counts = Counter(module_kind(path) for path in MODULE_PATHS)
    print(f"Corpus: {CORPUS_ROOT}")
    for kind, count in sorted(counts.items()):
        print(f"  {kind}: {count}")
    assert sum(counts.values()) == len(MODULE_PATHS)


@pytest.mark.parametrize("module_path", MODULE_PATHS, ids=MODULE_IDS)
def test_module_is_readable(module_path: Path) -> None:
    validate_module(module_path)


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("KJV+.SQLite3", "bible"),
        ("Strong.dictionary.SQLite3", "dictionary"),
        ("DV-c.commentaries.SQLite3", "commentaries"),
        ("KJV-s.subheadings.SQLite3", "subheadings"),
        ("OBX.crossreferences.SQLite3", "crossreferences"),
        ("BRP-1y.plan.SQLite3", "plan"),
        ("DBEE-d.devotions.SQLite3", "devotions"),
        ("Pack.bundle.zip", "bundle"),
    ],
)
def test_module_classification(filename: str, expected: str) -> None:
    assert module_kind(Path(filename)) == expected


@pytest.mark.parametrize(
    "filename",
    [
        "-downloads.cache.SQLite3",
        "-book-chapter-verse-count.cache.SQLite3",
        "ReferenceData.SQLite3",
        "KJV+.SQLite3.search",
        "dictionaries_lookup.SQLite3.new",
        "KJV+.SQLite3-journal",
        "KJV+.SQLite3-wal",
        "KJV+.SQLite3-shm",
    ],
)
def test_runtime_artifact_is_not_a_module(filename: str) -> None:
    assert is_runtime_artifact(Path(filename))


def test_discovery_skips_runtime_files() -> None:
    if not MODULE_PATHS:
        pytest.skip("No private module corpus available")
    assert not any(is_runtime_artifact(path) for path in MODULE_PATHS)


def test_reference_data_is_readable_but_not_a_module() -> None:
    if CORPUS_ROOT is None:
        pytest.skip("No private module corpus available")
    reference = next(
        (path for path in CORPUS_ROOT.rglob("ReferenceData.SQLite3")), None
    )
    if reference is None:
        pytest.skip("ReferenceData.SQLite3 is not present in this corpus")
    assert reference not in MODULE_PATHS
    with closing(open_read_only(reference)) as connection:
        assert table_names(connection)


def test_modules_are_opened_read_only() -> None:
    paths = [path for path in MODULE_PATHS if module_kind(path) != "bundle"]
    if not paths:
        pytest.skip("No SQLite module available")
    with closing(open_read_only(paths[0])) as connection:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("CREATE TABLE _sola_write_probe (id INTEGER)")


def test_special_filename_uri_handling(tmp_path: Path) -> None:
    """A filename with an apostrophe, plus sign, and Cyrillic must stay addressable."""
    path = tmp_path / "Тест'name+1.SQLite3"
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE info (name TEXT, value TEXT)")
        connection.execute(
            "INSERT INTO info (name, value) VALUES ('description', 'ok')"
        )
        connection.commit()

    with closing(open_read_only(path)) as connection:
        info = dict(connection.execute("SELECT name, value FROM info"))
    assert info == {"description": "ok"}
