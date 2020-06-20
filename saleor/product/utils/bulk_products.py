import json
import csv
import os
from django.http import (
    JsonResponse,
)
from django.utils.text import slugify
from ..models import (
    Category,
    ProductType,
    Product,
    ProductVariant,
    ProductImage,
    Attribute,
    AttributeValue,
    AttributeVariant,
    AttributeProduct,
    AssignedProductAttribute,
    AssignedVariantAttribute
)


def create_category(product):
    category = product.get("category")
    background_image = product.get("category_image")
    if not isinstance(category, str):
        return {"error": "Invalid Category"}
    description_json = product.get("description_json").replace("\n", " ")
    try:
        obj = Category.objects.get(name=category)
        return obj
    except:
        obj = Category.objects.create(
            name=category.strip(), slug=slugify(category.strip()), background_image=background_image.replace("media/", ""), description_json=json.loads("{\"blocks\":[{\"key\":\"5g23\",\"text\":\"" + description_json + "\",\"type\":\"unstyled\",\"depth\":0,\"inlineStyleRanges\":[],\"entityRanges\":[],\"data\":{}}],\"entityMap\":{}}"))
        print(obj)
        return obj


def create_product_type(product):
    product_type = product.get("product_type")
    if not isinstance(product_type, str):
        return {"error": "Invalid Product Type"}
    obj, created = ProductType.objects.get_or_create(
        name=product_type, has_variants=False, weight=1, defaults={'name': product_type})
    return obj


def create_attribute(product):
    attribute_name = product["attribute_name"]

    try:
        attribute = Attribute.objects.get(name=attribute_name)
        attribute_value = create_attribute_value(product, attribute)
        return (attribute, attribute_value)
    except:
        attribute = Attribute.objects.create(
            name=attribute_name, slug=slugify(attribute_name), value_required=True)
        attribute_value = create_attribute_value(product, attribute)
        return (attribute, attribute_value)


def create_attribute_value(product, attribute):
    attribute_value = product["attribute_value"]
    try:
        attribute_value = AttributeValue.objects.get(
            name=attribute_value, attribute=attribute)
        return attribute_value
    except:
        attribute_value = AttributeValue.objects.create(
            name=attribute_value, slug=slugify(attribute_value), value=attribute_value, attribute=attribute)
        return attribute_value


def create_attributeproduct(product_type, attribute):
    try:
        attributeproduct = AttributeProduct.objects.get(
            attribute=attribute, product_type=product_type)
        return attributeproduct
    except:
        return AttributeProduct.objects.create(attribute=attribute, product_type=product_type)


def create_variantproduct(product_type, attribute):
    try:
        attributevariant = AttributeVariant.objects.get(
            attribute=attribute, product_type=product_type)
        return attributevariant
    except:
        return AttributeVariant.objects.create(attribute=attribute, product_type=product_type)


def create_variant(product):
    variant_name = product["variant_name"]
    variant_value = product["variant_value"]
    return create_attribute(
        {"attribute_name": variant_name, "attribute_value": variant_value})


def create_assignedproductattrib(product, attributeproduct, attribute_value):
    assignedproductattrib, created = AssignedProductAttribute.objects.get_or_create(
        product=product, defaults={"product": product, "assignment": attributeproduct})
    print(product.id, attribute_value)
    assignedproductattrib.values.add(attribute_value)
    return assignedproductattrib.save()


def create_assignedvariantattrib(product_variant, variantproduct, variant_value):
    assignedvariantattrib, created = AssignedVariantAttribute.objects.get_or_create(
        variant=product_variant, defaults={"variant": product_variant, "assignment": variantproduct})

    assignedvariantattrib.values.add(variant_value)
    return assignedvariantattrib.save()


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
    attribute, attribute_value = create_attribute(product)
    variant, variant_value = create_variant(product)
    attributeproduct = create_attributeproduct(product_type, attribute)
    # variantproduct = create_variantproduct(product_type, variant)

    name = product.get("name")
    description_json = product.get("description_json").replace("\n", " ")
    description_json = json.loads("{\"blocks\":[{\"key\":\"5g23\",\"text\":\"" + description_json +
                                  "\",\"type\":\"unstyled\",\"depth\":0,\"inlineStyleRanges\":[],\"entityRanges\":[],\"data\":{}}],\"entityMap\":{}}")
    price_amount = product.get("price_amount")
    minimal_variant_price_amount = price_amount
    charge_taxes = product.get("charge_taxes")
    seo_title = product.get("seo_title")
    seo_description = product.get("seo_description")
    sku = product.get("sku")
    quantity = product.get("quantity")
    image = product.get("image")
    print(f"------------{name}-----------")
    try:
        new_product = Product.objects.get(name=name)
        Product.objects.filter(name=name).update(name=name, description_json=description_json, category=category, product_type=product_type, price_amount=price_amount, minimal_variant_price_amount=minimal_variant_price_amount,
                                                 seo_title=seo_title, seo_description=seo_description)
        product_variant, created = ProductVariant.objects.get_or_create(sku=sku, defaults={
                                                                        "name": variant_value, "sku": sku, "product": new_product, "quantity": quantity, "quantity_allocated": 50})
        # assignedvariantattrib = create_assignedvariantattrib(product_variant,variantproduct,variant_value)
        create_productimage(product, new_product)
        return
    except Product.DoesNotExist:
        new_product = Product.objects.create(name=name, description_json=description_json, category=category,
                                             product_type=product_type, price_amount=price_amount, minimal_variant_price_amount=minimal_variant_price_amount,
                                             seo_title=seo_title, seo_description=seo_description)
        assignedproductattrib = create_assignedproductattrib(
            new_product, attributeproduct, attribute_value)
        product_variant = ProductVariant.objects.create(name=variant_value,
                                                        sku=sku, product=new_product, quantity=quantity, quantity_allocated=100)
        # assignedvariantattrib = create_assignedvariantattrib(product_variant,variantproduct,variant_value)
        create_productimage(product, new_product)


def create_productimage(product, instance):
    if not os.path.exists("media/products/" + product["image"]):
        return
    try:
        productimage = ProductImage.objects.get(product=instance)
        ProductImage.objects.filter(product=instance).update(
            product=instance, image="products/" + product["image"], alt=product["name"])
    except:
        ProductImage.objects.create(
            product=instance, image="products/" + product["image"], alt=product["name"])


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
        # if ProductVariant.objects.filter(sku=product.get("sku")).exists():
        #     return {"error": "Product SKU Must Be Unique"}
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
