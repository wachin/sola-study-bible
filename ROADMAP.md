# Sola Study Bible — Development Roadmap

> Status snapshot: 2026-11-07. Only repository facts verified on disk are marked `[x]`. No application source exists yet, so no task is marked `[~]`.

## Statuses

- [x] Implemented
- [~] Partially implemented
- [ ] Not yet implemented

### Status rules

- `[x]` means the feature is implemented and verified.
- `[~]` means a partial implementation exists, but at least one important requirement, test, integration, or validation remains.
- `[ ]` means the feature is not implemented.
- Do not change `[ ]` or `[~]` to `[x]` merely because related code exists.
- A task may be marked `[x]` only when the complete requirement is implemented and, where applicable, tested.

Task counts in this document refer to checklist lines with task IDs (`M0.1`, `M1.2`, and so on). The three legend lines above are not tasks.

## Project summary

Sola Study Bible is a Linux desktop Bible study application written in Python 3.11+ and PyQt6. It reproduces the core four-pane reading and study workflow — Bible, dictionary or Strong's lexicon, commentary, and Markdown notes — in a touch-first layout with no traditional menu bar. The project is licensed under the GNU General Public License v3.0 (GPLv3); the complete license text is in the repository root at [LICENSE](LICENSE), and all source, assets, and documentation must remain GPLv3-compatible. Copyrighted Bible modules are never redistributed: the application reads user-supplied modules from a configurable local directory at runtime.

**Scope for the first public release**

- Linux desktop (Debian/MX Linux first), Python 3.11+, PyQt6, standard-library `sqlite3`.
- A four-pane workspace with nested `QSplitter` widgets, per-pane icon toolbars, and no `QMenuBar`.
- Bible reading with embedded tags, Strong's numbers, footnotes, and cross-reference navigation.
- Dictionary and Strong's lexicon lookup using the documented NF1/NF2 rules.
- Commentary with verse and chapter-range matching and footnote mode.
- A custom Markdown notes editor with preview.
- Navigation history, search, bookmarks, and reading plans after the core reading experience is stable.
- Day/night theming, font scaling, module selection, and a configurable module directory.
- Debian packaging with a reproducible build and a GPLv3 compliance audit.

**Out of scope for v0.1**

- Windows, macOS, mobile, and web targets.
- Accounts, cloud sync, and telemetry.
- Bundling or redistributing copyrighted Bible modules.
- A traditional desktop menu bar or MDI window chrome.
- Full-text search across every installed module (v0.1 searches the active Bible translation).

## License and module-distribution policy

- The repository is GPLv3. [LICENSE](LICENSE) must ship with source and binary distributions, and the source for distributed binaries must remain available.
- Every source file, icon, theme, font, and document added to the repository must have a GPLv3-compatible license. Third-party assets need a provenance entry in `docs/ASSETS.md` and a compatible license.
- Bible modules are user-supplied data, not application assets. The app opens them read-only from a configurable directory and never writes into that directory.
- The public repository may contain only modules whose redistribution rights are confirmed. The two modules under `data/` are public development samples; their provenance must be recorded before they are distributed in a source archive, and they must never be bundled into an installed application or binary package.
- Binary release artifacts contain no Bible modules at all. The user points the installed application at their own module directory on first run.
- PyQt6 is GPLv3 (with a commercial alternative), so the GPLv3 application license is compatible. Any optional dependency added later must be checked for GPLv3 compatibility before adoption.

## Architecture

### Workspace layout

The main window is a frameless `QMainWindow` with a single workspace widget. The workspace is an outer vertical `QSplitter`; each row is a nested horizontal `QSplitter`:

```text
QSplitter(Qt.Vertical)                     outer splitter: top row / bottom row
├── QSplitter(Qt.Horizontal)               top row
│   ├── BiblePane          (top-left)
│   └── CommentaryPane     (top-right, hosts the window controls)
└── QSplitter(Qt.Horizontal)               bottom row
    ├── DictionaryPane     (bottom-left)
    └── NotesPane          (bottom-right)
```

- All four panes are resizable in both axes: the outer splitter changes row heights, and each nested splitter changes column widths.
- Handles are at least 12 px wide, with a visible hover and drag state. Panes have practical minimum sizes (about 320 px wide and 220 px high) so content never collapses to an unusable strip.
- Splitter sizes and the last selected modules are persisted and restored. A reset-layout command lives in a pane overflow menu, not a menu bar.
- The top-right pane header hosts the minimize, maximize/restore, and close controls, matching the mockup at [idea/GUI-idea.png](idea/GUI-idea.png). The main window has no OS title bar by default; a native-frame fallback is available in settings for desktops where frameless windows behave poorly.
- When the Commentary pane's content is collapsed, its header remains visible so the window controls never disappear.

### Pane anatomy and toolbar policy

Each pane is a `PaneFrame` with a fixed-height header (52 px target) and a content area:

```text
PaneFrame
├── PaneHeader
│   ├── module selector (text + icon, touch popup)
│   ├── primary icon actions (44 × 44 px minimum)
│   ├── secondary actions in a "⋯" overflow popup
│   └── window controls (top-right pane only)
└── content (QTextBrowser, Markdown editor, or picker)
```

- There is no `QMenuBar`, no `QMainWindow.menuBar()` call, and no File/Edit/View menu. Every command is an icon button in the relevant pane header.
- Secondary commands use a `QMenu` popup anchored to the `⋯` button. Popup menus are not a menu bar and are styled with large, touch-friendly rows.
- Primary buttons use icon-only presentation with accessible names and tooltips. Text is reserved for module selectors and status labels.
- Every pane owns its context: the Bible pane controls translation and passage; the dictionary pane controls lookup mode and dictionary; the commentary pane controls its module and follow state; the notes pane controls formatting and preview.
- Inline links inside text cannot be 44 px tall; they get a larger line height and a clear link style instead. This exception is documented in the touch checklist.

### Layer boundaries

| Layer | Package | May depend on | Responsibilities | Must not |
| --- | --- | --- | --- | --- |
| Data | `sola/data` | Python standard library, `sqlite3` | Module discovery, read-only module access, INFO parsing, books/verses, dictionary/commentary/plan queries, normalization, app-owned lookup indexes | Import PyQt6; produce HTML; write to module files |
| Rendering | `sola/render` | Python standard library | Verse-tag tokenizer, HTML fragment generation, module HTML sanitization, link rewriting, theme-token substitution | Import PyQt6; open databases; navigate widgets |
| Services | `sola/services` | Data, rendering, app storage | Use cases: open passage, look up word, navigate, search, notes, bookmarks, reading plans, settings | Contain widget code; bypass the data layer with ad-hoc SQL |
| UI | `sola/ui` | PyQt6, services | Windows, panes, toolbars, dialogs, models/views, theming | Execute SQL; parse module formats; rewrite module HTML |
| Storage | `sola/storage` | Standard library `sqlite3` | Application database, migrations, notes/bookmarks/progress, caches | Modify module databases |

The dependency direction is UI → services → data/render/storage. A test asserts that `sola/data`, `sola/render`, and `sola/storage` do not import PyQt6.

### Data and storage model

