
from django.urls import path, include
from .views import BookAPIView


urlpatterns = [
    path("", BookAPIView.as_view(), name="book_list"),
]


