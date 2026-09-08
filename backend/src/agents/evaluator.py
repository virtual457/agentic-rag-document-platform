from __future__ import annotations

import json
import re

from src.agents.state import AgentState
from src.config import get_settings
from src.llm import get_llm


def _keyword_score(query: str, answer: str) -> float:
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "of", "for", "and", "or",
        "to", "in", "on", "with", "by", "as", "at", "it", "that", "this", "be",
        "what", "how", "why", "when", "where", "who", "which", "do", "does", "did",
    }
    q = {t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 2 and t not in stopwords}
    a = {t for t in re.findall(r"[a-z0-9]+", answer.lower())}
    if not q:
        return 35.0
    return round(35.0 * len(q & a) / len(q), 2)


_LLM_PROMPT = """Score the answer out of 65:
- 25 relevance
- 20 completeness
- 15 clarity
- 5 citations present

Query: {q}

Answer: {a}

Retrieved context:
{c}

JSON only: {{"score": <0-65>, "reasoning": "..."}}
"""


async def evaluator_node(state: AgentState) -> AgentState:
    settings = get_settings()
    answer = state.get("draft_answer", "")
    context = state.get("context", "")
    kw = _keyword_score(state["query"], answer)
    llm = get_llm()
    text = await llm.chat(_LLM_PROMPT.format(q=state["query"], a=answer, c=context[:6000]), temperature=0.0)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    llm_score = 40.0
    reasoning = "parse-fallback"
    if m:
        try:
            d = json.loads(m.group(0))
            llm_score = float(min(65, max(0, int(d.get("score", 40)))))
            reasoning = str(d.get("reasoning", ""))
        except Exception:
            pass
    total = round(kw + llm_score, 2)
    round_no = len(state.get("eval_rounds", [])) + 1
    r = {
        "round": round_no,
        "keyword_score": kw,
        "llm_score": llm_score,
        "total_score": total,
        "passed": total >= settings.quality_threshold,
        "reasoning": reasoning,
    }
    return {
        "eval_rounds": state.get("eval_rounds", []) + [r],
        "final_score": max(state.get("final_score", 0.0), total),
        "events": state.get("events", []) + [
            {
                "type": "eval_round",
                "round": round_no,
                "score": total,
                "passed": r["passed"],
                "label": f"Evaluation round {round_no}: {total}/100 ({'passed gate' if r['passed'] else 'below gate, will retry'})",
            }
        ],
    }
