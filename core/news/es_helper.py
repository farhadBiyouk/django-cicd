from core.news.es_client import ElasticsearchClient


class ESHelper:
    VALID_ORDERS = {"asc", "desc"}

    def __init__(self, index_name):
        self.es_client = ElasticsearchClient(index_name)
        self.client = self.es_client.get_client()
        self.index = self.es_client.get_index()

    def get(self, doc_id):
        try:
            res = self.client.get(index=self.index, id=doc_id)
            source = res.get("_source", {})
            source["_id"] = res.get("_id")
            return source
        except Exception:
            return None

    def create(self, data):
        try:
            return self.client.index(index=self.index, document=data)
        except TypeError:
            return self.client.index(index=self.index, body=data)

    def update(self, doc_id, data):
        try:
            return self.client.update(index=self.index, id=doc_id, doc=data)
        except TypeError:
            return self.client.update(index=self.index, id=doc_id, body={"doc": data})

    def delete(self, doc_id):
        return self.client.delete(index=self.index, id=doc_id)

    def _resolve_sort(self, sort_field, sort_order, sort_map, default_sort_field):
        order = (sort_order or "desc").strip().lower()
        if order not in self.VALID_ORDERS:
            order = "desc"

        config = sort_map.get(sort_field) or sort_map[default_sort_field]
        return (
            config["field"],
            order,
            config.get("unmapped_type", "keyword"),
            config.get("missing", "_last"),
        )

    def search(
        self,
        query=None,
        page=1,
        page_size=20,
        sort_field="created_at",
        sort_order="desc",
        filters=None,
        sort_map=None,
        default_sort_field="created_at",
        search_fields=None,
        extra_filter_clauses=None,
    ):
        sort_map = sort_map or {
            default_sort_field: {"field": default_sort_field, "unmapped_type": "date"}
        }

        sort_es_field, order, unmapped_type, missing = self._resolve_sort(
            sort_field=sort_field,
            sort_order=sort_order,
            sort_map=sort_map,
            default_sort_field=default_sort_field,
        )

        body = {
            "from": (max(int(page), 1) - 1) * max(int(page_size), 1),
            "size": max(int(page_size), 1),
            "track_total_hits": True,
            "sort": [
                {
                    sort_es_field: {
                        "order": order,
                        "unmapped_type": unmapped_type,
                        "missing": missing,
                    }
                }
            ],
        }

        must_filters = []
        if filters:
            for key, value in filters.items():
                if isinstance(value, (list, tuple, set)):
                    must_filters.append({"terms": {key: list(value)}})
                else:
                    must_filters.append({"term": {key: value}})

        if extra_filter_clauses:
            must_filters.extend(extra_filter_clauses)

        if query:
            body["query"] = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": search_fields
                                or [
                                    "title",
                                    "description",
                                    "short_summary",
                                    "detailed_summary",
                                ],
                            }
                        }
                    ],
                    "filter": must_filters,
                }
            }
        elif must_filters:
            body["query"] = {"bool": {"filter": must_filters}}
        else:
            body["query"] = {"match_all": {}}

        res = self.client.search(index=self.index, body=body)
        hits = res.get("hits", {}).get("hits", [])
        total_raw = res.get("hits", {}).get("total", 0)
        total = total_raw.get("value", 0) if isinstance(total_raw, dict) else total_raw

        return hits, total
