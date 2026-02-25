from app.core.errors import InvalidTransitionError
from app.domain.enums import LeadStage


def ensure_transition_allowed(current_stage: LeadStage, target_stage: LeadStage) -> None:
    if current_stage in {LeadStage.won, LeadStage.lost} and target_stage != current_stage:
        raise InvalidTransitionError(
            f"Invalid stage transition from '{current_stage}' to '{target_stage}'."
        )
