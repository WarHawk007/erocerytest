from django.core.exceptions import ValidationError

from ...account.forms import get_address_form
from ...account.models import Address
from ...account.validators import validate_possible_number
from .validation import isPhoneNumber

class I18nMixin:
    """A mixin providing methods necessary to fulfill the internationalization process.

    It is to be used with BaseMutation or ModelMutation.
    """

    @classmethod
    def validate_address(cls, address_data: dict, instance=None):
        phone = address_data.get("phone", None)
        if phone:
            isPhoneNumber(phone)

        # address_form, _ = get_address_form(address_data, address_data.get("country"))

        # if not address_form.is_valid():
        #     raise ValidationError(address_form.errors.as_data())

        if not instance:
            instance = Address()
        cls.construct_instance(instance, address_data)
        print(f"===={instance}========")
        cls.clean_instance(instance)
        return instance
