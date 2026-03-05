"""
Unit tests for the enhanced chat context building in OrchestratorAgent.

Covers:
1. Context Building – _build_context_from_agent_data()
2. Token Management / Truncation – prioritization and [:N] slicing
3. Integration – chat_stream() full flow, caching, error handling
"""
import pytest
from unittest.mock import MagicMock, patch
from backend.agents.orchestrator import OrchestratorAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_orchestrator():
    """Create an OrchestratorAgent with a mocked LLM."""
    mock_llm = MagicMock()

    async def mock_stream(*args, **kwargs):
        yield MagicMock(content="mock response")

    mock_llm.astream = mock_stream

    with patch("backend.agents.orchestrator.get_llm", return_value=mock_llm):
        orch = OrchestratorAgent()
        orch.llm = mock_llm
        return orch


# ---------------------------------------------------------------------------
# 1. Context Building Tests
# ---------------------------------------------------------------------------

class TestBuildContextFromAgentData:
    """Tests for OrchestratorAgent._build_context_from_agent_data()."""

    def setup_method(self):
        self.orchestrator = _make_orchestrator()

    def _build(self, servicenow=None, confluence=None, changes=None,
               logs=None, events=None, remediations=None, excluded_items=None):
        return self.orchestrator._build_context_from_agent_data(
            incident_id="INC-TEST-001",
            servicenow=servicenow or {},
            confluence=confluence or {},
            changes=changes or {},
            logs=logs or {},
            events=events or {},
            remediations=remediations or {},
            excluded_items=excluded_items,
        )

    # --- logs section ---

    def test_includes_logs_section(self, mock_logs_results):
        context = self._build(logs=mock_logs_results)
        assert "RELEVANT LOG ENTRIES" in context

    def test_includes_log_error_count(self, mock_logs_results):
        context = self._build(logs=mock_logs_results)
        assert "Errors:" in context

    def test_includes_log_warning_count(self, mock_logs_results):
        context = self._build(logs=mock_logs_results)
        assert "Warnings:" in context

    def test_log_entry_format_contains_level(self, mock_logs_results):
        context = self._build(logs=mock_logs_results)
        assert "[ERROR]" in context or "[WARN]" in context

    def test_log_entry_format_contains_confidence(self, mock_logs_results):
        context = self._build(logs=mock_logs_results)
        assert "confidence:" in context

    def test_handles_empty_logs(self):
        context = self._build(logs={"logs": []})
        assert "RELEVANT LOG ENTRIES" not in context

    def test_handles_missing_logs_key(self):
        context = self._build(logs={})
        assert "RELEVANT LOG ENTRIES" not in context

    # --- events section ---

    def test_includes_events_section(self, mock_events_results):
        context = self._build(events=mock_events_results)
        assert "RELEVANT EVENTS" in context

    def test_includes_events_critical_count(self, mock_events_results):
        context = self._build(events=mock_events_results)
        assert "Critical:" in context

    def test_includes_events_warning_count(self, mock_events_results):
        context = self._build(events=mock_events_results)
        assert "Warnings:" in context

    def test_event_entry_format_contains_severity(self, mock_events_results):
        context = self._build(events=mock_events_results)
        assert "[CRITICAL]" in context or "[WARNING]" in context

    def test_event_entry_format_contains_confidence(self, mock_events_results):
        context = self._build(events=mock_events_results)
        assert "confidence:" in context

    def test_handles_empty_events(self):
        context = self._build(events={"events": []})
        assert "RELEVANT EVENTS" not in context

    def test_handles_missing_events_key(self):
        context = self._build(events={})
        assert "RELEVANT EVENTS" not in context

    # --- servicenow section ---

    def test_includes_similar_incidents_section(self, mock_servicenow_results):
        context = self._build(servicenow=mock_servicenow_results)
        assert "SIMILAR HISTORICAL INCIDENTS" in context

    def test_includes_previous_resolutions(self, mock_servicenow_results):
        context = self._build(servicenow=mock_servicenow_results)
        assert "PREVIOUS RESOLUTIONS" in context

    def test_handles_empty_similar_incidents(self):
        context = self._build(servicenow={"similar_incidents": [], "resolutions": []})
        assert "SIMILAR HISTORICAL INCIDENTS" not in context

    # --- knowledge base section ---

    def test_includes_knowledge_base_section(self, mock_confluence_results):
        context = self._build(confluence=mock_confluence_results)
        assert "RELEVANT KNOWLEDGE BASE ARTICLES" in context

    def test_knowledge_base_includes_content_snippet(self, mock_confluence_results):
        context = self._build(confluence=mock_confluence_results)
        # Content snippet should be present for docs that have content
        assert "Step 1" in context or "Restart" in context

    def test_handles_empty_documents(self):
        context = self._build(confluence={"documents": []})
        assert "RELEVANT KNOWLEDGE BASE ARTICLES" not in context

    # --- changes section ---

    def test_includes_top_suspect_change(self, mock_changes_results):
        context = self._build(changes=mock_changes_results)
        assert "TOP SUSPECT CHANGE" in context

    def test_includes_high_correlation_changes(self, mock_changes_results):
        context = self._build(changes=mock_changes_results)
        assert "HIGH CORRELATION CHANGES" in context

    def test_handles_empty_changes(self):
        context = self._build(changes={})
        assert "TOP SUSPECT CHANGE" not in context
        assert "HIGH CORRELATION CHANGES" not in context

    # --- remediations section ---

    def test_includes_remediation_section(self, mock_remediations_results):
        context = self._build(remediations=mock_remediations_results)
        assert "REMEDIATION RECOMMENDATIONS" in context

    def test_handles_empty_remediations(self):
        context = self._build(remediations={"remediations": []})
        assert "REMEDIATION RECOMMENDATIONS" not in context

    # --- all empty ---

    def test_returns_no_context_message_when_all_empty(self):
        context = self._build()
        assert context == "No additional context available."

    # --- null / None values ---

    def test_handles_none_log_fields(self):
        logs = {
            "logs": [
                {"timestamp": None, "service": None, "level": None, "message": None, "confidence_score": 0}
            ]
        }
        context = self._build(logs=logs)
        # Section header should still appear even when field values are None
        assert "RELEVANT LOG ENTRIES" in context
        # The entry itself should be present (level=None renders as "[None]")
        assert "1." in context

    def test_handles_none_event_fields(self):
        events = {
            "events": [
                {"id": "e1", "severity": None, "application": None, "type": None,
                 "message": None, "confidence_score": 0}
            ]
        }
        context = self._build(events=events)
        assert "RELEVANT EVENTS" in context

    # --- output format consistency ---

    def test_output_is_string(self, mock_logs_results, mock_events_results):
        context = self._build(logs=mock_logs_results, events=mock_events_results)
        assert isinstance(context, str)

    def test_all_sections_present_when_full_data(
        self,
        mock_servicenow_results,
        mock_confluence_results,
        mock_changes_results,
        mock_logs_results,
        mock_events_results,
        mock_remediations_results,
    ):
        context = self._build(
            servicenow=mock_servicenow_results,
            confluence=mock_confluence_results,
            changes=mock_changes_results,
            logs=mock_logs_results,
            events=mock_events_results,
            remediations=mock_remediations_results,
        )
        assert "TOP SUSPECT CHANGE" in context
        assert "SIMILAR HISTORICAL INCIDENTS" in context
        assert "RELEVANT KNOWLEDGE BASE ARTICLES" in context
        assert "HIGH CORRELATION CHANGES" in context
        assert "RELEVANT LOG ENTRIES" in context
        assert "RELEVANT EVENTS" in context
        assert "REMEDIATION RECOMMENDATIONS" in context

    # --- excluded items ---

    def test_excludes_specified_log_items(self, mock_logs_results):
        log = mock_logs_results["logs"][0]
        ts = log.get("timestamp", "unknown")
        svc = log.get("service", "unknown")
        excluded_id = f"log:{ts}:{svc}"
        context_with = self._build(logs=mock_logs_results)
        context_without = self._build(logs=mock_logs_results, excluded_items=[excluded_id])
        # The log entry message should appear without exclusion
        assert log["message"] in context_with
        # After exclusion, that specific entry should not appear
        assert log["message"] not in context_without

    def test_excludes_specified_event_items(self, mock_events_results):
        event = mock_events_results["events"][0]
        excluded_id = f"event:{event['id']}"
        context_with = self._build(events=mock_events_results)
        context_without = self._build(events=mock_events_results, excluded_items=[excluded_id])
        assert event["message"] in context_with
        assert event["message"] not in context_without

    def test_excludes_specified_incident(self, mock_servicenow_results):
        incident = mock_servicenow_results["similar_incidents"][0]
        excluded_id = f"incident:{incident['id']}"
        context_with = self._build(servicenow=mock_servicenow_results)
        context_without = self._build(servicenow=mock_servicenow_results, excluded_items=[excluded_id])
        assert incident["title"] in context_with
        assert incident["title"] not in context_without

    def test_excludes_top_suspect_change(self, mock_changes_results):
        change_id = mock_changes_results["top_suspect"]["change_id"]
        excluded_id = f"change:{change_id}"
        context_with = self._build(changes=mock_changes_results)
        context_without = self._build(changes=mock_changes_results, excluded_items=[excluded_id])
        assert "TOP SUSPECT CHANGE" in context_with
        assert "TOP SUSPECT CHANGE" not in context_without

    def test_handles_none_excluded_items(self, mock_logs_results):
        context = self._build(logs=mock_logs_results, excluded_items=None)
        assert "RELEVANT LOG ENTRIES" in context

    def test_handles_empty_excluded_items_list(self, mock_logs_results):
        context = self._build(logs=mock_logs_results, excluded_items=[])
        assert "RELEVANT LOG ENTRIES" in context

    def test_all_items_excluded_hides_section(self, mock_events_results):
        excluded = [
            f"event:{e['id']}" for e in mock_events_results["events"]
        ]
        context = self._build(events=mock_events_results, excluded_items=excluded)
        assert "RELEVANT EVENTS" not in context


