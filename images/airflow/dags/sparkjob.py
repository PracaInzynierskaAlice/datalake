from pyspark.sql import SparkSession
from pyspark.sql import functions
import os


path = "local://opt/spark/jars/"
jars = ["bundle-2.20.18.jar", "nessie-spark-extensions-3.4_2.12-0.65.1.jar", "url-connection-client-2.20.18.jar", "iceberg-spark-runtime-3.4_2.12-1.3.0.jar", "postgresql-42.6.0.jar"]

class_path = ":".join([path + jar for jar in jars])
log_dir = "/logs/spark-events"

spark = SparkSession.builder.master("k8s://https://kubernetes.default.svc.cluster.local:443") \
                            .appName("spark")\
                            .config("spark.executor.instances", 3)\
                            .config("spark.submit.deployMode", "client")\
                            .config("spark.driver.host", "spark-master")\
                            .config("spark.driver.port", "8002")\
                            .config("spark.driver.extraClassPath", class_path) \
                            .config("spark.blockManager.port", "8001")\
                            .config("spark.kubernetes.namespace", os.getenv("NAMESPACE"))\
                            .config("spark.kubernetes.container.image", "nowickib/spark-executor:latest")\
                            .config("spark.kubernetes.container.image.pullPolicy", "IfNotPresent")\
                            .config("spark.kubernetes.authenticate.driver.serviceAccountName", "spark")\
                            .config("spark.kubernetes.authenticate.executor.serviceAccountName", "spark")\
                            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions,org.projectnessie.spark.extensions.NessieSparkSessionExtensions")\
                            .config("spark.sql.catalog.nessie", "org.apache.iceberg.spark.SparkCatalog")\
                            .config("spark.sql.catalog.nessie.catalog-impl", "org.apache.iceberg.nessie.NessieCatalog")\
                            .config("spark.sql.catalog.nessie.uri", os.getenv("NESSIE_URL"))\
                            .config("spark.sql.catalog.nessie.authentication.type", "NONE")\
                            .config("spark.sql.catalog.nessie.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")\
                            .config("spark.sql.catalog.nessie.s3.endpoint", os.getenv("S3_ENDPOINT"))\
                            .config("spark.sql.catalog.nessie.warehouse", "s3a://alice-data-lake-dev")\
                            .config("spark.sql.catalog.nessie.s3.access-key-id", os.getenv("S3_ACCESS_KEY_ID"))\
                            .config("spark.sql.catalog.nessie.s3.secret-access-key", os.getenv("S3_SECRET_ACCESS_KEY"))\
                            .config("spark.sql.catalog.nessie.s3.path-style-access", "true") \
                            .config("spark.executorEnv.AWS_REGION", os.getenv("S3_REGION")) \
                            .config("spark.sql.defaultCatalog", "nessie")\
                            .config("spark.eventLog.enabled", "true")\
                            .config("spark.eventLog.dir", log_dir)\
                            .config("spark.history.fs.logDirectory", log_dir)\
                            .config("spark.sql.catalogImplementation", "in-memory")\
                            .getOrCreate()

url = "jdbc:postgresql://149.156.10.139:5432/mon_data"

table_name = "job_info"

df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:postgresql://149.156.10.139:5432/mon_data") \
    .option("driver", "org.postgresql.Driver") \
    .option("query", f"select * from {table_name} limit 100000") \
    .option("user", "mon_user") \
    .option("password", "cern") \
    .load()

df.show()
df.writeTo(f"nessie.{table_name}").create()