- Modules are opened with `sqlite3.connect("file:<path>?mode=ro", uri=True)` and `PRAGMA query_only=ON`. They are never modified, vacuumed, or written to.
- Application state lives in `$XDG_DATA_HOME/sola-study-bible/app.db`, falling back to `~/.local/share/sola-study-bible/app.db`. It is created on first run and uses WAL mode.
- The application database owns notes, bookmarks, reading progress, module metadata/cache, the derived reference cache, lookup indexes, and the search index. The schema is versioned with `PRAGMA user_version`; migrations back up the database first.
- The derived reference cache stores per-book chapter counts and per-chapter verse counts. It is disposable and regenerated when a module's path, size, or modification time changes. It is never treated as a source of truth and never written beside the module.
- One SQLite connection is used per thread. Writes go through the storage service and are serialized. Read-only module connections are created per worker thread.
- `PRAGMA foreign_keys=ON`, a busy timeout, and explicit transactions are used for the application database.

### Rendering pipeline

1. The data layer returns raw verse text or module HTML.
2. Bible text uses a dedicated tokenizer, not an HTML parser: known tags become styled spans or anchors; every other angle-bracketed sequence is escaped. This prevents module text from injecting markup.
3. Module HTML (dictionary, commentary, notes preview) is sanitized with an allowlist, then has its links rewritten to internal schemes. `CONTENT_FRAGMENTS` inclusions are resolved before sanitization, with a recursion guard.
4. Theme tokens such as `%COLOR_TEXT%` and `<font color="0..5">` indexes are replaced with the active theme's colors.
5. The fragment is passed to a read-only `QTextBrowser` with `setOpenLinks(False)` and `setOpenExternalLinks(False)`. `anchorClicked` is routed through the link handler; the browser never navigates itself.
6. No JavaScript engine is part of v0.1. If Qt rich-text fidelity proves insufficient, ADR-0001 defines the criteria for an optional QtWebEngine fallback with a hardened, script-disabled profile.

### Link scheme

| Internal scheme | Meaning | Handler |
| --- | --- | --- |
| `strong:H7225`, `strong:G25` | Strong's number | Dictionary/lexicon lookup |
| `verse:<book>:<chapter>:<verse>` | Bible passage | Bible navigation |
| `topic:<topic>` | Dictionary topic | Dictionary article |
| `commentary:<book>:<chapter>:<verse>` | Commentary article | Commentary navigation |
| `note:<id>` | Note reference | Notes pane |
| `xref:<book>:<chapter>:<verse>` | Cross-reference target | Bible navigation and highlight |
| `http://`, `https://` | External link | Confirmation, then `QDesktopServices.openUrl` |

Module link targets (`B:`, `S:`, `C:@`, and external URLs) are rewritten to these schemes before display. `file:`, `javascript:`, `data:`, and unknown schemes are blocked.

### Navigation and synchronization

- A `Location` value object identifies translation, book, chapter, and verse.
- The Bible pane drives the current passage. The commentary pane follows it when follow mode is enabled; the dictionary pane receives the tapped word or Strong's number; the notes pane binds to the canonical passage (with an optional translation scope).
- Bible navigation has back/forward history with a bounded stack. Dictionary topics and commentary articles keep their own small histories where useful.
- The last Bible location and the active modules are restored on startup.

### Threading and performance

- Module scanning, reference-cache builds, lookup-index builds, and search run on a `QThreadPool`; the UI never blocks for more than one frame.
- Long operations report progress, can be cancelled, and never leave a half-written index: build to a temporary database, validate, then swap atomically.
- Chapter reads are indexed and bounded; no query loads an entire Bible, commentary set, or dictionary into memory.
- Performance targets are defined in M1, M3, M4, M7, and M8 and measured with a benchmark script, not guessed.

### Packaging target

- Primary target: Debian 12+/MX Linux, Python 3.11+.
- A PyInstaller one-directory build with the required Qt plugins is the reference desktop bundle; a Debian `.deb` is the primary system package. An AppImage is optional later.
- The package ships a desktop entry, icon, AppStream metadata, `LICENSE`, and third-party notices. It ships no modules.
- Builds run on the oldest supported Debian baseline to keep the glibc requirement low, and release artifacts carry SHA-256 checksums.

## Milestones

### Sequence at a glance

| ID | Theme | Depends on | Exit artifact |
| --- | --- | --- | --- |
| M0 | Repository baseline and specification | — | SPEC, project metadata, CI skeleton |
| M1 | Data access, storage, and module parsing | M0 | Read-only module layer and app database with tests |
| M2 | Application shell and four-pane layout | M0, M1 (partial) | Touch-first window with placeholders |
| M3 | Bible pane and tag rendering | M1, M2 | Readable Bible with working links |
| M4 | Dictionary, Strong's, and NF1/NF2 lookup | M1, M3 | Working dictionary pane and lookup engine |
| M5 | Commentary pane and range matching | M1, M3 | Synced commentary with footnote mode |
| M6 | Markdown notes editor | M2, M5 | Durable Markdown notes with preview |
| M7 | Navigation, search, bookmarks, reading plans | M3, M5 | Deferred study tools complete |
| M8 | Settings, theming, touch polish, performance | M2–M7 | Product-quality desktop experience |
| M9 | Packaging, documentation, release | M0–M8 | Installable GPLv3 release with audit |
| M10 | Post-1.0 backlog | M9 | Prioritised future work |

---

### M0 — Repository baseline and specification

**Goal:** turn the existing repository facts into a precise, testable specification and a minimal Python project scaffold.

#### Checklist

- [x] **M0.1** Repository is initialized and contains the full GPLv3 license text at `LICENSE`.
- [x] **M0.2** `README.md` exists with the project name and a one-line description.
- [x] **M0.3** MyBible format documentation ([MyBible Modules Format](<resources/mybible/MyBible Modules Format.md>)), the [user guide PDF](<resources/mybible/MyBible Guidebook by DanielVanLeeuwen v2.pdf>), and supplementary help PDFs are present under `resources/mybible/`.
- [x] **M0.4** The four-pane GUI mockup is present at `idea/GUI-idea.png` (1456 × 1064).
- [x] **M0.5** Public sample modules are present at `data/KJV1611.SQLite3` (31,102 verses, `books_all` table) and `data/KJV+.SQLite3` (31,102 verses, `books` table, `strong_numbers=true`).
- [ ] **M0.6** Write `docs/SPEC.md`: module suffixes, INFO keys, table schemas including optional-column variations, supported tags, link grammar, NF1/NF2/NF0 rules, and commentary range semantics.
- [ ] **M0.7** Update `README.md` for Python 3.11+, PyQt6, GPLv3, the module-directory policy, setup, run, and test commands. The current badge still says Python 3.8+.
- [ ] **M0.8** Add `pyproject.toml` with project metadata, the chosen GPLv3 SPDX license expression, dependencies (`PyQt6`, `markdown`), and dev dependencies (`pytest`, `pytest-qt`, `ruff`); pin exact versions in `constraints.txt`.
- [ ] **M0.9** Adopt the chosen GPLv3 SPDX header for source files and add `CONTRIBUTING.md` with the licensing and asset-provenance rules.
- [ ] **M0.10** Harden `.gitignore` for the app database, caches, build outputs, and virtual environments; add `scripts/audit_repo.py` to fail if a non-public module database is tracked.
- [ ] **M0.11** Add Debian-based CI that runs `ruff`, `pytest`, and the repository audit on every push and pull request.
- [ ] **M0.12** Write ADR-0001 covering the rendering engine choice (QTextBrowser vs optional QtWebEngine), application-data location, and the frameless-window fallback.

