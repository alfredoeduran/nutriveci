# NutriVeci Project Schema

## Project Overview
This document provides a comprehensive overview of the NutriVeci project structure, detailing the organization of files and directories across the application.

## Root Directory Structure
```
nutriveci_proyect/
├── .venv/                  # Python virtual environment
├── venv/                   # Additional virtual environment
├── .git/                   # Git repository
├── docs/                   # Project documentation
├── backend/               # Backend application
├── frontend/              # Frontend application
├── web/                   # Web-related files
├── scripts/               # Utility scripts
├── tests/                 # Test files
├── data/                  # Data storage
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # Project documentation
```

## Backend Structure
```
backend/
├── api/                   # API endpoints and routes
├── bot/                   # Bot implementation
├── bots/                  # Additional bot modules
├── core/                  # Core functionality
├── db/                    # Database related files
├── schemas/              # Data schemas
├── ai/                   # AI/ML components
├── logging/              # Logging configuration
├── __pycache__/          # Python cache files
├── main.py               # Main application entry point
└── requirements.txt      # Backend dependencies
```

## Frontend Structure
```
frontend/
├── src/                  # Source code
│   ├── components/       # React components
│   ├── services/        # API services
│   └── utils/           # Utility functions
└── public/              # Static assets
```

## Documentation Structure
```
docs/
├── development_plan.md   # Development planning document
├── pasoapaso.md         # Step-by-step guide
├── context.md           # Project context
└── schema.md            # This schema document
```

## Key Components

### Backend Components
- **API**: Handles HTTP requests and responses
- **Bot**: Main bot implementation
- **Core**: Core business logic and functionality
- **Database**: Data persistence and management
- **AI**: Artificial Intelligence and Machine Learning components
- **Logging**: Application logging and monitoring

### Frontend Components
- **Components**: Reusable UI components
- **Services**: API integration and data fetching
- **Utils**: Helper functions and utilities

### Documentation
- **Development Plan**: Project roadmap and planning
- **Step-by-Step Guide**: Implementation instructions
- **Context**: Project background and requirements
- **Schema**: This document, providing project structure

## Dependencies
- Python backend with FastAPI
- React frontend
- Various Python packages (see requirements.txt)
- Database system (specific details in backend/db)

## Development Environment
- Python virtual environment (.venv)
- Node.js environment for frontend
- Git for version control
- Testing framework in tests/ directory

## Data Storage
- Database configurations in backend/db
- Static data in data/ directory
- Environment variables and configurations

## Testing
- Test files located in tests/ directory
- Unit tests and integration tests
- Test utilities and fixtures

## Scripts
- Utility scripts in scripts/ directory
- Build and deployment scripts
- Development helper scripts 