import pypyodbc as odbc  # pip install pypyodbc

# Properly escape the backslash or use a raw string
DRIVER_NAME = 'SQL SERVER'
SERVER_NAME = r'abhik'  # Use raw string to avoid escape sequence issues
DATABASE_NAME = 'JJ'

# Connection string with corrected format
connection_string = f"""
DRIVER={{SQL Server}};
SERVER={SERVER_NAME};
DATABASE={DATABASE_NAME};
Trusted_Connection=yes;
"""

# Establishing connection
try:
    conn = odbc.connect(connection_string)
    print("Connection successful:", conn)
except odbc.Error as e:
    print("Error occurred:", e)