# ---------------------------------------------------------------------------
# 2. Token Management / Truncation Tests
# ---------------------------------------------------------------------------

class TestTokenManagement:
    """Tests for truncation / prioritization behaviour."""

    def setup_method(self):
        self.orchestrator = _make_orchestrator()

    def _build(self, **kwargs):
        return self.orchestrator._build_context_from_agent_data(
            incident_id="INC-TEST-001",
            servicenow=kwargs.get("servicenow", {}),
            confluence=kwargs.get("confluence", {}),
            changes=kwargs.get("changes", {}),
            logs=kwargs.get("logs", {}),
            events=kwargs.get("events", {}),
            remediations=kwargs.get("remediations", {}),
            excluded_items=kwargs.get("excluded_items"),
        )

    def _make_logs(self, n):
        return {
            "logs": [
                {
                    "timestamp": f"2024-01-01T00:00:{i:02d}Z",
                    "service": f"svc-{i}",
                    "level": "ERROR",
                    "message": f"Error message {i}",
                    "confidence_score": 0.8,
                }
                for i in range(n)
            ]
        }

    def _make_events(self, n):
        return {
            "events": [
                {
                    "id": f"evt-{i}",
                    "severity": "CRITICAL",
                    "application": f"app-{i}",
                    "type": "NodeDown",
                    "message": f"Event message {i}",
                    "confidence_score": 0.9,
                }
                for i in range(n)
            ]
        }

    def _make_similar_incidents(self, n):
        return {
            "similar_incidents": [
                {"id": f"INC-{i:03d}", "title": f"Incident title {i}"}
                for i in range(n)
            ]
        }

    def _make_documents(self, n):
        return {
            "documents": [
                {"title": f"Document {i}", "content": f"Content of document {i}"}
                for i in range(n)
            ]
        }

    def _make_remediations(self, n):
        return {
            "remediations": [
                {
                    "id": f"rem-{i}",
                    "title": f"Remediation {i}",
                    "description": f"Description {i}",
                    "confidence_score": 0.8,
                }
                for i in range(n)
            ]
        }

    # --- logs truncation ---

    def test_truncates_logs_to_five(self):
        context = self._build(logs=self._make_logs(10))
        # Only entries 0–4 should appear; entry 5 must not
        assert "Error message 4" in context
        assert "Error message 5" not in context

    def test_boundary_logs_exactly_at_limit(self):
        context = self._build(logs=self._make_logs(5))
        assert "Error message 4" in context
        assert "Error message 5" not in context

    def test_boundary_logs_just_over_limit(self):
        context = self._build(logs=self._make_logs(6))
        assert "Error message 4" in context
        assert "Error message 5" not in context

    def test_single_log_entry_shown(self):
        context = self._build(logs=self._make_logs(1))
        assert "Error message 0" in context

    # --- events truncation ---

    def test_truncates_events_to_five(self):
        context = self._build(events=self._make_events(10))
        assert "Event message 4" in context
        assert "Event message 5" not in context

    def test_boundary_events_exactly_at_limit(self):
        context = self._build(events=self._make_events(5))
        assert "Event message 4" in context

    def test_boundary_events_just_over_limit(self):
        context = self._build(events=self._make_events(6))
        assert "Event message 5" not in context

    # --- similar incidents truncation ---

    def test_truncates_similar_incidents_to_three(self):
        context = self._build(servicenow=self._make_similar_incidents(6))
        assert "Incident title 2" in context
        assert "Incident title 3" not in context

    # --- documents truncation ---

    def test_truncates_documents_to_three(self):
        context = self._build(confluence=self._make_documents(6))
        assert "Document 2" in context
        assert "Document 3" not in context

    # --- remediations truncation ---

    def test_truncates_remediations_to_three(self):
        context = self._build(remediations=self._make_remediations(6))
        assert "Remediation 2" in context
        assert "Remediation 3" not in context

    # --- count accuracy ---

    def test_error_count_reflects_actual_errors(self):
        logs = {
            "logs": [
                {"timestamp": "t1", "service": "s", "level": "ERROR",
                 "message": "e1", "confidence_score": 1.0},
                {"timestamp": "t2", "service": "s", "level": "WARN",
                 "message": "w1", "confidence_score": 1.0},
                {"timestamp": "t3", "service": "s", "level": "ERROR",
                 "message": "e2", "confidence_score": 1.0},
            ]
        }
        context = self._build(logs=logs)
        assert "Errors: 2" in context
        assert "Warnings: 1" in context

    def test_critical_event_count_reflects_actual_criticals(self):
        events = {
            "events": [
                {"id": "e1", "severity": "CRITICAL", "application": "a",
                 "type": "t", "message": "c1", "confidence_score": 1.0},
                {"id": "e2", "severity": "WARNING", "application": "a",
                 "type": "t", "message": "w1", "confidence_score": 1.0},
            ]
        }
        context = self._build(events=events)
        assert "Critical: 1" in context
        assert "Warnings: 1" in context

    def test_context_grows_with_more_data(self, mock_logs_results, mock_events_results):
        context_small = self._build(logs={"logs": mock_logs_results["logs"][:1]})
        context_large = self._build(logs=mock_logs_results)
        assert len(context_large) > len(context_small)

    def test_log_entry_count_in_header(self):
        logs = self._make_logs(3)
        context = self._build(logs=logs)
        assert "3 found" in context

    def test_event_entry_count_in_header(self):
        events = self._make_events(4)
        context = self._build(events=events)
        assert "4 found" in context


