# ShopSphere

A full-featured e-commerce platform built with Django, featuring product management, shopping cart, orders, wishlists, and user reviews.

![Django](https://img.shields.io/badge/Django-5.2.14-092E20?style=flat-square&logo=django)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🌟 Features

### Core Functionality
- **Product Management** - Browse, filter, and search products with categories and tags
- **Shopping Cart** - Add/remove items, update quantities with session-based storage
- **Order Processing** - Checkout flow with order history and status tracking
- **User Authentication** - Secure registration and login system
- **Wishlist** - Save favorite products for later
- **Reviews & Ratings** - Rate and review products with star ratings

### Advanced Features
- **Product Filtering** - Filter by category, price range, and search keywords
- **Pagination** - Efficient product listing with pagination
- **Image Uploads** - Support for product images with Pillow
- **Email Notifications** - Order confirmation and cancellation emails
- **Session-Based Cart** - No database overhead for temporary carts
- **Admin Interface** - Django admin for content management
- **API Endpoints** - RESTful API with JWT authentication and Swagger docs

### Technology Stack
- **Backend**: Django 5.2.14
- **Database**: PostgreSQL (production) / SQLite (development)
- **API**: Django REST Framework + drf-spectacular (Swagger/Redoc)
- **Authentication**: Django built-in + JWT
- **Async Tasks**: Celery + Redis
- **Caching**: Redis + django-redis
- **Image Handling**: Pillow
- **Server**: Gunicorn + WhiteNoise
- **Filtering**: django-filter

---

## 📋 Prerequisites

- Python 3.11+
- pip (Python package manager)
- PostgreSQL (optional, SQLite for development)
- Redis (optional, for Celery and caching)

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/shopsphere.git
cd shopsphere
```

### 2. Create Virtual Environment
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
```

### 5. Database Setup
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

---

## 📦 Project Structure

```
shopsphere/
├── accounts/              # User authentication & profiles
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── products/              # Product catalog management
│   ├── migrations/
│   ├── models.py          # Product, Category, Tag models
│   ├── views.py
│   ├── filters.py         # Product filtering logic
│   ├── cache.py           # Caching utilities
│   ├── signals.py         # Signal handlers
│   ├── management/        # Custom management commands
│   │   └── commands/
│   │       └── seed_data.py
│   └── urls.py
├── cart/                  # Shopping cart functionality
│   ├── models.py
│   ├── views.py
│   ├── services.py        # Cart business logic
│   └── urls.py
├── orders/                # Order processing
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── services.py
│   ├── tasks.py           # Celery tasks
│   └── urls.py
├── wishlist/              # User wishlist management
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── reviews/               # Product reviews & ratings
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── api/                   # REST API endpoints
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── config/                # Project configuration
│   ├── settings.py        # Main settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── templates/             # HTML templates
│   ├── base.html
│   ├── products.html
│   ├── product_detail.html
│   ├── cart.html
│   ├── login.html
│   └── ...
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🔧 Configuration

### Development Setup

```bash
# Start development server
python manage.py runserver

# Access the application
# Frontend: http://localhost:8000
# Admin: http://localhost:8000/admin
# API Docs: http://localhost:8000/api/v1/docs
```

### Redis Setup (Optional)

```bash
# macOS (using Homebrew)
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis-server
```

### Celery Setup (Optional)

```bash
# Terminal 1: Start Celery worker
celery -A config worker -l info

# Terminal 2: Start Celery beat (for scheduled tasks)
celery -A config beat -l info
```

---

## 📝 Usage

### Seed Sample Data

```bash
python manage.py seed_data
```

This creates sample products, categories, and tags for testing.

### Create Product

Navigate to `/admin` and create products with:
- Name
- Description
- Price
- Stock quantity
- Category
- Tags
- Product image

### Shopping Flow

1. Browse products at `/`
2. Filter by category or price
3. Click "Add to Cart"
4. View cart at `/cart/`
5. Proceed to checkout
6. Enter shipping information
7. Complete payment (demo only)
8. View order at `/orders/history/`

### API Usage

#### Get All Products
```bash
curl http://localhost:8000/api/v1/products/
```

#### Get Product Details
```bash
curl http://localhost:8000/api/v1/products/{product_id}/
```

#### Create Review
```bash
curl -X POST http://localhost:8000/api/v1/reviews/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"rating": 5, "comment": "Great product!"}'
```

#### API Documentation
- **Swagger UI**: http://localhost:8000/api/v1/docs/
- **ReDoc**: http://localhost:8000/api/v1/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/v1/schema/

---

## 🗄️ Database Models

### Product
```python
- id (Primary Key)
- name (CharField)
- slug (SlugField)
- description (TextField)
- price (DecimalField)
- stock (IntegerField)
- category (ForeignKey)
- tags (ManyToManyField)
- image (ImageField)
- is_active (BooleanField)
- created_at (DateTimeField)
- updated_at (DateTimeField)
```

### Order
```python
- id (Primary Key)
- user (ForeignKey)
- status (CharField: pending, completed, cancelled)
- total_amount (DecimalField)
- items (ManyToManyField via OrderItem)
- created_at (DateTimeField)
- updated_at (DateTimeField)
```

### Review
```python
- id (Primary Key)
- product (ForeignKey)
- user (ForeignKey)
- rating (IntegerField: 1-5)
- comment (TextField)
- created_at (DateTimeField)
```

---

## 🛠️ Development

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test cart

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Code Style & Linting

```bash
# Install linting tools
pip install flake8 black

# Format code
black .

# Check code style
flake8 .
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

---

## 🔒 Security Features

- CSRF protection on all forms
- Session-based authentication
- Password hashing with Django's default hasher
- SQL injection prevention via ORM
- XSS protection via template auto-escaping
- Secure headers configuration (development ready)
- JWT tokens for API authentication

---

## 📦 Deployment

### Using Gunicorn

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Docker Support (Optional)

Create a `Dockerfile` and `docker-compose.yml` for containerized deployment.

### Environment Variables for Production

```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@host/dbname
REDIS_URL=redis://redis-host:6379/0
```

---

## 🐛 Troubleshooting

### Cart Items Not Persisting
- Ensure sessions middleware is enabled
- Check `SESSION_ENGINE` in settings
- Clear browser cookies and try again

### Static Files Not Loading
```bash
python manage.py collectstatic --clear --noinput
```

### Database Connection Issues
```bash
# Check PostgreSQL service
psql -U postgres -d shopsphere

# Reset migrations (development only)
python manage.py migrate --fake products zero
python manage.py migrate
```

### Email Not Sending
- Configure email backend in settings
- Check email service credentials in `.env`
- Review console email output in development

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1/
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/` | List all products |
| GET | `/products/{id}/` | Get product details |
| GET | `/products/{id}/reviews/` | Get product reviews |
| POST | `/reviews/` | Create review (authenticated) |
| GET | `/cart/` | Get current cart |
| POST | `/cart/add/{product_id}/` | Add to cart |
| POST | `/orders/` | Create order (authenticated) |
| GET | `/orders/history/` | Order history (authenticated) |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👨‍💻 Author

**ShopSphere Development Team**

---

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: support@shopsphere.local
- Documentation: [Wiki Link]

---

## 🗺️ Roadmap

- [ ] Payment gateway integration (Stripe/PayPal)
- [ ] User profile management
- [ ] Advanced analytics dashboard
- [ ] Mobile app
- [ ] Social authentication (Google, GitHub)
- [ ] Product recommendations engine
- [ ] Multi-language support
- [ ] Inventory management system

---

## 📊 Stats

- **Total Products**: Browse thousands of products
- **Users**: Secure user management system
- **Orders**: Complete order tracking
- **Reviews**: Community-driven product ratings

---

**Last Updated**: May 2026  
**Version**: 1.0.0
