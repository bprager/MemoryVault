from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import ExpectedItem, Scenario, TaskEvent


@dataclass(frozen=True, slots=True)
class HuggingFaceAdapterSpec:
    adapter_id: str
    dataset_name: str
    default_config: str
    default_split: str
    domain: str
    description: str


ADAPTER_SPECS: dict[str, HuggingFaceAdapterSpec] = {
    "hf_qasper": HuggingFaceAdapterSpec(
        adapter_id="hf_qasper",
        dataset_name="allenai/qasper",
        default_config="qasper",
        default_split="train",
        domain="research",
        description="Evidence-grounded document questions with cited answers.",
    ),
    "hf_conversation_bench": HuggingFaceAdapterSpec(
        adapter_id="hf_conversation_bench",
        dataset_name="arcada-labs/conversation-bench",
        default_config="default",
        default_split="train",
        domain="conversation",
        description="Multi-turn dialogue turns with tool use, state tracking, and long-range memory checks.",
    ),
    "hf_swe_bench_verified": HuggingFaceAdapterSpec(
        adapter_id="hf_swe_bench_verified",
        dataset_name="princeton-nlp/SWE-bench_Verified",
        default_config="default",
        default_split="test",
        domain="coding",
        description="Public coding issues with problem statements and test expectations.",
    ),
    "hf_taskbench": HuggingFaceAdapterSpec(
        adapter_id="hf_taskbench",
        dataset_name="microsoft/Taskbench",
        default_config="dailylifeapis",
        default_split="test",
        domain="tool_use",
        description="Tool-use tasks with steps and dependency links.",
    ),
}

STOP_WORDS = {
    "about",
    "after",
    "before",
    "because",
    "build",
    "from",
    "have",
    "into",
    "keep",
    "only",
    "that",
    "then",
    "this",
    "using",
    "with",
    "without",
}


def list_hf_adapters() -> list[HuggingFaceAdapterSpec]:
    return [ADAPTER_SPECS[key] for key in sorted(ADAPTER_SPECS)]


