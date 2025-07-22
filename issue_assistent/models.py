from pydantic import BaseModel, Field
from typing import Literal

class AssistIssue(BaseModel):
    """Structured response representing a customer's issue and its resolution."""

    actual_issue: str = Field(
        description="The original customer issue exactly as received, in their own words."
    )
    actual_language: str = Field(
        description="The detected language of the original issue. Use full names like 'English' or 'Hindi'."
    )
    translated_issue: str = Field(
        description="The issue translated into English. If already in English, respond with: 'Same as actual_issue'."
    )
    issue_summary: str = Field(
        description="A concise summary of the issue in English, limited to approximately 20 words."
    )
    issue_type: Literal["billing", "shipping", "technical"] = Field(
        description="Categorize the issue as either 'billing', 'shipping', or 'technical'."
    )
    sample_solution: str = Field(
        description="A sample solution to the issue in the same language as the original issue."
    )
    translated_sample_solution: str = Field(
        description="Translate the sample solution into English. This should always be in English regardless of the original language."
    )
