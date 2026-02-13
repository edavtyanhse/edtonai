
import asyncio
import uuid
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.services.resume import ResumeService
from backend.services.vacancy import VacancyService
from backend.services.match import MatchService
from backend.services.adapt import AdaptService # Using AdaptService for version creation? Or VersionService?
from backend.services.cover_letter import CoverLetterService
from backend.repositories import (
    ResumeRepository, 
    VacancyRepository, 
    AIResultRepository,
    ResumeVersionRepository,
    UserVersionRepository
)
# Check if VersionService exists or if it is part of AdaptService or ResumeService
# Based on file list: adapt.py, resume.py, cover_letter.py...
# I'll Assume there is no 'VersionService' file but maybe a class in one of them?
# Let's check where create_version is defined.
# Based on previous context, I used services.version.create_version.
# But there is no version.py in services.
# Maybe in orchestrator.py? Or resume.py?

from backend.schemas.resume import ResumeParseRequest
from backend.schemas.vacancy import VacancyParseRequest
from backend.schemas.match import MatchRequest
from backend.schemas.version import VersionCreateRequest
from backend.schemas.cover_letter import CoverLetterRequest
from backend.core.database import get_session

async def verify():
    # MOCK USER ID - In a real scenario, this would be a valid user ID from the DB
    # For now, we simulate the flow. If strict FK checks are enabled, this might fail without a real user.
    # We'll use a hardcoded UUID that matches "auth" if possible, or create a dummy user logic if needed.
    # Assuming test DB has no strict FKs on user_id or we are skipping auth middleware here (service level).
    MOCK_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000") 

    async with get_session() as session:
        # services = ServiceFactory(session) <-- REMOVED
        resume_service = ResumeService(session)
        vacancy_service = VacancyService(session)
        match_service = MatchService(session)
        
        print("1. Parsing Resume...")
        resume_text = "Experienced Python Developer with 5 years in backend."
        resume_res = await resume_service.parse_resume(ResumeParseRequest(resume_text=resume_text))
        print(f"   Resume ID: {resume_res.resume_id}")

        print("\n2. Parsing Vacancy...")
        vacancy_text = "Looking for Python Developer with FastAPI experience."
        vacancy_res = await vacancy_service.parse_vacancy(VacancyParseRequest(vacancy_text=vacancy_text))
        print(f"   Vacancy ID: {vacancy_res.vacancy_id}")

        print("\n3. Analyzing Match...")
        analysis = await match_service.analyze_match(MatchRequest(
            resume_text=resume_text,
            vacancy_text=vacancy_text
        ))
        print(f"   Analysis ID: {analysis.analysis_id}")

        print("\n4. Creating Version (Simulating Frontend Step 4)...")
        # THIS IS THE KEY STEP: Passing analysis_id
        try:
             # Use UserVersionRepository directly as in API
             user_version_repo = UserVersionRepository(session)
             version = await user_version_repo.create(
                user_id=MOCK_USER_ID,
                type="adapt",
                title="Test Version",
                resume_text=resume_text,
                vacancy_text=vacancy_text,
                result_text="Generic result text",
                change_log=[],
                selected_checkbox_ids=[],
                analysis_id=analysis.analysis_id  # <--- NEW FIELD
            )
             await session.commit() # Important!
             
             print(f"   Version ID: {version.id}")
             print(f"   Stored Analysis ID: {version.analysis_id}")
             assert version.analysis_id == analysis.analysis_id, "Analysis ID not stored!"
        except Exception as e:
            print(f"   FAILED to create version: {e}")
            return


        print("\n5. Generating Cover Letter...")
        try:
            # Instantiate service directly
            cl_service = CoverLetterService(session)
            cl = await cl_service.generate_cover_letter(
                resume_version_id=version.id,
                user_id=MOCK_USER_ID # Passing user_id for ownership check
            )
            print(f"   SUCCESS! Cover Letter ID: {cl.cover_letter_id}")
            print(f"   Vacancy ID in result: {cl.vacancy_id} (Should be None for UserVersion)")
        except Exception as e:
            print(f"   FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify())
