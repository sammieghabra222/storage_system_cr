# Bodega CR

A multi-tenant SaaS platform for storage facility management in Costa Rica, featuring native integration with local payment systems (SINPE) and compliance with Costa Rican electronic invoicing (Factura Electrónica).

## Features

### Core Functionality
- **Storage Unit Management** - Track units by type, size, status, and pricing
- **Customer Management** - Individual and business customers with cédula support
- **Contract Lifecycle** - Move-in/move-out flows, auto-renewal, deposits
- **Invoicing** - Automated billing with late fees and prorated calculations
- **Payment Processing** - SINPE Móvil, bank transfers, credit cards

### Costa Rica Compliance
- **Factura Electrónica** - Hacienda API v4.4 integration
- **IVA Handling** - 13% tax calculations
- **SINPE Integration** - QR code generation for mobile payments
- **Multi-Currency** - CRC, USD, EUR with BCCR exchange rates

### Analytics & Reporting
- Occupancy dashboards with charts
- Revenue reports by period
- Aging reports for overdue payments
- Payment method breakdowns

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python 3.11+) |
| Frontend | Next.js 14 (React, TypeScript) |
| Styling | Tailwind CSS |
| State | Zustand |
| i18n | next-intl (ES/EN) |
| Auth | JWT + OAuth2 |
| Database | Repository Pattern (in-memory, PostgreSQL-ready) |

## Project Structure

```
storage_system_cr/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # API endpoints
│   │   ├── core/             # Security, middleware
│   │   ├── domain/
│   │   │   ├── models/       # Pydantic models
│   │   │   └── services/     # Business logic
│   │   └── infrastructure/
│   │       ├── repositories/ # Data access layer
│   │       └── integrations/ # SINPE, Hacienda, Card processors
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/[locale]/     # Next.js pages with i18n
│   │   ├── components/       # UI, forms, charts
│   │   ├── lib/              # API client, utilities
│   │   ├── stores/           # Zustand stores
│   │   └── types/            # TypeScript definitions
│   └── package.json
│
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Docker Setup

```bash
# Run both services
docker-compose up -d

# Or for development with hot reload
docker-compose -f docker-compose.dev.yml up
```

## Environment Variables

### Backend (`backend/.env`)

```env
# App
SECRET_KEY=your-secret-key-here
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000

# Database (when using PostgreSQL)
DATABASE_URL=postgresql://user:pass@localhost:5432/bodega_cr

# Hacienda (Costa Rica e-invoicing)
HACIENDA_ENV=sandbox
HACIENDA_USERNAME=your-username
HACIENDA_PASSWORD=your-password

# Stripe (optional)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_...
```

## API Overview

### Authentication
- `POST /api/v1/auth/register` - Register new tenant + admin user
- `POST /api/v1/auth/login` - Login and receive JWT tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user

### Resources
- `/api/v1/storage-units` - Storage unit CRUD
- `/api/v1/customers` - Customer management
- `/api/v1/contracts` - Contract lifecycle
- `/api/v1/invoices` - Invoice generation and management
- `/api/v1/payments` - Payment recording and confirmation

### Payments
- `POST /api/v1/payments/sinpe` - Record SINPE payment
- `POST /api/v1/payments/sinpe/qr` - Generate SINPE QR code
- `POST /api/v1/payments/card/intent` - Create card payment intent
- `POST /api/v1/payments/{id}/confirm` - Confirm pending payment

### Analytics
- `GET /api/v1/analytics/dashboard` - Dashboard summary
- `GET /api/v1/analytics/revenue` - Revenue reports
- `GET /api/v1/analytics/occupancy` - Occupancy statistics
- `GET /api/v1/analytics/aging` - Accounts receivable aging

### Integrations
- `GET /api/v1/exchange-rates/current` - BCCR exchange rates
- `POST /api/v1/invoices/{id}/submit-hacienda` - Submit to Hacienda

## Test Credentials

For development, you can register a new account or use:

```
Email: admin@test.com
Password: testpassword123
```

### Test Card Numbers (Sandbox)

| Card Number | Result |
|-------------|--------|
| 4242 4242 4242 4242 | Success |
| 4000 0000 0000 0002 | Decline |
| 4000 0000 0000 9995 | Insufficient funds |

## TODO / Roadmap

### High Priority
- [ ] **PostgreSQL Repository** - Replace in-memory storage with persistent database
- [ ] **Unit Tests** - Add pytest tests for backend, Jest for frontend
- [ ] **CI/CD Pipeline** - GitHub Actions for automated testing and deployment
- [ ] **Production Docker Config** - Nginx, SSL, production optimizations

### Medium Priority
- [ ] **Document Storage** - Upload ID scans and contract PDFs (S3/MinIO)
- [ ] **PDF Export** - Generate invoice PDFs for download/email
- [ ] **Excel Reports** - Export analytics to Excel format
- [ ] **BAC Credomatic** - Local CR card processor integration
- [ ] **Email Templates** - Branded HTML email templates

### Future Enhancements
- [ ] **Mobile App** - React Native or Flutter app
- [ ] **Facility Map** - Interactive visual unit layout
- [ ] **SMS Notifications** - Via Twilio or local provider
- [ ] **WhatsApp Integration** - Customer communication
- [ ] **Audit Trail UI** - View action history in dashboard
- [ ] **Multi-facility** - Support multiple locations per tenant

## Costa Rica Specific Notes

### SINPE Móvil
SINPE has no public API. The current implementation:
1. Displays tenant's SINPE number to customers
2. Generates QR codes in SINPE format: `SINPE|phone|name|amount|CRC|description|reference`
3. Admin manually confirms payments after verifying bank deposits

### Factura Electrónica
Integration with Hacienda's electronic invoicing system (v4.4):
- Sandbox: `api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1`
- Production: `api.comprobanteselectronicos.go.cr/recepcion/v1`
- Requires digital certificate (Llave Criptográfica) from BCCR

### IVA (Sales Tax)
- Standard rate: 13%
- Applied automatically to invoice line items
- Configurable per tenant in settings

## License

Proprietary - All rights reserved

## Support

For questions or issues, contact the development team.
