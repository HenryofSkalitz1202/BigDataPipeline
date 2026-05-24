import duckdb
import time

MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = 'password123'
MINIO_BUCKET = 'warehouse'

csv_customer = "../data/raw_tbl/customer.tbl"
csv_orders = "../data/raw_tbl/orders.tbl"
csv_lineitem = "../data/raw_tbl/lineitem.tbl"

con = duckdb.connect()

con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")
con.execute(f"SET s3_endpoint='{MINIO_ENDPOINT}';")
con.execute(f"SET s3_access_key_id='{MINIO_ACCESS_KEY}';")
con.execute(f"SET s3_secret_access_key='{MINIO_SECRET_KEY}';")
con.execute("SET s3_use_ssl=false;")
con.execute("SET s3_url_style='path';")

customer_names = ['c_custkey', 'c_name', 'c_address', 'c_nationkey', 'c_phone', 'c_acctbal', 'c_mktsegment', 'c_comment', 'dummy']
orders_names = ['o_orderkey', 'o_custkey', 'o_orderstatus', 'o_totalprice', 'o_orderdate', 'o_orderpriority', 'o_clerk', 'o_shippriority', 'o_comment', 'dummy']
lineitem_names = ['l_orderkey', 'l_partkey', 'l_suppkey', 'l_linenumber', 'l_quantity', 'l_extendedprice', 'l_discount', 'l_tax', 'l_returnflag', 'l_linestatus', 'l_shipdate', 'l_commitdate', 'l_receiptdate', 'l_shipinstruct', 'l_shipmode', 'l_comment', 'dummy']

print("=" * 50)
print("       THREE-LAYER PERFORMANCE BENCHMARK       ")
print("=" * 50 + "\n")

print("Executing Query on Layer 1: Raw CSV Files (Bronze)...")
start = time.time()
csv_query = f"""
    SELECT 
        c.c_custkey AS customer_key,
        c.c_name AS customer_name,
        count(distinct o.o_orderkey) AS total_orders,
        sum(l.l_extendedprice * (1 - l.l_discount)) AS total_revenue
    FROM read_csv('{csv_customer}', sep='|', header=False, names={customer_names}) c
    JOIN read_csv('{csv_orders}', sep='|', header=False, names={orders_names}) o ON c.c_custkey = o.o_custkey
    JOIN read_csv('{csv_lineitem}', sep='|', header=False, names={lineitem_names}) l ON o.o_orderkey = l.l_orderkey
    WHERE c.c_custkey < 30000
    GROUP BY 1, 2
"""
con.execute(csv_query).fetchall()
t1 = time.time() - start
print(f"-> Layer 1 Time: {t1:.2f} seconds\n")


print("Executing Query on Layer 2: Raw Iceberg/Parquet Tables (Silver)...")
start = time.time()
lakehouse_query = f"""
    SELECT 
        c._c0 AS customer_key,
        c._c1 AS customer_name,
        count(distinct o._c0) AS total_orders,
        sum(l._c5 * (1 - l._c6)) AS total_revenue
    FROM read_parquet('s3://{MINIO_BUCKET}/raw/customer/data/*.parquet') c
    JOIN read_parquet('s3://{MINIO_BUCKET}/raw/orders/data/*.parquet') o ON c._c0 = o._c1
    JOIN read_parquet('s3://{MINIO_BUCKET}/raw/lineitem/data/**.parquet') l ON o._c0 = l._c0
    WHERE c._c0 < 30000
    GROUP BY 1, 2
"""
con.execute(lakehouse_query).fetchall()
t2 = time.time() - start
print(f"-> Layer 2 Time: {t2:.2f} seconds\n")


print("Executing Query on Layer 3: Data Mart Gold Table (Pre-calculated)...")
start = time.time()
mart_query = f"""
    SELECT 
        customer_key,
        customer_name,
        total_orders,
        total_revenue
    FROM read_parquet('s3://{MINIO_BUCKET}/mart/mart_customer_revenue-*/data/**.parquet')
    WHERE customer_key < 30000
"""
con.execute(mart_query).fetchall()
t3 = time.time() - start
print(f"-> Layer 3 Time: {t3:.2f} seconds\n")


print("=" * 50)
print("                BENCHMARK RESULTS               ")
print("=" * 50)
print(f"Layer 1 (Raw CSV)        : {t1:.2f}s")
print(f"Layer 2 (Lakehouse Tables): {t2:.2f}s  ({t1/t2:.1f}x faster than CSV)")
print(f"Layer 3 (Data Mart Gold) : {t3:.2f}s  ({t2/t3:.1f}x faster than Lakehouse)")
print("-" * 50)
print(f"TOTAL SPEEDUP (CSV vs Mart): {t1/t3:.1f}x FASTER!")
print("=" * 50)