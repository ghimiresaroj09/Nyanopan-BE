from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response


class DefaultPagination(PageNumberPagination):
    """Standard page-number pagination used by every list endpoint."""

    page_size = 20
    # Accept both the REST-standard page_size and the rows_per_page name used
    # by the dashboard tables. Keep a single paginator and response format.
    page_size_query_param = "rows_per_page"
    max_page_size = 100

    def get_page_size(self, request):
        requested_size = request.query_params.get("rows_per_page")
        if requested_size is None:
            requested_size = request.query_params.get("page_size")
        if requested_size is None:
            return self.page_size
        try:
            requested_size = int(requested_size)
        except (TypeError, ValueError):
            return self.page_size
        if requested_size < 1:
            return self.page_size
        return min(requested_size, self.max_page_size)


def paginate_list_or_return(request, items, serializer_class=None, context=None):
    """Paginate a custom list response while retaining its item schema.

    Custom APIViews that return arrays do not inherit DRF's generic list
    pagination. This helper applies the shared page/page-size parameters and
    returns the usual count/next/previous/results structure. It is intended
    for collection endpoints implemented as APIViews instead of DRF list
    generics.
    """
    items = list(items)
    if not hasattr(request, "query_params"):
        request = Request(request)
    paginator = DefaultPagination()
    paginator.request = request
    paginator.page = None
    paginator._paginator = None
    page_size = paginator.get_page_size(request)
    if not page_size:
        data = serializer_class(items, many=True, context=context).data if serializer_class else items
        return Response(data)

    paginator.page_size = page_size
    page = paginator.paginate_queryset(items, request, view=None)
    data = serializer_class(page, many=True, context=context).data if serializer_class else page
    return paginator.get_paginated_response(data)
