from app.core.errors import InvalidTransitionError
from app.domain.enums import LeadStage


def ensure_transition_allowed(current_stage: LeadStage, target_stage: LeadStage) -> None:
    if current_stage in {LeadStage.won, LeadStage.lost} and target_stage != current_stage:
        raise InvalidTransitionError(
            f"Invalid stage transition from '{current_stage}' to '{target_stage}'."
        )


FORWARD_STAGE_MAP: dict[LeadStage, tuple[LeadStage, ...]] = {
    LeadStage.new: (LeadStage.qualified,),
    LeadStage.qualified: (LeadStage.proposal,),
    LeadStage.proposal: (LeadStage.won, LeadStage.lost),
    LeadStage.won: (),
    LeadStage.lost: (),
}

PREVIOUS_STAGE_MAP: dict[LeadStage, LeadStage] = {
    LeadStage.qualified: LeadStage.new,
    LeadStage.proposal: LeadStage.qualified,
    LeadStage.won: LeadStage.proposal,
    LeadStage.lost: LeadStage.proposal,
}


def ensure_forward_transition(current_stage: LeadStage, target_stage: LeadStage) -> None:
    if target_stage not in FORWARD_STAGE_MAP[current_stage]:
        raise InvalidTransitionError(
            f"Managers can only move forward from '{current_stage}' to {FORWARD_STAGE_MAP[current_stage]}."
        )


def resolve_previous_stage(current_stage: LeadStage) -> LeadStage:
    try:
        return PREVIOUS_STAGE_MAP[current_stage]
    except KeyError as exc:
        raise InvalidTransitionError(
            f"Lead in stage '{current_stage}' cannot request a return to a previous stage."
        ) from exc
