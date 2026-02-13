# Architecture Documentation

This document describes the architecture of **EdTon.ai** using the **C4 Model** (Context, Containers, Components, Code) and a Deployment diagram.

## 1. C4 Level 1: System Context Diagram

The System Context diagram shows the software system in the context of its users and external systems.

```mermaid
C4Context
    title System Context Diagram for EdTon.ai

    Person(user, "Job Seeker", "A user looking to optimize their resume for specific job vacancies.")
    
    System(edtonai, "EdTon.ai Interface", "AI-powered resume adaptation platform.")

    System_Ext(supabase, "Supabase", "Provides Authentication (Auth), Database (PostgreSQL), and Row Level Security.")
    System_Ext(deepseek, "DeepSeek API", "LLM for complex reasoning, gap analysis, and content generation.")
    System_Ext(groq, "Groq API", "High-speed LLM inference for text parsing (Resume/Vacancy).")

    Rel(user, edtonai, "Uses", "HTTPS")
    Rel(edtonai, supabase, "Reads/Writes User Data", "HTTPS/PostgreSQL")
    Rel(edtonai, deepseek, "Sends context for analysis", "HTTPS/JSON")
    Rel(edtonai, groq, "Sends text for fast parsing", "HTTPS/JSON")
    
    UpdateRelStyle(user, edtonai, $textColor="blue", $lineColor="blue")
```

---

## 2. C4 Level 2: Container Diagram

The Container diagram shows the high-level shape of the software architecture and how responsibilities are distributed.

```mermaid
C4Container
    title Container Diagram for EdTon.ai

    Person(user, "Job Seeker", "Uses the web application")

    Container_Boundary(c1, "EdTon.ai System") {
        Container(spa, "Single Page Application", "React, TypeScript, Vite, Tailwind", "Provides the interactive UI for the Wizard, History, and Resume Editing.")
        Container(api, "API Application", "Python, FastAPI", "Handles business logic, parsing orchestration, and LLM integration.")
    }

    System_Ext(supabase_auth, "Supabase Auth", "Manages user identity and JWT tokens.")
    System_Ext(supabase_db, "Supabase Database", "PostgreSQL", "Stores resumes, vacancies, analysis results, and user profiles.")
    
    System_Ext(llm_deepseek, "DeepSeek API", "External AI Service")
    System_Ext(llm_groq, "Groq API", "External AI Service")

    Rel(user, spa, "Visits", "HTTPS")
    Rel(spa, api, "API Calls", "HTTPS/JSON (JWT Auth)")
    Rel(spa, supabase_auth, "Authenticates", "SDK")
    
    Rel(api, supabase_db, "Reads/Writes", "AsyncPG/SQLAlchemy")
    Rel(api, llm_deepseek, "Analyze & Adapt", "REST API")
    Rel(api, llm_groq, "Parse Text", "REST API")
```

---

## 3. Deployment Diagram

The Deployment diagram illustrates how the system is hosted and the infrastructure used.

```mermaid
graph TB
    user((User))

    subgraph "Google Cloud Platform (GCP)"
        subgraph "Cloud Run (Managed Serverless)"
            frontend[("Frontend Service<br/>(Nginx + React Static)")]
            backend[("Backend Service<br/>(Uvicorn + FastAPI)")]
        end
    end

    subgraph "External Managed Services"
        supabase[("Supabase<br/>(PostgreSQL + Auth)")]
        deepseek[("DeepSeek API")]
        groq[("Groq API")]
    end

    user -- "HTTPS (Port 443)" --> frontend
    frontend -- "HTTPS (API Calls)" --> backend
    
    backend -- "Connection Pool" --> supabase
    backend -- "REST" --> deepseek
    backend -- "REST" --> groq
```

## 4. Key Decisions & Technology Stack

### Backend
- **FastAPI**: Chosen for high performance (async), automatic OpenAPI documentation, and easy integration with Pydantic for strict data validation (crucial for LLM structured outputs).
- **SQLAlchemy (Async) + Pydantic**: Ensures rigorous type safety from the database layer up to the API response.
- **Hybrid AI Approach**: 
    - **Groq (Llama 3)** is used for *parsing* tasks where speed is critical and complexity is moderate.
    - **DeepSeek V3** is used for *reasoning* tasks (gap analysis, content adaptation) where model intelligence is paramount.

### Frontend
- **React + Vite**: Industrial standard for fast SPA development.
- **Tailwind CSS**: Utility-first styling for rapid UI iteration and consistent design system.
- **TanStack Query (React Query)**: Manages server state, caching, and background updates, significantly simplifying exact data fetching logic required for a wizard-like step interface.
