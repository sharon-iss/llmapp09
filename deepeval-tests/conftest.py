"""
Shared fixtures and configuration for deepeval LLM evaluation tests.

Uses Ollama Cloud (glm-5.2) as the judge LLM instead of OpenAI.
"""

import os

from openai import OpenAI
from deepeval.metrics import GEval
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCaseParams


OLLAMA_CLOUD_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com").rstrip("/")
OLLAMA_CLOUD_MODEL = os.getenv("DEEPEVAL_JUDGE_MODEL", "glm-5.2")


class OllamaCloudJudge(DeepEvalBaseLLM):
    """DeepEval judge backed by Ollama Cloud's OpenAI-compatible API."""

    def __init__(
        self,
        model: str = OLLAMA_CLOUD_MODEL,
        base_url: str = OLLAMA_CLOUD_BASE_URL,
        api_key: str | None = None,
    ):
        self.model_name = model
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "OLLAMA_API_KEY is required for DeepEval Ollama Cloud judge. "
                "Set it in the environment before running tests."
            )
        # OpenAI-compatible chat endpoint lives under /v1
        self.base_url = f"{base_url}/v1" if not base_url.endswith("/v1") else base_url
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def load_model(self):
        return self.client

    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content or ""

    async def a_generate(self, prompt: str, **kwargs) -> str:
        return self.generate(prompt, **kwargs)

    def get_model_name(self) -> str:
        return f"ollama-cloud/{self.model_name}"


judge = OllamaCloudJudge()


# ---------------------------------------------------------------------------
# Reusable GEval metric factories
# ---------------------------------------------------------------------------

def json_schema_metric(schema_description: str):
    """Creates a GEval metric that checks JSON schema compliance."""
    return GEval(
        name="JSON Schema Compliance",
        criteria=(
            "Evaluate whether the actual output is valid JSON that conforms to "
            "the required schema. Only check structure, key names, and data "
            "types — do NOT penalize for specific values. "
            + schema_description
        ),
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=0.5,
        model=judge,
    )


def output_correctness_metric():
    """Creates a GEval metric that checks factual/logical correctness."""
    return GEval(
        name="Output Correctness",
        criteria=(
            "Determine whether the actual output is logically correct and "
            "reasonable given the input text. The analysis should make sense "
            "for the provided input."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=0.5,
        model=judge,
    )


def answer_relevancy_metric():
    """Creates a GEval metric that checks whether the output is topically
    relevant to the input.  Unlike AnswerRelevancyMetric (which assumes a
    Q&A format), this works for classification and analysis endpoints where
    the output is structured metadata about the input text."""
    return GEval(
        name="Answer Relevancy",
        criteria=(
            "Evaluate whether the actual output is a relevant analysis of the "
            "input text for an NLP API (classify, sentiment, summarize, or "
            "intent). Structured JSON metadata — including overallSentiment, "
            "emotions, confidence, labels, categories, or summaries — that "
            "describes or analyzes the input MUST be scored as relevant, even "
            "when the input is factual/neutral (e.g. a meeting reminder) and "
            "the result is overallSentiment=neutral with an empty emotions "
            "list. Only score low if the output is off-topic, unrelated to "
            "the input, or not analysis of that text."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=0.4,
        model=judge,
    )
