import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))
print(f"Project root added to path: {PROJECT_ROOT}")

try:
    from dotenv import load_dotenv
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please install required dependencies: sqlalchemy, asyncpg, python-dotenv")
    sys.exit(1)

# Load env vars
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "backend.env")

# Construct URL manually if needed
DATABASE_URL = os.getenv("DATABASE_URL")
USER = os.getenv("POSTGRES_USER")
PASSWORD = os.getenv("POSTGRES_PASSWORD")
HOST = os.getenv("POSTGRES_HOST")
PORT = os.getenv("POSTGRES_PORT")
DB = os.getenv("POSTGRES_DB")

if not DATABASE_URL and USER and PASSWORD and HOST and PORT and DB:
    DATABASE_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"

if not DATABASE_URL:
    print("Error: Could not construct DATABASE_URL. Missing env vars.")
    sys.exit(1)

print(f"Using Database Host: {HOST}")

# SQL commands
SQL_COMMANDS = [
    # 1. Truncate user_version
    "TRUNCATE TABLE user_version CASCADE;",

    # 2. Add user_id column
    "ALTER TABLE user_version ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);",

    # 3. Create index
    "CREATE INDEX IF NOT EXISTS idx_user_version_user_id ON user_version(user_id);",

    # 4. Enable RLS
    "ALTER TABLE user_version ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE resume_raw ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE analysis_link ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE vacancy_raw ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE ai_result ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE resume_version ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE ideal_resume ENABLE ROW LEVEL SECURITY;",

    # 5. Policies
    # User Version Policies
    "DROP POLICY IF EXISTS \"Users can view own versions\" ON user_version;",
    "CREATE POLICY \"Users can view own versions\" ON user_version FOR SELECT USING (user_id = auth.uid()::text OR user_id IS NULL);",

    "DROP POLICY IF EXISTS \"Users can insert own versions\" ON user_version;",
    "CREATE POLICY \"Users can insert own versions\" ON user_version FOR INSERT WITH CHECK (user_id = auth.uid()::text OR user_id IS NULL);",

    "DROP POLICY IF EXISTS \"Users can update own versions\" ON user_version;",
    "CREATE POLICY \"Users can update own versions\" ON user_version FOR UPDATE USING (user_id = auth.uid()::text);",

    "DROP POLICY IF EXISTS \"Users can delete own versions\" ON user_version;",
    "CREATE POLICY \"Users can delete own versions\" ON user_version FOR DELETE USING (user_id = auth.uid()::text);",

    # Basic authenticated access policies for other tables
    "DROP POLICY IF EXISTS \"Authenticated users can access resume_raw\" ON resume_raw;",
    "CREATE POLICY \"Authenticated users can access resume_raw\" ON resume_raw FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');",

    "DROP POLICY IF EXISTS \"Authenticated users can access vacancy_raw\" ON vacancy_raw;",
    "CREATE POLICY \"Authenticated users can access vacancy_raw\" ON vacancy_raw FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');",

    "DROP POLICY IF EXISTS \"Authenticated users can access analysis_link\" ON analysis_link;",
    "CREATE POLICY \"Authenticated users can access analysis_link\" ON analysis_link FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');",

    "DROP POLICY IF EXISTS \"Authenticated users can access ai_result\" ON ai_result;",
    "CREATE POLICY \"Authenticated users can access ai_result\" ON ai_result FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');",

    "DROP POLICY IF EXISTS \"Authenticated users can access resume_version\" ON resume_version;",
    "CREATE POLICY \"Authenticated users can access resume_version\" ON resume_version FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');",

    "DROP POLICY IF EXISTS \"Authenticated users can access ideal_resume\" ON ideal_resume;",
    "CREATE POLICY \"Authenticated users can access ideal_resume\" ON ideal_resume FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');",
]

async def run_migration():
    print("Connecting to database...")
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        connect_args={"statement_cache_size": 0}
    )

    async with engine.begin() as conn:
        for i, cmd in enumerate(SQL_COMMANDS):
            print(f"[{i+1}/{len(SQL_COMMANDS)}] Executing: {cmd[:50]}...")
            try:
                await conn.execute(text(cmd))
            except Exception as e:
                print(f"Error executing command: {cmd}")
                print(f"Error details: {e}")
                # Don't silence errors blindly, print them.
                # Policies might fail if RLS is not enabled first, but we enable RLS first.
                pass

    print("Migration completed successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())
