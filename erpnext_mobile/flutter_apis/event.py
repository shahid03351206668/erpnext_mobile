import frappe
from frappe.utils import cstr, cint, flt, getdate, now
from datetime import datetime
from .main import create_log, make_response, get_user_details
from frappe.utils.file_manager import save_file
from json import loads


@frappe.whitelist()
def get_event_list():
    try:
        user_details = get_user_details()
        if user_details:
            data = (
                frappe.get_list(
                    "Event",
                    fields=["subject", "starts_on", "ends_on", "event_type"],
                    order_by="starts_on desc",
                )
                or []
            )
            make_response(success=True, data=data)
        else:
            make_response(success=False, message="Invalid User")
    except Exception as e:
        make_response(success=False, message=str(e))


@frappe.whitelist(allow_guest=True)
def add_event():
    try:
        data = loads(frappe.request.data)
        if data:
            doc = frappe.new_doc("Event")
            doc.subject = data.get("subject")
            doc.starts_on = datetime.strptime(
                data.get("starts_on"), "%d-%m-%Y %H:%M:%S"
            )
            doc.ends_on = datetime.strptime(data.get("ends_on"), "%d-%m-%Y %H:%M:%S")
            doc.description = data.get("description")
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.response["message"] = "Event added"
        else:
            frappe.response["message"] = "Data not found"
    except Exception as e:
        create_log("Api Failed", e)


#  {
#      "content": "content",
#      "comment_type": "Like" or "Comment",
#      "post_id": "post_id"
#  }


@frappe.whitelist(allow_guest=True)
def add_post_comment():
    try:
        data = loads(frappe.request.data)
        user = get_user_details()
        comment_doc = frappe.new_doc("Comment")
        comment_doc.comment_type = data.get("comment_type")
        comment_doc.content = data.get("content") or ""
        comment_doc.reference_doctype = "Feed Post"
        comment_doc.reference_name = data.get("post_id") or ""
        comment_doc.comment_by = user.get("username") or ""
        comment_doc.save()
        frappe.db.commit()
        frappe.response["message"] = "Comment added successfully."
    except Exception as e:
        frappe.response["message"] = e


#  {
#      "id": "POST id" for deleting post,
#      "content": "content",
#      "title": "Tile",
#      "files": [
# {
#     "image_name":image_name,
#     "image_base64":image_base64,
# }
#   ]
#  }


@frappe.whitelist(allow_guest=True)
def add_post():
    try:
        data = loads(frappe.request.data)
        user = get_user_details()
        if data.get("id"):
            frappe.delete_doc("Feed Post", data.get("id"))
            frappe.response["message"] = "Post deleted successfully."
        else:
            post_doc = frappe.new_doc("Feed Post")
            post_doc.content = data.get("content")
            post_doc.title = data.get("title")
            post_doc.user = user.get("email")
            post_doc.save()

            for row in data.get("files") or []:
                f = save_file(
                    row.get("image_name"),
                    row.get("image_base64"),
                    "Feed Post",
                    post_doc.name,
                    decode=True,
                    is_private=0,
                )
                frappe.db.commit()

            frappe.db.commit()
            frappe.response["message"] = "Post added successfully."
            frappe.response["data"] = post_doc
    except Exception as e:
        frappe.response["message"] = e


def get_post_likes(name):
    c = frappe.db.sql(
        f""" SELECT COUNT(name) as count FROM 
		`tabComment` WHERE comment_type = 'Like'
		AND reference_name = '{name}' """,
        as_dict=True,
    )
    if c:
        c = c[0].get("count")
    else:
        c = 0
    return c


def get_post_comments(name):
    return frappe.db.sql(
        f""" SELECT comment_by, creation, content FROM 
		`tabComment` WHERE comment_type = 'Comment'
		AND reference_name = '{name}' """,
        as_dict=True,
    )


