import mysql.connector
import time
from datetime import datetime

def truncate(n, decimals=0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def main():
  connection = "null"
  db_server = "null"
  write_performed = "null"

  try:
      cnx = mysql.connector.connect(user='root', password='root', host='rome', port=6446, connection_timeout=5, autocommit=True)

      cursor = cnx.cursor()

      # Check to which instances the queries are sent
      query = ("SELECT @@report_host, @@port")
      cursor.execute(query)

      for (host, port) in cursor:
        db_server = str(host) + ":" + str(port)

      # Write some data
      query = ("CREATE SCHEMA IF NOT EXISTS test")
      cursor.execute(query)

      query = ("CREATE TABLE IF NOT EXISTS test.data (a int primary key auto_increment, data longtext)")
      cursor.execute(query)

      start_time = time.time()
      query = ("INSERT INTO test.data values (default, repeat('x', 8))")
      cursor.execute(query)
      elapsed_time = time.time() - start_time
      elapsed_time_ms = truncate(elapsed_time * 1000, 3)

      cursor.close()
      cnx.close()
      connection = "OK"
      write_performed = str(elapsed_time_ms) + "ms"
  except mysql.connector.Error as e:
      connection = "ERROR: " + e.msg
  except Exception as e:
      print("Unexpected error:", e)

  return connection, db_server, write_performed

i=-1

while True:
    i+=1
    if i % 15 == 0:
      # Print header
      print("TIME\t\tCONNECTION\t\tDB SERVER\t\tWRITE PERFORMED")

    result = main()

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    print("{0}\t\t{1}\t\t{2}\t\t{3}".format(current_time, result[0], result[1], result[2]))
    time.sleep(1)
