import datetime
import json
import mimetypes
import os
import csv
import string
from typing import Union

from django.http import (
    FileResponse,
    HttpResponseNotFound,
    HttpResponsePermanentRedirect,
    JsonResponse,
)
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from draftjs_sanitizer import SafeJSONEncoder

from ..checkout.utils import (
    get_checkout_from_request,
    get_or_create_checkout_from_request,
    set_checkout_cookie,
)
from ..core.utils import serialize_decimal
from ..seo.schema.product import product_json_ld
from .filters import ProductCategoryFilter, ProductCollectionFilter
from .forms import ProductForm
from .models import Category, DigitalContentUrl, ProductType, Product, ProductVariant, ProductImage
from .utils import (
    collections_visible_to_user,
    get_product_images,
    get_product_list_context,
    products_for_checkout,
    products_for_products_list,
    products_with_details,
    bulk_products
)
from .utils.availability import get_product_availability
from .utils.digital_products import (
    digital_content_url_is_valid,
    increment_download_count,
)
from .utils.variants_picker import get_variant_picker_data
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError

def uploadFile(files):
    for file in files.getlist('images'):
        if file.content_type not in ["image/png","image/jpeg"]:
            return HttpResponse({"error":"Only Images Allowed"},status=400)
        with open("media/products/"+file.name, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
    return HttpResponse({"resp":"Images Uploaded"},status=200)


@csrf_exempt
def post(request):
    # return JsonResponse({"error":"No Authorized"})
    if request.method == "POST":
        path = uploadFile(request.FILES)
        if(path.status_code == 400):
            return JsonResponse({"error":"Images of jpeg and png format are allowed"},status=400)
        return HttpResponse(f"Image Uploaded")
    return JsonResponse({"error":"Only Get allowed"},status=400)        

def product_details(request, slug, product_id, form=None):
    """Product details page.

    The following variables are available to the template:

    product:
        The Product instance itself.

    is_visible:
        Whether the product is visible to regular users (for cases when an
        admin is previewing a product before publishing).

    form:
        The add-to-checkout form.

    price_range:
        The PriceRange for the product including all discounts.

    undiscounted_price_range:
        The PriceRange excluding all discounts.

    discount:
        Either a Price instance equal to the discount value or None if no
        discount was available.

    local_price_range:
        The same PriceRange from price_range represented in user's local
        currency. The value will be None if exchange rate is not available or
        the local currency is the same as site's default currency.
    """
    products = products_with_details(user=request.user)
    product = get_object_or_404(products, id=product_id)
    if product.get_slug() != slug:
        return HttpResponsePermanentRedirect(product.get_absolute_url())
    today = datetime.date.today()
    is_visible = product.publication_date is None or product.publication_date <= today
    if form is None:
        checkout = get_checkout_from_request(request)
        form = ProductForm(
            checkout=checkout,
            product=product,
            data=request.POST or None,
            discounts=request.discounts,
            country=request.country,
            extensions=request.extensions,
        )
    availability = get_product_availability(
        product,
        discounts=request.discounts,
        country=request.country,
        local_currency=request.currency,
        extensions=request.extensions,
    )
    product_images = get_product_images(product)
    variant_picker_data = get_variant_picker_data(
        product,
        request.discounts,
        request.extensions,
        request.currency,
        request.country,
    )
    # show_variant_picker determines if variant picker is used or select input
    show_variant_picker = all(
        [v["attributes"] for v in variant_picker_data["variants"]]
    )
    json_ld_data = product_json_ld(product)
    ctx = {
        "description_json": product.translated.description_json,
        "description_html": product.translated.description,
        "is_visible": is_visible,
        "form": form,
        "availability": availability,
        "product": product,
        "product_images": product_images,
        "show_variant_picker": show_variant_picker,
        "variant_picker_data": json.dumps(
            variant_picker_data, default=serialize_decimal, cls=SafeJSONEncoder
        ),
        "json_ld_product_data": json.dumps(
            json_ld_data, default=serialize_decimal, cls=SafeJSONEncoder
        ),
    }
    return TemplateResponse(request, "product/details.html", ctx)


def digital_product(request, token: str) -> Union[FileResponse, HttpResponseNotFound]:
    """Return the direct download link to content if given token is still valid."""

    qs = DigitalContentUrl.objects.prefetch_related("line__order__user")
    content_url = get_object_or_404(qs, token=token)  # type: DigitalContentUrl
    if not digital_content_url_is_valid(content_url):
        return HttpResponseNotFound("Url is not valid anymore")

    digital_content = content_url.content
    digital_content.content_file.open()
    opened_file = digital_content.content_file.file
    filename = os.path.basename(digital_content.content_file.name)
    file_expr = 'filename="{}"'.format(filename)

    content_type = mimetypes.guess_type(str(filename))[0]
    response = FileResponse(opened_file)
    response["Content-Length"] = digital_content.content_file.size

    response["Content-Type"] = content_type
    response["Content-Disposition"] = "attachment; {}".format(file_expr)

    increment_download_count(content_url)
    return response


def product_add_to_checkout(request, slug, product_id):
    # types: (int, str, dict) -> None

    if not request.method == "POST":
        return redirect(
            reverse("product:details", kwargs={"product_id": product_id, "slug": slug})
        )

    products = products_for_checkout(user=request.user)
    product = get_object_or_404(products, pk=product_id)
    checkout = get_or_create_checkout_from_request(request)
    form = ProductForm(
        checkout=checkout,
        product=product,
        data=request.POST or None,
        discounts=request.discounts,
        country=request.country,
        extensions=request.extensions,
    )
    if form.is_valid():
        form.save()
        if request.is_ajax():
            response = JsonResponse({"next": reverse("checkout:index")}, status=200)
        else:
            response = redirect("checkout:index")
    else:
        if request.is_ajax():
            response = JsonResponse({"error": form.errors}, status=400)
        else:
            response = product_details(request, slug, product_id, form)
    if not request.user.is_authenticated:
        set_checkout_cookie(checkout, response)
    return response


def category_index(request, slug, category_id):
    categories = Category.objects.prefetch_related("translations")
    category = get_object_or_404(categories, id=category_id)
    if slug != category.slug:
        return redirect(
            "product:category",
            permanent=True,
            slug=category.slug,
            category_id=category_id,
        )
    # Check for subcategories
    categories = category.get_descendants(include_self=True)
    products = (
        products_for_products_list(user=request.user)
        .filter(category__in=categories)
        .order_by("name")
        .prefetch_related("collections")
    )
    product_filter = ProductCategoryFilter(
        request.GET, queryset=products, category=category
    )
    ctx = get_product_list_context(request, product_filter)
    ctx.update({"object": category})
    return TemplateResponse(request, "category/index.html", ctx)


def collection_index(request, slug, pk):
    collections = collections_visible_to_user(request.user).prefetch_related(
        "translations"
    )
    collection = get_object_or_404(collections, id=pk)
    if collection.slug != slug:
        return HttpResponsePermanentRedirect(collection.get_absolute_url())
    products = (
        products_for_products_list(user=request.user)
        .filter(collections__id=collection.id)
        .order_by("name")
    )
    product_filter = ProductCollectionFilter(
        request.GET, queryset=products, collection=collection
    )
    ctx = get_product_list_context(request, product_filter)
    ctx.update({"object": collection})
    return TemplateResponse(request, "collection/index.html", ctx)


def uploadCSVFile(files):
    for file in files.getlist('productcsv'):
        if file.content_type != "text/csv":
            return JsonResponse({"error": "Only csv File Supported"}, status=500)
        with open("csv/" + file.name, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        return "csv/" + file.name


@csrf_exempt
def bulk_product(request):
    if request.method == "POST":
        path = uploadCSVFile(request.FILES)
        products = bulk_products.csv_to_json(path)
        errors = []
        row = 1
        for product in products:
            obj = bulk_products.create_product(product)
            if obj is not None and obj.get("error"):
                errors.append({"row": row, "error": obj["error"]})
            row = row + 1
        if len(errors) > 0:
            return JsonResponse({"error": json.dumps(errors)}, status=400)
        return JsonResponse({"message": "Success"}, status=200)
    return JsonResponse("Only Get allowed")