#### Verification

| Task(s) | How it is validated |
| --- | --- |
| M0.1–M0.5 | Re-run `git ls-files`, `head -n 1 LICENSE`, `file idea/GUI-idea.png`, and `sqlite3` counts for both sample modules; results match the task text. |
| M0.6 | Review `docs/SPEC.md` against the format documentation: every module suffix, every supported tag, the link grammar, the NF rules, and the commentary range cases are present and unambiguous. |
| M0.7 | Follow the README from a clean shell: create a venv, install, run the app entry point, and run the test command. The Python 3.11+ requirement is stated and enforced. |
| M0.8 | `python -m pip install -e ".[dev]"` in a fresh venv; `pip check` passes; importing `PyQt6`, `markdown`, and `pytest` works. |
| M0.9 | `reuse lint` (or an equivalent SPDX scan) reports no missing headers; `docs/ASSETS.md` lists the provenance of every icon, font, and sample module. |
| M0.10 | `python scripts/audit_repo.py` exits 0 on a clean tree and fails on a deliberately added private module fixture. |
| M0.11 | CI is green on a pull request; ruff and pytest failures block merges. |
| M0.12 | ADR is reviewed and accepted; the decision and fallback criteria are recorded in `docs/adr/0001-rendering-and-storage.md`. |

**Exit criteria:** SPEC, project metadata, CI, and ADR-0001 are merged; `docs/SPEC.md` is the reference for every later implementation task.

---

### M1 — Data access, storage, and module parsing

**Goal:** read every supported module type safely, establish the application database, and keep both free of UI dependencies.

#### Checklist

- [ ] **M1.1** Implement `sola/data/discovery.py`: recursively scan a configured root without following symlink escapes; accept `.SQLite3` case-insensitively and `.bundle.zip`; classify by longest suffix (`.dictionary`, `.commentaries`, `.subheadings`, `.crossreferences`, `.plan`, `.devotions`, `.bundle`, plain Bible); derive the abbreviation from the filename; ignore `-*.cache.SQLite3`, `*.search`, `*.new`, `*-journal`, `*-wal`, and `*-shm`.
- [ ] **M1.2** Open modules read-only with URI mode, `PRAGMA query_only=ON`, a busy timeout, and a per-type schema probe; handle WAL/journal sidecars, locked files, corrupt databases, and non-SQLite files with typed errors. Never write to the module directory.
- [ ] **M1.3** Implement `sola/data/info.py`: case-insensitive INFO access, a documented duplicate-key policy (last row wins with a warning), strict boolean parsing with defaults, raw-value retention, and typed accessors per module type.
- [ ] **M1.4** Implement a module registry keyed by resolved path, modification time, and size; refresh adds, removes, and reclassifies modules deterministically; duplicate abbreviations are disambiguated by filename and surfaced in the UI.
- [ ] **M1.5** Implement `sola/data/bible.py`: prefer `books_all`, fall back to `books`; use `title`, then `long_name`; sort by `sorting_order` when present; expose books, chapters, verse ranges, last chapter/verse, and empty-verse records.
- [ ] **M1.6** Create the application database in `sola/storage/db.py`: XDG path, WAL, foreign keys, busy timeout, `PRAGMA user_version`, and a migration runner; add module-metadata and reference-cache tables, then build the derived reference cache (per-book chapter counts and per-chapter verse counts) keyed by module identity and rebuilt in the background when a module changes. Deleting the cache must regenerate it without touching module files.
- [ ] **M1.7** Add a typed error model (`ModuleError`, `SchemaError`, `LookupError`) and structured logging; every error maps to a user-readable message, and no traceback is shown in the UI.
- [ ] **M1.8** Add SQLite fixture builders for every module type, including optional-column variants for commentaries and subheadings; use the public sample modules for integration tests; read private modules only through an environment variable and skip those tests when absent.
- [ ] **M1.9** Add benchmarks: scan 100 modules in under 200 ms, query a chapter in under 20 ms, and build the reference cache for 31k verses in under 2 s on the reference machine.
- [ ] **M1.10** Document the data layer in `docs/MODULES.md`: supported tables, schema variations, read-only policy, cache lifecycle, and how to add a new module type.

#### Verification

| Task(s) | How it is validated |
| --- | --- |
| M1.1 | Fixture directory test asserts the exact inventory and classification, including ignored cache/sidecar files, a `.bundle.zip`, and an unknown database. |
| M1.2 | Attempts to `CREATE`, `UPDATE`, and `DROP` on an opened module raise `OperationalError`; file mtimes are unchanged; corrupt and truncated fixtures produce typed errors. |
| M1.3 | Unit tests cover missing keys, duplicate keys, `true`/`False`/garbage booleans, defaults, and raw-value preservation. |
| M1.4 | Touch a module and assert INFO is re-read; delete one and assert it disappears; rename one and assert the abbreviation changes; duplicate-name handling is deterministic. |
| M1.5 | KJV1611 (`books_all`) and KJV+ (`books`) both list 66 books and 31,102 verses; chapter queries return contiguous verses; empty-text verses remain addressable. |
| M1.6 | The database is created at the XDG path with WAL and a schema version; cached counts equal direct SQL counts; changing a module's mtime invalidates the cache; deleting the cache rebuilds it; module files are unchanged. |
| M1.7 | Every error path has a test and a message; a UI smoke test confirms no traceback text is displayed. |
| M1.8 | `pytest tests/data -q` passes with no private files present; the optional integration run is documented. |
| M1.9 | `python -m tests.benchmarks.data` reports timings within the stated thresholds and writes a machine-readable result. |
| M1.10 | A contributor follows the document to add a synthetic module type and passes the registry test without reading the source. |

**Exit criteria:** all supported module types load read-only; discovery and schema variations are covered by tests; no Qt import exists under `sola/data` or `sola/storage`.

---

### M2 — Application shell and four-pane layout

**Goal:** deliver the touch-first, menu-free workspace shell with four live panes and per-pane toolbars.

#### Checklist

