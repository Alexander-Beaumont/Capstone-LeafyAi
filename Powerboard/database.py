def save_statuses_to_db(statuses):
    """
    Simulates inserting data into a database.
    Replace this with your actual database engine (e.g., SQLAlchemy, psycopg2, or PyMongo).
    """
    print("--- Database Ingestion Started ---")
    
    for status in statuses:
        # Example SQL concept:
        # INSERT INTO device_logs (device_id, is_on, timestamp) VALUES (...)
        
        print(f"Saved: {status['name']:<15} | Status: {str(status['is_on']):<5} | Time: {status['timestamp']}")
        
    print("--- Database Ingestion Complete ---\n")