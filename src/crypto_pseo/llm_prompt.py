from __future__ import annotations

import json
from typing import Any


JsonDict = dict[str, Any]


BLOG_POST_SCHEMA: JsonDict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "h1_title",
        "meta_description",
        "target_keyword",
        "html_content",
        "schema_markup",
        "winner_verdict",
    ],
    "properties": {
        "h1_title": {"type": "string"},
        "meta_description": {"type": "string", "maxLength": 158},
        "target_keyword": {"type": "string"},
        "html_content": {
            "type": "string",
            "description": "HTML content with H2/H3 sections and comparison tables. No Markdown fences.",
        },
        "schema_markup": {
            "type": "string",
            "description": "A valid JSON-LD string, preferably FAQPage for comparison posts.",
        },
        "winner_verdict": {
            "type": "string",
            "description": "Clear verdict explaining which user type should choose each platform.",
        },
    },
}


def build_llm_prompt_package(brief: JsonDict) -> JsonDict:
    """Build a provider-agnostic prompt package for a structured-output writer."""

    system_prompt = _system_prompt(brief)
    user_payload = _user_payload(brief)
    return {
        "provider_notes": {
            "openai": "Use this as system/developer instructions plus the user payload. Request JSON matching output_schema.",
            "anthropic": "Use system_prompt as the system message and user_payload as the user message. Ask for only valid JSON.",
            "gemini": "Use system_prompt as instructions and user_payload as contents. Enforce JSON schema if available.",
        },
        "system_prompt": system_prompt,
        "user_payload": user_payload,
        "output_schema_name": "BlogPostStructure",
        "output_schema": BLOG_POST_SCHEMA,
        "editorial_gate": brief["editorial_gate"],
    }


def _system_prompt(brief: JsonDict) -> str:
    persona = brief["persona"]
    forbidden = "\n".join(f"- {phrase}" for phrase in persona.get("forbidden_phrases", []))
    rules = "\n".join(f"- {rule}" for rule in persona.get("rules", []))
    required_sections = "\n".join(f"- {section.replace('_', ' ')}" for section in brief["editorial_gate"].get("required_sections", []))
    return f"""You are {persona['name']}.

Write as a skeptical crypto analyst: objective, consumer-first, data-driven, and zero-hyperbole.

Core rules:
{rules}

Forbidden phrases:
{forbidden}

Required sections:
{required_sections}

Output only valid JSON matching BlogPostStructure. Do not wrap the JSON in Markdown. Do not invent facts, bonuses, fees, regions, or source URLs. Use the computed insights as the article's analytical spine."""


def _user_payload(brief: JsonDict) -> JsonDict:
    return {
        "task": "Generate a publishable crypto affiliate comparison article.",
        "job": brief["job"],
        "platforms": brief["platforms"],
        "information_gain": brief["information_gain"],
        "required_output_schema": brief["required_output_schema"],
        "writing_requirements": [
            "Lead with the practical verdict.",
            "Treat headline bonuses as marketing until requirements are explained.",
            "Use realistic bonus value before headline value.",
            "Include a comparison table in html_content.",
            "Include source notes or claim caveats in html_content.",
            "Do not overstate certainty when a claim depends on promotion terms or expiry.",
            "Avoid generic SEO filler introductions.",
        ],
        "example_output_shape": {
            "h1_title": "string",
            "meta_description": "string",
            "target_keyword": brief["job"]["target_keyword"],
            "html_content": "<h2>Quick Verdict</h2>...",
            "schema_markup": json.dumps({"@context": "https://schema.org", "@type": "FAQPage"}, ensure_ascii=False),
            "winner_verdict": "string",
        },
    }