- [ ] **M2.1** Implement `sola/__main__.py`: Python 3.11+ check, `QApplication` metadata, high-DPI rounding policy, Qt version logging, `--module-dir`, `--version`, and `--help`.
- [ ] **M2.2** Implement the main window with no `QMenuBar` and no `menuBar()` call; all commands live in pane headers. A test fails if a `QMenuBar` is instantiated anywhere in the window.
- [ ] **M2.3** Implement `Workspace` using an outer vertical `QSplitter` and two nested horizontal `QSplitter` rows; set 12 px handles, minimum pane sizes, stretch factors, and non-collapsible content.
- [ ] **M2.4** Implement `PaneFrame` and `PaneHeader`: module selector, icon actions, `⋯` overflow, 44 × 44 px minimum buttons, 24 px icons, accessible names, and tooltips.
- [ ] **M2.5** Implement the frameless shell with window controls in the top-right pane header: drag via `startSystemMove`, double-click maximize, edge resizing via `startSystemResize`, and a native-frame fallback setting.
- [ ] **M2.6** Persist splitter state and sizes in `QSettings`; validate restored values; add a reset-layout action to the overflow menu.
- [ ] **M2.7** Add four placeholder panes with titles and empty states; reserve the `MarkdownEditorHost` insertion point in the notes pane without implementing the editor yet.
- [ ] **M2.8** Create an original or GPL-compatible SVG icon set, tint it from the active palette, and record provenance in `docs/ASSETS.md`.
- [ ] **M2.9** Add a pytest-qt offscreen shell test: four panes, three workspace-level splitters, no `QMenuBar`, minimum button sizes, splitter restore, and reset layout. Identify workspace splitters by object name so the notes editor can add an inner splitter later.
- [ ] **M2.10** Perform visual QA at 1456 × 1064 and 1920 × 1080 against the mockup; record intentional deviations in `docs/ui/LAYOUT.md`.

#### Verification

| Task(s) | How it is validated |
| --- | --- |
| M2.1 | `python -m sola --version` and `--help` work without opening a window; the app opens with a valid module directory; Qt version is logged. |
| M2.2 | `window.findChildren(QMenuBar) == []`; a source scan finds no `menuBar()` call; no File/Edit/View actions exist. |
| M2.3 | Assert three named workspace-level splitters and four panes; drag both axes with `QTest` and assert non-zero pane sizes; minimum sizes hold at 1366 × 768. |
| M2.4 | Button-size audit asserts at least 44 × 44 px; every icon button has an accessible name and tooltip; tab order follows the visual order. |
| M2.5 | X11 and Wayland smoke tests: drag, maximize, restore, resize, and close; the native-frame fallback renders correctly. |
| M2.6 | Restart the app and assert sizes/state restore; corrupt the saved state and assert the default layout loads; reset restores the initial ratios. |
| M2.7 | All four panes render at 1366 × 768; the notes placeholder exposes a documented host interface that M6 can replace without changing the layout. |
| M2.8 | Icons render in day and night themes; the asset audit finds a compatible license for every file. |
| M2.9 | `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_shell.py` passes in CI. |
| M2.10 | Side-by-side screenshots at both resolutions; the review checklist covers pane order, toolbar order, no OS title bar, and touch target size. |

**Exit criteria:** the four-pane shell runs, resizes, persists, and passes the no-menu-bar and touch-target tests; the notes pane is ready for M6.

---

### M3 — Bible pane and tag rendering

**Goal:** render Bible chapters faithfully, with working Strong's, footnote, cross-reference, and link behavior.

#### Checklist

- [ ] **M3.1** Wire `BiblePane` to the active translation service; render the current chapter with a book/chapter heading and a clear empty state when no module is selected.
- [ ] **M3.2** Implement navigation: previous/next chapter, a basic reference field (the full parser arrives in M7.2), book/chapter/verse picker, and clamping at canon boundaries; invalid references show an inline message.
- [ ] **M3.3** Implement `sola/render/verse_tags.py` for `<S>`, `<J>`, `<f>`, `<n>`, `<e>`, `<t>`, `<br/>`, `<pb/>`, and `<h>`; escape all other text and tags; preserve whitespace; emit stable HTML with dedicated CSS classes.
- [ ] **M3.4** Generate Strong's anchors: validate one to four digits, choose H/G from the book/testament, honor `strong_numbers_prefix`, and emit `strong:H7225` or `strong:G25` links.
- [ ] **M3.5** Render footnote markers as superscript links to `note:<book>:<chapter>:<verse>:<marker>`; honor `add_space_before_footnote_marker`; show a clear message when no matching footnote exists.
- [ ] **M3.6** Support `<m>` morphology annotations and `<l>` inserted words with dedicated styles and a setting to hide morphology annotations.
- [ ] **M3.7** Implement the link router: rewrite module `B:`, `S:`, `C:@`, and `http(s)` targets; intercept `anchorClicked`; block `file:`, `javascript:`, `data:`, and unknown schemes; confirm external links.
- [ ] **M3.8** Resolve `CONTENT_FRAGMENTS` and `<!-- INCLUDE(...) -->` comments for current-module and cross-module references, with a recursion guard, `TEXTUAL` handling, and a missing-fragment placeholder.
- [ ] **M3.9** Display subheadings from a `.subheadings` module and embedded `stories`: honor language matching, `order_if_several`, module font settings, `<h>` inline headings, and `<x>` hyperlinks; add a show/hide toggle.
- [ ] **M3.10** Build the Bible pane toolbar: translation selector, reference label, previous/next chapter, font size, and overflow. Back/forward, search, and commentary sync are added when their services land in M5 and M7; keep every current control touch-sized.
- [ ] **M3.11** Add golden-HTML tests for every tag, integration tests with KJV+ and KJV1611, boundary tests for first/last chapters, empty verses, and mocked link routing.
- [ ] **M3.12** Add security tests for module text containing `<script>`, `<iframe>`, event-handler attributes, `javascript:` links, remote images, and oversized tags; assert no network fetch occurs.
- [ ] **M3.13** Benchmark rendering a 150-verse chapter at under 150 ms and a warm chapter switch at under 100 ms; profile long chapters and eliminate layout stalls.

#### Verification

| Task(s) | How it is validated |
| --- | --- |
| M3.1 | Open KJV+ and KJV1611 and navigate to Eph 6 and Ps 119; all verses render, headings are correct, and the empty state works with no module. |
| M3.2 | Navigate to Gen 1, Mal 4, and Rev 22; previous/next clamps correctly; picker selection matches the module's book list; an invalid reference shows an inline error. |
| M3.3 | Golden HTML snapshots for each tag; unknown `<script>` text is escaped; no raw module markup reaches the document. |
| M3.4 | Fixture matrix for Hebrew, Greek, and `strong_numbers_prefix=G`; clicking emits the expected lookup signal. |
| M3.5 | Footnote click with a matching commentary opens the article; an unmatched marker shows the no-footnote message; spacing behavior matches INFO. |
| M3.6 | Morphology and inserted-word fixtures render with the expected classes; hiding morphology removes the annotation without breaking spacing. |
| M3.7 | Table-driven link tests for every scheme; blocked schemes produce no navigation; external links require confirmation. |
| M3.8 | Recursion, cross-module, missing-fragment, and `TEXTUAL` cases pass; no infinite loop or unbounded expansion. |
| M3.9 | KJV-s fixture subheadings appear before the correct verses; `order_if_several` is respected; `<x>` links navigate; toggle hides them in both embedded and module modes. |
| M3.10 | Every toolbar action works; overflow contains secondary actions; buttons meet the touch-size audit. |
| M3.11 | `pytest tests/render tests/ui/test_bible_pane.py` passes; both public modules are exercised. |
| M3.12 | Sanitizer tests assert no `script`, `iframe`, `onclick`, `javascript:`, or remote image URL survives; a network spy observes zero requests. |
| M3.13 | Benchmark script reports the timings; no UI event-loop stall over 100 ms during a chapter switch. |

**Exit criteria:** a chapter renders correctly from both public samples, every required tag has a golden test, and all link types route safely without widget navigation.

