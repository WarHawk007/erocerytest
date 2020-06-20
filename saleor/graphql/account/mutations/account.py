import graphene
import random

from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from graphql_jwt.shortcuts import get_token
from ....account import emails, events as account_events, models, utils
from ....account.error_codes import AccountErrorCode
from ....checkout import AddressType
from ....core.utils.url import validate_storefront_url
from ....core.sms import send_sms
from ...account.enums import AddressTypeEnum
from ...account.types import Address, AddressInput, User
from ...core.mutations import (
    BaseMutation,
    ModelDeleteMutation,
    ModelMutation,
    UpdateMetaBaseMutation,
)
from ...core.types import MetaInput
from ...core.types.common import AccountError
from ..validation import isPhoneNumber
from .base import (
    INVALID_TOKEN,
    BaseAddressDelete,
    BaseAddressUpdate,
    BaseCustomerCreate,
)
import requests
from django.http import (
    JsonResponse,
    HttpResponse
)
import json


class AccountRegisterInput(graphene.InputObjectType):
    phone = graphene.String(description="The valid phone of the user.", required=True)
    password = graphene.String(description="Password.", required=True)
    email = graphene.String(description="Email", required=False)

class AccountVerifyInput(graphene.InputObjectType):
    phone = graphene.String(description="Registered Phone Number.", required=True)
    sms_code = graphene.String(description="The valid sms_code.", required=True)
    password = graphene.String(description="Enter password.", required=True)


class AccountForgotVerifyInput(graphene.InputObjectType):
    new_password = graphene.String(description="New Password.", required=True)
    phone = graphene.String(description="Registered Phone Number.", required=True)
    sms_code = graphene.String(description="The valid sms_code.", required=True)


class AccountForgotPasswordInput(graphene.InputObjectType):
    phone = graphene.String(description="Registered Phone Number.", required=True)


class AccountRegister(ModelMutation):
    class Arguments:
        input = AccountRegisterInput(
            description="Fields required to create a user.", required=True
        )

    class Meta:
        description = "Register a new user."
        exclude = ["password"]
        model = models.User
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def save(cls, info, user, cleaned_input):
        password = cleaned_input["password"]
        isPhoneNumber(user.phone)
        user.set_password(password)
        sms_code = random.randint(100000, 999999)
        user.sms_code = sms_code
        user.email = cleaned_input["email"]
        message = f"Erocery Verification Code : {sms_code}"
        send_sms(user.phone, message)
        user.save()
        account_events.customer_account_created_event(user=user)
        info.context.extensions.customer_created(customer=user)


class AccountInput(graphene.InputObjectType):
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    default_billing_address = AddressInput(
        description="Billing address of the customer."
    )
    default_shipping_address = AddressInput(
        description="Shipping address of the customer."
    )


class AccountVerifyType(graphene.ObjectType):
    token = graphene.Field(graphene.ObjectType)


class AccountVerify(ModelMutation):
    token = graphene.String()

    class Arguments:
        input = AccountVerifyInput(
            description="Fields required verify user's phone number",
            required=True,
        )

    class Meta:
        description = "Verify New User "
        exclude = ["password", "sms_code"]
        model = models.User
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        phone = data["input"]["phone"]
        sms_code = data["input"]["sms_code"]
        password = data["input"]["password"]
        print(phone,sms_code,password)
        try:
            user = models.User.objects.verify(sms_code=sms_code,phone=phone)
            token = get_token(user)
            return AccountVerify(token=token)

        except:
            raise ValidationError(
                {"sms_code": "Invalid Sms Code"}, code=AccountErrorCode.INVALID
            )


class AccountForgotPassword(ModelMutation):
    class Arguments:
        input = AccountForgotPasswordInput(
            description="Fields required to send sms",
            required=True,
        )

    class Meta:
        description = "send sms to reset password"
        exclude = ["password"]
        model = models.User
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        phone = data["input"]["phone"]
        try:
            print(phone)
            user = models.User.objects.get(phone=phone)
            sms_code = random.randint(100000, 999999)
            user.sms_code = sms_code
            message = f"Erocery Verification Code : {sms_code}"
            send_sms(user.phone, message)
            user.save()
            return cls.success_response(user)
        except:
            raise ValidationError(
                {"phone": "Account with this phone number does not exist"}, code=AccountErrorCode.INVALID
            )


class AccountForgotVerify(ModelMutation):
    class Arguments:
        input = AccountForgotVerifyInput(
            description="Fields required to update password",
            required=True,
        )

    class Meta:
        description = "Update Password "
        exclude = ["new_password", "sms_code"]
        model = models.User
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        phone = data["input"]["phone"]
        sms_code = data["input"]["sms_code"]
        new_password = data["input"]["new_password"]
        try:
            user = models.User.objects.get(sms_code=sms_code, phone=phone)
            user.set_password(new_password)
            user.sms_code = ""
            user.save()
            return cls.success_response(user)
        except:
            raise ValidationError(
                {"sms_code": "Invalid Sms Code"}, code=AccountErrorCode.INVALID
            )


