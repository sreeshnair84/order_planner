# Order Management System

A comprehensive web-based order management system that allows retailers to upload order documents (CSV, logs, XML) to FMCG/OEM providers. The system processes orders, validates data, handles missing information through email communication, and provides real-time order tracking.

## 🚀 Features

### Core Functionality
- **Multi-format File Upload**: Support for CSV, XML, and LOG files
- **Intelligent File Processing**: Automatic data extraction and validation
- **SKU-Level Processing**: Detailed tracking of individual SKU items with processing remarks
- **Real-time Order Tracking**: Live status updates with detailed timeline
- **Email Communication**: Automated emails for missing information requests
- **User Authentication**: Secure JWT-based authentication
- **Responsive Design**: Modern, mobile-first UI

### Order Processing Pipeline
1. **UPLOADED** → File received and queued
2. **PROCESSING** → Extracting and validating data
3. **PENDING_INFO** → Waiting for missing information
4. **INFO_RECEIVED** → Processing retailer response
5. **VALIDATED** → Order data complete and valid
6. **SUBMITTED** → Order sent to FMCG provider
7. **CONFIRMED** → FMCG provider confirmed order
8. **IN_TRANSIT** → Order dispatched for delivery
9. **DELIVERED** → Order successfully delivered

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL** - Robust relational database
- **SQLAlchemy** - Python SQL toolkit and ORM
- **Pydantic** - Data validation using Python type annotations
- **JWT** - JSON Web Tokens for authentication
- **Pandas** - Data manipulation and analysis
- **Redis** - In-memory data structure store (caching & background tasks)

### Frontend
- **React** - JavaScript library for building user interfaces
- **React Router** - Client-side routing
- **React Query** - Data synchronization and caching
- **React Hook Form** - Performant forms with easy validation
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icon library

### DevOps
- **Docker** - Containerization platform
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Web server and reverse proxy

## 📋 Prerequisites

- **Docker** and **Docker Compose** installed
- **Node.js** 18+ (for local development)
- **Python** 3.11+ (for local development)
- **PostgreSQL** 15+ (for local development)

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd order_planner
   ```

2. **Create environment file**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Update environment variables**
   Edit `backend/.env` with your configuration:
   ```env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/order_management
   SECRET_KEY=your-secret-key-here-please-change-in-production
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

4. **Start the application**
   ```bash
   docker-compose up --build
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the backend**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

## 📁 Project Structure

```
order_planner/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   ├── database/      # Database configuration
│   │   ├── utils/         # Utility functions
│   │   └── main.py        # FastAPI application
│   ├── tests/             # Backend tests
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   ├── contexts/      # React contexts
│   │   └── utils/         # Utility functions
│   ├── public/            # Public assets
│   ├── package.json       # Node.js dependencies
│   └── Dockerfile
├── docker-compose.yml     # Docker orchestration
└── README.md
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/order_management

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads
ALLOWED_FILE_TYPES=.csv,.xml,.log,.txt

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Redis
REDIS_URL=redis://localhost:6379
```

#### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000
```

## 📦 SKU Item Processing

### Processing Remarks Feature
The system now includes detailed SKU-level processing with automatic generation of processing remarks for missing or invalid data:

#### What are Processing Remarks?
- Automatically generated notes about missing or problematic data in SKU items
- Help identify specific issues with individual products in an order
- Displayed in the Order Processing interface for easy review

#### Examples of Processing Remarks
- "Missing SKU code"
- "Missing or invalid pricing information" 
- "Missing product category"
- "Using default weight (1kg) - actual weight not provided"
- "Processing error: Invalid data format"

#### SKU Items Tab
In the Order Processing interface, navigate to the **SKU Items** tab to:
- View detailed information for all SKU items in an order
- See processing remarks for items with issues
- Review summary statistics (total items, total value, items with remarks)
- Access product attributes and physical details

#### Database Migration
For existing installations, run the database migration to add the new processing_remarks column:

**Windows:**
```batch
cd backend\scripts
.\migrate_add_processing_remarks.ps1
```

**Manual SQL:**
```sql
ALTER TABLE order_sku_items ADD COLUMN processing_remarks TEXT;
```

## 📊 API Documentation

The API documentation is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/refresh` - Refresh access token

#### Orders
- `POST /api/requestedorders/upload` - Upload order file
- `GET /api/requestedorders` - Get user orders
- `GET /api/requestedorders/{order_id}` - Get specific order
- `DELETE /api/requestedorders/{order_id}` - Cancel order

#### Tracking
- `GET /api/tracking/{order_id}` - Get order tracking
- `GET /api/tracking` - Get all orders tracking
- `POST /api/tracking/{order_id}/status` - Update order status

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🔒 Security Features

- **JWT Authentication** with refresh tokens
- **Password hashing** using bcrypt
- **Input validation** and sanitization
- **File type validation** and size limits
- **Rate limiting** on authentication endpoints
- **CORS configuration** for cross-origin requests

## 🚀 Deployment

### Production Environment Variables

Update your `.env` file for production:

```env
# Use strong, unique secret key
SECRET_KEY=your-production-secret-key

# Use production database
DATABASE_URL=postgresql://user:password@prod-db:5432/order_management

# Configure production email service
SMTP_SERVER=smtp.your-email-provider.com
SMTP_USERNAME=your-production-email@company.com
SMTP_PASSWORD=your-production-email-password

# Set allowed origins for your domain
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### Docker Production Deployment

```bash
# Build and run in production mode
docker-compose -f docker-compose.yml up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📈 Monitoring and Logging

- **Application logs** are written to stdout/stderr
- **Database queries** are logged in development mode
- **API access logs** are available through FastAPI
- **Health checks** are implemented for all services

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, please contact:
- Email: support@orderManagement.com
- Documentation: [Project Wiki](link-to-wiki)
- Issues: [GitHub Issues](link-to-issues)

## 🔄 Changelog

### v1.0.0 (2025-07-05)
- Initial release
- Multi-format file upload support
- Real-time order tracking
- Email notification system
- JWT authentication
- Responsive web interface

---

Built with ❤️ using FastAPI and React
