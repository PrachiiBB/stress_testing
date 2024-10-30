import os
import psutil
import time
import requests
import multiprocessing
import mysql.connector
import logging
import threading

# Set up logging
logging.basicConfig(filename='stress_test.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

THRESHOLD = 80  # Percentage threshold for resource usage

# MySQL database connection details
MYSQL_CONFIG = {
    'user': 'exporter',  # replace with your MySQL username
    'password': 'password',  # replace with your MySQL password
    'host': 'localhost',  # or your MySQL server IP
    'database': 'newdb'  # replace with your test database
}

# Stress increase functions
def increase_memory_stress():
    memory_list = []
    process = psutil.Process(os.getpid())
    while process.memory_percent() < THRESHOLD:
        memory_list.append(' ' * 1024 * 1024)  # 1 MB per iteration
        logging.info(f"Memory Usage: {process.memory_percent()}%")  # Log usage during stress
    logging.info("Memory stress test reached target usage.")

def increase_disk_stress():
    with open("stress_test_file", "wb") as f:
        while psutil.disk_usage('/').percent < THRESHOLD:
            f.write(b'0' * 1024 * 1024 * 10)  # Write 10 MB at a time
            logging.info(f"Disk Usage: {psutil.disk_usage('/').percent}%")  # Log usage during stress
    logging.info("Disk stress test reached target usage.")
    os.remove("stress_test_file")

def increase_network_stress():
    url = "https://www.google.com/"  # Replace with a valid URL
    while (psutil.net_io_counters().bytes_recv * 100 / psutil.virtual_memory().total) < THRESHOLD:  # Rough estimate for % usage
        requests.get(url)
        logging.info(f"Network usage estimated: {(psutil.net_io_counters().bytes_recv * 100 / psutil.virtual_memory().total):.2f}%")  # Log usage during stress
    logging.info("Network stress test reached target usage.")

def increase_cpu_stress():
    def stress():
        while True:
            pass  # Infinite loop to max out CPU

    processes = [multiprocessing.Process(target=stress) for _ in range(multiprocessing.cpu_count())]
    for p in processes:
        p.start()
        logging.info(f"CPU Usage: {psutil.cpu_percent(interval=1)}%")
    time.sleep(5)  # Run for a few seconds to increase CPU usage
    for p in processes:
        logging.info(f"CPU Usage: {psutil.cpu_percent(interval=1)}%")  # Log usage while stressing
        p.terminate()
    logging.info("CPU stress test completed.")

def execute_stress_queries():
    try:
        # Establish MySQL connection
        db_connection = mysql.connector.connect(
            host="localhost",
            user="exporter",
            password="password",
            database="newdb"
        )

        cursor = db_connection.cursor()

        # Run a high volume of complex queries
        for _ in range(10000):  # Increase the number of iterations significantly
            # This query does a join with itself which is CPU intensive
            cursor.execute("""
            SELECT a.id, b.value
            FROM sbtest1 a
            JOIN sbtest1 b ON a.id = b.id;
            """)
            cursor.fetchall()  # Clear the result to avoid "Unread result" error

    except mysql.connector.Error as e:
        logging.error(f"MySQL Error: {e}")
    finally:
        # Close the cursor and database connection
        if 'cursor' in locals():
            cursor.close()
        db_connection.close()

def increase_mysql_stress():
    try:
        # Establish MySQL connection
        db_connection = mysql.connector.connect(
            host="localhost",
            user="exporter",
            password="password",
            database="newdb"
        )

        cursor = db_connection.cursor()

        # Create the table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sbtest1 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            value VARCHAR(255)
        );
        """)

        # Insert sample values if the table is empty
        cursor.execute("SELECT COUNT(*) FROM sbtest1;")
        count = cursor.fetchone()[0]
        if count == 0:
            for i in range(100000):  # Increase number of records significantly
                cursor.execute("INSERT INTO sbtest1 (value) VALUES (%s);", (f'value_{i}',))
            db_connection.commit()  # Commit the inserts

        # Create multiple threads to run the stress queries concurrently
        threads = []
        for _ in range(5):  # Number of threads
            thread = threading.Thread(target=execute_stress_queries)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        logging.info("MySQL stress test executed successfully.")

    except mysql.connector.Error as e:
        logging.error(f"MySQL Error: {e}")
    finally:
        # Cleanup: Drop the table
        if 'cursor' in locals():
            cursor.execute("DROP TABLE IF EXISTS sbtest1;")
            cursor.close()
        # Close the database connection
        db_connection.close()

# Monitoring functions
def memory_stress_test():
    usage = psutil.virtual_memory().percent
    logging.info(f"Memory Usage: {usage}%")
    if usage < THRESHOLD:
        logging.info("Increasing memory stress to exceed threshold.")
        increase_memory_stress()
    else:
        logging.info("Memory usage exceeded threshold!")

def disk_stress_test():
    usage = psutil.disk_usage('/').percent
    logging.info(f"Disk Usage: {usage}%")
    if usage < THRESHOLD:
        logging.info("Increasing disk stress to exceed threshold.")
        increase_disk_stress()
    else:
        logging.info("Disk usage exceeded threshold!")

def network_stress_test():
    logging.info("Increasing network stress to attempt to reach threshold.")
    increase_network_stress()

def cpu_stress_test():
    usage = psutil.cpu_percent(interval=1)
    logging.info(f"Initial CPU Usage: {usage}%")
    if usage < THRESHOLD:
        logging.info("Increasing CPU stress to exceed threshold.")
        increase_cpu_stress()
    else:
        logging.info("CPU usage exceeded threshold!")

def mysql_stress_test():
    exporter_url = "http://192.168.0.104:9104/metrics"  # Adjust IP/port if needed
    thresholds = {
        "process_cpu_seconds_total": 1.0  # Set a threshold for CPU usage in seconds
    }

    try:
        response = requests.get(exporter_url)
        response.raise_for_status()

        metrics = {}
        for line in response.text.splitlines():
            if line.startswith("#"):
                continue
            if "process_cpu_seconds_total" in line:
                try:
                    metrics["process_cpu_seconds_total"] = float(line.split()[-1])
                except ValueError:
                    logging.warning(f"Could not convert value to float: {line}")

        # Check CPU time threshold
        if "process_cpu_seconds_total" in metrics:
            logging.info(f"process_cpu_seconds_total: {metrics['process_cpu_seconds_total']}")
            if metrics["process_cpu_seconds_total"] > thresholds["process_cpu_seconds_total"]:
                logging.error(f"CPU usage exceeds threshold - {metrics['process_cpu_seconds_total']} seconds (Threshold: {thresholds['process_cpu_seconds_total']} seconds)")
            else:
                logging.info("CPU usage is within limits.")

        # Now stress MySQL
        increase_mysql_stress()

    except requests.RequestException as e:
        logging.error(f"Failed to retrieve metrics from mysqld_exporter: {e}")

def main():
    while True:
        print("\nSelect an option:")
        print("1. Memory Stress Testing")
        print("2. Disk Stress Testing")
        print("3. Network Stress Testing")
        print("4. CPU Stress Testing")
        print("5. MySQL Stress Testing")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            memory_stress_test()
        elif choice == '2':
            disk_stress_test()
        elif choice == '3':
            network_stress_test()
        elif choice == '4':
            cpu_stress_test()
        elif choice == '5':
            mysql_stress_test()
        elif choice == '6':
            logging.info("Exiting")
            print("Exit")
            break
        else:
            logging.warning("Invalid option selected.")
            print("Enter a valid option")

if __name__ == "__main__":
    main()
