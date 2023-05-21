from rest_framework.pagination import PageNumberPagination


class RecipesFollowsPagination(PageNumberPagination):
    page_size = 6
