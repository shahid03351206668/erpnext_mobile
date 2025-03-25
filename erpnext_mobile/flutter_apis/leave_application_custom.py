from __future__ import unicode_literals
import frappe
from typing import Dict, Optional, Tuple
from frappe import _
from frappe.utils import (
    cint,
    cstr,
    date_diff,
    flt,
    getdate,
    add_days,
    nowdate,
)
from hrms.hr.doctype.leave_application.leave_application import (
    get_leaves_pending_approval_for_period,
    get_leave_allocation_records,
    get_allocation_expiry_for_cf_leaves,
    get_leave_entries,
    get_leave_approver,
    get_holidays,
)


@frappe.whitelist()
def get_number_of_leave_days(
    employee: str,
    leave_type: str,
    from_date: str,
    to_date: str,
    half_day: Optional[int] = None,
    half_day_date: Optional[str] = None,
    holiday_list: Optional[str] = None,
    hourly_leave: Optional[str] = None,
    hours=0,
) -> float:
    """Returns number of leave days between 2 dates after considering half day and holidays
    (Based on the include_holiday setting in Leave Type)"""
    number_of_days = 0
    if cint(half_day) == 1:
        if getdate(from_date) == getdate(to_date):
            number_of_days = 0.5
        elif half_day_date and getdate(from_date) <= getdate(half_day_date) <= getdate(
            to_date
        ):
            number_of_days = date_diff(to_date, from_date) + 0.5
        else:
            number_of_days = date_diff(to_date, from_date) + 1

    else:
        number_of_days = date_diff(to_date, from_date) + 1

    if not frappe.db.get_value("Leave Type", leave_type, "include_holiday"):
        number_of_days = flt(number_of_days) - flt(
            get_holidays(employee, from_date, to_date, holiday_list=holiday_list)
        )

    if hourly_leave:
        shift = frappe.db.get_value(
            "Employee Shift", {"employee": employee, "date": from_date}, "shift"
        )
        if not shift:
            frappe.throw(
                "You cannot apply hourly leave, you've not assigned to any shift on selected date {}, employee {}.".format(
                    from_date, employee
                )
            )
        total_shift_hours = frappe.db.get_value("Shift", shift, "total_shift_hours")
        # frappe.msgprint(str(total_shift_hours))
        total_shift_hours = int(total_shift_hours.split(":")[0])
        # frappe.msgprint(str(total_shift_hours))
        if int(hours) >= int(total_shift_hours):
            frappe.throw(
                "Hourly leave must be less then total shift hours {}".format(
                    str(total_shift_hours)
                )
            )

        number_of_days = flt((1 / int(total_shift_hours)) * int(hours), 3)
    return number_of_days


def get_remaining_leaves(
    allocation: Dict, leaves_taken: float, date: str, cf_expiry: str
) -> Dict[str, float]:
    """Returns a dict of leave_balance and leave_balance_for_consumption
    leave_balance returns the available leave balance
    leave_balance_for_consumption returns the minimum leaves remaining after comparing with remaining days for allocation expiry
    """

    def _get_remaining_leaves(remaining_leaves, end_date):
        """Returns minimum leaves remaining after comparing with remaining days for allocation expiry"""
        if remaining_leaves > 0:
            remaining_days = date_diff(end_date, date) + 1
            remaining_leaves = min(remaining_days, remaining_leaves)

        return remaining_leaves

    if cf_expiry and allocation.unused_leaves:
        # allocation contains both carry forwarded and new leaves
        new_leaves_taken, cf_leaves_taken = get_new_and_cf_leaves_taken(
            allocation, cf_expiry
        )

        if getdate(date) > getdate(cf_expiry):
            # carry forwarded leaves have expired
            cf_leaves = remaining_cf_leaves = 0
        else:
            cf_leaves = flt(allocation.unused_leaves) + flt(cf_leaves_taken)
            remaining_cf_leaves = _get_remaining_leaves(cf_leaves, cf_expiry)

        # new leaves allocated - new leaves taken + cf leave balance
        # Note: `new_leaves_taken` is added here because its already a -ve number in the ledger
        leave_balance = (
            flt(allocation.new_leaves_allocated) + flt(new_leaves_taken)
        ) + flt(cf_leaves)
        leave_balance_for_consumption = (
            flt(allocation.new_leaves_allocated) + flt(new_leaves_taken)
        ) + flt(remaining_cf_leaves)
    else:
        # allocation only contains newly allocated leaves
        leave_balance = leave_balance_for_consumption = flt(
            allocation.total_leaves_allocated
        ) + flt(leaves_taken)

    remaining_leaves = _get_remaining_leaves(
        leave_balance_for_consumption, allocation.to_date
    )
    return frappe._dict(
        leave_balance=leave_balance, leave_balance_for_consumption=remaining_leaves
    )


def get_new_and_cf_leaves_taken(
    allocation: Dict, cf_expiry: str
) -> Tuple[float, float]:
    """returns new leaves taken and carry forwarded leaves taken within an allocation period based on cf leave expiry"""
    cf_leaves_taken = get_leaves_for_period(
        allocation.employee, allocation.leave_type, allocation.from_date, cf_expiry
    )
    new_leaves_taken = get_leaves_for_period(
        allocation.employee,
        allocation.leave_type,
        add_days(cf_expiry, 1),
        allocation.to_date,
    )

    # using abs because leaves taken is a -ve number in the ledger
    if abs(cf_leaves_taken) > allocation.unused_leaves:
        # adjust the excess leaves in new_leaves_taken
        new_leaves_taken += -(abs(cf_leaves_taken) - allocation.unused_leaves)
        cf_leaves_taken = -allocation.unused_leaves

    return new_leaves_taken, cf_leaves_taken


