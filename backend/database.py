from neo4j import GraphDatabase
from config import settings

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
    return _driver


def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None


def get_session():
    return get_driver().session(database=settings.NEO4J_DATABASE)


def run_query(query: str, parameters: dict = None):
    with get_session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]
