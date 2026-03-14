"""Smoke test for DI container — verifies the wiring graph is valid."""

from __future__ import annotations

from backend.containers import Container


class TestContainerSmoke:
    """Verify the container can be instantiated and providers resolve."""

    def test_container_creates_without_error(self):
        """Container should instantiate without raising."""
        container = Container()
        assert container is not None

    def test_settings_singleton(self):
        """Settings provider should return the same instance."""
        container = Container()
        s1 = container.config()
        s2 = container.config()
        assert s1 is s2

    def test_service_factories_defined(self):
        """All expected service providers should be registered."""
        container = Container()
        expected = [
            "resume_service",
            "vacancy_service",
            "match_service",
            "orchestrator_service",
            "adapt_resume_service",
            "ideal_resume_service",
            "cover_letter_service",
        ]
        for name in expected:
            assert hasattr(container, name), f"Missing provider: {name}"

    def test_repository_factories_defined(self):
        """All expected repo providers should be registered."""
        container = Container()
        expected = [
            "resume_repo",
            "vacancy_repo",
            "ai_result_repo",
            "analysis_repo",
            "resume_version_repo",
            "ideal_resume_repo",
            "user_version_repo",
            "feedback_repo",
        ]
        for name in expected:
            assert hasattr(container, name), f"Missing provider: {name}"
