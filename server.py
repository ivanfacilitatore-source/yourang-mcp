"""
YouRang MCP Server
"""

import json
import os
from typing import Optional
import httpx
from fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict

API_BASE = "https://api.yourang.ai/v1"
API_KEY = os.getenv("YOURANG_API_KEY", "yk_m2tjb0uBnRr2yM93G3RqXVkCxJY3qC7II1nTErdnGQU")
PORT = int(os.getenv("PORT", "8080"))
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

mcp = FastMCP("yourang_mcp")


def _handle_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text
        return json.dumps({"error": f"HTTP {e.response.status_code}", "detail": detail})
    if isinstance(e, httpx.TimeoutException):
        return json.dumps({"error": "Request timed out."})
    return json.dumps({"error": f"{type(e).__name__}: {e}"})


async def _get(path: str, params: dict = None) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{API_BASE}{path}", headers=HEADERS, params=params)
        r.raise_for_status()
        return r.json()


async def _post(path: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{API_BASE}{path}", headers=HEADERS, json=body)
        r.raise_for_status()
        return r.json()


async def _patch(path: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.patch(f"{API_BASE}{path}", headers=HEADERS, json=body)
        r.raise_for_status()
        return r.json()


class ListContactsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit: Optional[int] = Field(default=50, ge=1, le=500)
    offset: Optional[int] = Field(default=0, ge=0)
    search: Optional[str] = Field(default=None)


class GetContactByPhoneInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone_number: str = Field(..., description="E.164 format e.g. +393486734487")


class CreateContactInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    first_name: str = Field(...)
    last_name: Optional[str] = Field(default=None)
    phone_number: str = Field(..., description="E.164 format")
    email: Optional[str] = Field(default=None)
    custom_fields: Optional[dict] = Field(default=None)


class UpdateContactInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contact_id: str = Field(..., description="Contact UUID")
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    phone_number: Optional[str] = Field(default=None)
    custom_fields: Optional[dict] = Field(default=None)


class UpdateContactByPhoneInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone_number: str = Field(..., description="E.164 format")
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    custom_fields: Optional[dict] = Field(default=None)


class GetWorkflowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workflow_id: str = Field(...)


class ExecuteWorkflowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workflow_id: str = Field(...)
    input_data: Optional[dict] = Field(default=None)


class ListWorkflowsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit: Optional[int] = Field(default=50, ge=1, le=100)
    offset: Optional[int] = Field(default=0, ge=0)
    filter: Optional[str] = Field(default=None)


@mcp.tool(name="yourang_list_contacts")
async def yourang_list_contacts(params: ListContactsInput) -> str:
    """List contacts in YouRang CRM."""
    try:
        query = {"limit": params.limit, "offset": params.offset}
        if params.search:
            query["search"] = params.search
        return json.dumps(await _get("/contacts", params=query), indent=2, ensure_ascii=False)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="yourang_get_contact_by_phone")
async def yourang_get_contact_by_phone(params: GetContactByPhoneInput) -> str:
    """Get a YouRang contact by phone number in E.164 format."""
    try:
        encoded = params.phone_number.replace("+", "%2B")
        return json.dumps(await _get(f"/contacts/by-phone/{encoded}"), indent=2, ensure_ascii=False)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="yourang_create_contact")
async def yourang_create_contact(params: CreateContactInput) -> str:
    """Create a new contact in YouRang."""
    try:
        body = {"first_name": params.first_name, "phone_number": params.phone_number}
        if params.last_name:
            body["last_name"] = params.last_name
        if params.email:
            body["email"] = params.email
        if params.custom_fields:
            body["custom_fields"] = params.custom_fields
        return json.dumps(await _post("/contacts", body), indent=2, ensure_ascii=False)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="yourang_update_contact")
async def yourang_update_contact(params: UpdateContactInput) -> str:
    """Update a YouRang contact by UUID."""
    try:
        body = {k: v for k, v in {"first_name": params.first_name, "last_name": params.last_name,
                "email": params.email, "phone_number": params.phone_number,
                "custom_fields": params.custom_fields}.items() if v is not None}
        return json.dumps(await _patch(f"/contacts/{params.contact_id}", body), indent=2, ensure_ascii=False)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="yourang_update_contact_by_phone")
async def yourang_update_contact_by_phone(params: UpdateContactByPhoneInput) -> str:
    """Update a YouRang contact by phone number."""
    try:
        body = {k: v for k, v in {"first_name": params.first_name, "last_name": params.last_name,
                "email": params.email, "custom_fields": params.custom_fields}.items() if v is not None}
        encoded = params.phone_number.replace("+", "%2B")
        return json.dumps(await _patch(f"/contacts/phone/{encoded}", body), indent=2, ensure_ascii=False)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="yourang_list_workflows")
async def yourang_list_workflows(params: ListWorkflowsInput) -> str:
    """List all YouRang workflows."""
    try:
        query = {"limit": params.limit, "offset": params.offset}
        if params.filter:
            query["filter"] = params.filter
        return json.dumps(await _get("/workflows/", params=query), indent=2, ensure_ascii=False)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="yourang_get_workflow")
async def yourang_get_workflow(params: GetWorkflowInput) -> str:
    """Get a YouRang workflow by UUID."""
    try:
        return json.dumps(await _get(f"/workflows/{params.workflow_id}"), indent=2, ensure_ascii=False)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="yourang_execute_workflow")
async def yourang_execute_workflow(params: ExecuteWorkflowInput) -> str:
    """Execute a YouRang workflow with optional input data."""
    try:
        return json.dumps(await _post(f"/workflows/{params.workflow_id}/execute", params.input_data or {}), indent=2, ensure_ascii=False)
    except Exception as e:
        return _handle_error(e)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=PORT)
