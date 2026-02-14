
import logging
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# HH.ru URL patterns: hh.ru/vacancy/123, hh.kz/vacancy/123, headhunter.ru/vacancy/123
_HH_VACANCY_RE = re.compile(
    r"(?:hh\.ru|hh\.kz|headhunter\.ru|headhunter\.kz)/vacancy/(\d+)",
    re.IGNORECASE,
)

# HH.ru public API base
_HH_API_BASE = "https://api.hh.ru"


class WebScraper:
    """Service to scrape and clean text from URLs."""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    _HH_API_HEADERS = {
        "User-Agent": "EdtonAI/1.0 (resume-adapter)",
        "Accept": "application/json",
    }

    MAX_RETRIES = 2

    # ─── Public interface ───────────────────────────────────────────

    @classmethod
    async def fetch_text(cls, url: str) -> str:
        """Fetch URL and return cleaned text content.

        For HH.ru URLs, uses the public API for structured data.
        For all other URLs, falls back to HTML scraping.
        """
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        # Try HH.ru API path first
        vacancy_id = cls._extract_hh_vacancy_id(url)
        if vacancy_id:
            return await cls._fetch_hh_api(vacancy_id)

        # Generic HTML scraping for non-HH URLs
        return await cls._fetch_html(url)

    # ─── HH.ru API path ────────────────────────────────────────────

    @classmethod
    def _extract_hh_vacancy_id(cls, url: str) -> str | None:
        """Extract vacancy ID from HH.ru URL, or None if not an HH URL."""
        match = _HH_VACANCY_RE.search(url)
        return match.group(1) if match else None

    @classmethod
    async def _fetch_hh_api(cls, vacancy_id: str) -> str:
        """Fetch vacancy via HH.ru public API and format as clean text."""
        api_url = f"{_HH_API_BASE}/vacancies/{vacancy_id}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            for attempt in range(cls.MAX_RETRIES + 1):
                try:
                    resp = await client.get(api_url, headers=cls._HH_API_HEADERS)
                    resp.raise_for_status()
                    data = resp.json()
                    return cls._format_hh_vacancy(data)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        raise ValueError(
                            f"Вакансия не найдена на HH.ru (ID: {vacancy_id})"
                        )
                    if attempt < cls.MAX_RETRIES:
                        logger.warning(
                            "HH.ru API attempt %d failed (%s), retrying...",
                            attempt + 1,
                            e.response.status_code,
                        )
                        continue
                    raise ValueError(
                        f"HH.ru API error: HTTP {e.response.status_code}"
                    )
                except (httpx.RequestError, Exception) as e:
                    if attempt < cls.MAX_RETRIES:
                        logger.warning(
                            "HH.ru API attempt %d failed (%s), retrying...",
                            attempt + 1,
                            str(e),
                        )
                        continue
                    logger.error("HH.ru API failed after retries: %s", e)
                    raise ValueError(
                        f"Не удалось получить вакансию с HH.ru: {str(e)}"
                    )

        # Unreachable, but satisfies type checker
        raise ValueError("HH.ru API request failed")

    @classmethod
    def _format_hh_vacancy(cls, data: dict[str, Any]) -> str:
        """Convert HH.ru API JSON into clean structured text for LLM parsing.

        Extracts all relevant fields and formats them as human-readable text
        that the PARSE_VACANCY_PROMPT can process effectively.
        """
        parts: list[str] = []

        # Title
        if name := data.get("name"):
            parts.append(f"Название вакансии: {name}")

        # Company
        if employer := data.get("employer"):
            if emp_name := employer.get("name"):
                parts.append(f"Компания: {emp_name}")

        # Location
        if area := data.get("area"):
            if area_name := area.get("name"):
                parts.append(f"Локация: {area_name}")

        # Address details
        if addr := data.get("address"):
            if raw_addr := addr.get("raw"):
                parts.append(f"Адрес: {raw_addr}")

        # Salary
        salary = data.get("salary")
        if salary:
            salary_parts = []
            if salary.get("from"):
                salary_parts.append(f"от {salary['from']}")
            if salary.get("to"):
                salary_parts.append(f"до {salary['to']}")
            if salary.get("currency"):
                salary_parts.append(salary["currency"])
            if salary.get("gross"):
                salary_parts.append("до вычета налогов")
            if salary_parts:
                parts.append(f"Зарплата: {' '.join(salary_parts)}")

        # Experience
        if exp := data.get("experience"):
            if exp_name := exp.get("name"):
                parts.append(f"Опыт работы: {exp_name}")

        # Employment type
        if empl := data.get("employment"):
            if empl_name := empl.get("name"):
                parts.append(f"Тип занятости: {empl_name}")

        # Schedule
        if sched := data.get("schedule"):
            if sched_name := sched.get("name"):
                parts.append(f"График работы: {sched_name}")

        # Work format
        if work_formats := data.get("work_format"):
            if isinstance(work_formats, list):
                names = [wf.get("name", "") for wf in work_formats if wf.get("name")]
                if names:
                    parts.append(f"Формат работы: {', '.join(names)}")

        # Professional roles
        if roles := data.get("professional_roles"):
            role_names = [r.get("name", "") for r in roles if r.get("name")]
            if role_names:
                parts.append(f"Профессиональная роль: {', '.join(role_names)}")

        parts.append("")  # Blank line separator

        # Description (HTML → plain text)
        if desc_html := data.get("description"):
            desc_text = cls._html_to_text(desc_html)
            parts.append("Описание вакансии:")
            parts.append(desc_text)
            parts.append("")

        # Key skills
        if key_skills := data.get("key_skills"):
            skill_names = [s.get("name", "") for s in key_skills if s.get("name")]
            if skill_names:
                parts.append("Ключевые навыки:")
                parts.append(", ".join(skill_names))
                parts.append("")

        # Languages
        if languages := data.get("languages"):
            lang_parts = []
            for lang in languages:
                lang_name = lang.get("name", "")
                level = lang.get("level", {})
                level_name = level.get("name", "") if isinstance(level, dict) else ""
                if lang_name:
                    lang_parts.append(
                        f"{lang_name} ({level_name})" if level_name else lang_name
                    )
            if lang_parts:
                parts.append(f"Языки: {', '.join(lang_parts)}")

        # Driver license
        if licenses := data.get("driver_license_types"):
            lic_ids = [lic.get("id", "") for lic in licenses if lic.get("id")]
            if lic_ids:
                parts.append(f"Водительские права: {', '.join(lic_ids)}")

        text = "\n".join(parts)

        # Limit length
        return text[:30000]

    @classmethod
    def _html_to_text(cls, html: str) -> str:
        """Convert an HTML snippet (e.g. vacancy description) to plain text."""
        soup = BeautifulSoup(html, "lxml")
        # Replace <li> with bullet points for readability
        for li in soup.find_all("li"):
            li.insert_before("• ")
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)

    # ─── Generic HTML scraping path ─────────────────────────────────

    @classmethod
    async def _fetch_html(cls, url: str) -> str:
        """Fetch URL via HTML scraping with retries."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            for attempt in range(cls.MAX_RETRIES + 1):
                try:
                    response = await client.get(url, headers=cls.HEADERS)
                    response.raise_for_status()
                    html = response.text
                    return cls._clean_html(html)
                except (httpx.HTTPError, Exception) as e:
                    if attempt < cls.MAX_RETRIES:
                        logger.warning(
                            "Scrape attempt %d failed for %s: %s, retrying...",
                            attempt + 1,
                            url,
                            str(e),
                        )
                        continue
                    logger.error("Failed to fetch vacancy URL %s: %s", url, e)
                    raise ValueError(
                        f"Failed to fetch URL (site may block bots): {str(e)}"
                    )

        raise ValueError("Failed to fetch URL after retries")

    @classmethod
    def _clean_html(cls, html: str) -> str:
        """Use BeautifulSoup to extract readable text, removing boilerplate."""
        soup = BeautifulSoup(html, "lxml")

        # Remove irrelevant tags
        for tag in soup(
            ["script", "style", "nav", "footer", "header", "iframe", "svg", "noscript"]
        ):
            tag.decompose()

        # Remove cookie/banner/popup elements by class/id keywords.
        # Use word-boundary-safe patterns to avoid false positives
        # (e.g. "broad-spacing" was matching "ad-" previously).
        _noise_patterns = re.compile(
            r"\bcookie\b|\bbanner\b|\bpopup\b|\bmodal\b|\bsidebar\b"
            r"|\bad-container\b|\bad-block\b|\bads[-_]\b|\brelated-posts\b",
            re.IGNORECASE,
        )
        for tag in soup.find_all(True):
            try:
                attr_str = " ".join(
                    " ".join(v) if isinstance(v, list) else str(v)
                    for v in tag.attrs.values()
                )
                if _noise_patterns.search(attr_str):
                    tag.decompose()
            except Exception:
                pass

        text = soup.get_text(separator="\n")

        # Normalize whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        # Limit length to avoid blowing up LLM context
        return text[:30000]