---

### M4 — Dictionary, Strong's, and NF1/NF2 lookup

**Goal:** implement the dictionary pane and the documented lookup pipeline, including Strong's numbers and normalized word forms.

#### Checklist

- [ ] **M4.1** Implement the dictionary loader: tolerate an absent `DICTIONARY` table, resolve type with `type` first and `is_strong` second, apply the documented heuristic, and read topic, definition, short definition, lexeme, transliteration, and pronunciation.
- [ ] **M4.2** Implement `sola/data/normalization.py` for NF1, NF2, and NF0: Unicode NFD, lowercase for NF1/NF2, combining-mark removal for NF2, no lowercasing for NF0, data-driven pre/post processing from `WORDS_PROCESSING`, and the documented Greek, Hebrew, Russian, and Syriac rules.
- [ ] **M4.3** Derive the lookup language list from the Bible module's `language` and `hyperlink_languages`, adding `el`/`Original` for Greek codepoints and `iw`/`he`/`Original` for Hebrew codepoints.
- [ ] **M4.4** Build the app-owned lookup index: normalized `lookup_word` and `lookup_topic` tables with B-tree indexes, optional place columns, matching type, and a version keyed by module identity; build in the background and rebuild atomically. Do not depend on module hash columns.
- [ ] **M4.5** Implement Strong's lookup: lowercase topic, current lexicon first, current-place filter, then any dictionary or lexicon; return a typed result or a no-result.
- [ ] **M4.6** Implement the word lookup pipeline: stage 1 with NF1/NF2 and matching type, stage 2 with NF2; filters for current dictionary, current place, default topic, and any dictionary; NF0 for concordance dictionaries; lookup-mode order for Strong vs Dictionaries.
- [ ] **M4.7** Implement dictionary topic links (`S:`), exact-topic matching, NF2 fallback, and dictionary back/forward history.
- [ ] **M4.8** Render dictionary articles: sanitized HTML, header with topic, lexeme, transliteration, pronunciation, short definition, module label, and resolved content fragments.
- [ ] **M4.9** Build dictionary pane controls: dictionary/lexicon selector, lookup-mode toggle, multiple-result picker, and a no-result state with a clear next action.
- [ ] **M4.10** Add normalization vectors, lookup-filter unit tests, an end-to-end fixture test, and an optional integration test with a local Strong's module through an environment variable.
- [ ] **M4.11** Benchmark index construction for a 14k-topic dictionary at under 2 s and a warm lookup at under 50 ms; keep all database work off the UI thread.

#### Verification

| Task(s) | How it is validated |
| --- | --- |
| M4.1 | A Strong's module, an explanatory module, a word-forms-only module, and a module with no `type` all classify correctly; optional columns are absent without failure. |
| M4.2 | Table-driven vectors for Greek accents, Hebrew niqqud, Russian stress marks, and French diacritics; expected NF1/NF2/NF0 strings match exactly. |
| M4.3 | Fixture matrix confirms language lists for monolingual, bilingual, Greek, and Hebrew cases. |
| M4.4 | Index rebuild completes; `EXPLAIN QUERY PLAN` uses the normalized indexes; deleting the index rebuilds it; a module change invalidates it. |
| M4.5 | Strong's fixtures resolve the current lexicon, current place, and fallback paths; missing topics return no result. |
| M4.6 | Each filter has a unit test; stage 1 and stage 2 are distinguished; concordance NF0 works; the two lookup modes try targets in the documented order. |
| M4.7 | `S:` links resolve exact topics and NF2 fallbacks; back/forward restores prior articles. |
| M4.8 | A known article renders its header and definition; included fragments appear; XSS tests pass. |
| M4.9 | Lookup-mode switch changes behavior; multiple results show the picker; no-result state offers a useful action. |
| M4.10 | `pytest tests/data/test_normalization.py tests/data/test_lookup.py` passes without private files; the optional integration run is documented. |
| M4.11 | Benchmark script reports build and lookup times within target; a UI responsiveness test observes no blocked event loop. |

**Exit criteria:** Strong's and word lookups pass the fixture matrix, the dictionary pane renders articles and links, and NF behavior is locked by golden vectors.

---

### M5 — Commentary pane and range matching

**Goal:** show the right commentary article for the current passage, including footnote-mode modules and optional schema columns.

#### Checklist

- [ ] **M5.1** Implement the commentary loader: active module, INFO `is_footnotes`, optional `books`, and schema introspection for missing `is_preceding`, `marker`, `chapter_number_to`, and `verse_number_to` columns.
- [ ] **M5.2** Implement range normalization and querying: whole-book rows (`chapter_number_from = 0`), null end chapter, null end verse, both null, cross-chapter ranges, inclusive boundaries, and `is_preceding` link-placement semantics.
- [ ] **M5.3** Implement `is_footnotes=true`: show the position and marker header, ignore `chapter_number_to`, and match the marker from the Bible `<f>` link; for `false`, show the position on a separate line and ignore markers.
- [ ] **M5.4** Render multiple matching articles with `commentary_header` and `break_between_articles` separators, module `html_style`, resolved fragments, and sanitization.
- [ ] **M5.5** Sync the commentary pane to Bible navigation, with a follow toggle; preserve a manually selected article when follow is off; reload the current place on module switch.
- [ ] **M5.6** Route commentary links: `B:` to the Bible, `C:@` to another commentary article, `S:` to the dictionary, and external links through confirmation.
- [ ] **M5.7** Build the commentary toolbar: module selector, current range label, copy, follow toggle, search placeholder, and collapse; keep window controls reachable.
- [ ] **M5.8** Add tests for the range matrix, footnote mode, ordering, optional columns, empty state, and article separators.
- [ ] **M5.9** Add a pytest-qt integration test: clicking a Bible footnote marker opens the matching commentary article, and Bible navigation refreshes the commentary.

#### Verification

| Task(s) | How it is validated |
| --- | --- |
| M5.1 | The local commentary fixture without `is_preceding` loads correctly; a module with the column also loads; a missing `books` table falls back to the Bible book names. |
| M5.2 | A boundary matrix covers whole-book, single-verse, multi-verse, cross-chapter, null-end, inclusive-start/end, and `is_preceding` cases; the Python predicate and SQL prefilter agree. |
| M5.3 | True and false footnote fixtures produce the correct headers and marker behavior; a marker mismatch shows the no-match state. |
| M5.4 | Multiple rows render in order with separators; module style is applied; included fragments appear; XSS tests pass. |
| M5.5 | Navigating the Bible updates the commentary when follow is on and leaves it alone when off; switching modules reloads the current place. |
| M5.6 | Each link type routes correctly; external links confirm; `C:@` selects the target article. |
| M5.7 | Every toolbar control works and meets the touch-size audit; collapsing the pane does not hide the window controls. |
| M5.8 | `pytest tests/data/test_commentary.py` passes; fixtures cover optional columns and null semantics. |
| M5.9 | `pytest tests/ui/test_commentary_pane.py` passes; footnote click and sync are exercised end to end. |

**Exit criteria:** commentary selection matches the range specification, footnote mode works both ways, and pane synchronization is verified by UI tests.

---

### M6 — Markdown notes editor

