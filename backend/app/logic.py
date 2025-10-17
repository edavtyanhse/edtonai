import re

COMMON = {
    "python",
    "sql",
    "pandas",
    "react",
    "fastapi",
    "ml",
    "product",
    "metrics",
    "a/b",
    "testing",
    "jira",
    "figma",
}


def extract_skills(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-zА-Яа-я0-9\-\+/#\.]{2,}", text.lower())
    return sorted(set(tokens) & COMMON)


def compute_match(resume_skills: list[str], vacancy_skills: list[str]):
    rs, vc = set(resume_skills), set(vacancy_skills)
    matched = sorted(rs & vc)
    missing = sorted(vc - rs)
    score = round(100 * (len(matched) / max(1, len(vc))), 1)
    return matched, missing, score


def ats_score(resume_text: str, vacancy_text: str) -> float:
    kws = extract_skills(vacancy_text)
    cover = len([k for k in kws if k in resume_text.lower()]) / max(1, len(kws))
    structure = sum(
        1
        for h in [
            "опыт",
            "experience",
            "skills",
            "навыки",
            "projects",
            "контакты",
            "education",
            "образование",
        ]
        if h in resume_text.lower()
    ) / 8
    return round(100 * (0.7 * cover + 0.3 * structure), 1)

