"""Query-optimization tests: product endpoints must not suffer N+1 queries."""

import pytest

pytestmark = pytest.mark.django_db


class TestQueryCounts:
    def test_product_detail_query_count_is_bounded(self, api_client, product_full, django_assert_num_queries):
        # 1 product (+category/model joins) + 1 PAV prefetch + 1 additional-image
        # prefetch + 1 variant prefetch + 1 option prefetch = 5 queries
        # regardless of data volume.
        with django_assert_num_queries(5):
            response = api_client.get(f"/api/v1/products/{product_full.slug}/")
        assert response.status_code == 200

    def test_product_list_query_count_is_bounded(self, api_client, product_full, django_assert_num_queries):
        # 1 count + 1 list (+annotations) + 2 prefetches = 4 queries.
        with django_assert_num_queries(4):
            response = api_client.get("/api/v1/products/")
        assert response.status_code == 200
