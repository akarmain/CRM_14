from enum import StrEnum


class Users(StrEnum):
    manager_1 = "manager_1"
    manager_2 = "manager_2"
    sales_head = "sales_head"
    analyst = "analyst"



class LeadStage(StrEnum):
    new = "new"
    qualified = "qualified"
    proposal = "proposal"
    won = "won"
    lost = "lost"


class SourcesCode(StrEnum):
    advertisement = "advertisement"
    website = "website"
    recommendation = "recommendation"
    event = "event"
    other = "other"