def get_leaves_for_period(
    employee: str,
    leave_type: str,
    from_date: str,
    to_date: str,
    skip_expired_leaves: bool = True,
) -> float:
    leave_entries = get_leave_entries(employee, leave_type, from_date, to_date)
    leave_days = 0

    for leave_entry in leave_entries:
        inclusive_period = leave_entry.from_date >= getdate(
            from_date
        ) and leave_entry.to_date <= getdate(to_date)

        if leave_entry.transaction_type == "Salary Slip":
            leave_days += leave_entry.leaves

        if inclusive_period and leave_entry.transaction_type == "Leave Encashment":
            leave_days += leave_entry.leaves

        elif (
            inclusive_period
            and leave_entry.transaction_type == "Leave Allocation"
            and leave_entry.is_expired
            and not skip_expired_leaves
        ):
            leave_days += leave_entry.leaves

        elif leave_entry.transaction_type == "Leave Application":
            if leave_entry.from_date < getdate(from_date):
                leave_entry.from_date = from_date
            if leave_entry.to_date > getdate(to_date):
                leave_entry.to_date = to_date

            half_day = 0
            half_day_date = None
            hourly_leave = 0
            hours = 0
            # fetch half day date for leaves with half days
            if leave_entry.leaves % 1:
                half_day = 1
                half_day_date = frappe.db.get_value(
                    "Leave Application",
                    {"name": leave_entry.transaction_name},
                    ["half_day_date"],
                )
                if not half_day_date:
                    half_day = 0
                    hourly_leave = 1
                    hours = frappe.db.get_value(
                        "Leave Application",
                        {"name": leave_entry.transaction_name},
                        ["hours"],
                    )

            leave_days += (
                get_number_of_leave_days(
                    employee,
                    leave_type,
                    leave_entry.from_date,
                    leave_entry.to_date,
                    half_day,
                    half_day_date,
                    holiday_list=leave_entry.holiday_list,
                    hourly_leave=hourly_leave,
                    hours=hours,
                )
                * -1
            )

    return leave_days


@frappe.whitelist()
def get_leave_balance_on(
    employee: str,
    leave_type: str,
    date: str,
    to_date: str = None,
    consider_all_leaves_in_the_allocation_period: bool = False,
    for_consumption: bool = False,
):
    """
    Returns leave balance till date
    :param employee: employee name
    :param leave_type: leave type
    :param date: date to check balance on
    :param to_date: future date to check for allocation expiry
    :param consider_all_leaves_in_the_allocation_period: consider all leaves taken till the allocation end date
    :param for_consumption: flag to check if leave balance is required for consumption or display
            eg: employee has leave balance = 10 but allocation is expiring in 1 day so employee can only consume 1 leave
            in this case leave_balance = 10 but leave_balance_for_consumption = 1
            if True, returns a dict eg: {'leave_balance': 10, 'leave_balance_for_consumption': 1}
            else, returns leave_balance (in this case 10)
    """

    if not to_date:
        to_date = nowdate()

    allocation_records = get_leave_allocation_records(employee, date, leave_type)
    allocation = allocation_records.get(leave_type, frappe._dict())

    end_date = (
        allocation.to_date
        if cint(consider_all_leaves_in_the_allocation_period)
        else date
    )
    cf_expiry = get_allocation_expiry_for_cf_leaves(
        employee, leave_type, str(to_date), allocation.from_date
    )

    leaves_taken = get_leaves_for_period(
        employee, leave_type, allocation.from_date, end_date
    )

    remaining_leaves = get_remaining_leaves(allocation, leaves_taken, date, cf_expiry)

    if for_consumption:
        return remaining_leaves
    else:
        return remaining_leaves.get("leave_balance")


@frappe.whitelist()
def get_leave_details(employee, date):
    allocation_records = get_leave_allocation_records(employee, str(date))
    leave_allocation = {}
    for d in allocation_records:
        allocation = allocation_records.get(d, frappe._dict())
        remaining_leaves = get_leave_balance_on(
            employee,
            d,
            str(date),
            to_date=str(allocation.to_date),
            consider_all_leaves_in_the_allocation_period=True,
        )

        end_date = allocation.to_date
        leaves_taken = (
            get_leaves_for_period(employee, d, allocation.from_date, end_date) * -1
        )
        leaves_pending = get_leaves_pending_approval_for_period(
            employee, d, allocation.from_date, end_date
        )
        expired_leaves = allocation.total_leaves_allocated - (
            remaining_leaves + leaves_taken
        )

        leave_allocation[d] = {
            "total_leaves": flt(allocation.total_leaves_allocated, 1),
            "expired_leaves": flt(expired_leaves, 1) if expired_leaves > 0 else 0,
            "leaves_taken": flt(leaves_taken, 1),
            "leaves_pending_approval": flt(leaves_pending, 1),
            "remaining_leaves": flt(remaining_leaves, 1),
        }

    # is used in set query
    lwp = frappe.get_list("Leave Type", filters={"is_lwp": 1}, pluck="name")

    return {
        "leave_allocation": leave_allocation,
        "leave_approver": get_leave_approver(employee),
        "lwps": lwp,
    }
