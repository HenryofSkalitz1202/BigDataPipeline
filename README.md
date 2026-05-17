# BigDataPipeline
## Pre-Requisite
- Docker & Docker Compose
- WSL (Windows Subsystem for Linux) — Recommended for dbgen execution
- 20-25 GB of storage on host drive
- 6GB RAM minimal

## Setup
### A. Initialize Infra
1. Navigate to /Kode directory
```
cd /Kode
```

2. Activate Docker
```
docker-compose up -d
```

3. Access MinIO via `http://localhost:9001` with user `admin` and pass `password123` 
<br>

#### Common errors:
- Unexpected commit digest

    ```
    commit failed: unexpected commit digest... expected sha256:...
    ``` 
    It is most likely the result of insufficient space in the local which results in the download being interrupted, leaving a corrupted file fragment on containerd.
<br>
    To handle it, follow these debugging steps: <br>
    1. Clear cache build

        ```
        docker builder prune -a -f
        ```
    2. If the error still persists, do a hard purge via Docker Desktop GUI
        - Click the bug icon (troubleshoot) on the top right toolbar
        -  Choose clean/purge data
        - Checklist all options
        - Delete

    3. Do make sure that the host drive has sufficient storage (about 20GB)

- Port conflict
    ```
    Ports are not available: listen tcp 0.0.0.0:8181: bind: ... forbidden by its access permissions
    ```
    It is caused by the chosen port being on the port exclusion range set by WinNat on Windows Hyper -V on booting
<br>
<br>
To handle it, follow these debugging steps:
1. Find out the port exclusion range set by WinNat

    ```
    netsh int ipv4 show excludedportrange protocol=tcp
    ```
2. Modify the host port mapping on `docker-compose.yml` to a port outside the exclusion range (e.g, 9181)

### B. Generate Data
1. Navigate to folder `tpch-dbgen`
2. Run the command to generate 10GB of data

    ```
    ./dbgen -s 10
    ```

    If 10GB of data is too heavy for your laptop, you can modify the number after the `-s` flag to a smaller number (e.g, 0.1 or 1)
3. Make sure that .tbl files are generated into the data folder

### C. Ingestion
Transform the generated .tbl files into Parquet format in MinIO
1. Execute the ingestion script in the Spark container

    ```
    docker exec -it spark-iceberg spark-submit /home/iceberg/ingestion/loader.py
    ```
2. Verify the bucket `warehouse` in minIO contains Parquet files

### D. Data Mart
1. Navigate to the dbt_project directory

    ```
    cd Kode/dbt_project
    ```

2. Create the `profiles.yml` file based on the example given on `profiles.yml.example`. Default `user` and `password` works just fine, however you can modify it if necessary

3. Run the command

    ```
    dbt clean
    dbt run
    ```
#### Common errors:
- TrinoUserError(....Schema 'raw' does not exist")
<br>
    It is usually encountered after composing the containers back up.
    <br> 

    The solution is really simple you only need to make sure that you have run the ingestion script on the previous section before running `dbt clean` and `dbt run` 
<br> 
- TrinoQueryError(type=INSUFFICIENT_RESOURCES, name=EXCEEDED_LOCAL_MEMORY_LIMIT...)
<br>
    As the name suggests, it is a result of the query exceeding the per-node memory limit. <br>
    
    Logically, the solution would be to increase the memory limit in the config.properties
