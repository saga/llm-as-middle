"""Shared utilities and models for nodes"""
import os
import boto3
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from auth import get_access_token


class SearchQuery(BaseModel):
    """Confluence search query structure"""
    query: str = Field(description="CQL search query string")
    reasoning: str = Field(description="Brief explanation of why this query was generated")


class DocumentSummary(BaseModel):
    """Document summary structure"""
    answer: str = Field(description="Direct answer to user's question")
    key_points: list[str] = Field(description="Key points extracted from documents")
    references: list[dict[str, str]] = Field(description="Referenced documents with title and url")


def get_llm():
    """Get LLM instance configured with MSAL authentication"""
    access_token = get_access_token()
    from pydantic import SecretStr
    
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4"),
        temperature=0.7,
        api_key=SecretStr(access_token),
        base_url=os.getenv("LITELLM_BASE_URL", "http://localhost:4000"),
        default_headers={"Authorization": f"Bearer {access_token}"}
    )


def get_s3_client():
    """Get S3 client"""
    return boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )


def get_s3_bucket():
    """Get S3 bucket name"""
    return os.getenv("S3_BUCKET", "confluence-docs-backup")