**Goal:** replace the notes placeholder with a durable, touch-friendly Markdown editor and preview.

#### Checklist

- [ ] **M6.1** Implement `MarkdownEditor`: `QPlainTextEdit` plus `QTextBrowser` preview, edit/split/preview modes, an inner splitter, and minimum sizes that work at 1366 × 768.
- [ ] **M6.2** Render Markdown with the `markdown` package (extra, sane lists, line breaks), sanitize the output with an allowlist, strip raw HTML by default, and route links through the shared link handler.
- [ ] **M6.3** Add the notes, bookmarks, and reading-progress schema migration on top of the M1 storage layer; use `PRAGMA user_version` and back up before migration.
- [ ] **M6.4** Bind notes to a canonical passage (book/chapter/verse/range) with an optional translation scope; support general notes; show an empty state and load the current passage on navigation.
- [ ] **M6.5** Add autosave with a 1.5 s debounce plus saves on focus loss, pane switch, and close; show a dirty indicator; use transactions and WAL; prompt before discarding unsaved text.
- [ ] **M6.6** Build the notes toolbar: bold, italic, heading, bullet and numbered lists, quote, code, link, and preview; insert Markdown syntax at the cursor; keep icon buttons at least 44 × 44 px.
- [ ] **M6.7** Add shortcuts and undo/redo: Ctrl+B, Ctrl+I, Ctrl+S, Ctrl+Z, Ctrl+Y, Ctrl+Shift+P; Tab indentation; accessible names for every action.
- [ ] **M6.8** Add a notes list for the current book and translation, with open, delete, and timestamps; rows meet the touch-size requirement.
- [ ] **M6.9** Add tests for Markdown round-tripping, autosave timing, dirty-state transitions, sanitizer XSS, note scoping, migration, and deletion.
- [ ] **M6.10** Add a pytest-qt test: type a note, preview it, switch passage, return, confirm persistence, and resize the pane without losing text.

#### Verification

| Task(s) | How it is validated |
| --- | --- |
| M6.1 | All three modes switch without layout jumps; the inner splitter resizes; the editor remains usable at the minimum window size. |
| M6.2 | Markdown tables, lists, code blocks, and links render; a raw `<script>` payload is removed; external links confirm before opening. |
| M6.3 | Fresh database migrates to the current version; CRUD works; a migration from v1 to v2 preserves notes and bookmarks. |
| M6.4 | A note saved at Gen 1:1 reloads at Gen 1:1; a general note persists; switching translation follows the documented scope behavior. |
| M6.5 | Typing stops and the note is committed within 2 s; closing with a dirty buffer prompts; a simulated crash reopens the last committed draft. |
| M6.6 | Each formatting action inserts the expected syntax and can be undone; preview reflects changes. |
| M6.7 | QTest key events trigger each shortcut; undo/redo restores text; focus order is sane. |
| M6.8 | The list updates after save; opening and deleting work; timestamps are correct; delete requires confirmation. |
| M6.9 | `pytest tests/services/test_notes.py tests/render/test_markdown.py` passes; sanitizer cases are covered. |
| M6.10 | `pytest tests/ui/test_notes_pane.py` passes; no text loss on passage switch or pane resize. |

**Exit criteria:** notes survive restarts, autosave and sanitization are tested, and the pane is fully usable with touch and keyboard.

---

### M7 — Navigation, search, bookmarks, and reading plans

**Goal:** add the deferred study tools: reliable history, reference parsing, search, cross-references, bookmarks, and reading plans.

#### Checklist

- [ ] **M7.1** Implement the navigation service: a `Location` dataclass, bounded back/forward stacks (100 entries), last-location restore, change signals for panes, and back/forward buttons in the Bible toolbar.
- [ ] **M7.2** Implement the reference parser and formatter: `Gen 1:1`, `1 John 3:16`, `John 3`, `Gen 1:1-3`, and `Gen 1-2`; use module short/long names plus canonical aliases; match case-insensitively and ignore diacritics; report invalid input clearly.
- [ ] **M7.3** Implement verse search for the active translation: FTS5 when available, `LIKE` fallback otherwise; build and update the search index; wire the Bible toolbar search action; show reference and snippet; click to navigate and highlight; support cancellation and a result limit.
- [ ] **M7.4** Implement cross-reference support: load `.crossreferences`, query the current verse and verse ranges, honor `requires_reverse_processing`, sort by votes, render a list, and navigate on click.
- [ ] **M7.5** Implement bookmarks: model and CRUD in the application database, a toggle for the current verse, toolbar bookmark actions in the Bible and commentary panes, a manager dialog with labels, jump-to, and duplicate handling.
- [ ] **M7.6** Implement reading-plan loading: `.plan` modules, `READING_PLAN` rows, plan selector using `description_LL`, day/evening/item grouping, and a progress table.
- [ ] **M7.7** Implement reading-plan navigation: choose a start date or plan day, compute "today," mark a day complete, move to previous/next day, and jump to the passage.
- [ ] **M7.8** Add persistence tests for history, bookmarks, and plan progress across restarts and schema migrations.
- [ ] **M7.9** Add search tests for accents, Greek, Hebrew, punctuation-only queries, empty queries, and large result sets; verify ranking is deterministic.
- [ ] **M7.10** Add pytest-qt tests for back/forward, search-result navigation, bookmark toggling, and opening a plan day.
- [ ] **M7.11** Document navigation, search, and plans in `docs/NAVIGATION.md`, `docs/SEARCH.md`, and `docs/PLANS.md`.

#### Verification

| Task(s) | How it is validated |
| --- | --- |
| M7.1 | Visit A, B, C and traverse back/forward; restart restores the last location; the stack is bounded and does not duplicate entries. |
| M7.2 | A table of valid and invalid references passes; formatter output round-trips through the parser; module abbreviations and canonical names both work. |
| M7.3 | Search 31k verses in under 300 ms on the reference machine; FTS5 absence falls back cleanly; cancellation stops work; clicking a result navigates and highlights. |
| M7.4 | A cross-reference fixture returns the expected targets; reverse processing removes duplicates; votes sort deterministically. |
| M7.5 | Toggle a bookmark, restart, and confirm it persists; the manager jumps to it; duplicates are prevented; no module file changes. |
| M7.6 | The plan fixture loads the expected days and items; `description_LL` selection falls back to `description`; evening items group correctly. |
| M7.7 | A fake clock computes the correct day; day 1 and the last day are handled; marking complete persists and updates progress. |
| M7.8 | Restart tests preserve history, bookmarks, and progress; migration tests pass. |
| M7.9 | Unicode search cases pass; empty and punctuation-only queries return a clear message; ranking is stable across runs. |
| M7.10 | UI tests exercise each flow with no unexpected dialog or freeze. |
| M7.11 | Docs are reviewed against the implemented behavior; screenshots are current. |

**Exit criteria:** history, reference entry, search, cross-references, bookmarks, and plans work end to end and persist across restarts.

---

### M8 — Settings, theming, touch polish, and performance

**Goal:** turn the feature-complete app into a product-quality desktop experience.

#### Checklist

