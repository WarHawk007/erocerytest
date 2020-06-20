import json
import csv
import os
from django.http import (
    JsonResponse,
)
from django.core.exceptions import ValidationError
from ....product.models import Category, ProductType, Product, ProductVariant, ProductImage


def uploadCSVFile(file):
    if file.content_type != "text/csv":
        raise ValidationError({"productcsv": "Only csv File Supported"})
    with open("csv/" + file.name, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return "csv/" + file.name


def bulk_product(file):
    path = uploadCSVFile(file)
    products = csv_to_json(path)
    errors = []
    row = 1
    for product in products:
        obj = create_product(product)
        if obj is not None and obj.get("error"):
            errors.append({"row": row, "error": obj["error"]})
        row = row + 1
    if len(errors) > 0:
        raise ValidationError({"productcsv": json.dumps(errors)})
    return "Success"


def create_category(product):
    category = product.get("category")
    if not isinstance(category, str):
        return {"error": "Invalid Category"}
    obj, created = Category.objects.get_or_create(
        name=category, slug=category, description_json="{\"blocks\":[{\"key\":\"cufpr\",\"text\":\"asdsadsad\",\"type\":\"unstyled\",\"depth\":0,\"inlineStyleRanges\":[],\"entityRanges\":[],\"data\":{}}],\"entityMap\":{}}",
        defaults={'slug': category})
    return obj


def create_product_type(product):
    product_type = product.get("product_type")
    if not isinstance(product_type, str):
        return {"error": "Invalid Product Type"}
    obj, created = ProductType.objects.get_or_create(
        name=product_type, has_variants=False, weight=1, defaults={'name': product_type})
    return obj


def create_product(product):
    category = create_category(product)
    if isinstance(category, dict) and category.get("error"):
        return category
    product_type = create_product_type(product)
    if isinstance(product_type, dict) and product_type.get("error"):
        return product_type
    error = validate_product(product).get("error")
    if error != "":
        return {"error": error}
    name = product.get("name")
    description_json = json.loads("{\"blocks\":[{\"key\":\"5g23\",\"text\":\"" + product.get("description_json") +
                                  "\",\"type\":\"unstyled\",\"depth\":0,\"inlineStyleRanges\":[],\"entityRanges\":[],\"data\":{}}],\"entityMap\":{}}")
    price_amount = product.get("price_amount")
    minimal_variant_price_amount = price_amount
    charge_taxes = product.get("charge_taxes")
    seo_title = product.get("seo_title")
    seo_description = product.get("seo_description")
    sku = product.get("sku")
    quantity = product.get("quantity")
    image = product.get("image")
    try:
        new_product = Product.objects.get(name=name)
        Product.objects.filter(name=name).update(name=name, description_json=description_json, category=category, product_type=product_type, price_amount=price_amount, minimal_variant_price_amount=minimal_variant_price_amount,
                                                 seo_title=seo_title, seo_description=seo_description)
        create_productimage(product, new_product)
        return
    except Product.DoesNotExist:
        new_product = Product.objects.create(name=name, description_json=description_json, category=category,
                                             product_type=product_type, price_amount=price_amount, minimal_variant_price_amount=minimal_variant_price_amount,
                                             seo_title=seo_title, seo_description=seo_description)
        variant = ProductVariant.objects.create(
            sku=sku, product=new_product, quantity=quantity, quantity_allocated=100)
        create_productimage(product, new_product)


def create_productimage(product, instance):
    if not os.path.exists(product.get("image")):
        return
    try:
        productimage = ProductImage.objects.get(product=instance)
        ProductImage.objects.filter(product=instance).update(
            product=instance, image=product["image"].replace("media/", ""), alt=product["name"])
    except:
        ProductImage.objects.create(
            product=instance, image=product["image"].replace("media/", ""), alt=product["name"])


def validate_product(product):

    try:
        if not isinstance(product.get("name"), str) or product.get("name") == "":
            return {"error": "Invalid Product Name"}
        if not isinstance(product.get("description_json"), str) or product.get("description_json") == "":
            return {"error": "Invalid Product Description"}
        if not isinstance(int(product.get("price_amount")), int) or int(product.get("price_amount")) == 0:
            return {"error": "Invalid Product Price"}
        if not isinstance(product.get("seo_title"), str) or product.get("seo_title") == "":
            return {"error": "Invalid Product Seo Title"}
        if not isinstance(product.get("seo_description"), str) or product.get("seo_description") == "":
            return {"error": "Invalid Product Seo Description"}
        if not isinstance(product.get("sku"), str) or product.get("sku") == "":
            return {"error": "Invalid Product SKU"}
        if ProductVariant.objects.filter(sku=product.get("sku")).exists():
            return {"error": "Product SKU Must Be Unique"}
        if not isinstance(int(product.get("quantity")), int) or int(product.get("quantity")) == 0:
            return {"error": "Invalid Product Quantity"}

        return {"error": ""}
    except:
        return {"error": "Invalid Product"}


def csv_to_json(csvpath):
    arr = []
    with open(csvpath) as csvFile:
        csvReader = csv.DictReader(csvFile)
        for csvRow in csvReader:
            arr.append(csvRow)
        return json.loads(json.dumps(arr, indent=4))
