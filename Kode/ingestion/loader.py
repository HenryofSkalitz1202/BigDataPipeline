from pyspark.sql import SparkSession
import os
import sys

print("\n=======================================================")
print("=== STARTING INGESTION PIPELINE (PATCHED DEMO S3) ===")
print("=======================================================\n")

base_path = "/home/iceberg/data/"
tables = ["customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier"]

# Validasi File
for table in tables:
    if not os.path.exists(f"{base_path}{table}.tbl"):
        print(f"[FATAL ERROR] File {table}.tbl tidak ditemukan di {base_path}")
        sys.exit(1)

# Inisialisasi session dengan menyuntikkan override S3 ke katalog 'demo'
spark = SparkSession.builder \
    .appName("TPCH_Data_Ingestion") \
    .config("spark.driver.extraJavaOptions", "-Djava.net.preferIPv4Stack=true") \
    .config("spark.sql.catalog.demo.s3.endpoint", "http://minio:9000") \
    .config("spark.sql.catalog.demo.s3.path-style-access", "true") \
    .config("spark.sql.catalog.demo.s3.access-key-id", "admin") \
    .config("spark.sql.catalog.demo.s3.secret-access-key", "password123") \
    .getOrCreate()

print("✔ Spark Session berhasil terhubung ke ekosistem 'rest'.")
print("Mendaftarkan namespace 'raw'...")
spark.sql("CREATE NAMESPACE IF NOT EXISTS demo.raw")

for table in tables:
    print(f"-> Mengonversi & Memuat tabel: {table} ...")
    file_path = f"{base_path}{table}.tbl"
    
    df = spark.read \
        .option("delimiter", "|") \
        .option("inferSchema", "true") \
        .csv(file_path)
        
    df.writeTo(f"demo.raw.{table}") \
        .using("iceberg") \
        .createOrReplace()
        
    print(f"✔ Tabel '{table}' sukses tersimpan di Lakehouse.")

spark.stop()
print("\n[PROSES INGESTION SELESAI SEPENUHNYA]")