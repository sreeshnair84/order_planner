# Trip Route Optimization System

## Overview

The Trip Route Optimization System is an advanced logistics and supply chain management solution designed for FMCG/OEM providers. It provides comprehensive order management, SKU consolidation, route optimization, and real-time tracking capabilities to maximize delivery efficiency and minimize operational costs.

## Key Features

### 🚚 Advanced Trip Planning & Optimization
- **SKU Consolidation**: Intelligent grouping of SKUs across multiple retailer orders for optimal trip planning
- **Route Optimization**: Advanced algorithms using distance matrix calculations, TSP (Traveling Salesman Problem) solving, and 2-opt optimization
- **Capacity Planning**: Automated analysis of manufacturing location capacities and truck utilization
- **Real-time Tracking**: Live monitoring of delivery routes with GPS integration and automated alerts

### 📊 Analytics & Business Intelligence
- **Performance Metrics**: Comprehensive KPI dashboard with efficiency, cost, and sustainability metrics
- **Optimization Logs**: Detailed tracking of optimization algorithms performance and improvements
- **Cost Savings Analysis**: ROI calculation and cost-benefit analysis for optimization initiatives
- **Sustainability Reporting**: Carbon footprint reduction and environmental impact metrics

### 🏭 Manufacturing & Logistics Management
- **Multi-location Support**: Management of multiple manufacturing locations and distribution centers
- **Fleet Management**: Truck assignment, capacity management, and availability tracking
- **Constraint-based Optimization**: Considers weight, volume, time windows, and special handling requirements
- **Dynamic Scheduling**: Adaptive scheduling based on real-time demand and capacity changes

## System Architecture

### Backend Components

#### Core Models
- **Trip Planning Models** (`app/models/trip_planning.py`):
  - `ManufacturingLocation`: Manufacturing facility management
  - `Truck`: Fleet vehicle tracking and capacity management
  - `DeliveryRoute`: Optimized delivery route planning
  - `RouteOrder`: Individual order assignments within routes
  - `ConsolidationGroup`: SKU consolidation management
  - `DeliveryTracking`: Real-time delivery progress tracking
  - `TripOptimizationLog`: Optimization performance logging

#### Optimization Engines
- **Trip Route Optimizer** (`app/services/trip_route_optimizer.py`):
  - Distance matrix calculation using Haversine formula
  - Advanced TSP solving with nearest neighbor and 2-opt improvements
  - Constraint validation (weight, volume, time windows)
  - Multi-objective optimization (distance, efficiency, capacity)

- **SKU Consolidation Engine** (`app/services/sku_consolidation_engine.py`):
  - Cross-order SKU consolidation algorithms
  - Geographic clustering for delivery efficiency
  - Trip group creation with capacity constraints
  - Consolidation efficiency scoring

#### API Endpoints

##### Trip Optimization (`/api/trips/`)
- `POST /optimize-routes`: Route optimization for multiple orders
- `POST /optimize-skus`: SKU consolidation across orders
- `GET /routes/{route_id}`: Detailed route information
- `GET /analytics`: Trip performance analytics
- `GET /manufacturing-locations`: Available manufacturing locations
- `GET /trucks`: Fleet availability and status
- `POST /routes/{route_id}/assign-truck`: Truck assignment to routes

##### Logistics Management (`/api/logistics/`)
- `POST /optimize-logistics`: Comprehensive logistics optimization
- `POST /capacity-planning`: Capacity planning analysis
- `POST /real-time-tracking`: Real-time tracking setup
- `GET /performance-metrics`: Performance KPI dashboard
- `GET /delivery-tracking/{order_id}`: Individual order tracking
- `GET /optimization-logs`: Optimization history and performance

### Frontend Components

#### Trip Planning Interface (`TripPlanningPage.js`)
- **Order Selection**: Multi-select interface for order grouping
- **Manufacturing Location Management**: Location selection and capacity viewing
- **Interactive Route Maps**: Leaflet-based mapping with route visualization
- **Optimization Controls**: Algorithm selection and parameter tuning
- **Results Dashboard**: Optimization results and performance metrics

#### Logistics Dashboard (`LogisticsDashboard.js`)
- **Real-time Metrics**: Live KPI monitoring with auto-refresh
- **Performance Analytics**: Chart.js-based visualizations
- **Sustainability Metrics**: Environmental impact tracking
- **Alert System**: Real-time notifications and alerts
- **Historical Analysis**: Trend analysis and performance tracking

## Optimization Algorithms

### Route Optimization
1. **Distance Matrix Generation**: Calculates distances between all delivery points using Haversine formula
2. **Nearest Neighbor Algorithm**: Greedy approach for initial route construction
3. **2-opt Optimization**: Local search improvement for route refinement
4. **Constraint Validation**: Ensures weight, volume, and time window compliance

