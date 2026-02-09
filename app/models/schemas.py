from datetime import datetime
from pydantic import BaseModel, Field


# === Entry Enrichment Schemas (LLM 输出) ===

class Entity(BaseModel):
    name: str
    type: str = Field(description="concept|person|place|tool|theory|event|other")


class Claim(BaseModel):
    text: str
    type: str = Field(description="definition|rule|procedure|insight|fact|question")


class Relation(BaseModel):
    from_entity: str = Field(alias="from")
    to_entity: str = Field(alias="to")
    type: str = Field(description="depends_on|part_of|causes|contrasts|applies_to|example_of")

    class Config:
        populate_by_name = True


class Prerequisite(BaseModel):
    concept: str
    why: str


class Example(BaseModel):
    text: str
    source: str = "from_entry"


class OpenQuestion(BaseModel):
    question: str


class Signals(BaseModel):
    clarity: float = Field(ge=0.0, le=1.0)
    is_fragment: bool = False
    is_actionable: bool = False


class EnrichmentResult(BaseModel):
    summary: str
    entities: list[Entity] = []
    claims: list[Claim] = []
    relations: list[Relation] = []
    prerequisites: list[Prerequisite] = []
    examples: list[Example] = []
    open_questions: list[OpenQuestion] = []
    signals: Signals


# === Report Schemas (LLM 输出) ===

class OutlineNode(BaseModel):
    path: str
    coverage: int = Field(ge=0, le=100)
    node_summary: str
    evidence_entry_ids: list[str] = []
    children: list["OutlineNode"] = []


class MainlineStep(BaseModel):
    step_title: str
    path_ref: str
    evidence_entry_ids: list[str] = []
    notes: str = ""


class Mainline(BaseModel):
    title: str
    steps: list[MainlineStep] = []
    mainline_score: float = Field(ge=0.0, le=1.0)


class Gap(BaseModel):
    gap_title: str
    gap_type: str = Field(description="missing_prerequisite|unclear_definition|no_examples|isolated_item|big_leap")
    severity: int = Field(ge=1, le=5)
    where: str
    why: str
    evidence_entry_ids: list[str] = []
    fix_suggestion: str = ""
    minimal_task: str = ""


class IsolatedItem(BaseModel):
    entry_id: str
    why_isolated: str


class Metrics(BaseModel):
    entry_count: int = 0
    topic_count: int = 0
    scatter_score: float = 0.0
    gap_count: int = 0


class RepairTask(BaseModel):
    priority: int
    task: str
    related_gaps: list[str] = []
    expected_effect: str = ""


class ReportResult(BaseModel):
    outline_tree: OutlineNode
    mainline: Mainline
    gaps: list[Gap] = []
    isolated_items: list[IsolatedItem] = []
    metrics: Metrics
    repair_plan: list[RepairTask] = []


# === API Request/Response Schemas ===

class EntryCreate(BaseModel):
    entry_text: str = Field(min_length=1)


class EntryResponse(BaseModel):
    id: str
    created_at: datetime
    entry_text: str
    enrich_json: EnrichmentResult | None = None

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    id: str
    period_type: str
    period_key: str
    time_start: datetime
    time_end: datetime
    report_json: ReportResult | None = None
    generated_at: datetime

    class Config:
        from_attributes = True
