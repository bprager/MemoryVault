from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PublicDataLead:
    dataset_id: str
    name: str
    focus: str
    why_it_fits: str
    how_to_use_it: str
    url: str


PUBLIC_DATA_LEADS: list[PublicDataLead] = [
    PublicDataLead(
        dataset_id="hf_swe_bench_verified",
        name="Hugging Face: SWE-bench Verified",
        focus="Public coding issues with test-based outcomes",
        why_it_fits=(
            "Useful for tool development because it gives clean public tasks with problem statements, repository state, "
            "and pass/fail tests without assuming private production data."
        ),
        how_to_use_it=(
            "Turn each issue into several interrupted checkpoints: after issue reading, after repo inspection, "
            "after the first failed patch, and before the final patch."
        ),
        url="https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified",
    ),
    PublicDataLead(
        dataset_id="hf_swe_agent_trajectories",
        name="Hugging Face: SWE-agent trajectories",
        focus="Full public agent runs over software tasks",
        why_it_fits=(
            "Useful because it contains full agent histories, failed runs, patches, and test logs. That makes it a strong source "
            "for interrupted-task replay without needing your own production traces."
        ),
        how_to_use_it=(
            "Slice each trajectory into interruption points and test whether the tool rebuilds the right next-step memory package."
        ),
        url="https://huggingface.co/datasets/nebius/SWE-agent-trajectories",
    ),
    PublicDataLead(
        dataset_id="hf_taskbench",
        name="Hugging Face: TaskBench",
        focus="Tool-use plans, decomposition, and action graphs",
        why_it_fits=(
            "Strong fit for a domain-agnostic tool because it covers different tool graphs and user instructions instead of one narrow workflow."
        ),
        how_to_use_it=(
            "Convert each instruction and tool graph into a multi-step interrupted trace, then test whether the tool remembers the plan, "
            "dependencies, and next action."
        ),
        url="https://huggingface.co/datasets/microsoft/Taskbench",
    ),
    PublicDataLead(
        dataset_id="hf_longmemeval_cleaned",
        name="Hugging Face: LongMemEval cleaned",
        focus="Long-horizon conversational memory",
        why_it_fits=(
            "Direct fit for testing goal drift, changing facts, and long-session continuity with public data."
        ),
        how_to_use_it=(
            "Pause the conversation history at several points and ask whether the tool preserves the right user state, preferences, and recent corrections."
        ),
        url="https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned",
    ),
    PublicDataLead(
        dataset_id="hf_conversation_bench",
        name="Hugging Face: conversation-bench",
        focus="Multi-turn dialogue with tool use and long-range memory checks",
        why_it_fits=(
            "Useful for a zero-domain tool because it mixes ordinary dialogue, tool actions, long-range memory, ambiguity, and adversarial turns."
        ),
        how_to_use_it=(
            "Use the turn schema and golden answers to create interruption points and score whether the resume packet restores the right user and task state."
        ),
        url="https://huggingface.co/datasets/arcada-labs/conversation-bench",
    ),
    PublicDataLead(
        dataset_id="hf_qasper",
        name="Hugging Face: QASPER",
        focus="Evidence-grounded document tasks",
        why_it_fits=(
            "Useful because it tests whether the tool keeps source links and evidence when the task depends on long documents."
        ),
        how_to_use_it=(
            "Treat each paper question as a resume task: pause after partial reading, then score whether the tool preserves the right evidence trail."
        ),
        url="https://huggingface.co/datasets/allenai/qasper",
    ),
    PublicDataLead(
        dataset_id="hf_multi_xscience",
        name="Hugging Face: Multi-XScience",
        focus="Multi-source synthesis and cross-document memory",
        why_it_fits=(
            "Useful because the tool must keep track of relationships across several source documents rather than just one context."
        ),
        how_to_use_it=(
            "Use it to test whether interrupted synthesis tasks preserve source coverage, open comparisons, and evidence grouping."
        ),
        url="https://huggingface.co/datasets/bigbio/multi_xscience",
    ),
    PublicDataLead(
        dataset_id="hf_hotpot_qa",
        name="Hugging Face: HotpotQA",
        focus="Multi-hop evidence retrieval",
        why_it_fits=(
            "Good generic test for whether the tool remembers linked evidence and intermediate facts across interruption points."
        ),
        how_to_use_it=(
            "Pause after the first supporting document and test whether the tool retains the missing link needed to finish the answer."
        ),
        url="https://huggingface.co/datasets/hotpotqa/hotpot_qa",
    ),
]


def list_public_data() -> list[PublicDataLead]:
    return PUBLIC_DATA_LEADS
