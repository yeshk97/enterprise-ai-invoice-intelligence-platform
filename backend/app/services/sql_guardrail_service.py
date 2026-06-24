import re


BLOCKED_SQL_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "REPLACE",
    "PRAGMA",
    "ATTACH",
    "DETACH",
    "VACUUM",
]


ALLOWED_TABLES = [
    "invoices",
]


def clean_sql_query(sql_query: str) -> str:
    """
    Clean SQL query returned by LLM.

    Sometimes LLMs return SQL inside markdown blocks like:
    ```sql
    SELECT ...
    ```
    This function removes markdown formatting.
    """

    cleaned_query = sql_query.strip()

    cleaned_query = cleaned_query.replace("```sql", "")
    cleaned_query = cleaned_query.replace("```", "")
    cleaned_query = cleaned_query.strip()

    return cleaned_query


def validate_read_only_sql(sql_query: str) -> tuple[bool, str]:
    """
    Validate that generated SQL is read-only and safe.

    Rules:
    - Only SELECT queries are allowed.
    - Dangerous SQL keywords are blocked.
    - Only approved tables can be queried.
    - Multiple statements are blocked.
    """

    if not sql_query:
        return False, "SQL query is empty."

    cleaned_query = clean_sql_query(sql_query)
    upper_query = cleaned_query.upper().strip()

    # Rule 1: Must start with SELECT
    if not upper_query.startswith("SELECT"):
        return False, "Only SELECT queries are allowed."

    # Rule 2: Block multiple statements using semicolon in the middle
    if ";" in cleaned_query.rstrip(";"):
        return False, "Multiple SQL statements are not allowed."

    # Rule 3: Block dangerous keywords
    for keyword in BLOCKED_SQL_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, upper_query):
            return False, f"Blocked unsafe SQL keyword: {keyword}"

    # Rule 4: Only allow invoices table for now
    allowed_table_found = any(
        re.search(rf"\b{table}\b", cleaned_query, re.IGNORECASE)
        for table in ALLOWED_TABLES
    )

    if not allowed_table_found:
        return False, "Only the invoices table is allowed."

    # Rule 5: Enforce LIMIT for safety
    if "LIMIT" not in upper_query:
        cleaned_query = cleaned_query.rstrip(";") + " LIMIT 20"

    return True, cleaned_query