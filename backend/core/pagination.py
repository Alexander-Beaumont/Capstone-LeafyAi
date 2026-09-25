from rest_framework.pagination import LimitOffsetPagination


class OperatorLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 500