@frappe.whitelist(allow_guest=True)
def get_user_feed():
    polls = (
        frappe.db.sql(
            f""" SELECT name as poll_id, owner as user, question,answer,creation , expiry_date FROM `tabPoll`""",
            as_dict=1,
        )
        or []
    )
    for row in polls:
        row["type"] = "poll"
        if getdate(row.get("expiry_date")) <= getdate(now()):
            row["is_expired"] = True
        else:
            row["is_expired"] = False

        row["options"] = frappe.db.sql(
            f"""SELECT options, count from `tabPoll Options` where parent = '{row.poll_id}'""",
            as_dict=True,
        )

    posts = (
        frappe.db.sql(
            f""" SELECT
				name,
				user,
				content,
				title,
				creation
			FROM `tabFeed Post` """,
            as_dict=True,
        )
        or []
    )
    for row in posts:
        row["type"] = "post"
        row["comments"] = get_post_comments(row.name)
        row["likes"] = get_post_likes(row.name)
        row["is_liked"] = get_post_is_liked(row.name)

        row["images"] = frappe.db.sql(
            f"SELECT name, file_url FROM `tabFile` WHERE attached_to_doctype = 'Feed Post' AND attached_to_name = '{row.name}' ",
            as_dict=True,
        )

    # return [*polls]
    a = [*posts, *polls]
    import random

    random.shuffle(a)
    return a


def get_post_is_liked(name):
    likes = frappe.db.sql(
        f""" SELECT name  FROM 
		`tabComment` WHERE comment_type = 'Like'
		AND reference_name = '{name}' AND comment_by = '{get_user_details().username}'  """,
        as_dict=True,
    )
    if likes:
        return True
    return False


# @frappe.whitelist(allow_guest=True)
# def add_feed():
# feed_doc = frappe.new_doc("Feed")

# feed_doc.post_title
# feed_doc.posted_time
# feed_doc.post_type


@frappe.whitelist(allow_guest=True)
def add_poll():
    try:
        data: dict = loads(frappe.request.data)
        poll = frappe.new_doc("Poll")
        poll.question = data.get("question")
        poll.answer = data.get("answer")
        poll.expiry_date = data.get("expiry_date")

        for row in data.get("options"):
            row["count"] = 0
            poll.append("poll_options", row)

        poll.save()
        frappe.db.commit()
        frappe.response["data"] = poll

    except Exception as e:
        frappe.response["message"] = e


@frappe.whitelist(allow_guest=True)
def add_poll_vote():
    try:
        data = loads(frappe.request.data)
        poll_vote = frappe.new_doc("Poll Vote")
        poll_vote.user = get_user_details().email
        poll_vote.option = data.get("option")
        poll_vote.poll_id = data.get("poll_id")
        poll_vote.save()

        ch_name = frappe.db.sql(
            f""" SELECT c.name FROM `tabPoll` p INNER JOIN  `tabPoll Options` c WHERE p.name = '{data.get("poll_id")}' AND c.option = '{data.get("option")}' """
        )

        if ch_name:
            po_doc = frappe.get_doc("Poll Options", ch_name[0].get("name"))
            po_doc.count = cint(po_doc.count) + 1
            po_doc.save()

        if poll_vote.name:
            frappe.response["message"] = "Poll added successfully!"
    except Exception as e:
        frappe.response["message"] = e


# @frappe.whitelist(allow_guest=True)
# def get_user_feed_poll():
#     polls = frappe.db.sql(
#         f""" SELECT p.name FROM `tabPoll` p INNER JOIN  `tabPoll Options` c WHERE 1=1 """
#     )
#     polls = frappe.db.sql(
#         f""" SELECT
# 				name,
# 				user,
# 				content,
# 				title,
# 				creation
# 			FROM `tabFeed Poll` """,
#         as_dict=True,
#     )
#     for row in polls:
#         row["comments"] = get_post_comments(row.name)
#         row["likes"] = get_post_likes(row.name)
#         # row["images"] = frappe.db.sql(
#         #     f"SELECT name, file_url FROM `tabFile` WHERE attached_to_doctype = 'Feed Post' AND attached_to_name = '{row.name}' ",
#         #     as_dict=True,
#         # )

#     return polls
