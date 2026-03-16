from database.db_config import engine

connection = engine.connect()

print("Database connected successfully!")

connection.close()