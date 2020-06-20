import re
from django.core.exceptions import ValidationError
from ...account.error_codes import AccountErrorCode

def isPhoneNumber(number):
    if not re.match("^[03]\d{10}$", number):
        raise ValidationError(
            {"phone": "Invalid phone number"},
            code=AccountErrorCode.INVALID_PHONE,
        )
def isCnic(cnic):
    if not re.match("^\d{13}$", cnic):
        raise ValidationError(
            {"cnic": "Invalid cnic number"},
            code=AccountErrorCode.INVALID_CNIC,
        )