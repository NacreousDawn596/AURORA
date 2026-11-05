from aurora.benchmark.change import parse_unified_diff


def test_parse_unified_diff_counts_added_and_deleted_lines() -> None:
    diff = """diff --git a/src/a.py b/src/a.py
index 111..222 100644
--- a/src/a.py
+++ b/src/a.py
@@ -1,2 +1,3 @@
 keep
-old
+new
+added
"""
    summary = parse_unified_diff(diff)
    assert summary.changed_file_count == 1
    assert summary.additions == 2
    assert summary.deletions == 1
    assert summary.change_size == 3
    assert summary.extension_counts == {".py": 1}


def test_parse_new_file() -> None:
    diff = """diff --git a/new.txt b/new.txt
new file mode 100644
--- /dev/null
+++ b/new.txt
@@ -0,0 +1,2 @@
+one
+two
"""
    result = parse_unified_diff(diff)
    assert result.files[0].path == "new.txt"
    assert result.files[0].old_path is None
    assert result.additions == 2
    assert result.deletions == 0


def test_parse_deleted_file() -> None:
    diff = """diff --git a/old.py b/old.py
deleted file mode 100644
--- a/old.py
+++ /dev/null
@@ -1 +0,0 @@
-gone
"""
    result = parse_unified_diff(diff)
    assert result.files[0].path == "old.py"
    assert result.files[0].old_path == "old.py"
    assert result.deletions == 1


def test_parse_rename_preserves_old_and_new_paths() -> None:
    diff = """diff --git a/old.py b/new.py
similarity index 100%
rename from old.py
rename to new.py
"""
    item = parse_unified_diff(diff).files[0]
    assert item.old_path == "old.py"
    assert item.path == "new.py"


def test_parse_binary_file_marks_binary_without_line_counts() -> None:
    diff = """diff --git a/image.png b/image.png
index 111..222 100644
Binary files a/image.png and b/image.png differ
"""
    result = parse_unified_diff(diff)
    assert result.binary_file_count == 1
    assert result.additions == 0
    assert result.deletions == 0


def test_parse_ignores_hunk_headers_and_file_markers() -> None:
    diff = """diff --git a/a.txt b/a.txt
--- a/a.txt
+++ b/a.txt
@@ -2 +2 @@
+real
\ No newline at end of file
"""
    assert parse_unified_diff(diff).additions == 1


def test_empty_or_unrecognized_diff_is_empty() -> None:
    assert parse_unified_diff("").changed_file_count == 0
    assert parse_unified_diff("not a git diff\n+not counted").changed_file_count == 0


def test_extension_counts_include_extensionless_files() -> None:
    diff = """diff --git a/Dockerfile b/Dockerfile
--- a/Dockerfile
+++ b/Dockerfile
@@ -0,0 +1 @@
+FROM scratch
"""
    assert parse_unified_diff(diff).extension_counts == {"<none>": 1}
