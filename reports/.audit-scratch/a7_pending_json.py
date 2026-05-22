"""A7 - Pending decisions JSON."""
import json
from pathlib import Path

OUT = Path("c:/dev/rdm/dev/discussion/reports")


def main() -> None:
    data = {
        "generated_at": "2026-05-22",
        "sources": [
            "rdm-bot/STATE.md §G",
            "rdm-bot/OPEN_QUESTIONS.md",
            "rdm-discussion/STATE.md §E",
            "rdm-discussion/QUESTIONS.md",
            "rdm-platform/STATE.md §C",
            "threads/145..176",
        ],
        "summary_counts": {
            "rdm-bot_STATE_G": 7,
            "rdm-bot_OPEN_QUESTIONS_historical_PR1_PR3": 28,
            "rdm-discussion_STATE_E": 7,
            "rdm-discussion_QUESTIONS_alex_queue": 10,
            "rdm-discussion_QUESTIONS_cc_queue": 10,
            "rdm-discussion_QUESTIONS_research_queue": 6,
            "rdm-platform_STATE_C": 11,
            "net_pending_after_dedupe": 38,
            "audience_alex_share": "~25/38",
        },
        "bot_state_G": [
            {"id": "G1", "topic": "A5 Airbnb bulk-approve writeback 67%", "owner": "Alex", "category": "provisioning", "blocks": "A5 100% completion"},
            {"id": "G2", "topic": "Browserbase AirBnB KPI scraper", "owner": "Alex", "category": "business", "blocks": "scraper start"},
            {"id": "G3", "topic": "A6 reglas_adicionales deploy PR #130 review", "owner": "Alex", "category": "business", "blocks": "merge"},
            {"id": "G4", "topic": "Journey templates editor PR #114", "owner": "Alex", "category": "business", "blocks": "merge"},
            {"id": "G5", "topic": "Casa Chamán renovation timeline", "owner": "Alex", "category": "business", "blocks": "Greeter content"},
            {"id": "G6", "topic": "PDF endpoint removal spec for CC", "owner": "WC drafts -> CC executes", "category": "technical", "blocks": "cleanup"},
            {"id": "G7", "topic": "F1/F2/F3 foundations + ADR-002 vote thread/148", "owner": "Alex", "category": "business+technical", "blocks": "M1 Pricing start"},
            {"id": "G8", "topic": "Analytics activation thread/149", "owner": "Alex", "category": "business+provisioning", "blocks": "tracker emit, GA4 readout"},
            {"id": "G9", "topic": "Migration 0039 collision rename", "owner": "n/a", "category": "RESOLVED 2026-05-21 PR #140"},
        ],
        "discussion_state_E_net_new": [
            {"id": "D5", "topic": "Canary HSM critical path thread/123 - defer + cancel-race", "owner": "Alex"},
        ],
        "platform_state_C": [
            {"id": "P1", "topic": "ADR-002 charter / foundations seal", "status": "Accepted 2026-05-20"},
            {"id": "P2", "topic": "F1 events bus implementation", "effort": "12-16h CC", "status": "spec accepted; NOT started"},
            {"id": "P3", "topic": "F2 observability lite implementation", "effort": "6-9h CC", "status": "spec accepted; NOT started"},
            {"id": "P4", "topic": "F3 staff PWA shell implementation", "effort": "22-30h CC", "status": "spec accepted; NOT started"},
            {"id": "P5", "topic": "M1 Pricing Agent deep spec", "status": "not started, blocked by P2-P4"},
            {"id": "P6", "topic": "M2 Menu spec"},
            {"id": "P7", "topic": "M3 Inventory spec"},
            {"id": "P8", "topic": "M4 Staff scheduling spec", "depends_on": "F3"},
            {"id": "P9", "topic": "M5 Tasks module spec"},
            {"id": "P10", "topic": "Casa Chamán launch coordinator spec", "trigger": "Q3 2026"},
            {"id": "P11", "topic": "I1-I19 ideas expansion"},
        ],
        "questions_alex_queue_status": [
            {"id": "A1", "status": "resolved (rdm-bot private, rdm-discussion public)"},
            {"id": "A2", "topic": "PriceLabs", "status": "SUPERSEDED — custom agent kept; ADR-03 not updated"},
            {"id": "A3", "status": "partly answered (work happening, slower than plan)"},
            {"id": "A4", "topic": "WABA propia Stage 2", "status": "OPEN"},
            {"id": "A5", "topic": "Pricing override Stage 2", "status": "OPEN"},
            {"id": "A6", "status": "resolved YES — Better Auth shipped"},
            {"id": "A7", "status": "resolved — 7 roles per PR #129"},
            {"id": "A8", "topic": "APK timing", "status": "OPEN — PWA not delivered"},
            {"id": "A9", "topic": "Sunset ManyChat", "status": "OPEN — Stage 2 dependent"},
            {"id": "A10", "topic": "Domain destinations", "status": "partly resolved; admin.r.club not realized"},
        ],
        "open_questions_bot_net_pending": [
            "Q3 R2 + Knowledge_Refresh_v2 (partially resolved)",
            "Q4 Photos pipeline real fotos",
            "Q6 Turnstile sitekey + secret",
            "Q7 CF Web Analytics token (= G8)",
            "Q8 CF Images hash",
            "Q10 Lighthouse CI ≥ 95",
            "Q17 Account merge UI (never implemented)",
            "Q19 EN translations review by Alex",
        ],
        "critical_path": [
            {"item": "F2 ship (G7/P3)", "blocks": ["F1 ship", "F3 ship", "M1 Pricing", "M5 Tasks", "F2.1 daily digest"]},
            {"item": "F1 ship (G7/P2)", "blocks": ["M1 dispatcher", "M5 notifications", "I3/I5/I7/I8"]},
            {"item": "F3 ship (G7/P4)", "blocks": ["M3/M4/M5", "Casa Chamán launch coord"]},
            {"item": "Analytics activation (G8/Q7)", "blocks": ["A/B test readout", "GA4 events", "conversion tracking", "GSC verify"]},
            {"item": "PDF endpoint removal spec (G6)", "blocks": ["cleanup, prevents bad-PR loop"]},
            {"item": "A5 Airbnb session + writeback (G1)", "blocks": ["content sync to Airbnb"]},
            {"item": "Stage 2 ManyChat sunset (A9/decisions-02)", "blocks": ["A4 WABA", "A5 pricing override Stage 2"]},
        ],
        "stale_items_gt_30d": [],  # none — repo is only 12 days old
        "recommendations": [
            "Resolve G7 (Alex vote on thread/148) — gates foundations + M1 path.",
            "Close G6 (PDF removal spec) — WC drafts, CC executes, 1 PR.",
            "Resolve G8 (analytics activation) — Alex picks variant; 1h CC ship.",
            "Archive rdm-bot/OPEN_QUESTIONS.md as docs/archive/OPEN_QUESTIONS-2026-05-08-PR1-PR3.md.",
            "Update decisions/03 (PriceLabs) status — mark superseded.",
            "Add an Anti-pattern ADR for 'WC does not implement code in rdm-bot/rdm-platform'.",
        ],
    }
    (OUT / "2026-05-22-META-A7-pending-decisions.json").write_text(
        json.dumps(data, indent=2, default=str), encoding="utf-8"
    )
    print("A7 JSON done")


if __name__ == "__main__":
    main()