- [ ] **M8.1** Implement the settings model: module directory, active modules, day/night theme, font scale, splitter layout, lookup mode, frame mode, autosave interval, and search options; validate values and migrate defaults.
- [ ] **M8.2** Build the settings dialog as a `QDialog` with a directory picker, module selection, theme and font controls, apply/cancel, and a first-run flow that chooses a module directory.
- [ ] **M8.3** Handle module-directory changes: background rescan, progress and cancel, invalid or empty path messages, selection preservation by filename, and safe pane reloads when a module disappears.
- [ ] **M8.4** Implement the theme engine: day and night palettes plus QSS tokens; replace `%COLOR_*%` tokens; map `<font color="0..5">` indexes; apply module `html_style`; sanitize CSS; switch live without restart.
- [ ] **M8.5** Implement font scaling: global 80–200%, multiplied by the module's `font_scale`; live update; reset; persistence; no clipping at either extreme.
- [ ] **M8.6** Perform the touch audit: 44 × 44 px controls, 8 px spacing, `QScroller` kinetic scrolling in every pane, long-press actions, tap-versus-drag thresholds, and a documented inline-link exception.
- [ ] **M8.7** Make the layout responsive: 1366 × 768 minimum, 1920 × 1080 target, maximize/restore, pane collapse, header overflow on narrow widths, and no fixed pixel widths that clip content.
- [ ] **M8.8** Meet performance targets: warm startup under 2.5 s, chapter switch under 100 ms, dictionary lookup under 150 ms, search under 300 ms, memory under 300 MB; keep index builds in the background.
- [ ] **M8.9** Add accessibility: accessible names and descriptions, visible focus, logical focus order, contrast checks, keyboard shortcuts for every primary action, and an Orca smoke test.
- [ ] **M8.10** Add tests for settings round-trips, theme-token snapshots, absence of hardcoded UI colors, the data/render/storage no-PyQt6 boundary, and performance benchmarks.
- [ ] **M8.11** Run and sign a manual touchscreen checklist covering tap, scroll, long-press, splitter drag, settings, notes typing, and on-screen keyboard behavior.

#### Verification

| Task(s) | How it is validated |
| --- | --- |
| M8.1 | Every setting round-trips through restart; invalid values fall back to defaults; the settings schema is versioned. |
| M8.2 | Apply changes the running app; cancel reverts; the first-run flow handles a valid directory, an invalid directory, and an empty directory. |
| M8.3 | Switch between two module directories; selections with matching filenames survive; missing modules show a safe empty state; the UI stays responsive. |
| M8.4 | Snapshot tests assert token substitution; day/night switch updates panes and module HTML; CSS sanitization blocks remote `url()` and unsafe constructs. |
| M8.5 | Font-size measurements match the requested scale; module `font_scale` multiplies correctly; no clipping at 80% or 200%. |
| M8.6 | Manual checklist on a touchscreen confirms scroll and tap behavior; no accidental navigation while kinetic scrolling; controls meet the size audit. |
| M8.7 | Screenshots at 1366 × 768 and 1920 × 1080 show no clipping; collapse/restore works; headers overflow gracefully. |
| M8.8 | `python -m tests.benchmarks.app` reports metrics within target; profiling shows no long UI-thread stall. |
| M8.9 | Accessibility checklist passes; Orca reads pane titles, buttons, and editor content; focus is never trapped. |
| M8.10 | `pytest tests/services/test_settings.py tests/ui/test_theme.py tests/test_architecture.py` passes; the architecture test rejects PyQt6 imports in data, render, and storage, and the color scan finds no unexplained hardcoded values. |
| M8.11 | Signed checklist stored in `docs/testing/TOUCH.md`; every row has a pass/fail note and an issue link when failing. |

**Exit criteria:** settings, theming, touch, accessibility, and performance checks pass on the reference desktop and a touchscreen.

---

### M9 — Packaging, documentation, and release

**Goal:** produce a clean, installable, GPLv3-compliant binary release that bundles no Bible modules.

#### Checklist

- [ ] **M9.1** Lock dependencies with exact versions and hashes in `requirements.lock`; test Python 3.11, 3.12, and 3.13; record the supported PyQt6 and `markdown` versions.
- [ ] **M9.2** Build the PyInstaller one-directory bundle with a spec file covering hidden imports, Qt platform/imageformat/style plugins, and excludes; decide and record whether Nuitka remains an alternative.
- [ ] **M9.3** Build the Debian package: `debian/control`, `rules`, `.install`, desktop entry, icon, and dependencies; test install, upgrade, and removal on a clean system.
- [ ] **M9.4** Add AppStream metadata and a desktop entry with id, name, summary, the chosen GPLv3 identifier, screenshots, and release notes; validate with `appstreamcli` and `desktop-file-validate`.
- [ ] **M9.5** Implement `scripts/audit_release.py`: fail on any module database or bundle archive in a binary release staging tree; for source archives, allow only the documented public samples; reject caches, private paths, and test fixtures. Audit the git history for proprietary modules.
- [ ] **M9.6** Complete the GPLv3 compliance package: `LICENSE` in source and binary artifacts, a source-offer or source link, third-party notices for PyQt6/Qt/`markdown`/icons, and an asset-license audit.
- [ ] **M9.7** Write the user guide: install, first run and module directory, module types, Bible/dictionary/commentary use, notes, search, bookmarks, plans, themes, shortcuts, backup, and troubleshooting.
- [ ] **M9.8** Write developer documentation: architecture, data model, module parsing, test strategy, release process, and an ADR index.
- [ ] **M9.9** Set version 0.1.0, add `CHANGELOG.md`, define the release checklist, and create the git tag.
- [ ] **M9.10** Add the CI release job: tag-triggered build, SHA-256 checksums, artifacts, and optional provenance attestation; no secrets in logs.
- [ ] **M9.11** Run clean-VM QA on Debian 12 and MX Linux: install, launch, open public modules, exercise every pane, test touch and keyboard, uninstall, and record results.

#### Verification

| Task(s) | How it is validated |
| --- | --- |
| M9.1 | Fresh venv installs from the lock file with hashes; `pip check` passes; all three Python versions pass the test suite. |
| M9.2 | The built bundle launches on a clean Debian VM; Qt platform and image plugins load; `--version` matches the package version. |
| M9.3 | `dpkg -i` installs cleanly; the desktop entry launches the app; upgrading preserves user data; `dpkg -r` removes the package without deleting notes. |
| M9.4 | `appstreamcli validate` and `desktop-file-validate` exit 0; metadata fields match the release. |
| M9.5 | Audit exits 0 on the release tree and fails when a fixture module is added; the binary artifact listing contains zero module files (`.SQLite3` and `.bundle.zip`), while the source archive contains only allowlisted public samples with recorded provenance. |
| M9.6 | License audit checklist is complete; every third-party component has a compatible license and notice; source availability is documented. |
| M9.7 | A new user follows the guide from install to notes on a clean VM without developer help; screenshots match the current UI. |
| M9.8 | A new contributor can set up, run tests, and build the package using only the docs. |
| M9.9 | Changelog and version are consistent across `pyproject.toml`, the desktop file, AppStream, and the tag. |
| M9.10 | The release workflow produces the expected artifacts and checksums; a re-run is reproducible within documented limits. |
| M9.11 | QA record is signed; no blocker bugs remain; known issues are documented in the release notes. |

