"""
Challenge bank for ARI'Lab.

Each challenge is a dict with the following keys:
    id          — unique identifier used for database logging
    filename    — simulated filename shown in the IDE tab
    category    — one of five review categories
    difficulty  — JUNIOR / MID / SENIOR
    points      — how many points a full correct answer is worth
    code        — the buggy or poorly written Python snippet
    description — the question prompt shown to the reviewer
    keywords    — list of keyword lists; scoring requires matching
                  at least one keyword from each inner list
    ideal_comment  — what a senior developer would actually write
    explanation    — why the code is problematic in plain English

The keyword matching in scorer.py checks whether the user's answer
contains at least one term from each inner list. This means you can
describe the same problem in different ways and still score full marks.
For example, ["sql injection", "injection", "unsanitised"] means any
of those three terms counts as recognising the core security issue.
"""

CHALLENGES = [

    {
        "id": "logic_001",
        "filename": "calculate_discount.py",
        "category": "Logic Bug",
        "difficulty": "JUNIOR",
        "points": 10,
        "code": """\
def calculate_discount(price, discount_pct):
    discount = price * discount_pct
    final_price = price - discount
    return final_price

result = calculate_discount(100, 20)
print(result)  # expected: 80, actual: -1900
""",
        "description": "This function is supposed to apply a percentage "
                       "discount to a price. A discount of 20% on R100 "
                       "should return R80. What is wrong?",
        "keywords": [
            ["percent", "percentage", "divide", "100", "fraction", "0.20", "decimal"],
        ],
        "ideal_comment": "The discount_pct parameter is treated as a whole "
                         "number instead of a fraction. Multiply by "
                         "discount_pct / 100 to convert the percentage "
                         "correctly before applying it to the price.",
        "explanation": "When discount_pct is 20, the function computes "
                       "100 * 20 = 2000 as the discount and returns 100 - 2000 = -1900. "
                       "The fix is price * (discount_pct / 100).",
    },

    {
        "id": "logic_002",
        "filename": "find_max.py",
        "category": "Logic Bug",
        "difficulty": "JUNIOR",
        "points": 10,
        "code": """\
def find_max(numbers):
    max_val = 0
    for n in numbers:
        if n > max_val:
            max_val = n
    return max_val

print(find_max([-5, -3, -1]))  # returns 0, should return -1
""",
        "description": "This function should return the largest number "
                       "in the list. It fails when all numbers are negative. "
                       "What is the problem?",
        "keywords": [
            ["initialise", "initialize", "first", "negative", "assumption",
             "max_val = 0", "zero", "initial value"],
        ],
        "ideal_comment": "Initialising max_val to 0 assumes the list "
                         "contains at least one positive number. Use "
                         "max_val = numbers[0] or float('-inf') so the "
                         "function works correctly for all-negative inputs.",
        "explanation": "When all numbers are negative, none of them are "
                       "greater than 0, so max_val stays at 0 and the "
                       "function returns 0 instead of -1.",
    },

    {
        "id": "logic_003",
        "filename": "paginate.py",
        "category": "Logic Bug",
        "difficulty": "MID",
        "points": 20,
        "code": """\
def get_page(items, page, page_size=10):
    start = page * page_size
    end = start + page_size
    return items[start:end]

# Page 1 should return items 0-9
# Page 2 should return items 10-19
results = get_page(items, page=1)
""",
        "description": "This pagination function is supposed to return "
                       "the correct slice of items for a given page number. "
                       "Page 1 should return the first 10 items. "
                       "What is wrong with the indexing?",
        "keywords": [
            ["zero", "0", "one-based", "off by one", "index", "page 1",
             "first page", "offset"],
        ],
        "ideal_comment": "The page parameter appears to be one-based from "
                         "the caller's perspective but the formula treats it "
                         "as zero-based. Page 1 computes start=10 and skips "
                         "the first 10 items. Either document that pages are "
                         "zero-indexed or subtract 1: start = (page - 1) * page_size.",
        "explanation": "With page=1 and page_size=10, start = 1 * 10 = 10. "
                       "The first page is skipped entirely. The caller likely "
                       "expects page 1 to be the first page.",
    },

    {
        "id": "security_001",
        "filename": "auth_handler.py",
        "category": "Security",
        "difficulty": "MID",
        "points": 20,
        "code": """\
import sqlite3

def get_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()

user = get_user("admin' OR '1'='1")
""",
        "description": "This function retrieves a user from the database "
                       "by username. There is a critical security vulnerability. "
                       "What is it and how would you fix it?",
        "keywords": [
            ["sql injection", "injection", "unsanitised", "sanitise",
             "parameterised", "parameterized", "f-string", "user input"],
        ],
        "ideal_comment": "This is a classic SQL injection vulnerability. "
                         "The username is interpolated directly into the query "
                         "string. Use a parameterised query instead: "
                         "cursor.execute('SELECT * FROM users WHERE username = ?', "
                         "(username,))",
        "explanation": "An attacker can pass a crafted username like "
                       "admin' OR '1'='1 to bypass authentication. "
                       "Parameterised queries prevent this by treating "
                       "user input as data, not as SQL.",
    },

    {
        "id": "security_002",
        "filename": "config.py",
        "category": "Security",
        "difficulty": "JUNIOR",
        "points": 10,
        "code": """\
# Application configuration
DATABASE_URL = "postgresql://admin:SuperSecret123@prod-db.company.com/appdb"
API_KEY      = "sk-live-a8f3k2m9p4q7r1s6t0"
SECRET_KEY   = "my-flask-secret-key-do-not-share"

DEBUG = True
ALLOWED_HOSTS = ["*"]
""",
        "description": "Review this configuration file. "
                       "What are the security problems here?",
        "keywords": [
            ["hardcoded", "hard-coded", "credentials", "secret",
             "environment", "env", "password", "api key", "committed",
             "version control", "git"],
        ],
        "ideal_comment": "Credentials, API keys, and secret keys must never "
                         "be hardcoded in source files. These will be committed "
                         "to version control and exposed to anyone with repository "
                         "access. Move all secrets to environment variables and "
                         "load them with os.environ. Also: DEBUG=True and "
                         "ALLOWED_HOSTS=['*'] are dangerous in production.",
        "explanation": "Hardcoded secrets in source code are one of the most "
                       "common and serious security mistakes. Once committed "
                       "to git they are effectively public, even if the repo "
                       "is later made private.",
    },

    {
        "id": "security_003",
        "filename": "file_upload.py",
        "category": "Security",
        "difficulty": "SENIOR",
        "points": 30,
        "code": """\
import os

def save_upload(filename, content):
    upload_dir = "/var/www/uploads"
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, 'wb') as f:
        f.write(content)
    return file_path
""",
        "description": "This function saves an uploaded file to disk. "
                       "There are two distinct security vulnerabilities. "
                       "Can you identify both?",
        "keywords": [
            ["path traversal", "directory traversal", "../", "filename",
             "sanitise", "validate", "basename"],
            ["extension", "file type", "executable", "script", "php",
             "validate type", "whitelist"],
        ],
        "ideal_comment": "Two vulnerabilities: (1) Path traversal — a filename "
                         "like ../../etc/passwd would write outside the upload "
                         "directory. Use os.path.basename(filename) to strip "
                         "directory components. (2) No file type validation — "
                         "an attacker could upload a .php or .py script and "
                         "execute it. Whitelist allowed extensions.",
        "explanation": "Path traversal lets attackers write files anywhere on "
                       "the filesystem. Without extension validation, uploaded "
                       "scripts can be executed by the web server.",
    },

    {
        "id": "performance_001",
        "filename": "find_duplicates.py",
        "category": "Performance",
        "difficulty": "MID",
        "points": 20,
        "code": """\
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                if items[i] not in duplicates:
                    duplicates.append(items[i])
    return duplicates
""",
        "description": "This function finds duplicate values in a list. "
                       "It works correctly but has a serious performance problem. "
                       "What is it and how would you fix it?",
        "keywords": [
            ["o(n", "quadratic", "nested loop", "n squared", "n^2",
             "set", "seen", "hash", "linear"],
        ],
        "ideal_comment": "This is O(n²) due to the nested loop. For a list "
                         "of 10,000 items that is 100 million comparisons. "
                         "Use a set to track seen items: iterate once, add "
                         "to seen, if already in seen add to duplicates. "
                         "That reduces it to O(n).",
        "explanation": "Nested loops over the same list produce quadratic "
                       "time complexity. A set lookup is O(1) so a single "
                       "pass with a seen set gives O(n) performance.",
    },

    {
        "id": "performance_002",
        "filename": "report_generator.py",
        "category": "Performance",
        "difficulty": "SENIOR",
        "points": 30,
        "code": """\
def generate_report(user_ids):
    report = []
    for user_id in user_ids:
        user  = db.query(f"SELECT * FROM users WHERE id = {user_id}")
        orders = db.query(f"SELECT * FROM orders WHERE user_id = {user_id}")
        report.append({"user": user, "orders": orders})
    return report
""",
        "description": "This function generates a report for a list of users. "
                       "There is a critical performance problem that gets worse "
                       "as the list grows. What is it?",
        "keywords": [
            ["n+1", "n plus 1", "loop", "database call", "query", "batch",
             "single query", "join", "in clause", "bulk"],
        ],
        "ideal_comment": "This is the N+1 query problem. For 1,000 users "
                         "this executes 2,001 database queries. Fetch all "
                         "users and orders in two bulk queries using WHERE id "
                         "IN (...) and join them in Python, or use a single "
                         "JOIN query.",
        "explanation": "One query to get user IDs plus two queries per user "
                       "equals 2N+1 database round trips. Database latency "
                       "compounds rapidly at scale.",
    },

    {
        "id": "performance_003",
        "filename": "string_builder.py",
        "category": "Performance",
        "difficulty": "MID",
        "points": 20,
        "code": """\
def build_csv(rows):
    result = ""
    for row in rows:
        result += ",".join(str(v) for v in row) + "\\n"
    return result
""",
        "description": "This function builds a CSV string from a list of rows. "
                       "It works but has a performance issue for large datasets. "
                       "What is it?",
        "keywords": [
            ["string concatenation", "immutable", "new string", "join",
             "list", "append", "o(n", "quadratic", "memory"],
        ],
        "ideal_comment": "String concatenation in a loop creates a new string "
                         "object on every iteration because strings are immutable "
                         "in Python. For large datasets this is O(n²) in memory "
                         "and time. Collect lines in a list and join at the end: "
                         "return '\\n'.join(','.join(str(v) for v in row) for row in rows)",
        "explanation": "Each += creates a new string by copying the existing "
                       "content plus the new part. With 10,000 rows that means "
                       "10,000 copy operations of increasing size.",
    },

    {
        "id": "smell_001",
        "filename": "user_service.py",
        "category": "Code Smell",
        "difficulty": "JUNIOR",
        "points": 10,
        "code": """\
def process(u, t, d, f, s):
    if t == 1:
        u.balance += d
        u.last = f
        return True
    elif t == 2:
        if u.balance >= d:
            u.balance -= d
            u.last = f
            return True
        return False
    elif t == 3:
        u.status = s
        return True
""",
        "description": "This function manages user account operations. "
                       "What are the code quality issues that would make this "
                       "hard to maintain in a real codebase?",
        "keywords": [
            ["name", "variable", "meaningful", "descriptive",
             "readable", "magic number", "t == 1", "t == 2"],
        ],
        "ideal_comment": "Single-letter parameter names make this completely "
                         "unreadable. What is u, t, d, f, s? The magic numbers "
                         "1, 2, 3 for transaction types should be named constants "
                         "or an enum. This function also does three different "
                         "things — consider splitting into deposit(), withdraw(), "
                         "and update_status().",
        "explanation": "Code is read far more often than it is written. "
                       "Unreadable names and magic numbers make maintenance "
                       "error-prone and onboarding new developers nearly impossible.",
    },

    {
        "id": "smell_002",
        "filename": "validator.py",
        "category": "Code Smell",
        "difficulty": "MID",
        "points": 20,
        "code": """\
def validate_user_input(name, email, age, phone,
                        address, city, country, zip_code,
                        account_type, referral_code):
    if not name:
        return False
    if not email or '@' not in email:
        return False
    if age < 18 or age > 120:
        return False
    # ... 50 more lines of validation
    return True
""",
        "description": "This validation function receives 10 parameters "
                       "and continues for 50 more lines. What design problems "
                       "do you see?",
        "keywords": [
            ["parameter", "argument", "too many", "object", "dict",
             "dataclass", "single responsibility", "long", "split"],
        ],
        "ideal_comment": "Ten parameters is a strong signal that the function "
                         "is doing too much and the caller has no way to know "
                         "what order they go in without constantly checking "
                         "the signature. Accept a UserInput dataclass or dict "
                         "instead. Also consider splitting into separate "
                         "validators per concern.",
        "explanation": "Functions with many parameters are hard to call "
                       "correctly, hard to test, and hard to extend. "
                       "Grouping related parameters into an object is "
                       "a standard refactoring.",
    },

    {
        "id": "smell_003",
        "filename": "calculator.py",
        "category": "Code Smell",
        "difficulty": "JUNIOR",
        "points": 10,
        "code": """\
def calculate(a, b, operation):
    if operation == "add":
        result = a + b
    if operation == "subtract":
        result = a - b
    if operation == "multiply":
        result = a * b
    if operation == "divide":
        result = a / b
    return result
""",
        "description": "This function performs basic arithmetic. "
                       "There are two distinct issues — one is a logic bug "
                       "and one is a code quality issue. What are they?",
        "keywords": [
            ["elif", "else if", "if else", "falls through", "redundant",
             "all conditions", "evaluated"],
            ["divide by zero", "division", "zero", "error", "validate"],
        ],
        "ideal_comment": "Two issues: (1) All four if statements are evaluated "
                         "every time instead of using elif — this causes "
                         "incorrect results if the first branch modifies result. "
                         "Use elif. (2) There is no check for division by zero "
                         "which will raise an unhandled ZeroDivisionError.",
        "explanation": "Using if instead of elif means every condition is "
                       "checked even after one matches. The missing zero check "
                       "is a reliability issue that would crash the program.",
    },

    {
        "id": "exception_001",
        "filename": "data_parser.py",
        "category": "Exception Handling",
        "difficulty": "JUNIOR",
        "points": 10,
        "code": """\
def parse_config(filepath):
    try:
        with open(filepath) as f:
            data = f.read()
        return data
    except:
        pass
""",
        "description": "This function reads a configuration file. "
                       "What is wrong with the exception handling?",
        "keywords": [
            ["bare except", "swallow", "silent", "specific", "exception type",
             "pass", "hide", "catch all", "broad"],
        ],
        "ideal_comment": "Bare except with pass silently swallows all errors "
                         "including KeyboardInterrupt and SystemExit. The caller "
                         "gets None back with no indication that anything went "
                         "wrong. Catch specific exceptions like FileNotFoundError "
                         "and PermissionError, log the error, and either re-raise "
                         "or return a meaningful error signal.",
        "explanation": "Silent failures are one of the hardest bugs to diagnose "
                       "in production. If the config file is missing or corrupt "
                       "the application silently continues with no data.",
    },

    {
        "id": "exception_002",
        "filename": "payment_processor.py",
        "category": "Exception Handling",
        "difficulty": "SENIOR",
        "points": 30,
        "code": """\
def process_payment(amount, card_token):
    conn = get_db_connection()
    try:
        charge = payment_api.charge(card_token, amount)
        conn.execute("INSERT INTO payments VALUES (?)", (charge.id,))
        conn.commit()
    except PaymentError as e:
        log.error(e)
""",
        "description": "This payment processing function has a resource "
                       "management problem and an incomplete error recovery "
                       "strategy. What are they?",
        "keywords": [
            ["finally", "close", "connection", "resource", "leak",
             "context manager", "with"],
            ["rollback", "commit", "transaction", "partial", "inconsistent",
             "state", "recovery"],
        ],
        "ideal_comment": "Two issues: (1) The database connection is never "
                         "closed if an exception occurs — use a with statement "
                         "or a finally block. (2) If the payment succeeds but "
                         "the database insert fails, the charge is real but "
                         "not recorded — the except block should rollback the "
                         "transaction and either retry or reverse the charge.",
        "explanation": "Resource leaks degrade performance over time. "
                       "The partial failure scenario — charge processed but "
                       "not recorded — is a data consistency problem that "
                       "is very difficult to reconcile after the fact.",
    },

    {
        "id": "exception_003",
        "filename": "api_client.py",
        "category": "Exception Handling",
        "difficulty": "MID",
        "points": 20,
        "code": """\
import requests

def fetch_user(user_id):
    try:
        response = requests.get(f"/api/users/{user_id}")
        data = response.json()
        return data["user"]
    except Exception as e:
        return None
""",
        "description": "This function fetches a user from an API. "
                       "What are the exception handling problems here?",
        "keywords": [
            ["status code", "http", "200", "error", "response",
             "raise_for_status", "4xx", "5xx"],
            ["keyerror", "key", "missing", "user", "response structure",
             "validate"],
        ],
        "ideal_comment": "Two issues: (1) The HTTP response status is never "
                         "checked — a 404 or 500 response will still call "
                         ".json() and potentially return bad data. Call "
                         "response.raise_for_status() before parsing. "
                         "(2) data['user'] will raise KeyError if the API "
                         "response structure changes. Use data.get('user') "
                         "and handle the None case explicitly.",
        "explanation": "HTTP errors don't raise exceptions by default in "
                       "requests — you must check the status code. Unguarded "
                       "dict access will crash on unexpected API responses.",
    },
]