### SKU Consolidation
1. **Geographic Clustering**: Groups SKUs by delivery location proximity
2. **Capacity Optimization**: Maximizes truck utilization while respecting constraints
3. **Efficiency Scoring**: Evaluates consolidation options based on multiple criteria
4. **Trip Group Creation**: Balances trip size with delivery efficiency

### Performance Metrics
- **Distance Optimization**: Minimizes total travel distance
- **Capacity Utilization**: Maximizes truck capacity usage
- **Time Efficiency**: Optimizes delivery time windows
- **Cost Reduction**: Reduces operational costs through consolidation
- **Sustainability**: Minimizes carbon footprint and fuel consumption

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Redis (for caching and real-time features)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python scripts/setup_database.py
python scripts/create_database.py
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm install leaflet react-leaflet chart.js react-chartjs-2
npm start
```

### Database Schema
The system uses PostgreSQL with the following key tables:
- `manufacturing_locations`: Manufacturing facility data
- `trucks`: Fleet vehicle information
- `delivery_routes`: Optimized route definitions
- `route_orders`: Order-to-route assignments
- `consolidation_groups`: SKU consolidation records
- `delivery_tracking`: Real-time tracking data
- `trip_optimization_logs`: Optimization performance logs

## API Usage Examples

### Optimize Routes
```bash
curl -X POST "http://localhost:8000/api/trips/optimize-routes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "order_ids": ["order-001", "order-002", "order-003"],
    "manufacturing_location_id": "mfg-001",
    "planned_date": "2024-01-15T08:00:00Z"
  }'
```

### SKU Consolidation
```bash
curl -X POST "http://localhost:8000/api/trips/optimize-skus" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "retailer_id": "retailer-001",
    "manufacturing_location_id": "mfg-001",
    "start_date": "2024-01-15T00:00:00Z",
    "end_date": "2024-01-22T23:59:59Z"
  }'
```

### Performance Metrics
```bash
curl -X GET "http://localhost:8000/api/logistics/performance-metrics?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Configuration

### Optimization Parameters
Key optimization parameters can be configured in the `TripRouteOptimizer` class:

```python
# Trip constraints
max_trip_duration = 8.0  # hours
max_delivery_stops = 20
sku_delivery_time_per_stop = 0.5  # hours
target_sku_min = 90
target_sku_max = 100
max_trip_weight = 25000  # kg
max_trip_volume = 100    # m3
```

### SKU Consolidation Settings
```python
# Consolidation constraints
target_sku_min = 90
target_sku_max = 100
max_trip_weight = 25000  # kg
max_trip_volume = 100    # m3
max_geographic_spread = 200  # km radius
```

## Testing

### Unit Tests
```bash
cd backend
python -m pytest tests/test_trip_optimization.py -v
```

### Integration Tests
```bash
python -m pytest tests/ -v --cov=app
```

### Performance Tests
The system includes performance tests for large-scale optimization scenarios:
- 500+ SKU optimization
- Multi-location route planning
- Concurrent optimization requests

## Monitoring & Analytics

### Key Performance Indicators (KPIs)
- **Route Efficiency**: Average improvement percentage from optimization
- **Capacity Utilization**: Percentage of truck capacity utilized
- **Cost Savings**: Dollar amount saved through optimization
- **Delivery Performance**: On-time delivery rate
- **Sustainability**: Carbon footprint reduction percentage

### Real-time Monitoring
- Route progress tracking
- Delivery status updates
- Alert notifications for delays or issues
- Performance metric dashboards

## Security & Compliance

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting
- Request validation and sanitization

### Data Protection
- Encrypted data storage
- Secure API endpoints
- Audit logging
- Privacy compliance features

## Scalability & Performance

### Optimization Techniques
- Asynchronous processing for large datasets
- Caching of optimization results
- Database query optimization
- Background task processing

### Horizontal Scaling
- Microservice architecture support
- Load balancing capabilities
- Distributed caching
- Database sharding support

## Future Enhancements

### Planned Features
- **Machine Learning Integration**: Predictive analytics for demand forecasting
- **Advanced OR-Tools Integration**: More sophisticated optimization algorithms
- **IoT Integration**: Real-time sensor data from trucks and warehouses
- **Mobile Applications**: Driver and manager mobile apps
- **Advanced Analytics**: Business intelligence and reporting suite
- **Third-party Integrations**: ERP, WMS, and TMS system connections

### Roadmap
- Q1 2024: Machine learning demand forecasting
- Q2 2024: Advanced route optimization with OR-Tools
- Q3 2024: Mobile application development
- Q4 2024: IoT and sensor integration

## Support & Documentation

### API Documentation
- Interactive API documentation available at `/docs`
- Postman collection for API testing
- OpenAPI/Swagger specification

### Developer Resources
- Code examples and tutorials
- Best practices guide
- Architecture documentation
- Troubleshooting guide

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

We welcome contributions! Please see our contributing guidelines and code of conduct.

## Contact

For support or questions:
- Email: support@orderplanner.com
- Documentation: https://docs.orderplanner.com
- GitHub Issues: https://github.com/yourorg/order-planner/issues
