import os
import json
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL  = "llama3-70b-8192"


def classify_and_summarize(email: dict) -> dict:
    """
    Returns dict with keys: priority, summary
    priority: 'HIGH' | 'MEDIUM' | 'LOW'
    summary: one-line TL;DR
    """
    prompt = f"""You are an expert email triage assistant. Analyze the following email and respond ONLY with valid JSON.

Email Details:
- Subject: {email.get('subject', '')}
- From: {email.get('sender_name', '')} <{email.get('sender_email', '')}>
- Preview: {email.get('body_preview', '')}
- Body (truncated): {email.get('full_body', '')[:1500]}

Classify this email and respond with this exact JSON structure:
{{
  "priority": "HIGH" | "MEDIUM" | "LOW",
  "summary": "one sentence TL;DR of what this email is about and what action (if any) is needed",
  "reason": "one sentence explaining why this priority was assigned"
}}

Priority Guidelines:
- HIGH: Requires urgent action or response, time-sensitive, from important sender (boss, client, payment, security alert, deadline)
- MEDIUM: Important but not urgent, FYI updates, meeting invites, requires response but not immediately
- LOW: Newsletters, marketing, automated notifications, social updates, promotional emails, no action needed

Respond with ONLY the JSON object, no other text."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)
        return {
            "priority": data.get("priority", "MEDIUM"),
            "summary":  data.get("summary", "No summary available."),
            "reason":   data.get("reason", ""),
        }
    except Exception as e:
        return {
            "priority": "MEDIUM",
            "summary":  "Could not generate summary.",
            "reason":   str(e),
        }


def batch_classify(emails: list[dict], progress_callback=None) -> list[dict]:
    """Process a list of emails, returning enriched dicts."""
    results = []
    for i, email in enumerate(emails):
        enriched = {**email}
        result = classify_and_summarize(email)
        enriched.update(result)
        results.append(enriched)
        if progress_callback:
            progress_callback(i + 1, len(emails))
    return results
