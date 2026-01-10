import os
import json
import httpx
from typing import Any, Optional


# LeanIX configuration
LEANIX_SUBDOMAIN = os.getenv("LEANIX_SUBDOMAIN", "")  # e.g., "mycompany"
LEANIX_API_TOKEN = os.getenv("LEANIX_API_TOKEN", "")
LEANIX_BASE_URL = f"https://{LEANIX_SUBDOMAIN}.leanix.net" if LEANIX_SUBDOMAIN else ""
LEANIX_AUTH_URL = f"{LEANIX_BASE_URL}/services/mtm/v1/oauth2/token"
LEANIX_GRAPHQL_URL = f"{LEANIX_BASE_URL}/services/pathfinder/v1/graphql"


async def get_access_token() -> str:
    """
    Get LeanIX access token using API token
    
    Authentication flow:
    1. Use API token to get OAuth2 access token
    2. Use access token for GraphQL API requests
    
    Returns:
        Access token string
    """
    if not LEANIX_API_TOKEN or not LEANIX_SUBDOMAIN:
        raise ValueError("LEANIX_API_TOKEN and LEANIX_SUBDOMAIN must be set in environment variables")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LEANIX_AUTH_URL,
                data={
                    "grant_type": "client_credentials"
                },
                headers={
                    "Authorization": f"Bearer {LEANIX_API_TOKEN}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token", "")
            else:
                raise Exception(f"Failed to get access token: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error getting LeanIX access token: {e}")
        raise


async def execute_graphql_query(query: str, variables: Optional[dict] = None) -> dict[str, Any]:
    """
    Execute a GraphQL query against LeanIX API
    
    Args:
        query: GraphQL query string
        variables: Optional variables for the query
    
    Returns:
        GraphQL response data
    """
    try:
        # Get access token
        access_token = await get_access_token()
        
        # Prepare request payload
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        # Execute GraphQL request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LEANIX_GRAPHQL_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("errors"):
                    print(f"GraphQL errors: {result['errors']}")
                return result
            else:
                raise Exception(f"GraphQL request failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error executing GraphQL query: {e}")
        return {"errors": [{"message": str(e)}]}


async def search_fact_sheets(
    search_term: str,
    fact_sheet_type: Optional[str] = None,
    limit: int = 10,
    include_fields: Optional[list[str]] = None
) -> list[dict[str, Any]]:
    """
    Search for fact sheets in LeanIX
    
    Args:
        search_term: Search term to find in fact sheet names or descriptions
        fact_sheet_type: Optional fact sheet type filter (e.g., "Application", "DataObject", "ITComponent")
        limit: Maximum number of results to return
        include_fields: Optional list of additional fields to include in response
        
    Common fact sheet types:
        - Application
        - BusinessCapability
        - Process
        - DataObject
        - ITComponent
        - UserGroup
        - Project
        - Provider
        - Interface
    
    Returns:
        List of fact sheet objects with id, name, type, description, and other metadata
    """
    # Build the GraphQL query
    fields = ["id", "name", "type", "description", "displayName"]
    if include_fields:
        fields.extend(include_fields)
    
    fields_str = "\n        ".join(fields)
    
    # Build filter condition
    filter_conditions = [f'fullTextSearch: "{search_term}"']
    if fact_sheet_type:
        filter_conditions.append(f'facetFilters: [{{facetKey: "FactSheetTypes", keys: ["{fact_sheet_type}"]}}]')
    
    filter_str = ", ".join(filter_conditions)
    
    query = f"""
    query {{
      allFactSheets(filter: {{{filter_str}}}, first: {limit}) {{
        edges {{
          node {{
            {fields_str}
          }}
        }}
      }}
    }}
    """
    
    try:
        result = await execute_graphql_query(query)
        
        if result.get("errors"):
            return []
        
        # Extract fact sheets from response
        edges = result.get("data", {}).get("allFactSheets", {}).get("edges", [])
        fact_sheets = [edge["node"] for edge in edges]
        
        return fact_sheets
    except Exception as e:
        print(f"Error searching fact sheets: {e}")
        return []


async def get_fact_sheet(
    fact_sheet_id: str,
    include_relations: bool = False,
    include_documents: bool = False
) -> dict[str, Any]:
    """
    Get detailed information about a specific fact sheet
    
    Args:
        fact_sheet_id: ID of the fact sheet to retrieve
        include_relations: Whether to include related fact sheets
        include_documents: Whether to include associated documents
    
    Returns:
        Fact sheet object with detailed information
    """
    # Build fields list
    fields = [
        "id",
        "name",
        "type",
        "description",
        "displayName",
        "tags { name }",
        "updatedAt",
        "createdAt"
    ]
    
    if include_relations:
        fields.append("""
        relToChild {
          edges {
            node {
              factSheet {
                id
                name
                type
                displayName
              }
            }
          }
        }
        """)
    
    if include_documents:
        fields.append("""
        documents {
          edges {
            node {
              id
              name
              description
              url
            }
          }
        }
        """)
    
    fields_str = "\n      ".join(fields)
    
    query = f"""
    query {{
      factSheet(id: "{fact_sheet_id}") {{
        {fields_str}
      }}
    }}
    """
    
    try:
        result = await execute_graphql_query(query)
        
        if result.get("errors"):
            return {}
        
        fact_sheet = result.get("data", {}).get("factSheet", {})
        return fact_sheet
    except Exception as e:
        print(f"Error getting fact sheet: {e}")
        return {}


async def search_applications(
    search_term: str,
    limit: int = 10,
    include_lifecycle: bool = True
) -> list[dict[str, Any]]:
    """
    Search for Applications (a common use case)
    
    Args:
        search_term: Search term for application names/descriptions
        limit: Maximum number of results
        include_lifecycle: Include lifecycle information
    
    Returns:
        List of application fact sheets
    """
    fields = ["id", "name", "displayName", "description", "alias"]
    
    if include_lifecycle:
        fields.append("lifecycle { asString phases { phase startDate } }")
    
    fields_str = "\n        ".join(fields)
    
    query = f"""
    query {{
      allFactSheets(
        filter: {{
          facetFilters: [{{facetKey: "FactSheetTypes", keys: ["Application"]}}]
          fullTextSearch: "{search_term}"
        }}
        first: {limit}
      ) {{
        edges {{
          node {{
            ... on Application {{
              {fields_str}
            }}
          }}
        }}
      }}
    }}
    """
    
    try:
        result = await execute_graphql_query(query)
        
        if result.get("errors"):
            return []
        
        edges = result.get("data", {}).get("allFactSheets", {}).get("edges", [])
        applications = [edge["node"] for edge in edges]
        
        return applications
    except Exception as e:
        print(f"Error searching applications: {e}")
        return []


async def get_fact_sheet_types() -> list[str]:
    """
    Get all available fact sheet types in the workspace
    
    Returns:
        List of fact sheet type names
    """
    query = """
    query {
      allFactSheets(first: 0) {
        edges {
          node {
            type
          }
        }
      }
      __type(name: "FactSheetType") {
        enumValues {
          name
        }
      }
    }
    """
    
    try:
        result = await execute_graphql_query(query)
        
        if result.get("errors"):
            return []
        
        # Get from enum values
        enum_values = result.get("data", {}).get("__type", {}).get("enumValues", [])
        types = [value["name"] for value in enum_values]
        
        return types
    except Exception as e:
        print(f"Error getting fact sheet types: {e}")
        return []
