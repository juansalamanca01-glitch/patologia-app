from rest_framework.pagination import PageNumberPagination


class PaginacionEstandar(PageNumberPagination):
    """
    Paginación de todos los listados: 20 elementos por página (PAGE_SIZE en settings.py).
    Con ?page_size= se puede pedir una página más grande, hasta 1000 elementos. Lo usan
    los menús desplegables del frontend, que necesitan la lista completa.
    """
    page_size_query_param = 'page_size'
    max_page_size = 1000
