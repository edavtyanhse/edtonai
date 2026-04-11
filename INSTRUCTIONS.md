# AI Coding Agent – System Development Guidelines
Project: Bachelor Thesis (ВКР) – AI-driven system  
Goal: Production-ready, scalable, extensible architecture without future refactoring cycles.

---

## 1. GENERAL PRINCIPLES

You are not just implementing a feature.  
You are designing a long-term scalable system suitable for academic defense and potential production usage.

Every implementation MUST:

- Be modular
- Be testable
- Be extensible
- Respect separation of concerns
- Avoid tight coupling
- Avoid quick hacks
- Avoid architectural shortcuts

If a requested feature contradicts architecture quality — propose a better structural solution.

---

## 2. ARCHITECTURAL STYLE

Use Clean Architecture principles.

### Layers (strict separation):

1. **Presentation Layer**
    - FastAPI routers
    - Request/response DTOs
    - Validation

2. **Application Layer**
    - Use cases / services
    - Business logic
    - No framework dependencies

3. **Domain Layer**
    - Entities
    - Value objects
    - Domain rules
    - Pure Python

4. **Infrastructure Layer**
    - Database access (SQLAlchemy)
    - External APIs
    - ML models
    - File storage
    - Logging

Dependencies must point inward only.

---

## 3. BACKEND STACK REQUIREMENTS

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x (async preferred)
- PostgreSQL
- Pydantic
- Dependency Injection via FastAPI Depends
- Docker-ready configuration
- .env-based configuration
- Alembic for migrations

Never mix:
- ORM models with Pydantic schemas
- Business logic inside routers
- Raw SQL inside business layer

---

## 4. ML / AI COMPONENT RULES

- ML models must be isolated in a separate module
- No model loading inside routers
- Use lazy loading or singleton provider
- Configurable model path

Example interface:

```python
class ResumeClassifier:
    def predict(self, text: str) -> "PredictionResult":
        """
        Perform inference on resume text and return structured prediction.
        """
        raise NotImplementedError
```

Model layer must be replaceable without affecting business logic.

---

## 5. DATABASE DESIGN RULES

- Explicit relationships
- No implicit magic
- Proper indexing
- UUID as primary keys
- Soft delete if necessary
- created_at / updated_at timestamps

Use repository pattern:

```python
from uuid import UUID
from typing import Optional

class ResumeRepository:
    async def get_by_id(self, id: UUID) -> Optional["Resume"]:
        raise NotImplementedError
```

---

## 6. EXTENSIBILITY RULES

When adding a new feature:

- Do NOT modify existing core logic if avoidable
- Prefer extension over modification
- Follow Open/Closed principle
- Avoid rewriting large blocks of code

Before writing code:
- Explain where feature belongs architecturally
- Explain what new components are introduced

---

## 7. CODE QUALITY REQUIREMENTS

- Type hints everywhere
- No global state
- No hidden side effects
- No duplicated logic
- Functions < 40 lines when possible
- Clear naming (avoid generic names like data, obj, tmp)
- Docstrings for public classes

---

## 8. TESTABILITY

Code must allow:

- Unit testing of services
- Mocking repositories
- Mocking ML model

No hard dependency instantiation inside business logic.

---

## 9. ERROR HANDLING

- Custom domain exceptions
- Centralized exception handlers
- No silent failures
- Clear error messages

---

## 10. PERFORMANCE AWARENESS

- Avoid N+1 queries
- Use async I/O
- No heavy computation inside request thread
- Use background tasks when needed

---

## 11. DOCKER & CONFIGURATION

- All configs via environment variables
- No hardcoded paths
- Separate dev/prod config
- Reproducible setup

---

## 12. ACADEMIC QUALITY (IMPORTANT FOR THESIS)

The code must:

- Demonstrate architectural awareness
- Reflect software engineering best practices
- Be explainable during defense
- Contain meaningful abstractions
- Show clear separation of layers

Avoid overengineering, but justify architectural choices.

---

## 13. BEFORE WRITING CODE

Always:

1. Briefly describe architectural placement.
2. Explain why this design is scalable.
3. List new modules/files introduced.
4. Then provide implementation.

---

## 14. NEVER DO

- Monolithic files
- Business logic inside controllers
- Direct DB access from routers
- ML logic inside API layer
- Hardcoded configuration
- Quick prototype shortcuts


---

## 15. MANDATORY ARCHITECTURAL PATTERNS

The system MUST comply with the following architectural principles.

### 15.1 Clean Architecture (Enforced)

- No layer skipping
- No circular dependencies
- Infrastructure depends on Application/Domain only
- Domain layer must not depend on frameworks

Any violation must be explicitly justified.

---

### 15.2 SOLID Principles (Mandatory)

All code must follow:

- **S – Single Responsibility Principle**
  One class = one responsibility.

- **O – Open/Closed Principle**
  Extend behavior via abstraction, not modification.

- **L – Liskov Substitution Principle**
  Subtypes must be safely replaceable.

- **I – Interface Segregation Principle**
  Avoid fat interfaces.

- **D – Dependency Inversion Principle**
  High-level modules must not depend on low-level modules.

Violation of SOLID is not acceptable.

---

### 15.3 Dependency Injection (Strict Rules)

Dependency Injection is REQUIRED.

Rules:

- No service instantiation inside business logic.
- No `SomeService()` calls inside other services.
- Use constructor injection.
- Composition Root must be in API layer.
- FastAPI Depends is allowed only in presentation layer.
- Domain and Application layers must be framework-agnostic.

Example:

```python
class ResumeService:
    def __init__(self, repository: ResumeRepository):
        self._repository = repository
```

Forbidden:

```python
class ResumeService:
    def __init__(self):
        self._repository = PostgresResumeRepository()
```

No Service Locator pattern allowed.

---

### 15.4 Repository Pattern (Mandatory)

- Application layer depends on abstract repository interfaces.
- Infrastructure implements concrete repositories.
- No ORM model leakage into domain layer.

---

### 15.5 Factory Pattern (When Needed)

Use Factory pattern when:

- Creating ML models
- Creating complex domain objects
- Managing configurable providers

Do not instantiate complex objects directly in controllers.

---

### 15.6 Strategy Pattern (For ML / Business Variants)

If multiple algorithms or ranking strategies exist:

- Use Strategy pattern
- No `if/else` branching across entire system

---

### 15.7 CQRS (Recommended for Growth)

If system grows:

- Separate read models from write logic
- Do not overload services with both query and mutation logic

---

### 15.8 Transaction Boundaries

- Transactions must be controlled at application layer
- No implicit transactions in repository methods
- Explicit Unit of Work pattern preferred

---

### 15.9 Composition Root

All concrete dependency wiring must happen in one place:

- main.py
- dependency_container.py

No hidden instantiation across the codebase.

---

### 15.10 Anti-Patterns (Strictly Forbidden)

- God classes
- Fat controllers
- Anemic domain model
- Service Locator
- Static global state
- Business logic in ORM models
- Mixing DTO and domain models
- Massive utility modules

---

## 16. ARCHITECTURAL DECISION TRANSPARENCY

When introducing:

- New pattern
- New abstraction
- New service
- New dependency

You MUST:

1. Explain why this pattern is chosen.
2. Explain how it improves extensibility.
3. Explain what future change it protects against.
4. Confirm compliance with Clean Architecture + SOLID.

Architecture decisions must be intentional, not accidental.