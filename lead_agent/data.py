import json
from pathlib import Path

from pydantic import ValidationError

from lead_agent.models import Lead


class LeadDataError(RuntimeError):
    """Raised when leads cannot be loaded, parsed, or validated."""


def load_leads(path: Path) -> list[Lead]:
    """Read, parse, and validate the leads file.

    Raises:
        LeadDataError: if the file is missing/unreadable, not valid JSON, not a
            JSON array, or contains a record that fails schema validation.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise LeadDataError(f"Leads file not found: {path}") from exc
    except OSError as exc:
        raise LeadDataError(f"Could not read leads file {path}: {exc}") from exc

    try:
        records = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LeadDataError(f"Leads file {path} is not valid JSON: {exc}") from exc

    if not isinstance(records, list):
        raise LeadDataError(f"Leads file {path} must contain a JSON array of leads.")

    leads: list[Lead] = []
    for i, record in enumerate(records):
        try:
            leads.append(Lead.model_validate(record))
        except ValidationError as exc:
            raise LeadDataError(f"Lead at index {i} is invalid:\n{exc}") from exc
    return leads
