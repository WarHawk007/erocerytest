import requests
from requests.auth import HTTPBasicAuth


def send_sms(to, message):
    try:
        to = format_phone(to)
        url = f"http://api.bizsms.pk/api-send-branded-sms.aspx?username=rnss@bizsms.pk&pass=RNSsolution12345&text={message}&masking=8764&destinationnum={to}&language=English"
        print(url)
        res = requests.get(url)
        print(res.content)
    except:
        pass


def format_phone(phone):
    return "92" + phone[1:len(phone)]
