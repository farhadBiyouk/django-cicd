from importlib import import_module

from django.conf import settings


class ElasticsearchClient:
    def __init__(self, index_name):
        self.index_name = index_name
        self.hosts = getattr(settings, "ELASTICSEARCH_HOSTS", ["http://localhost:9200"])
        self.client_kwargs = getattr(settings, "ELASTICSEARCH_CLIENT_KWARGS", {})
        self._client = None

    def _build_client(self):
        try:
            elasticsearch_module = import_module("elasticsearch")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "elasticsearch package is required to use Elasticsearch-backed APIs"
            ) from exc

        elasticsearch_cls = getattr(elasticsearch_module, "Elasticsearch")
        return elasticsearch_cls(self.hosts, **self.client_kwargs)

    def get_client(self):
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def get_index(self):
        return self.index_name
