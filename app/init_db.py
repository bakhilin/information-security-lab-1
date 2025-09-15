from database import init_db, insert_initial_data

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    insert_initial_data()
    print("Database initialized successfully!")
