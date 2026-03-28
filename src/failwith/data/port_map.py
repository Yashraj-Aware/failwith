"""
Mapping of common ports to service names and start commands.
"""

from __future__ import annotations

from typing import Optional


# port -> (service_name, systemctl_name, docker_name, brew_name)
PORT_MAP: dict = {
    # Databases
    5432: ("PostgreSQL", "postgresql", "postgres", "postgresql"),
    3306: ("MySQL", "mysql", "mysql", "mysql"),
    3307: ("MySQL (alt)", "mysql", "mysql", "mysql"),
    27017: ("MongoDB", "mongod", "mongo", "mongodb-community"),
    6379: ("Redis", "redis", "redis", "redis"),
    6380: ("Redis (alt/TLS)", "redis", "redis", "redis"),
    9200: ("Elasticsearch", "elasticsearch", "elasticsearch", "elasticsearch"),
    9300: ("Elasticsearch (transport)", "elasticsearch", "elasticsearch", "elasticsearch"),
    7474: ("Neo4j", "neo4j", "neo4j", "neo4j"),
    8529: ("ArangoDB", "arangodb3", "arangodb", "arangodb"),
    5984: ("CouchDB", "couchdb", "couchdb", "couchdb"),
    26257: ("CockroachDB", "cockroach", "cockroachdb", None),
    9042: ("Cassandra", "cassandra", "cassandra", "cassandra"),
    11211: ("Memcached", "memcached", "memcached", "memcached"),

    # Message Queues
    5672: ("RabbitMQ", "rabbitmq-server", "rabbitmq", "rabbitmq"),
    15672: ("RabbitMQ Management", "rabbitmq-server", "rabbitmq", "rabbitmq"),
    9092: ("Kafka", "kafka", "kafka", None),
    4222: ("NATS", "nats-server", "nats", "nats-server"),

    # Web / App Servers
    80: ("HTTP Server", "nginx", "nginx", "nginx"),
    443: ("HTTPS Server", "nginx", "nginx", "nginx"),
    8080: ("HTTP Proxy / App Server", None, None, None),
    8000: ("Django / Uvicorn / Dev Server", None, None, None),
    8888: ("Jupyter Notebook", None, None, None),
    3000: ("Node.js / React Dev Server", None, None, None),
    5000: ("Flask Dev Server", None, None, None),
    5173: ("Vite Dev Server", None, None, None),
    4200: ("Angular Dev Server", None, None, None),

    # Infrastructure
    2181: ("Zookeeper", "zookeeper", "zookeeper", None),
    8500: ("Consul", "consul", "consul", "consul"),
    2379: ("etcd", "etcd", "etcd", "etcd"),
    9090: ("Prometheus", "prometheus", "prometheus", "prometheus"),
    3100: ("Grafana Loki", "loki", "loki", None),
    9411: ("Zipkin", "zipkin", "zipkin", None),
    14268: ("Jaeger", "jaeger", "jaeger", None),

    # Mail
    25: ("SMTP", "postfix", "postfix", None),
    587: ("SMTP (submission)", "postfix", "postfix", None),
    993: ("IMAP (SSL)", "dovecot", "dovecot", None),
    1025: ("MailHog / Dev SMTP", None, "mailhog", None),

    # Storage
    9000: ("MinIO / SonarQube", "minio", "minio", "minio"),

    # SSH
    22: ("SSH", "sshd", None, None),
}


def identify_service(port: int) -> Optional[dict]:
    """
    Identify a service by port number.

    Returns dict with service info or None if unknown.
    """
    if port not in PORT_MAP:
        return None

    name, systemctl, docker, brew = PORT_MAP[port]
    return {
        "name": name,
        "port": port,
        "systemctl": systemctl,
        "docker": docker,
        "brew": brew,
    }
