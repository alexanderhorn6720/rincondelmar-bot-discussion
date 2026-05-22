# A3 — Migrations inventory

**Repo**: rdm-bot, path `migrations/`
**Total migrations**: 45
**Highest number**: 45
**Missing numbers (gaps in sequence)**: none
**Active filename collisions**: 0

## Migrations table

| # | Filename | Topic | Size | First commit | Hash |
|---|---|---|---|---|---|
| 1 | 0001_users_sessions.sql | users_sessions | 3686 | 2026-05-08 | f46e3949a6c0 |
| 2 | 0002_magic_links.sql | magic_links | 943 | 2026-05-08 | 6067967ffa6a |
| 3 | 0003_waitlist.sql | waitlist | 612 | 2026-05-08 | b44a7a222eff |
| 4 | 0004_bookings.sql | bookings | 2419 | 2026-05-08 | a24d158c4686 |
| 5 | 0005_quote_requests.sql | quote_requests | 964 | 2026-05-08 | 1da368b96248 |
| 6 | 0006_linktree_clicks.sql | linktree_clicks | 1137 | 2026-05-09 | fe73a0fe66e4 |
| 7 | 0007_sessions_updated_at.sql | sessions_updated_at | 566 | 2026-05-09 | 500dcec620a6 |
| 8 | 0008_tour_views.sql | tour_views | 1144 | 2026-05-10 | 70e7161159e4 |
| 9 | 0009_conversations.sql | conversations | 1267 | 2026-05-11 | 44c0e9dcd62c |
| 10 | 0010_handoff_data.sql | handoff_data | 854 | 2026-05-11 | ba17b69b18b2 |
| 11 | 0011_beds24_events.sql | beds24_events | 2694 | 2026-05-12 | 1e44ad2b7c7a |
| 12 | 0012_reviews.sql | reviews | 2589 | 2026-05-12 | 3ede5b7c2bbd |
| 13 | 0013_bot_messages_inbox.sql | bot_messages_inbox | 2902 | 2026-05-12 | f555a6ee84c1 |
| 14 | 0014_guests_master.sql | guests_master | 6312 | 2026-05-13 | 393aa726d936 |
| 15 | 0015_leads.sql | leads | 7537 | 2026-05-13 | 4ee2a50839d4 |
| 16 | 0016_bookings.sql | bookings | 7367 | 2026-05-13 | 2fd9b1fbe7b9 |
| 17 | 0017_guest_events.sql | guest_events | 5552 | 2026-05-13 | 4c6c9a3be55a |
| 18 | 0018_guests_fts.sql | guests_fts | 3337 | 2026-05-13 | 770da809e890 |
| 19 | 0019_pending_welcomes.sql | pending_welcomes | 4095 | 2026-05-13 | 27ad6d9ba50f |
| 20 | 0020_admin_import_logs.sql | admin_import_logs | 1589 | 2026-05-13 | 5e9986e76f86 |
| 21 | 0021_bot_link_clicks.sql | bot_link_clicks | 2866 | 2026-05-15 | bf93a87b5cc7 |
| 22 | 0022_human_handoff_log.sql | human_handoff_log | 2582 | 2026-05-15 | 48c6f6372410 |
| 23 | 0023_bot_config.sql | bot_config | 1145 | 2026-05-15 | 99feb0734641 |
| 24 | 0024_data_v2_seed_marker.sql | data_v2_seed_marker | 1811 | 2026-05-15 | bdfd830c87b2 |
| 25 | 0025_greeter_turns.sql | greeter_turns | 2466 | 2026-05-15 | 9bed7839f925 |
| 26 | 0026_airbnb_confirmation_code.sql | airbnb_confirmation_code | 932 | 2026-05-15 | f77aa4206af4 |
| 27 | 0027_greeter_turns_v6_columns.sql | greeter_turns_v6_columns | 1708 | 2026-05-16 | 252be56713b5 |
| 28 | 0028_human_handoff_log_subscriber_name.sql | human_handoff_log_subscriber_name | 1152 | 2026-05-17 | 6b06f46dc826 |
| 29 | 0029_conversations_resolved_at.sql | conversations_resolved_at | 1202 | 2026-05-17 | 449cb515563b |
| 30 | 0030_inquiries_closed.sql | inquiries_closed | 1593 | 2026-05-17 | d65511fa4ade |
| 31 | 0031_conversations_closed_reason.sql | conversations_closed_reason | 993 | 2026-05-17 | d034efbcec65 |
| 32 | 0032_messenger_outbound.sql | messenger_outbound | 2205 | 2026-05-18 | ca8789436df5 |
| 33 | 0033_extra_guests_captures.sql | extra_guests_captures | 3203 | 2026-05-18 | 816b8571f630 |
| 34 | 0034_guests_name_locked.sql | guests_name_locked | 1165 | 2026-05-18 | 6b9a53ebc851 |
| 35 | 0035_pre_stay_columns.sql | pre_stay_columns | 1547 | 2026-05-18 | 3b3ac5a0aff6 |
| 36 | 0036_pre_arrival_t14_sent_at.sql | pre_arrival_t14_sent_at | 966 | 2026-05-18 | e62369b8d755 |
| 37 | 0037_guests_manychat_subscriber_id.sql | guests_manychat_subscriber_id | 1785 | 2026-05-18 | db28fb8c7937 |
| 38 | 0038_in_stay_post_stay_columns.sql | in_stay_post_stay_columns | 1231 | 2026-05-18 | a45dbbeb47b9 |
| 39 | 0039_audit_log.sql | audit_log | 1351 | 2026-05-19 | a4f494509573 |
| 40 | 0040_rules_link_clicks.sql | rules_link_clicks | 1458 | 2026-05-19 | 59fcaeb2d190 |
| 41 | 0041_bot_short_links.sql | bot_short_links | 2660 | 2026-05-21 | a3dd2a3be135 |
| 42 | 0042_feedback_system.sql | feedback_system | 3379 | 2026-05-21 | 2031e3ea9533 |
| 43 | 0043_booking_captures.sql | booking_captures | 3549 | 2026-05-21 | 3daa9bd1ad76 |
| 44 | 0044_outreach_templates.sql | outreach_templates | 1988 | 2026-05-21 | 5c28ecd562dd |
| 45 | 0045_mp_payments.sql | mp_payments | 3412 | 2026-05-22 | 5eb3e2af4fa8 |

## Active number collisions in workspace

None.

## Renumber / rename history (from git log)

- 0015_leads.sql: 6430512 fix(d1): rename Phase B bookings → beds24_bookings (collision con 0004)
- 0016_bookings.sql: 6430512 fix(d1): rename Phase B bookings → beds24_bookings (collision con 0004)
- 0017_guest_events.sql: 6430512 fix(d1): rename Phase B bookings → beds24_bookings (collision con 0004)
- 0040_rules_link_clicks.sql: dade0d3 chore(audit-wave-1): T2 renumber duplicate migration 0039_rules_link_clicks (#140)

## Note on 0039 historical collision

Per thread/172 and CLAUDE.md anti-pattern docs, a historical migration 0039 collision was resolved via PR #140 (renamed `0039_audit_log.sql` → to current numbering). Currently in workspace, 0039_audit_log.sql and 0040_rules_link_clicks.sql both exist with distinct numbers — collision is RESOLVED. No active migration number collisions detected.
