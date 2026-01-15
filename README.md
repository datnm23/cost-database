# BOQ System - Bill of Quantities Management

Modern web application for managing and standardizing Bill of Quantities (BOQ) data with AI-powered classification.

## 🚀 Tech Stack

### Backend
- **Python 3.11+** - Core language
- **FastAPI** - High-performance API framework
- **SQLAlchemy** - ORM and database toolkit
- **MySQL 8.0+** - Primary database
- **Redis** - Caching and session management
- **Celery** - Background task processing
- **Sentence Transformers** - ML classification

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Ant Design** - UI components
- **React Query** - Data fetching
- **Zustand** - State management
- **Recharts** - Data visualization

## � Features

- ✅ Project and BOQ file management
- ✅ Excel file upload and parsing
- ✅ Automated data cleaning and standardization
- ✅ AI-powered SEC code classification
- ✅ Manual review and correction interface
- ✅ Advanced filtering and search
- ✅ Analytics and reporting
- ✅ Export capabilities (Excel, CSV, PDF)
- ✅ Role-based access control
- ✅ Audit logging

## �️ Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- Make (optional, for convenience commands)

### Quick Start with Docker

1. **Clone the repository**
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start services**
   ```bash
   make up
   # Or: docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Redoc: http://localhost:8000/redoc

### Local Development Setup

1. **Start infrastructure services**
   ```bash
   make dev
   # This starts MySQL and Redis
   ```

2. **Setup backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. **Setup frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 📚 Documentation

- [Requirements](docs/REQUIREMENTS.md) - Detailed requirements and specifications
- [Project Overview](docs/PROJECT_OVERVIEW.md) - Architecture and system overview
- [Technical Design](docs/TECHNICAL_DESIGN.md) - In-depth technical documentation
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Production deployment instructions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

## 🧪 Testing

```bash
# Run all tests
make test

# Backend tests only
make test-backend

# Frontend tests only
make test-frontend
```

## 🔧 Useful Commands

```bash
# View logs
make logs

# Database shell
make db-shell

# Backup database
make backup

# Restore database
make restore FILE=backup.sql

# Format code
make format

# Lint code
make lint

# Clean everything
make clean
```

## 📁 Project Structure

```
cost-database/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configurations
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── main.py         # Application entry
│   ├── tests/              # Backend tests
│   ├── alembic/            # Database migrations
│   └── requirements.txt
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── hooks/          # Custom hooks
│   │   ├── store/          # State management
│   │   └── App.tsx         # Main component
│   ├── public/
│   └── package.json
│
├── docs/                   # Documentation
├── nginx/                  # Nginx configuration
├── docker-compose.yml      # Docker orchestration
├── Makefile               # Development commands
└── README.md              # This file
```

## 🌐 Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` - Database connection
- `REDIS_HOST`, `REDIS_PORT` - Redis connection
- `SECRET_KEY` - JWT secret key
- `BACKEND_CORS_ORIGINS` - Allowed CORS origins
- `ENVIRONMENT` - development/staging/production

## 🚢 Deployment

See [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for detailed production deployment instructions.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- Development Team - Initial work

## 🙏 Acknowledgments

- Built with FastAPI and React
- ML models powered by Sentence Transformers
- UI components from Ant Design

### 3. Review Items

```
📝 Review → Filter low confidence → Manual correct → Save
```

### 4. View Analytics

```
📊 Analytics → View charts → Export reports
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_database.py -v
```

---

## 📊 API Reference

### Database Module

```python
from modules.database import Database

db = Database()

# Projects
projects = db.get_all_projects()
project_id = db.create_project(code, name, type)

# Line Items
items = db.get_line_items(project_id=1, needs_review=True)
db.update_classification(item_id, sec_code, user)
```

### Classifier Module

```python
from modules.classifier import SECClassifier

classifier = SECClassifier(db)
results = classifier.classify("đào đất móng")
# Returns: [('SEC-01-01', 95.0), ('SEC-01', 85.0), ...]
```

---

## 🔒 Security

- ✅ Parameterized SQL queries
- ✅ Environment-based configuration
- ✅ Input validation
- ✅ File type validation
- ⬜ Authentication (planned)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📋 Roadmap

### Phase 1 (Current)
- [x] Core upload & processing
- [x] ML classification
- [x] Manual review
- [x] Basic analytics

### Phase 2 (Planned)
- [ ] Multi-user support
- [ ] Active learning
- [ ] Advanced analytics
- [ ] Price database integration

### Phase 3 (Future)
- [ ] Cloud deployment
- [ ] Mobile app
- [ ] API endpoints
- [ ] Template library

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) | Project summary & architecture |
| [REQUIREMENTS.md](docs/REQUIREMENTS.md) | Functional & non-functional requirements |
| [TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md) | Database schema & API design |
| [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | Step-by-step deployment |
| [IMPROVEMENT_PROPOSALS.md](docs/IMPROVEMENT_PROPOSALS.md) | Suggested improvements |

---

## 🐛 Troubleshooting

### MySQL Connection Failed

```bash
# Check Docker
docker-compose ps
docker-compose logs mysql

# Restart
docker-compose restart mysql
```

### ML Model Not Loading

```bash
# Re-download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('keepitreal/vietnamese-sbert')"
```

### Performance Issues

```sql
-- Analyze tables
ANALYZE TABLE line_items;

-- Check indexes
SHOW INDEX FROM line_items;
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 📞 Support

- 📧 Email: [your-email@example.com]
- 📖 Docs: [/docs](/docs)
- 🐛 Issues: [GitHub Issues]

---

**Made with ❤️ for construction cost management**
