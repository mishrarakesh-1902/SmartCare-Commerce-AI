from app.models import Category

def category_context(request):
    """
    Makes all product categories with their subcategories available across all templates.
    """
    try:
        categories = Category.objects.prefetch_related('sub_category_set').all()
    except Exception:
        categories = []
    return {
        'nav_categories': categories
    }
