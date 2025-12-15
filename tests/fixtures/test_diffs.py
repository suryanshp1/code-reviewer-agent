"""Test fixture diffs for code review testing.

This module provides various code diff scenarios to test different aspects
of the code review agents, including security, performance, and quality issues.
"""

# Security Issue: SQL Injection
SQL_INJECTION_DIFF = """diff --git a/app/auth.py b/app/auth.py
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

# Security Issue: XSS Vulnerability
XSS_VULNERABILITY_DIFF = """diff --git a/app/views.py b/app/views.py
new file mode 100644
index 0000000..xyz789
--- /dev/null
+++ b/app/views.py
@@ -0,0 +1,5 @@
+def render_comment(comment):
+    # Vulnerable to XSS - no sanitization
+    html = f"<div class='comment'>{comment.text}</div>"
+    return html
"""

# Security Issue: Hardcoded Secrets
HARDCODED_SECRETS_DIFF = """diff --git a/app/config.py b/app/config.py
new file mode 100644
index 0000000..abc456
--- /dev/null
+++ b/app/config.py
@@ -0,0 +1,5 @@
+# Bad practice: hardcoded credentials
+DATABASE_URL = "postgresql://admin:SuperSecret123@prod-db.example.com:5432/mydb"
+API_KEY = "sk-1234567890abcdefghijklmnop"
+SECRET_TOKEN = "my-super-secret-token-12345"
"""

# Performance Issue: N+1 Query Problem
N_PLUS_ONE_QUERY_DIFF = """diff --git a/app/models.py b/app/models.py
new file mode 100644
index 0000000..def789
--- /dev/null
+++ b/app/models.py
@@ -0,0 +1,8 @@
+def get_users_with_posts():
+    users = User.query.all()  # Query 1
+    result = []
+    for user in users:
+        # N+1 problem: separate query for each user
+        posts = Post.query.filter_by(user_id=user.id).all()
+        result.append({'user': user, 'posts': posts})
+    return result
"""

# Performance Issue: Inefficient Algorithm
INEFFICIENT_ALGORITHM_DIFF = """diff --git a/app/utils.py b/app/utils.py
new file mode 100644
index 0000000..ghi012
--- /dev/null
+++ b/app/utils.py
@@ -0,0 +1,10 @@
+def find_duplicates(items):
+    # O(n^2) algorithm - inefficient for large lists
+    duplicates = []
+    for i in range(len(items)):
+        for j in range(i + 1, len(items)):
+            if items[i] == items[j] and items[i] not in duplicates:
+                duplicates.append(items[i])
+    return duplicates
"""

# Code Quality Issue: Poor Naming and Complexity
POOR_QUALITY_DIFF = """diff --git a/app/processor.py b/app/processor.py
new file mode 100644
index 0000000..jkl345
--- /dev/null
+++ b/app/processor.py
@@ -0,0 +1,15 @@
+def p(d, x, y):
+    # Poor naming, high complexity
+    r = []
+    for i in d:
+        if i['a'] > x and i['b'] < y:
+            t = i['a'] * 2
+            if t > 100:
+                r.append(t)
+            else:
+                r.append(t / 2)
+        elif i['c']:
+            r.append(i['d'])
+    return r
"""

# Clean Code Example (Baseline)
CLEAN_CODE_DIFF = """diff --git a/app/services/user_service.py b/app/services/user_service.py
new file mode 100644
index 0000000..mno678
--- /dev/null
+++ b/app/services/user_service.py
@@ -0,0 +1,20 @@
+from typing import List
+from app.models import User
+from app.repositories import UserRepository
+
+
+class UserService:
+    \"\"\"Service layer for user operations.\"\"\"
+    
+    def __init__(self, repository: UserRepository):
+        self.repository = repository
+    
+    def get_active_users(self) -> List[User]:
+        \"\"\"Retrieve all active users from the database.
+        
+        Returns:
+            List of active User objects
+        \"\"\"
+        return self.repository.find_by_status('active')
"""

# Multiple Issues Combined
MULTIPLE_ISSUES_DIFF = """diff --git a/app/payment.py b/app/payment.py
new file mode 100644
index 0000000..pqr901
--- /dev/null
+++ b/app/payment.py
@@ -0,0 +1,15 @@
+import requests
+
+def process_payment(user_id, amount, card):
+    # Multiple issues:
+    # 1. Hardcoded API key (security)
+    api_key = "sk-live-secret123456"
+    
+    # 2. SQL injection vulnerability (security)
+    query = f"INSERT INTO payments (user, amount) VALUES ({user_id}, {amount})"
+    db.execute(query)
+    
+    # 3. No error handling (reliability)
+    # 4. Synchronous blocking call in async context (performance)
+    response = requests.post("https://api.stripe.com/charge", 
+                            headers={"Authorization": f"Bearer {api_key}"})
"""

# Test fixture mapping
TEST_DIFFS = {
    "sql_injection": SQL_INJECTION_DIFF,
    "xss_vulnerability": XSS_VULNERABILITY_DIFF,
    "hardcoded_secrets": HARDCODED_SECRETS_DIFF,
    "n_plus_one": N_PLUS_ONE_QUERY_DIFF,
    "inefficient_algorithm": INEFFICIENT_ALGORITHM_DIFF,
    "poor_quality": POOR_QUALITY_DIFF,
    "clean_code": CLEAN_CODE_DIFF,
    "multiple_issues": MULTIPLE_ISSUES_DIFF,
}
