import re
import jwt
import json
import time
import frappe
import requests

from frappe.utils import cstr


@frappe.whitelist(allow_guest=True)
def reset_device_token(user, token, log_out=None):
    try:
        doctype = "Firebase Device Token"
        already_made_docs = frappe.db.get_list(
            doctype, filters={"user": user, "token": token}, pluck="name"
        )

        if log_out:
            for already_made in already_made_docs:
                doc = frappe.get_doc(doctype, already_made)
                doc.flags.ignore_permissions = True
                doc.delete()

            frappe.db.commit()
            frappe.response["message"] = "Token Deleted."
            return

        elif not already_made_docs:

            previous_tokens = frappe.db.get_list(
                doctype, filters={"token": token}, pluck="name"
            )

            for i in previous_tokens:
                frappe.delete_doc(doctype, i)
                frappe.db.commit()

            doc = frappe.new_doc(doctype)
            doc.user = user
            doc.token = token
            doc.flags.ignore_permissions = True
            doc.save()

            frappe.db.commit()
            frappe.response["message"] = "Token Created."
        else:
            frappe.response["message"] = "Token Already Found."

    except Exception as e:
        frappe.log_error(
            "Token update Failed",
            str(e),
        )
        frappe.response["message"] = e


def get_access_token():
    now = int(time.time())

    payload = {
        "iss": "firebase-adminsdk-t2rnp@erp-next-android.iam.gserviceaccount.com",  # your  "client_email"
        "scope": "https://www.googleapis.com/auth/cloud-platform",
        "aud": "https://oauth2.googleapis.com/token",  # your "token_uri"
        "iat": now,
        "exp": now + 3600,
    }

    signed_jwt = jwt.encode(
        payload,
        "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCdPnlMxadLl3Xk\naBJwJjJhY3oKhHjcFPPU8NIkWjqE8DBShVapY8dqaCaJxCQh2ynfKGZd17FCFnWp\n3CMlTrAyUaDRo64sIS2V/gP995GI78C7kl56QqNKoJRtisLh961fR9qsHsd6DGlu\n27cahAT4JH+w6LtELbtdBMk1EQuN/ku4IPgTHmbLE0oZy1+YJIJoNvzujMj7kGB1\nj9HSpUAIqoTSZJE92I8xYRwc1O9E/815llhbzmD5CirLRc/J3inkFX+0uoeFayjX\ny+lafDuhN651YNOpH42lDtP/1oAKGQHc4vbakffQdiHDBMvp0pU/veTOGqs2s7jS\n7Rr6VltbAgMBAAECggEAJTUYt8lXTkQ/IbZckov/RNsokB+Lh6wvjDYVy4NMMJOz\nI3uop3lUQQH3CIdQc3BsJoFlQ5RbvcMZwYE1EcleWPHGx4RfHNMW+dR69lfj6I6u\nwNOgJnbpM6nupUL93UFhlVenzy2TTvZr5k74Mz6E/ICKdH6FfVsC6D5PLA7l+ImS\nBHHvH7pA0lsR24xb9y+nXXjabvA8iqIQtxU+ttbo+b2YhoegYbuJVhXBllw9kWGu\nDJTbhjYR+fOKNFaJoOsteDRiyMVTT36LVROJSLDx5hMdZaunY0AKA+AQhjw4NOkr\nx7KmtzznCOCK4Fsses78V1pkiSiIl2wTrbsHHqCpeQKBgQC6WVTfVQqtX4W5P535\nAvPywEsEzGbN0tHR5JORCeT7OsWGgielAi4LaIiam3ZGkx63MAUaXL2HzpsBjZwi\n23VpoDAYDzchor/nOjVuQnKjeIdFqcqLmA3gf+vjSbOgFAQbewm0XlygUEKgv1I4\nnM7jC95bFwRp8vhj1GfOvNS9yQKBgQDYBEJX5Edm9+pOF2Tq2GJVFT5J5tLUdT3H\nhnZK9+NTrPWna7aY9ce7qaCXB7Drk1fltTXRftZXIXpxHG+of+PvxxBeE9Xa1QLJ\nC99kL2JsVndIjNa4VxKyCohE1xtyeAcJxyCTiKMVWzai5inmIXdupU4WKEg4kMXB\nVx/umoASAwKBgFxYeou2G/VwudbkZMeKpBNvIX3+QQ/MYngOOuaMLbImHM6cX0MR\nQnoa0l8znTg6HeWP4Wd//9h2FTB+2ZoYgSXX4R17JMoBWfIfUW0TdrX1u6tVCe+F\naZMQMXhQBLjWUna/0T5V6Lb1Lx9z0C4H3yp6rjUbwe8zHc5y6wJzZ0WpAoGAdIU/\noBdT6Jf7/CmkVwVnbUurMMPgn5eqPnEqZ9/08JLQY4G3miShm3mxVSZh6YCuHgs0\nP4/yYEd/u3nCRRrPQeyXyJdceNED0pyj4G+q4JN3flvyCrd1LzJ9NNzvQjy6Vyzh\nRpOinId6Hj6XBTqyKK3kRBFwe4qkEVlEsTkHsi8CgYBk04feXGXtUGR3Bp5bmPXs\nZqtz/EPX+9SEvrYqFhjOGDP4Lyh2JH0wzMiFqHVwN6U//AgoapWLO9ka2KCC4Wny\nfsu50Ij1YiNCejPZZwd0tYdZ0E+MMuqeVKY4DoSPiEXNPGFKRJGn0/+7Kh9cYpAl\nk088Wnqj4UiJ790XDcbRNQ==\n-----END PRIVATE KEY-----\n",
        algorithm="RS256",
    )

    response = requests.post(
        "https://oauth2.googleapis.com/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signed_jwt,
        },
    )

    if response.ok:
        frappe.log_error("Access Token Generated", response.json())
        return response.json().get("access_token")


def notification_log_after_insert(self, method=None):
    TAG_RE = re.compile(r"<[^>]+>")
    subject = TAG_RE.sub("", cstr(self.subject))
    email_content = TAG_RE.sub("", cstr(self.email_content))

    try:
        device_tokens = frappe.db.get_list(
            "Firebase Device Token", filters={"user": self.for_user}, pluck="token"
        )
        device_tokens = set(device_tokens)
        frappe.log_error("Notification", f"Device Tokens: {device_tokens}")

        if not device_tokens:
            return
        for i in device_tokens:
            access_token = get_access_token()
            if not access_token:
                continue

            requests.post(
                "https://fcm.googleapis.com/v1/projects/erp-next-android/messages:send",
                headers={"Authorization": f"Bearer {access_token}"},
                data=json.dumps(
                    {
                        "message": {
                            "token": i,
                            "notification": {
                                "title": subject,
                                "body": email_content,
                            },
                            "apns": {
                                "payload": {"aps": {"sound": "default", "badge": 1}}
                            },
                        }
                    }
                ),
            )

    except Exception as e:
        frappe.log_error(str(e), "Notification Failed")
