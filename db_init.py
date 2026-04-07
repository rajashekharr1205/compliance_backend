import pymysql
from config import Config

def init_db():
    print("Connecting to MySQL...")
    try:
        # Connect without database first to create it
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        
        with connection.cursor() as cursor:
            # Create Database
            print(f"Creating database {Config.MYSQL_DB} if it doesn't exist...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
            connection.select_db(Config.MYSQL_DB)
            
            # Create Users Table
            print("Creating 'users' table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    designation VARCHAR(255),
                    registration_id VARCHAR(255),
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create Reports Table
            print("Creating 'reports' table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    report_name VARCHAR(255),
                    transcript TEXT,
                    score INT,
                    verdict VARCHAR(50),
                    duration VARCHAR(20),
                    recording_url VARCHAR(255),
                    patient_info TEXT,
                    folder_name VARCHAR(100) DEFAULT 'Audits',
                    timestamp VARCHAR(100),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create OTP Codes Table
            print("Creating 'otp_codes' table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS otp_codes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    otp VARCHAR(6) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
        connection.commit()
        print("Database initialization successful!")
        connection.close()
        return True
    except Exception as e:
        print(f"\n[ERROR] Database initialization failed: {e}")
        print("\nPlease ensure:")
        print("1. MySQL is running (XAMPP/WAMP/MySQL Service)")
        print(f"2. Your credentials in config.py are correct (User: {Config.MYSQL_USER})")
        return False

if __name__ == "__main__":
    init_db()
