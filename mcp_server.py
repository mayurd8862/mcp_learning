"""
Leave Management MCP Server

Run:
    uv run leave_management_mcp.py
"""

from datetime import datetime
from typing import Dict, List

from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("LeaveManagementSystem", json_response=True)

# -------------------------------------------------------------------
# Dummy Database
# -------------------------------------------------------------------

employees = {
    101: {
        "name": "Mayur",
        "department": "AI/ML",
        "leave_balance": 15,
    },
    102: {
        "name": "Rahul",
        "department": "Backend",
        "leave_balance": 10,
    },
}

leave_requests = []


# -------------------------------------------------------------------
# TOOLS
# -------------------------------------------------------------------

@mcp.tool()
def apply_leave(
    employee_id: int,
    start_date: str,
    end_date: str,
    reason: str,
) -> Dict:
    """
    Apply for leave
    """

    if employee_id not in employees:
        return {"status": "error", "message": "Employee not found"}

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    total_days = (end - start).days + 1

    if total_days <= 0:
        return {
            "status": "error",
            "message": "Invalid leave dates",
        }

    balance = employees[employee_id]["leave_balance"]

    if total_days > balance:
        return {
            "status": "error",
            "message": "Insufficient leave balance",
        }

    leave_request = {
        "employee_id": employee_id,
        "employee_name": employees[employee_id]["name"],
        "start_date": start_date,
        "end_date": end_date,
        "total_days": total_days,
        "reason": reason,
        "status": "Pending",
    }

    leave_requests.append(leave_request)

    employees[employee_id]["leave_balance"] -= total_days

    return {
        "status": "success",
        "message": "Leave applied successfully",
        "data": leave_request,
    }


@mcp.tool()
def get_leave_balance(employee_id: int) -> Dict:
    """
    Get employee leave balance
    """

    if employee_id not in employees:
        return {"status": "error", "message": "Employee not found"}

    return {
        "employee_id": employee_id,
        "employee_name": employees[employee_id]["name"],
        "leave_balance": employees[employee_id]["leave_balance"],
    }


@mcp.tool()
def get_leave_history(employee_id: int) -> List[Dict]:
    """
    Get leave history of employee
    """

    history = [
        leave
        for leave in leave_requests
        if leave["employee_id"] == employee_id
    ]

    return history


@mcp.tool()
def approve_leave(employee_id: int, start_date: str) -> Dict:
    """
    Approve leave request
    """

    for leave in leave_requests:
        if (
            leave["employee_id"] == employee_id
            and leave["start_date"] == start_date
        ):
            leave["status"] = "Approved"

            return {
                "status": "success",
                "message": "Leave approved successfully",
                "data": leave,
            }

    return {
        "status": "error",
        "message": "Leave request not found",
    }


@mcp.tool()
def reject_leave(employee_id: int, start_date: str) -> Dict:
    """
    Reject leave request
    """

    for leave in leave_requests:
        if (
            leave["employee_id"] == employee_id
            and leave["start_date"] == start_date
        ):
            leave["status"] = "Rejected"

            # Restore leave balance
            employees[employee_id]["leave_balance"] += leave["total_days"]

            return {
                "status": "success",
                "message": "Leave rejected successfully",
                "data": leave,
            }

    return {
        "status": "error",
        "message": "Leave request not found",
    }


# -------------------------------------------------------------------
# RESOURCES
# -------------------------------------------------------------------

@mcp.resource("employee://{employee_id}")
def get_employee_details(employee_id: str) -> Dict:
    """
    Get employee details
    """

    employee_id = int(employee_id)

    if employee_id not in employees:
        return {"status": "error", "message": "Employee not found"}

    return employees[employee_id]


@mcp.resource("leave-history://{employee_id}")
def employee_leave_history(employee_id: str) -> List[Dict]:
    """
    Get leave history resource
    """

    employee_id = int(employee_id)

    return [
        leave
        for leave in leave_requests
        if leave["employee_id"] == employee_id
    ]


# -------------------------------------------------------------------
# PROMPTS
# -------------------------------------------------------------------

@mcp.prompt()
def leave_approval_prompt(employee_name: str, days: int) -> str:
    """
    Generate leave approval prompt
    """

    return (
        f"Generate a professional leave approval email "
        f"for employee {employee_name} for {days} days leave."
    )


@mcp.prompt()
def leave_rejection_prompt(employee_name: str, reason: str) -> str:
    """
    Generate leave rejection prompt
    """

    return (
        f"Generate a professional leave rejection email "
        f"for employee {employee_name}. "
        f"Reason: {reason}"
    )


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
