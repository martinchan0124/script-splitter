"""Schema validator. Validates that records conform to their Pydantic models."""
import logging
from pydantic import ValidationError

logger = logging.getLogger(__name__)

def validate_records(records: list) -> list[str]:
    warnings = []
    for r in records:
        try:
            r.model_validate(r.model_dump(mode="json"))
        except ValidationError as e:
            msg = f"Validation failed for {r.__class__.__name__}: {e}"
            warnings.append(msg)
            logger.warning(msg)
    return warnings

