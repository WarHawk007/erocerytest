from django.contrib.postgres.search import TrigramSimilarity, TrigramDistance
from django.db.models import Q

from ...product.models import Product


def search(phrase):
    """Return matching products for storefront views.

    Fuzzy storefront search that is resistant to small typing errors made
    by user. Name is matched using trigram similarity, description uses
    standard postgres full text search.

    Args:
        phrase (str): searched phrase

    """
    name = Q(name__icontains=phrase)
    published = Q(is_published=True)
    ft_in_description = Q(description__search=phrase)
    return Product.objects.filter(
        (ft_in_description | name) & published
    )
