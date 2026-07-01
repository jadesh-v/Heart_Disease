from database import run_query

def setup():
    print("Setting up Fluxbase tables...")
    
    # Optional: drop if exists (Fluxbase SQL syntax relies on backend, likely PostgreSQL under the hood given "SERIAL")
    # For safety we just try to create.
    try:
        run_query("CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT, email TEXT UNIQUE, password_hash TEXT)")
        print("Created users table successfully.")
    except Exception as e:
        print("Error (table might already exist):", e)

if __name__ == "__main__":
    setup()
