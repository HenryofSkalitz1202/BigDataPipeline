from pyspark.sql import SparkSession
import os

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("TPCH_Data_Ingestion") \
    .config("spark.driver.extraJavaOptions", "-Djava.net.preferIPv4Stack=true") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.demo", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.demo.type", "rest") \
    .config("spark.sql.catalog.demo.uri", "http://iceberg-catalog:8181") \
    .config("spark.sql.catalog.demo.io-impl", "org.apache.iceberg.aws.s3.S3FileIO") \
    .config("spark.sql.catalog.demo.s3.endpoint", "http://minio:9000") \
    .config("spark.sql.catalog.demo.s3.path-style-access", "true") \
    .config("spark.sql.catalog.demo.s3.access-key-id", "admin") \
    .config("spark.sql.catalog.demo.s3.secret-access-key", "password123") \
    .getOrCreate()

tables = ["customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier"]
base_path = "/home/iceberg/data/"

spark.sql("CREATE NAMESPACE IF NOT EXISTS iceberg.raw")

# Ingestion Loop for each table
for table in tables:
    print(f"\n=================== MEMPROSES TABEL: {table} ===================")
    file_path = f"{base_path}{table}.tbl"
    
    if os.path.exists(file_path):
        # Read file .tbl with pipe (|) delimiter
        df = spark.read \
            .option("delimiter", "|") \
            .option("inferSchema", "true") \
            .csv(file_path)
            
        # Write to Iceberg with default Parquet storage format
        df.writeTo(f"iceberg.raw.{table}") \
            .using("iceberg") \
            .createOrReplace()
            
        print(f"Status: Berhasil memuat data '{table}' ke Data Lakehouse (iceberg.raw.{table})")
    else:
        print(f"Peringatan: File {file_path} tidak ditemukan. Melewati proses...")

# Stop Spark Session
spark.stop()
print("\n[PROSES INGESTION SELESAI SEPENUHNYA]")