# BigDataPipeline

## Setup
### Initialize Infra
1. Navigate to /Kode directory
```
cd /Kode
```

2. Activate Docker
```
docker-compose up -d
```

3. Access MinIO via `http://localhost:9001` with user `admin` and pass `password123`

### Generate Data
1. Navigate to folder `tpch-dbgen`
2. Run the command to generate 10GB of data
```
./dbgen -s 10
```
3. Make sure that .tbl files are generated into the data folder