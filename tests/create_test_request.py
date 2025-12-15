"""Integration test for the code review API."""

import json
from pathlib import Path

# Sample test request
sample_diff = """diff --git a/app/auth.py b/app/auth.py
new file mode 100644
index 0000000..abcdef
--- /dev/null
+++ b/app/auth.py
@@ -0,0 +1,6 @@
+def login(username, password):
+    # Vulnerable to SQL injection
+    query = f"SELECT * FROM users WHERE user='{username}' AND pass='{password}'"
+    return db.execute(query)
"""

sample_request = {
    "diff": sample_diff,
    "language": "python",
    "context": {
        "repo": "test/repo",
        "commit_sha": "abc123",
        "pr_number": 1,
        "author": "testuser"
    }
}

# Save to file for testing
test_dir = Path(__file__).parent
(test_dir / "sample_request.json").write_text(json.dumps(sample_request, indent=2))

print("✓ Test request file created: tests/sample_request.json")
