# EdTon.ai Frontend

React + TypeScript frontend for the resume adaptation service.

## Tech Stack

- React 18 with TypeScript
- Vite for bundling
- TanStack Query for API state management
- React Router for routing
- Tailwind CSS for styling
- diff library for text comparison

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

1. Create a `.env` file in `frontend/` (see `.env.example` in root) with:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`

2. Install dependencies:

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

The app will be available at http://localhost:3000

API calls are proxied to http://localhost:8000 (backend).

### Build for Production

```bash
npm run build
```

### Lint & Format

```bash
npm run lint
npm run format
```

## Project Structure

```
src/
├── api/           # API client, types, endpoints
├── components/    # Reusable UI components
├── pages/         # Page components (Workspace, History, Compare)
├── utils/         # Utility functions (diff, storage)
├── App.tsx        # Router setup
├── main.tsx       # Entry point
└── index.css      # Global styles
```

## Docker

Build and run with Docker:

```bash
docker build -t edtonai-frontend .
docker run -p 3000:80 edtonai-frontend
```

Or use docker-compose from the project root:

```bash
docker-compose up -d
```

## Features

- **Workspace**: Main screen for resume adaptation
  - Paste resume and vacancy text
  - Analyze match and get improvement suggestions
  - Adapt resume based on selected options
  - Generate ideal resume from vacancy
  - Save versions to history

- **History**: Version management
  - View saved versions
  - Restore to workspace
  - Delete versions
  - Navigate to compare

- **Compare**: Diff viewer for versions
  - Side-by-side comparison
  - Word or line granularity
  - Show only changes filter