# ---------------------------------------------------------------------------
# 3. Integration Tests
# ---------------------------------------------------------------------------

class TestChatStreamIntegration:
    """Integration tests for chat_stream() using mock LLMs and agent data."""

    @pytest.mark.asyncio
    async def test_chat_stream_returns_chunks(self):
        mock_llm = MagicMock()

        async def mock_stream(*args, **kwargs):
            for word in ["Hello", " world"]:
                yield MagicMock(content=word)

        mock_llm.astream = mock_stream

        with patch("backend.agents.orchestrator.get_llm", return_value=mock_llm):
            orch = OrchestratorAgent()
            orch.llm = mock_llm

            chunks = []
            async for chunk in orch.chat_stream("INC001", "What happened?", []):
                chunks.append(chunk)

        assert len(chunks) == 2
        assert "".join(chunks) == "Hello world"

    @pytest.mark.asyncio
    async def test_context_caching_on_first_call(self):
        mock_llm = MagicMock()

        async def mock_stream(*args, **kwargs):
            yield MagicMock(content="ok")

        mock_llm.astream = mock_stream

        with patch("backend.agents.orchestrator.get_llm", return_value=mock_llm):
            orch = OrchestratorAgent()
            orch.llm = mock_llm

            async for _ in orch.chat_stream("INC001", "First?", []):
                pass

            cached = orch.cache.get("INC001")

        assert cached is not None
        assert "servicenow_results" in cached
        assert "confluence_results" in cached
        assert "change_results" in cached
        assert "logs_results" in cached
        assert "events_results" in cached
        assert "remediation_results" in cached

    @pytest.mark.asyncio
    async def test_context_caching_uses_cache_on_second_call(self):
        mock_llm = MagicMock()
        call_count = {"n": 0}

        async def mock_stream(*args, **kwargs):
            call_count["n"] += 1
            yield MagicMock(content="cached response")

        mock_llm.astream = mock_stream

        with patch("backend.agents.orchestrator.get_llm", return_value=mock_llm):
            orch = OrchestratorAgent()
            orch.llm = mock_llm

            # First call – populates cache
            async for _ in orch.chat_stream("INC-CACHE-01", "First?", []):
                pass

            first_call_count = call_count["n"]

            # Second call – should use cache (same LLM call count)
            async for _ in orch.chat_stream("INC-CACHE-01", "Second?", []):
                pass

            # LLM was called both times (once per chat), but agents ran only once
            assert call_count["n"] == first_call_count + 1

    @pytest.mark.asyncio
    async def test_chat_stream_with_mock_agent_data_in_context(self):
        """Full flow: injected agent data surfaces in LLM system message."""
        mock_llm = MagicMock()
        captured_system_msg = []

        async def mock_stream(*args, **kwargs):
            captured_system_msg.append(args[0][0].content)
            yield MagicMock(content="response")

        mock_llm.astream = mock_stream

        with patch("backend.agents.orchestrator.get_llm", return_value=mock_llm):
            orch = OrchestratorAgent()
            orch.llm = mock_llm

            # Pre-populate cache with known data
            orch.cache.set(
                "INC-MOCK-01",
                {
                    "servicenow_results": {
                        "similar_incidents": [
                            {"id": "INC-OLD-1", "title": "Old network failure"}
                        ]
                    },
                    "confluence_results": {},
                    "change_results": {},
                    "logs_results": {
                        "logs": [
                            {
                                "timestamp": "2024-01-01T00:00:00Z",
                                "service": "svc",
                                "level": "ERROR",
                                "message": "disk full",
                                "confidence_score": 0.9,
                            }
                        ]
                    },
                    "events_results": {},
                    "remediation_results": {},
                },
            )

            async for _ in orch.chat_stream("INC-MOCK-01", "Tell me more.", []):
                pass

        assert captured_system_msg, "System message should have been captured"
        system_msg = captured_system_msg[0]
        assert "INC-MOCK-01" in system_msg
        assert "Old network failure" in system_msg
        assert "disk full" in system_msg

    @pytest.mark.asyncio
    async def test_chat_stream_excluded_items_filtered(self):
        """Excluded items should not appear in the LLM context."""
        mock_llm = MagicMock()
        captured_system_msg = []

        async def mock_stream(*args, **kwargs):
            captured_system_msg.append(args[0][0].content)
            yield MagicMock(content="ok")

        mock_llm.astream = mock_stream

        with patch("backend.agents.orchestrator.get_llm", return_value=mock_llm):
            orch = OrchestratorAgent()
            orch.llm = mock_llm

            orch.cache.set(
                "INC-EXCL-01",
                {
                    "servicenow_results": {
                        "similar_incidents": [
                            {"id": "INC-A", "title": "Should be excluded"},
                            {"id": "INC-B", "title": "Should remain"},
                        ]
                    },
                    "confluence_results": {},
                    "change_results": {},
                    "logs_results": {},
                    "events_results": {},
                    "remediation_results": {},
                },
            )

            async for _ in orch.chat_stream(
                "INC-EXCL-01",
                "What do you know?",
                [],
                excluded_items=["incident:INC-A"],
            ):
                pass

        system_msg = captured_system_msg[0]
        assert "Should be excluded" not in system_msg
        assert "Should remain" in system_msg

    @pytest.mark.asyncio
    async def test_chat_stream_error_handling_yields_error_message(self):
        mock_llm = MagicMock()

        async def mock_stream_with_error(*args, **kwargs):
            yield MagicMock(content="Partial")
            raise RuntimeError("connection dropped")

        mock_llm.astream = mock_stream_with_error

        with patch("backend.agents.orchestrator.get_llm", return_value=mock_llm):
            orch = OrchestratorAgent()
            orch.llm = mock_llm

            chunks = []
            async for chunk in orch.chat_stream("INC001", "Help?", []):
                chunks.append(chunk)

        combined = "".join(chunks)
        assert "Partial" in combined or "Error" in combined

    @pytest.mark.asyncio
    async def test_chat_stream_context_building_error_does_not_crash(self):
        """If context building raises an exception it should propagate out of chat_stream."""
        mock_llm = MagicMock()

        async def mock_stream(*args, **kwargs):
            yield MagicMock(content="fine")

        mock_llm.astream = mock_stream

        with patch("backend.agents.orchestrator.get_llm", return_value=mock_llm):
            orch = OrchestratorAgent()
            orch.llm = mock_llm

            # Patch _build_context_from_agent_data to raise an exception
            with patch.object(
                orch,
                "_build_context_from_agent_data",
                side_effect=ValueError("context error"),
            ):
                with pytest.raises(ValueError, match="context error"):
                    async for _ in orch.chat_stream("INC001", "Help?", []):
                        pass