class AccountUpdate(BaseCustomerCreate):
    class Arguments:
        input = AccountInput(
            description="Fields required to update the account of the logged-in user.",
            required=True,
        )

    class Meta:
        description = "Updates the account of the logged-in user."
        exclude = ["password"]
        model = models.User
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = info.context.user
        data["id"] = graphene.Node.to_global_id("User", user.id)
        return super().perform_mutation(root, info, **data)


class AccountRequestDeletion(BaseMutation):
    class Arguments:
        redirect_url = graphene.String(
            required=True,
            description=(
                "URL of a view where users should be redirected to "
                "delete their account. URL in RFC 1808 format."
            ),
        )

    class Meta:
        description = (
            "Sends an email with the account removal link for the logged-in user."
        )
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = info.context.user
        redirect_url = data["redirect_url"]
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error}, code=AccountErrorCode.INVALID
            )
        emails.send_account_delete_confirmation_email_with_url(redirect_url, user)
        return AccountRequestDeletion()


class AccountDelete(ModelDeleteMutation):
    class Arguments:
        token = graphene.String(
            description=(
                "A one-time token required to remove account. "
                "Sent by email using AccountRequestDeletion mutation."
            ),
            required=True,
        )

    class Meta:
        description = "Remove user account."
        model = models.User
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def clean_instance(cls, info, instance):
        super().clean_instance(info, instance)
        if instance.is_staff:
            raise ValidationError(
                "Cannot delete a staff account.",
                code=AccountErrorCode.DELETE_STAFF_ACCOUNT,
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        user = info.context.user
        cls.clean_instance(info, user)

        token = data.pop("token")
        if not default_token_generator.check_token(user, token):
            raise ValidationError(
                {"token": ValidationError(INVALID_TOKEN, code=AccountErrorCode.INVALID)}
            )

        db_id = user.id

        user.delete()
        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        user.id = db_id
        return cls.success_response(user)


class AccountAddressCreate(ModelMutation):
    user = graphene.Field(
        User, description="A user instance for which the address was created."
    )

    class Arguments:
        input = AddressInput(
            description="Fields required to create address.", required=True
        )
        type = AddressTypeEnum(
            required=False,
            description=(
                "A type of address. If provided, the new address will be "
                "automatically assigned as the customer's default address "
                "of that type."
            ),
        )

    class Meta:
        description = "Create a new address for the customer."
        model = models.Address
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        isPhoneNumber(data["input"]["phone"])
        success_response = super().perform_mutation(root, info, **data)
        address_type = data.get("type", None)
        user = info.context.user
        success_response.user = user
        if address_type:
            instance = success_response.address
            utils.change_user_default_address(user, instance, address_type)
        return success_response

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        user = info.context.user
        instance.user_addresses.add(user)


class AccountAddressUpdate(BaseAddressUpdate):
    class Meta:
        description = "Updates an address of the logged-in user."
        model = models.Address
        error_type_class = AccountError
        error_type_field = "account_errors"


class AccountAddressDelete(BaseAddressDelete):
    class Meta:
        description = "Delete an address of the logged-in user."
        model = models.Address
        error_type_class = AccountError
        error_type_field = "account_errors"


class AccountSetDefaultAddress(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the address to set as default."
        )
        type = AddressTypeEnum(required=True, description="The type of address.")

    class Meta:
        description = "Sets a default address for the authenticated user."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        address = cls.get_node_or_error(info, data.get("id"), Address)
        user = info.context.user

        if not user.addresses.filter(pk=address.pk).exists():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "The address doesn't belong to that user.",
                        code=AccountErrorCode.INVALID,
                    )
                }
            )

        if data.get("type") == AddressTypeEnum.BILLING.value:
            address_type = AddressType.BILLING
        else:
            address_type = AddressType.SHIPPING

        utils.change_user_default_address(user, address, address_type)
        return cls(user=user)


class AccountUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Updates metadata of the logged-in user."
        model = models.User
        public = True
        error_type_class = AccountError
        error_type_field = "account_errors"

    class Arguments:
        input = MetaInput(
            description="Fields required to update new or stored metadata item.",
            required=True,
        )

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def get_instance(cls, info, **data):
        return info.context.user


class AccountResendSMS(BaseMutation):
    message = graphene.String()

    class Meta:
        description = "Send SMS To Phone"
        error_type_class = AccountError
        error_type_field = "account_errors"

    class Arguments:
        phone = graphene.String(required=True)

    @classmethod
    def perform_mutation(cls, root, info, phone):
        try:
            user = models.User.objects.get(phone=phone)
            sms_code = random.randint(100000, 999999)
            user.sms_code = sms_code
            message = f"Erocery Verification Code : {sms_code}"
            send_sms(phone, message)
            user.save()
            return AccountResendSMS(message="Success")
        except:
            raise ValidationError({"phone": "Invalid Phone Number"})
