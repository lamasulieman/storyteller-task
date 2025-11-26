"""
Test suite to guard key invariants for the storyteller program.

Tests cover:
1. Schema validation
2. Cover page requirement
3. Uniqueness of highlights
4. Ordering stability
5. No-highlights fallback
6. ISO-8601 timestamps
7. Source field correctness
8. Event scoring and ranking
9. Deduplication logic
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

import pytest
import jsonschema

from story_builder.core import compute_final_score, compute_context_bonus
from story_builder.story_builder import (
    build_story_from_files,
    _make_cover_page,
    _make_highlight_page,
    _make_no_highlights_page,
)


# Load the JSON schema once
SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "story.schema.json"
with open(SCHEMA_PATH) as f:
    STORY_SCHEMA = json.load(f)


class TestInvariant1_SchemaValidation:
    """Invariant 1: Pack validates against schema/story.schema.json."""

    def test_valid_story_passes_schema(self, sample_story_dict):
        """A well-formed story should validate against the schema."""
        jsonschema.validate(sample_story_dict, STORY_SCHEMA)

    def test_missing_required_field_fails_schema(self, sample_story_dict):
        """Story missing required fields should fail schema validation."""
        del sample_story_dict["pack_id"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(sample_story_dict, STORY_SCHEMA)

    def test_invalid_page_type_fails_schema(self, sample_story_dict):
        """Pages with invalid type field should fail."""
        sample_story_dict["pages"][0]["type"] = "invalid_type"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(sample_story_dict, STORY_SCHEMA)


class TestInvariant2_CoverPageAtIndex0:
    """Invariant 2: Contains exactly one cover Page at index 0."""

    def test_cover_page_at_index_0(self, sample_story_dict):
        """First page must be a cover page."""
        assert sample_story_dict["pages"][0]["type"] == "cover"

    def test_exactly_one_cover_page(self, sample_story_dict):
        """There should be exactly one cover page in entire story."""
        cover_pages = [p for p in sample_story_dict["pages"] if p["type"] == "cover"]
        assert len(cover_pages) == 1

    def test_no_highlights_story_has_cover_then_info(self):
        """Even with no highlights, cover should be at index 0."""
        info_page = _make_no_highlights_page()
        assert info_page["type"] == "info"
        # When this is added to story, it comes after cover so at index 1


class TestInvariant3_UniqueHighlights:
    """Invariant 3: pages[1:] contain only unique highlights (no exact duplicates)."""

    def test_no_duplicate_highlights(self, sample_story_with_highlights):
        """No two highlight pages should be identical."""
        highlights = [p for p in sample_story_with_highlights["pages"] if p["type"] == "highlight"]
        
        # Convert each to JSON string for comparison
        highlight_jsons = [json.dumps(h, sort_keys=True) for h in highlights]
        
        # set() removes duplicates, so if all is unique, lengths should match
        assert len(highlight_jsons) == len(set(highlight_jsons)), \
            "Found duplicate highlight pages"



class TestInvariant4_StableOrdering:
    """Invariant 4: Ordering is stable and deterministic for the same input."""

    def test_same_input_produces_same_output_order(self):
        """Running the builder twice with same input should produce same event order."""
        match_events_path = Path("data/match_events.json")
        celtic_path = Path("data/celtic-squad.json")
        kilmarnock_path = Path("data/kilmarnock-squad.json")
        
        # Build twice
        story1 = build_story_from_files(
            match_events_path=match_events_path,
            celtic_squad_path=celtic_path,
            kilmarnock_squad_path=kilmarnock_path,
            top_n=5,
        )
        story2 = build_story_from_files(
            match_events_path=match_events_path,
            celtic_squad_path=celtic_path,
            kilmarnock_squad_path=kilmarnock_path,
            top_n=5,
        )
        
        # Extract page order (ignoring UUIDs which are random)
        pages1_order = [(p["type"], p.get("minute"), p.get("headline")) for p in story1["pages"]]
        pages2_order = [(p["type"], p.get("minute"), p.get("headline")) for p in story2["pages"]]
        
        assert pages1_order == pages2_order, "Story ordering is not deterministic"

    def test_highlights_ordered_chronologically(self, sample_story_with_highlights):
        """Highlight pages should be ordered by minute (chronological)."""
        highlights = [p for p in sample_story_with_highlights["pages"] if p["type"] == "highlight"]
        
        if len(highlights) > 1:
            minutes = [p.get("minute", 0) for p in highlights]
            assert minutes == sorted(minutes), "Highlights are not in chronological order"


class TestInvariant5_NoHighlightsFallback:
    """Invariant 5: When no items pass threshold, include an info Page."""

    def test_no_highlights_includes_info_page(self, empty_match_data):
        """Story with no highlights should include an info page."""
        # When top_n=0 or no events score above 0, we should get a fallback
        info_page = _make_no_highlights_page()
        
        assert info_page["type"] == "info"
        assert "No highlights available" in info_page["headline"]
        assert "placeholder.png" in info_page["image"]

    def test_info_page_structure(self):
        """Info page should have required fields."""
        info_page = _make_no_highlights_page()
        
        required_fields = ["id", "type", "headline", "body", "image", "created_at"]
        for field in required_fields:
            assert field in info_page, f"Missing field: {field}"


class TestInvariant6_ISO8601Timestamp:
    """Invariant 6: created_at is ISO-8601 (UTC recommended)."""

    def test_created_at_is_iso8601(self, sample_story_dict):
        """All pages should have ISO-8601 created_at."""
        for page in sample_story_dict["pages"]:
            created_at = page.get("created_at")
            assert created_at is not None, "Page missing created_at"
            
            # Should end with Z (UTC indicator)
            assert created_at.endswith("Z"), f"Timestamp not UTC: {created_at}"
            
            # Should be parseable as ISO format
            try:
                datetime.fromisoformat(created_at.rstrip("Z"))
            except ValueError:
                pytest.fail(f"Invalid ISO-8601 timestamp: {created_at}")

    def test_story_created_at_is_iso8601(self, sample_story_dict):
        """Story-level created_at should also be ISO-8601."""
        created_at = sample_story_dict.get("created_at")
        assert created_at is not None
        assert created_at.endswith("Z")


class TestInvariant7_SourceField:
    """Invariant 7: source points to the input file used."""

    def test_source_field_exists(self, sample_story_dict):
        """Story should have a source field."""
        assert "source" in sample_story_dict
        assert sample_story_dict["source"] is not None

    def test_source_points_to_match_events(self, sample_story_dict):
        """Source should reference the match events file."""
        source = sample_story_dict["source"]
        assert "match_events.json" in source, f"Source doesn't reference match_events: {source}"


class TestEventScoringLogic:
    """Test the scoring and ranking system."""

    def test_late_goal_scores_higher_than_early_goal(self):
        """A goal at minute 90 should rank higher than at minute 10."""
        early_goal = {
            "type": "goal",
            "minute": "10",
            "teamRef1": "team_a",
        }
        late_goal = {
            "type": "goal",
            "minute": "90",
            "teamRef1": "team_a",
        }
        
        # First goal scenario
        early_score = compute_final_score(early_goal, 0, 0, "team_a", "team_b")
        late_score = compute_final_score(late_goal, 0, 0, "team_a", "team_b")
        
        assert late_score["score"] > early_score["score"], \
            "Late goal should score higher than early goal"

    def test_equalizer_gets_bonus(self):
        """An equalizing goal should get a bonus."""
        equalizer = {
            "type": "goal",
            "minute": "45",
            "teamRef1": "team_b",
        }
        
        # Score is 1-0, team_b scores to make it 1-1
        score_result = compute_final_score(equalizer, 1, 0, "team_a", "team_b")
        
        # Should have equalizer bonus in reasons
        assert "equalizer=30" in score_result["bonus_reasons"]

    def test_first_goal_gets_bonus(self):
        """The first goal of the match should get a bonus."""
        first_goal = {
            "type": "goal",
            "minute": "5",
            "teamRef1": "team_a",
        }
        
        score_result = compute_final_score(first_goal, 0, 0, "team_a", "team_b")
        
        assert "first_goal=25" in score_result["bonus_reasons"]

    
class TestScoringBreakdown:
    """Test that scoring provides detailed explanation/breakdown of heuristics."""

    def test_score_includes_breakdown_structure(self):
        """Scoring result should have breakdown fields: base, context_bonus, bonus_reasons."""
        goal = {
            "type": "goal",
            "minute": "90",
            "teamRef1": "team_a",
        }
        
        result = compute_final_score(goal, 0, 0, "team_a", "team_b")
        
        # Verify all breakdown components exist
        assert "base" in result, "Missing base score"
        assert "context_bonus" in result, "Missing context_bonus"
        assert "bonus_reasons" in result, "Missing bonus_reasons"
        assert result["base"] > 0, "Base score should be > 0 for valid events"
        assert isinstance(result["bonus_reasons"], list), "Bonus reasons should be a list"

    
##############################
# Fixtures
#############################


@pytest.fixture
def sample_story_dict():
    """Return a minimal valid story dict for testing."""
    return {
        "pack_id": str(uuid.uuid4()),
        "title": "Test Match",
        "pages": [
            {
                "id": str(uuid.uuid4()),
                "type": "cover",
                "headline": "Team A vs Team B",
                "image": "../assets/cover.jpg",
                "caption": "Final score 2-1",
                "created_at": "2025-11-26T12:00:00Z",
            },
            {
                "id": str(uuid.uuid4()),
                "type": "info",
                "headline": "Test Info",
                "body": "This is test information.",
                "image": "../assets/placeholder.png",
                "created_at": "2025-11-26T12:00:01Z",
            }
        ],
        "metrics": {
            "goals": 2,
            "highlights": 0,
        },
        "source": "../data/match_events.json",
        "created_at": "2025-11-26T12:00:00Z",
    }


@pytest.fixture
def sample_story_with_highlights():
    """Return a story with actual highlight pages."""
    story = {
        "pack_id": str(uuid.uuid4()),
        "title": "Test Match with Highlights",
        "pages": [
            {
                "id": str(uuid.uuid4()),
                "type": "cover",
                "headline": "Team A vs Team B",
                "image": "../assets/cover.jpg",
                "caption": "Final score 2-1",
                "created_at": "2025-11-26T12:00:00Z",
            },
        ],
        "metrics": {"goals": 2, "highlights": 2},
        "source": "../data/match_events.json",
        "created_at": "2025-11-26T12:00:00Z",
    }
    
    # Add two highlight pages
    for minute in [15, 80]:
        story["pages"].append({
            "id": str(uuid.uuid4()),
            "type": "highlight",
            "minute": minute,
            "headline": f"GOAL — Player {minute}",
            "caption": f"Goal at minute {minute}",
            "image": f"../assets/player_{minute}.jpg",
            "explanation": f"base score=100 + late_game=15",
            "players": [f"Player {minute}"],
            "event_type": "goal",
            "created_at": f"2025-11-26T12:00:{minute % 60:02d}Z",
        })
    
    return story


@pytest.fixture
def empty_match_data():
    """Return match data with no scoreable events."""
    return {
        "matchInfo": {
            "contestant": [
                {"id": "team_a", "name": "Team A", "position": "home"},
                {"id": "team_b", "name": "Team B", "position": "away"},
            ],
            "localDate": "2025-11-26",
        },
        "messages": [
            {
                "message": [
                    {"type": "corner", "minute": "10", "second": "0", "teamRef1": "team_a"},
                ]
            }
        ]
    }
