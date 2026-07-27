from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

Industry = Literal[
    "Financial Services",
    "Education",
    "Manufacturing",
    "Insurance",
    "CPG",
    "Media & Entertainment",
    "Telecom",
    "Healthcare",
    "Cybersecurity",
    "Real Estate",
    "Mobility",
    "Travel",
    "AgTech",
    "Nonprofit",
    "SaaS",
    "AI/ML",
    "Retail",
    "Gaming",
    "Automotive",
    "HR Tech",
    "Pharma",
    "Government",
    "Ecommerce",
    "Energy",
    "Utilities",
    "Fintech",
    "Logistics",
    "DTC",
    "Airlines",
]

LeadSource = Literal[
    "Inbound - demo",
    "Partner referral",
    "Inbound - content",
    "Outbound - SDR",
    "Community",
    "Outbound - AE",
    "Event - trade show",
    "Inbound - webinar",
]

_LIST_SEP = "|"


class Lead(BaseModel):
    """A single sales lead."""

    id: int
    first_name: str
    last_name: str
    email: str
    job_title: str
    company: str
    company_size: int
    industry: str
    location: str
    website: str
    tech_stack: list[str] = Field(default_factory=list)
    lead_source: str
    last_contacted: str
    notes: str
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def high_priority(self) -> bool:
        title = self.job_title.lower()
        return "vp" in title or "director" in title or self.company_size > 500

    def to_embedding_text(self) -> str:
        """Natural-language profile string used as the embedded document.

        Prose embeds better than raw JSON. A short priority prefix is included
        only for high-priority leads (kept brief to avoid clustering them).
        """
        prefix = "[High Priority Lead] " if self.high_priority else ""
        tags = ", ".join(self.tags) if self.tags else "none"
        tech = ", ".join(self.tech_stack) if self.tech_stack else "none"
        return (
            f"{prefix}{self.full_name}, {self.job_title} at {self.company} "
            f"({self.industry}, {self.company_size} employees, {self.location}). "
            f"Notes: {self.notes} Tags: {tags}. Tech: {tech}. "
            f"Lead source: {self.lead_source}."
        )

    def to_metadata(self) -> dict[str, str | int | bool]:
        """Flat, Chroma-compatible metadata (scalars only).

        Contains every field so a `Lead` can be reconstructed on read, plus the
        filterable fields used by the search tool. List fields are joined with
        `_LIST_SEP` and split back in `from_metadata`.
        """
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "job_title": self.job_title,
            "company": self.company,
            "company_size": self.company_size,
            "industry": self.industry,
            "location": self.location,
            "website": self.website,
            "tech_stack": _LIST_SEP.join(self.tech_stack),
            "lead_source": self.lead_source,
            "last_contacted": self.last_contacted,
            "notes": self.notes,
            "tags": _LIST_SEP.join(self.tags),
            "high_priority": self.high_priority,
        }

    @classmethod
    def from_metadata(cls, meta: dict) -> "Lead":
        """Rebuild a `Lead` from the flat metadata produced by `to_metadata`."""
        data = dict(meta)
        data["tech_stack"] = data["tech_stack"].split(_LIST_SEP) if data.get("tech_stack") else []
        data["tags"] = data["tags"].split(_LIST_SEP) if data.get("tags") else []
        return cls.model_validate(data)


class ScoredLead(BaseModel):
    """A lead paired with a retrieval/rerank relevance score."""

    lead: Lead
    score: float


class SearchResponse(BaseModel):
    """The structured answer returned to the CLI for one user turn.

    `summary` is authored by the LLM; `leads` are attached verbatim from the
    tool output (the LLM never regenerates lead data).
    """

    summary: str
    leads: list[Lead] = Field(default_factory=list)