**Exit criteria:** a clean Debian/MX system installs the package, runs the app, loads user modules, and passes the release audit with no bundled modules.

---

### M10 — Post-1.0 backlog

**Goal:** capture valuable extensions without diluting the first release.

#### Checklist

- [ ] **M10.1** Add `.bundle.zip` import: validate the archive, block path traversal and symlinks, enforce size limits, extract fonts/themes into app data, and register bundled modules without executing scripts.
- [ ] **M10.2** Add a devotions pane for `.devotions` modules, with day selection and integration into the reading workflow.
- [ ] **M10.3** Add parallel Bible translations or a compare view using the existing splitter infrastructure.
- [ ] **M10.4** Add full morphology support: `MORPHOLOGY_INDICATIONS`, `MORPHOLOGY_TOPICS`, `<m>` details, and links to morphology topics.
- [ ] **M10.5** Add note export and import (Markdown, ZIP) with safe paths and conflict handling.
- [ ] **M10.6** Add advanced search: phrases, boolean operators, Strong's numbers, and cross-module search.
- [ ] **M10.7** Add right-to-left layout support and UI localization through Qt Linguist.
- [ ] **M10.8** Add custom reading-plan creation and import, with progress migration.
- [ ] **M10.9** Add backup and restore for the application database and notes, including a portable mode.

#### Verification

| Task(s) | How it is validated |
| --- | --- |
| M10.1 | Archive fixtures with traversal, symlink, oversized, and valid bundles; only the valid bundle extracts, and no code runs. |
| M10.2 | A devotions fixture renders the correct day; navigation between days persists. |
| M10.3 | Two translations stay in sync on navigation; independent scrolling is optional and documented. |
| M10.4 | Morphology fixtures resolve indications and topics; links open the correct article. |
| M10.5 | Round-trip export/import preserves Markdown and metadata; malicious paths are rejected. |
| M10.6 | Query-language tests cover precedence, phrases, and Unicode; performance remains bounded. |
| M10.7 | RTL screenshots show mirrored layout; translated strings load without truncation. |
| M10.8 | A custom plan imports, displays, and tracks progress across restarts. |
| M10.9 | Backup restores into a fresh profile; portable mode leaves no data outside its directory. |

**Exit criteria:** each backlog item is promoted to a milestone with its own spec, acceptance tests, and user documentation before implementation.

---

## Risks and open questions

### Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Qt rich text supports only a subset of HTML/CSS; module articles may render differently from the reference app. | Medium–high | Build a corpus of real dictionary/commentary articles; add golden rendering tests; sanitize and normalize; record fallback criteria for an optional QtWebEngine mode in ADR-0001. |
| Module HTML is untrusted and may contain scripts, remote resources, or pathological markup. | High | Allowlist sanitizer, no JavaScript engine, blocked remote loads, size limits, and XSS tests in M3/M4/M5/M6. |
| Large modules make initial indexing or search slow. | Medium | Background workers, incremental indexes, B-tree indexes, atomic swaps, progress/cancel, and benchmarks with the 31k-verse samples and a 14k-topic dictionary. |
| Proprietary modules or unverified sample provenance leak into a release. | High | Read-only runtime loading, `.gitignore` rules, a release audit that rejects every module database, and a documented provenance check for `data/` samples. |
| A dependency or asset is not GPLv3-compatible. | High | License inventory, SPDX headers, `reuse`-style checks, and a release gate for third-party notices. |
| Frameless windows behave poorly on some Wayland/GNOME configurations. | Medium | Test X11 and Wayland; use `startSystemMove`/`startSystemResize`; ship a native-frame fallback and document it. |
| Touch scrolling conflicts with text selection and inline-link taps. | Medium | `QScroller`, tap/drag thresholds, long-press for selection, generous line height for links, and a manual touchscreen checklist. |
| SQLite read-only opens fail because of WAL/journal sidecars or file locks. | Medium | Read-only URI mode, sidecar detection, clear errors, and an optional snapshot-copy path for stubborn files; never write to the module directory. |
| NF1/NF2 language rules are subtle and easy to get wrong. | High | Golden vectors for Greek, Hebrew, Russian, and accented Latin; data-driven `WORDS_PROCESSING`; isolate rules in one module. |
| Commentary range semantics around null end fields are ambiguous in real modules. | Medium | One normalization function, a boundary matrix, and fixtures that include missing optional columns. |
| Removing the menu bar hurts discoverability and accessibility. | Medium | Contextual icon toolbars, tooltips, accessible names, keyboard shortcuts, and an overflow menu that never hides primary actions. |
| Search depends on FTS5 being compiled into the runtime SQLite. | Medium | Capability check at startup with a `LIKE` fallback and a benchmark for both paths. |
| Notes data-model choices become hard to migrate. | Medium | Decide the binding model in M0/M6, version the schema, back up before migration, and test upgrades. |
| Reading-plan "today" depends on user time zone and start date. | Low–medium | Store an explicit start date and plan day; use local time consistently; document behavior and test with a fake clock. |
| Bundle ZIP import can escape the target directory. | High (post-1.0) | Reject traversal and symlinks, enforce size and count limits, extract into a staging directory, and never execute bundled content. |

### Open questions

1. **Notes binding:** should a note attach to a verse, a verse range, a chapter, or a free document? Is it shared across translations by default? Decide before M6.
2. **Parallel translations:** is a second Bible pane or a compare mode required for v1.0, or is it post-1.0?
3. **Rendering engine:** is QTextBrowser sufficient for the real module corpus, or is an optional QtWebEngine mode needed? ADR-0001 must record the decision and fallback criteria.
4. **Window chrome:** should frameless be the default on every desktop, or only where the compositor supports system move/resize cleanly?
5. **Lookup index location:** one central index for all dictionaries, or one index per module? Central is simpler to query; per-module is easier to invalidate.
6. **Minimum screen:** is 1366 × 768 the true minimum, and is portrait orientation supported? This affects pane minimums and toolbar overflow.
7. **Sample provenance:** are `data/KJV1611.SQLite3` and `data/KJV+.SQLite3` cleared for release-artifact redistribution, or should they remain development-only samples?
8. **License identifier:** is the project `GPL-3.0-only` or `GPL-3.0-or-later`? The current `LICENSE` is the GPLv3 text, but the "or later" choice must be explicit in `pyproject.toml` and source headers.
9. **Bundle behavior:** should `.bundle.zip` import copy modules into the user's module directory, or register them in place? Copying is safer but duplicates data.
10. **Search semantics:** should search ignore accents and diacritics by default, and should results rank by relevance or canonical order?
11. **Reading-plan start:** does "today" start when the user first opens the plan, on a user-chosen date, or on the calendar day of the first reading?
12. **Notes sync:** is external sync out of scope permanently, or should the notes store be designed for a future folder-based sync from the start?

### Assumptions to validate early

- The public sample modules remain usable as development fixtures and are not modified by the application.
- Module files are static during a session; the app can cache schema and counts safely and invalidate on path, size, or mtime changes.
- The primary user has a large touchscreen and a keyboard; both input paths must remain first-class.
- A single-process desktop app with background workers is sufficient; no server component is needed.
- The application database can live in the XDG data directory and be backed up independently of the modules.