def load_hf_rows_file(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [_unwrap_row(item) for item in payload]
    if isinstance(payload, dict) and "rows" in payload:
        rows = payload["rows"]
        if not isinstance(rows, list):
            raise ValueError("rows payload must be a list")
        return [_unwrap_row(item) for item in rows]
    if isinstance(payload, dict):
        return [_unwrap_row(payload)]
    raise ValueError("unsupported Hugging Face rows payload")


def fetch_hf_first_rows(
    adapter_id: str,
    *,
    config: str | None = None,
    split: str | None = None,
    length: int = 8,
    token: str | None = None,
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    spec = get_hf_adapter_spec(adapter_id)
    query = urlencode(
        {
            "dataset": spec.dataset_name,
            "config": config or spec.default_config,
            "split": split or spec.default_split,
        }
    )
    request = Request(f"https://datasets-server.huggingface.co/first-rows?{query}")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
    rows = load_hf_rows_payload(payload)
    return rows[:length]


def load_hf_rows_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise ValueError("rows payload must be a list")
    return [_unwrap_row(item) for item in rows]


def adapt_hf_rows(adapter_id: str, rows: list[dict[str, Any]]) -> list[Scenario]:
    adapter = {
        "hf_conversation_bench": adapt_conversation_bench_row,
        "hf_qasper": adapt_qasper_row,
        "hf_swe_bench_verified": adapt_swe_bench_verified_row,
        "hf_taskbench": adapt_taskbench_row,
    }.get(adapter_id)
    if adapter is None:
        raise ValueError(f"unsupported adapter: {adapter_id}")
    return [adapter(row, index=index) for index, row in enumerate(rows, start=1)]


def load_and_adapt_hf_rows(adapter_id: str, path: str | Path) -> list[Scenario]:
    return adapt_hf_rows(adapter_id, load_hf_rows_file(path))


def fetch_and_adapt_hf_rows(
    adapter_id: str,
    *,
    config: str | None = None,
    split: str | None = None,
    length: int = 8,
    token: str | None = None,
) -> list[Scenario]:
    rows = fetch_hf_first_rows(adapter_id, config=config, split=split, length=length, token=token)
    return adapt_hf_rows(adapter_id, rows)


def get_hf_adapter_spec(adapter_id: str) -> HuggingFaceAdapterSpec:
    if adapter_id not in ADAPTER_SPECS:
        raise ValueError(f"unsupported adapter: {adapter_id}")
    return ADAPTER_SPECS[adapter_id]


def adapt_taskbench_row(row: dict[str, Any], *, index: int) -> Scenario:
    instruction = str(row.get("instruction", "")).strip()
    scenario_id = f"hf_taskbench_{row.get('id', index)}"
    tool_steps = [str(item) for item in _as_list(row.get("tool_steps"))]
    tool_nodes = _parse_tool_nodes(row.get("tool_nodes", row.get("sampled_nodes", [])))
    dependency_links = _parse_links(row.get("tool_links", row.get("sampled_links", [])))
    first_task = tool_nodes[0]["task"] if tool_nodes else "tool"
    last_step = tool_steps[-1] if tool_steps else f"Finish the {first_task} flow in dependency order."
    dependency_text = dependency_links[0] if dependency_links else "follow the listed tool order"
    source_refs = [item["task"] for item in tool_nodes if item.get("task")]
    focus_keywords = _keywords_from_text(last_step)
    return Scenario(
        scenario_id=scenario_id,
        title="Hugging Face TaskBench tool-use task",
        domain="tool_use",
        goal=instruction,
        interruption_point="The public task was converted into an interrupted planning trace for onboarding.",
        events=[
            TaskEvent(sequence=1, actor="user", text=f"Goal: {instruction}"),
            TaskEvent(sequence=2, actor="assistant", text=f"Plan: {' '.join(tool_steps[:2]) or 'Inspect the tool graph and plan the safe order.'}"),
            TaskEvent(sequence=3, actor="assistant", text=f"Guardrail: Keep the dependency order intact: {dependency_text}."),
            TaskEvent(
                sequence=4,
                actor="assistant",
                text=f"Evidence: Available tools include {', '.join(source_refs[:3]) or first_task}.",
            ),
            TaskEvent(sequence=5, actor="assistant", text=f"Focus: {last_step}"),
            TaskEvent(sequence=6, actor="assistant", text="Assumption: The tool graph remains valid for the next run."),
        ],
        expected_items=[
            ExpectedItem(name="goal_guard", category="goal", keywords=_keywords_from_text(instruction)),
            ExpectedItem(name="keep_dependency_rule", category="constraint", keywords=_keywords_from_text(dependency_text)),
            ExpectedItem(name="keep_current_focus", category="current_focus", keywords=focus_keywords),
            ExpectedItem(name="keep_source_tools", category="source", keywords=[first_task]),
        ],
    )


def adapt_swe_bench_verified_row(row: dict[str, Any], *, index: int) -> Scenario:
    problem_statement = str(row.get("problem_statement", "")).strip()
    scenario_id = f"hf_swe_bench_verified_{row.get('instance_id', index)}"
    repo = str(row.get("repo", "unknown/repo"))
    base_commit = str(row.get("base_commit", "unknown"))
    hints_text = str(row.get("hints_text", "")).strip()
    failing_tests = [str(item) for item in _as_list(row.get("FAIL_TO_PASS"))]
    protected_tests = [str(item) for item in _as_list(row.get("PASS_TO_PASS"))]
    focus_text = f"Inspect {failing_tests[0]} before changing any code." if failing_tests else "Inspect the failing tests before patching."
    guardrail_text = (
        f"Keep these existing behaviors green: {protected_tests[0]}."
        if protected_tests
        else "Keep existing passing tests green while fixing the bug."
    )
    evidence_text = f"{repo} at {base_commit}"
    return Scenario(
        scenario_id=scenario_id,
        title="Hugging Face SWE-bench Verified issue",
        domain="coding",
        goal=problem_statement,
        interruption_point="The public issue was converted into an interrupted repair trace for onboarding.",
        events=[
            TaskEvent(sequence=1, actor="user", text=f"Goal: {problem_statement}"),
            TaskEvent(sequence=2, actor="assistant", text="Plan: Read the issue, inspect the failing tests, patch the smallest safe area, rerun the target checks."),
            TaskEvent(sequence=3, actor="assistant", text=f"Guardrail: {guardrail_text}"),
            TaskEvent(
                sequence=4,
                actor="assistant",
                text=f"Evidence: Base repo snapshot is {evidence_text}.",
            ),
            TaskEvent(sequence=5, actor="assistant", text=f"Focus: {focus_text}"),
            TaskEvent(sequence=6, actor="assistant", text=f"Observation: {hints_text or 'The issue statement is the main source of truth.'}"),
        ],
        expected_items=[
            ExpectedItem(name="goal_guard", category="goal", keywords=_keywords_from_text(problem_statement)),
            ExpectedItem(name="protect_existing_tests", category="constraint", keywords=_keywords_from_text(guardrail_text)),
            ExpectedItem(name="keep_current_focus", category="current_focus", keywords=_keywords_from_text(focus_text)),
            ExpectedItem(name="keep_source_snapshot", category="source", keywords=[repo]),
        ],
    )


def adapt_qasper_row(row: dict[str, Any], *, index: int) -> Scenario:
    title = str(row.get("title", f"paper-{index}"))
    question = _qasper_question(row)
    evidence = _qasper_evidence(row)
    abstract = _qasper_abstract(row)
    scenario_id = f"hf_qasper_{row.get('id', index)}"
    focus_text = f"Inspect the cited evidence for the question: {question}"
    return Scenario(
        scenario_id=scenario_id,
        title="Hugging Face QASPER paper question",
        domain="research",
        goal=f"Answer the paper question using evidence from {title}: {question}",
        interruption_point="The public paper question was converted into an interrupted evidence-grounded trace for onboarding.",
        events=[
            TaskEvent(sequence=1, actor="user", text=f"Goal: Answer the paper question using evidence from {title}: {question}"),
            TaskEvent(sequence=2, actor="assistant", text="Plan: Read the abstract, inspect the cited evidence, and answer only what the paper supports."),
            TaskEvent(sequence=3, actor="assistant", text="Guardrail: Do not answer beyond cited paper evidence."),
            TaskEvent(sequence=4, actor="assistant", text=f"Evidence: {title} evidence says {evidence}"),
            TaskEvent(sequence=5, actor="assistant", text=f"Focus: {focus_text}"),
            TaskEvent(sequence=6, actor="assistant", text=f"Observation: {abstract}"),
        ],
        expected_items=[
            ExpectedItem(name="goal_guard", category="goal", keywords=_keywords_from_text(question)),
            ExpectedItem(name="protect_evidence_boundary", category="constraint", keywords=["cited", "evidence"]),
            ExpectedItem(name="keep_current_focus", category="current_focus", keywords=_keywords_from_text(focus_text)),
            ExpectedItem(name="keep_source_title", category="source", keywords=_keywords_from_text(title, count=1)),
        ],
    )


def adapt_conversation_bench_row(row: dict[str, Any], *, index: int) -> Scenario:
    turn_id = row.get("turn_id", index)
    input_text = str(row.get("input_text", "")).strip()
    golden_text = str(row.get("golden_text", "")).strip()
    categories = [str(item) for item in _as_list(row.get("categories"))]
    scoring_dimensions = [str(item) for item in _as_list(row.get("scoring_dimensions"))]
    required_calls = _parse_function_calls(row.get("required_function_call"))
    call_names = [call["name"] for call in required_calls if call.get("name")]
    scenario_id = f"hf_conversation_bench_{turn_id}"
    goal = f"Handle the user turn correctly and preserve prior conversation state: {input_text}"
    plan_text = (
        "Listen to the turn, check prior state, decide whether a tool is needed, and answer in a way that stays grounded in the session."
    )
    guardrail_bits: list[str] = []
    if "long_range_memory" in categories or "state_tracking" in scoring_dimensions:
        guardrail_bits.append("Preserve the earlier conversation state and registrations.")
    if call_names:
        guardrail_bits.append(f"Only call the required tool flow when needed: {call_names[0]}.")
    if not guardrail_bits:
        guardrail_bits.append("Stay grounded in the current turn and known session state.")
    guardrail_text = " ".join(guardrail_bits)
    source_label = str(row.get("audio_file", f"turn_{turn_id}"))
    evidence_text = (
        f"Source turn {source_label}: {golden_text}"
        if golden_text
        else f"Source turn {source_label}: The golden response is the best available evidence for this turn."
    )
    focus_text = _conversation_focus_text(input_text, call_names)
    expected_keywords = _keywords_from_text(focus_text)
    source_keywords = call_names[:1] or _keywords_from_text(source_label, count=1)
    return Scenario(
        scenario_id=scenario_id,
        title="Hugging Face ConversationBench turn",
        domain="conversation",
        goal=goal,
        interruption_point="The public multi-turn benchmark turn was converted into an interrupted conversation-state trace for onboarding.",
        events=[
            TaskEvent(sequence=1, actor="user", text=f"Goal: {goal}"),
            TaskEvent(sequence=2, actor="assistant", text=f"Plan: {plan_text}"),
            TaskEvent(sequence=3, actor="assistant", text=f"Guardrail: {guardrail_text}"),
            TaskEvent(sequence=4, actor="assistant", text=f"Evidence: {evidence_text}"),
            TaskEvent(sequence=5, actor="assistant", text=f"Focus: {focus_text}"),
            TaskEvent(sequence=6, actor="assistant", text=f"Observation: Categories include {', '.join(categories) or 'none'} and scoring dimensions include {', '.join(scoring_dimensions) or 'none'}."),
        ],
        expected_items=[
            ExpectedItem(name="goal_guard", category="goal", keywords=_keywords_from_text(input_text)),
            ExpectedItem(name="preserve_state_guardrail", category="constraint", keywords=_keywords_from_text(guardrail_text)),
            ExpectedItem(name="keep_current_focus", category="current_focus", keywords=expected_keywords),
            ExpectedItem(name="keep_turn_source", category="source", keywords=source_keywords),
        ],
    )


def _unwrap_row(item: Any) -> dict[str, Any]:
    if isinstance(item, dict) and "row" in item and isinstance(item["row"], dict):
        return dict(item["row"])
    if isinstance(item, dict):
        return dict(item)
    raise ValueError("row entries must be objects")


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value]
        return parsed if isinstance(parsed, list) else [parsed]
    return [value]


def _parse_tool_nodes(value: Any) -> list[dict[str, Any]]:
    nodes = _as_list(value)
    parsed: list[dict[str, Any]] = []
    for node in nodes:
        if isinstance(node, dict):
            parsed.append(node)
    return parsed


def _parse_links(value: Any) -> list[str]:
    links = _as_list(value)
    parsed: list[str] = []
    for link in links:
        if isinstance(link, dict):
            source = str(link.get("source", "")).strip()
            target = str(link.get("target", "")).strip()
            if source and target:
                parsed.append(f"{source} before {target}")
    return parsed


def _parse_function_calls(value: Any) -> list[dict[str, Any]]:
    calls = _as_list(value)
    parsed: list[dict[str, Any]] = []
    for call in calls:
        if isinstance(call, dict):
            normalized_name = str(call.get("name") or call.get("task") or "").strip()
            if normalized_name:
                parsed.append({"name": normalized_name})
    return parsed


def _qasper_question(row: dict[str, Any]) -> str:
    if "question" in row:
        return str(row["question"])
    qas = row.get("qas")
    if isinstance(qas, dict):
        questions = qas.get("question")
        if isinstance(questions, list) and questions:
            return str(questions[0])
    return "What does the paper claim?"


def _qasper_abstract(row: dict[str, Any]) -> str:
    abstract = row.get("abstract")
    if isinstance(abstract, str):
        return abstract
    if isinstance(abstract, list):
        parts = [str(item) for item in abstract if str(item).strip()]
        return " ".join(parts[:2])
    return "Read the paper abstract before finalizing the answer."


def _qasper_evidence(row: dict[str, Any]) -> str:
    if "evidence" in row and isinstance(row["evidence"], str):
        return row["evidence"]
    qas = row.get("qas")
    if not isinstance(qas, dict):
        return "No evidence snippet was included."
    answers = qas.get("answers")
    if not isinstance(answers, list) or not answers:
        return "No evidence snippet was included."
    first_answer_group = answers[0]
    if isinstance(first_answer_group, dict):
        answer_entries = first_answer_group.get("answer", [])
        if isinstance(answer_entries, list) and answer_entries:
            first_answer = answer_entries[0]
            if isinstance(first_answer, dict):
                evidence = first_answer.get("evidence") or first_answer.get("highlighted_evidence")
                if isinstance(evidence, list) and evidence:
                    return str(evidence[0])
    return "No evidence snippet was included."


def _conversation_focus_text(input_text: str, call_names: list[str]) -> str:
    if call_names:
        return f"Decide whether to use {call_names[0]} while preserving earlier conversation state."
    return f"Answer the user turn while preserving earlier conversation state: {input_text}"


def _keywords_from_text(text: str, count: int = 2) -> list[str]:
    words: list[str] = []
    seen: set[str] = set()
    for raw_word in text.replace("/", " ").replace("_", " ").split():
        word = raw_word.strip(" ,.;:()[]{}'\"").lower()
        if len(word) < 4 or word in STOP_WORDS or word.isdigit() or word in seen:
            continue
        seen.add(word)
        words.append(word)
        if len(words) >= count:
            break
    return words or [text[: min(len(text), 24)].strip()]
