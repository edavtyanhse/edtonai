import asyncio
import ipaddress
import logging
import re
import socket
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

from backend.core.config import Settings
from backend.core.config import settings as app_settings
from backend.errors.integration import ScraperError

logger = logging.getLogger(__name__)

# HH.ru URL patterns: hh.ru/vacancy/123, hh.kz/vacancy/123, headhunter.ru/vacancy/123
_HH_VACANCY_RE = re.compile(
    r"(?:hh\.ru|hh\.kz|headhunter\.ru|headhunter\.kz)/vacancy/(\d+)",
    re.IGNORECASE,
)

# HH.ru public API base
_HH_API_BASE = "https://api.hh.ru"
_HH_ALLOWED_HOSTS = {"hh.ru", "hh.kz", "headhunter.ru", "headhunter.kz"}

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

    MAX_RETRIES = 2

    # ─── Public interface ───────────────────────────────────────────

    @classmethod
    async def fetch_text(cls, url: str, settings: Settings | None = None) -> str:
        """Fetch URL and return cleaned text content.

        For HH.ru URLs, uses the public API for structured data.
        For all other URLs, falls back to HTML scraping.
        """
        settings = settings or app_settings
        await cls._validate_public_http_url(url, settings)

        # Try HH.ru API path first
        vacancy_id = cls._extract_hh_vacancy_id(url)
        if vacancy_id:
            return await cls._fetch_hh_api(vacancy_id, url, settings)

        # Generic HTML scraping for non-HH URLs
        return await cls._fetch_html(url, settings)

    # ─── HH.ru API path ────────────────────────────────────────────

    @classmethod
    def _extract_hh_vacancy_id(cls, url: str) -> str | None:
        """Extract vacancy ID from HH.ru URL, or None if not an HH URL."""
        parsed = urlparse(url)
        hostname = parsed.hostname.lower() if parsed.hostname else ""
        if hostname not in _HH_ALLOWED_HOSTS:
            return None
        match = _HH_VACANCY_RE.search(f"{hostname}{parsed.path}")
        return match.group(1) if match else None

    @classmethod
    async def _fetch_hh_api(
        cls,
        vacancy_id: str,
        original_url: str,
        settings: Settings,
    ) -> str:
        """Fetch vacancy via HH.ru public API and format as clean text."""
        api_url = f"{_HH_API_BASE}/vacancies/{vacancy_id}"

        async with httpx.AsyncClient(timeout=settings.scraper_timeout_seconds) as client:
            for attempt in range(cls.MAX_RETRIES + 1):
                try:
                    resp = await client.get(
                        api_url,
                        headers=cls._hh_api_headers(settings),
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return cls._format_hh_vacancy(data)
                except httpx.HTTPStatusError as e:
                    status_code = e.response.status_code
                    if status_code == 404:
                        raise ScraperError(
                            f"Вакансия не найдена на HH.ru (ID: {vacancy_id})",
                            status_code=404,
                        )
                    if cls._should_fallback_to_hh_html(status_code):
                        if attempt < cls.MAX_RETRIES:
                            logger.warning(
                                "HH.ru API attempt %d failed (%s), retrying...",
                                attempt + 1,
                                status_code,
                            )
                            continue
                        logger.warning(
                            "HH.ru API failed for vacancy %s with HTTP %s; "
                            "falling back to HTML page",
                            vacancy_id,
                            status_code,
                        )
                        return await cls._fetch_html(
                            cls._normalize_hh_vacancy_url(original_url),
                            settings,
                        )
                    raise ScraperError(f"HH.ru API error: HTTP {status_code}")
                except ValueError:
                    raise ScraperError("HH.ru API returned invalid response")
                except httpx.RequestError as e:
                    if attempt < cls.MAX_RETRIES:
                        logger.warning(
                            "HH.ru API attempt %d failed (%s), retrying...",
                            attempt + 1,
                            type(e).__name__,
                        )
                        continue
                    logger.error(
                        "HH.ru API request failed after retries: %s",
                        type(e).__name__,
                    )
                    raise ScraperError("Не удалось получить вакансию с HH.ru")

        # Unreachable, but satisfies type checker
        raise ScraperError("HH.ru API request failed")

    @staticmethod
    def _hh_api_headers(settings: Settings) -> dict[str, str]:
        user_agent = settings.hh_api_user_agent.strip()
        return {
            "User-Agent": user_agent,
            "HH-User-Agent": user_agent,
            "Accept": "application/json",
        }

    @staticmethod
    def _should_fallback_to_hh_html(status_code: int) -> bool:
        return status_code in {403, 429} or status_code >= 500

    @staticmethod
    def _normalize_hh_vacancy_url(url: str) -> str:
        """Use HTTPS HH page without user-controlled query or fragment."""
        parsed = urlparse(url)
        hostname = parsed.hostname.lower() if parsed.hostname else "hh.ru"
        return urlunparse(("https", hostname, parsed.path, "", "", ""))

    @staticmethod
    def sanitize_source_url(url: str | None) -> str | None:
        """Return a safe URL variant for persistence."""
        if not url:
            return None
        parsed = urlparse(url)
        hostname = parsed.hostname.lower() if parsed.hostname else ""
        if not hostname:
            return None
        scheme = "https" if hostname in _HH_ALLOWED_HOSTS else parsed.scheme
        return urlunparse((scheme, hostname, parsed.path, "", "", ""))

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
    async def _fetch_html(cls, url: str, settings: Settings) -> str:
        """Fetch URL via HTML scraping with retries."""
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=settings.scraper_timeout_seconds,
        ) as client:
            for attempt in range(cls.MAX_RETRIES + 1):
                try:
                    response = await cls._get_with_safe_redirects(
                        client,
                        url,
                        settings,
                    )
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "")
                    if not cls._is_text_response(content_type):
                        raise ScraperError(
                            "URL did not return a text/html response",
                            status_code=422,
                        )
                    if len(response.content) > settings.scraper_max_html_bytes:
                        raise ScraperError(
                            "URL response is too large",
                            status_code=422,
                        )
                    html = response.text
                    return cls._clean_html(html)
                except ScraperError:
                    raise
                except httpx.HTTPStatusError as e:
                    status_code = e.response.status_code
                    if attempt < cls.MAX_RETRIES:
                        logger.warning(
                            "Scrape attempt %d failed for %s: HTTP %s, retrying...",
                            attempt + 1,
                            cls._safe_url_for_log(url),
                            status_code,
                        )
                        continue
                    logger.error(
                        "Failed to fetch vacancy URL %s: HTTP %s",
                        cls._safe_url_for_log(url),
                        status_code,
                    )
                    raise ScraperError("Failed to fetch URL (site may block bots)")
                except httpx.HTTPError as e:
                    if attempt < cls.MAX_RETRIES:
                        logger.warning(
                            "Scrape attempt %d failed for %s: %s, retrying...",
                            attempt + 1,
                            cls._safe_url_for_log(url),
                            type(e).__name__,
                        )
                        continue
                    logger.error(
                        "Failed to fetch vacancy URL %s: %s",
                        cls._safe_url_for_log(url),
                        type(e).__name__,
                    )
                    raise ScraperError("Failed to fetch URL (site may block bots)")
                except Exception as e:
                    if attempt < cls.MAX_RETRIES:
                        logger.warning(
                            "Scrape attempt %d failed for %s: %s, retrying...",
                            attempt + 1,
                            cls._safe_url_for_log(url),
                            type(e).__name__,
                        )
                        continue
                    logger.error(
                        "Failed to fetch vacancy URL %s: %s",
                        cls._safe_url_for_log(url),
                        type(e).__name__,
                    )
                    raise ScraperError("Failed to fetch URL (site may block bots)")

        raise ScraperError("Failed to fetch URL after retries")

    @classmethod
    async def _get_with_safe_redirects(
        cls,
        client: httpx.AsyncClient,
        url: str,
        settings: Settings,
    ) -> httpx.Response:
        """Fetch URL while validating every redirect target."""
        current_url = url
        for _ in range(settings.scraper_max_redirects + 1):
            await cls._validate_public_http_url(current_url, settings)
            response = await client.get(current_url, headers=cls.HEADERS)
            if response.status_code not in {301, 302, 303, 307, 308}:
                return response
            location = response.headers.get("location")
            if not location:
                return response
            current_url = urljoin(str(response.url), location)
        raise ScraperError("Too many redirects while fetching URL", status_code=422)

    @classmethod
    async def _validate_public_http_url(cls, url: str, settings: Settings) -> None:
        """Reject non-public HTTP(S) URLs to reduce SSRF risk."""
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ScraperError(
                "URL must start with http:// or https://",
                status_code=422,
            )
        if parsed.username or parsed.password:
            raise ScraperError("URL credentials are not allowed", status_code=422)
        if not parsed.hostname:
            raise ScraperError("URL host is required", status_code=422)
        try:
            port = parsed.port
        except ValueError:
            raise ScraperError("URL port is invalid", status_code=422)
        if port and port not in {80, 443}:
            raise ScraperError("URL port is not allowed", status_code=422)

        hostname = parsed.hostname.lower()
        if hostname == "localhost" or hostname.endswith(".localhost"):
            raise ScraperError("Localhost URLs are not allowed", status_code=422)
        if not cls._is_allowed_host(hostname, settings.scraper_allowed_host_set):
            raise ScraperError("URL host is not allowed", status_code=422)

        default_port = 443 if parsed.scheme == "https" else 80
        addresses = await cls._resolve_host(hostname, port or default_port)
        if not addresses:
            raise ScraperError("URL host could not be resolved", status_code=422)
        if any(cls._is_blocked_ip(address) for address in addresses):
            raise ScraperError("Private or local network URLs are not allowed", status_code=422)

    @staticmethod
    def _is_allowed_host(hostname: str, allowed_hosts: set[str]) -> bool:
        """Match exact allowlist entries or their subdomains."""
        if not allowed_hosts:
            return False
        return any(
            hostname == allowed_host or hostname.endswith(f".{allowed_host}")
            for allowed_host in allowed_hosts
        )

    @staticmethod
    async def _resolve_host(hostname: str, port: int) -> set[str]:
        loop = asyncio.get_running_loop()
        try:
            infos = await loop.getaddrinfo(
                hostname,
                port,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror:
            return set()
        return {info[4][0] for info in infos}

    @staticmethod
    def _is_blocked_ip(address: str) -> bool:
        ip = ipaddress.ip_address(address)
        return (
            not ip.is_global
            or ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )

    @staticmethod
    def _is_text_response(content_type: str) -> bool:
        return any(
            allowed in content_type.lower()
            for allowed in ("text/html", "text/plain", "application/xhtml+xml")
        )

    @staticmethod
    def _safe_url_for_log(url: str) -> str:
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

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
