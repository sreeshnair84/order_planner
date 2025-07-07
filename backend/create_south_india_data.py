"""
South India FMCG Data Initialization Script
==========================================

Creates sample retailers, manufacturers, and route data for South India with realistic 
truck route combinations for up to 4 retailers per route, including FMCG products.

This script creates:
- 20 Retailers across major South Indian cities
- 8 Manufacturers across South Indian states specializing in FMCG products
- 15 Optimized truck routes covering retailer combinations
- Realistic FMCG product catalog (Shampoo, Soap, Toothpaste, etc.)
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.models.retailer import Retailer, Manufacturer, Route
    from app.models.order import Order
    from app.models.sku_item import OrderSKUItem
    from app.models.tracking import OrderTracking, EmailCommunication
    from app.models.trip_planning import RouteOrder, ManufacturingLocation, Truck
    from app.database.connection import AsyncSessionLocal, engine
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker, selectinload
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import text, select
    print("✅ Successfully imported models and database session")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure the backend database models are available")
    sys.exit(1)

# FMCG Product Categories and Sample Products
FMCG_PRODUCTS = {
    "Personal Care": [
        {
            "sku_code": "PC001",
            "product_name": "Pantene Pro-V Shampoo 400ml",
            "category": "Hair Care",
            "brand": "Pantene",
            "unit_price": 285.00,
            "weight_kg": 0.42,
            "volume_m3": 0.0004,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "hair_type": "all",
                "volume_ml": 400,
                "ingredients": "Pro-Vitamin B5, Antioxidants"
            }
        },
        {
            "sku_code": "PC002", 
            "product_name": "Head & Shoulders Anti-Dandruff Shampoo 340ml",
            "category": "Hair Care",
            "brand": "Head & Shoulders",
            "unit_price": 320.00,
            "weight_kg": 0.36,
            "volume_m3": 0.00035,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "hair_type": "dandruff-prone",
                "volume_ml": 340,
                "active_ingredient": "Zinc Pyrithione"
            }
        },
        {
            "sku_code": "PC003",
            "product_name": "Dove Beauty Bar Soap 100g",
            "category": "Bath & Body",
            "brand": "Dove",
            "unit_price": 45.00,
            "weight_kg": 0.1,
            "volume_m3": 0.0001,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "skin_type": "all",
                "weight_g": 100,
                "moisturizing": True
            }
        },
        {
            "sku_code": "PC004",
            "product_name": "Colgate Total Toothpaste 150g",
            "category": "Oral Care",
            "brand": "Colgate",
            "unit_price": 89.00,
            "weight_kg": 0.15,
            "volume_m3": 0.00015,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "fluoride_content": "1450ppm",
                "weight_g": 150,
                "whitening": True
            }
        },
        {
            "sku_code": "PC005",
            "product_name": "Pepsodent Whitening Toothpaste 100g",
            "category": "Oral Care",
            "brand": "Pepsodent",
            "unit_price": 65.00,
            "weight_kg": 0.1,
            "volume_m3": 0.0001,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "fluoride_content": "1000ppm",
                "weight_g": 100,
                "whitening": True
            }
        },
        {
            "sku_code": "PC006",
            "product_name": "Lux Soft Touch Body Wash 240ml",
            "category": "Bath & Body",
            "brand": "Lux",
            "unit_price": 145.00,
            "weight_kg": 0.25,
            "volume_m3": 0.00025,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "skin_type": "sensitive",
                "volume_ml": 240,
                "fragrance": "Rose & Almond Oil"
            }
        }
    ],
    "Household Care": [
        {
            "sku_code": "HC001",
            "product_name": "Surf Excel Matic Liquid Detergent 1L",
            "category": "Laundry",
            "brand": "Surf Excel",
            "unit_price": 265.00,
            "weight_kg": 1.05,
            "volume_m3": 0.001,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "machine_type": "front_load",
                "volume_ml": 1000,
                "stain_removal": True
            }
        },
        {
            "sku_code": "HC002",
            "product_name": "Ariel Powder Detergent 1kg",
            "category": "Laundry",
            "brand": "Ariel",
            "unit_price": 180.00,
            "weight_kg": 1.0,
            "volume_m3": 0.0015,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "weight_g": 1000,
                "machine_type": "top_load",
                "color_protection": True
            }
        },
        {
            "sku_code": "HC003",
            "product_name": "Vim Dishwash Liquid 500ml",
            "category": "Kitchen Care",
            "brand": "Vim",
            "unit_price": 85.00,
            "weight_kg": 0.52,
            "volume_m3": 0.0005,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "volume_ml": 500,
                "grease_cutting": True,
                "fragrance": "Lemon"
            }
        },
        {
            "sku_code": "HC004",
            "product_name": "Domex Toilet Cleaner 500ml",
            "category": "Bathroom Care",
            "brand": "Domex",
            "unit_price": 78.00,
            "weight_kg": 0.55,
            "volume_m3": 0.0005,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "volume_ml": 500,
                "disinfectant": True,
                "kills_germs": "99.9%"
            }
        }
    ],
    "Food & Beverages": [
        {
            "sku_code": "FB001",
            "product_name": "Maggi 2-Minute Noodles Masala 70g",
            "category": "Instant Food",
            "brand": "Maggi",
            "unit_price": 14.00,
            "weight_kg": 0.07,
            "volume_m3": 0.0001,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "weight_g": 70,
                "cooking_time": "2 minutes",
                "flavor": "Masala"
            }
        },
        {
            "sku_code": "FB002",
            "product_name": "Bru Instant Coffee 50g",
            "category": "Beverages",
            "brand": "Bru",
            "unit_price": 125.00,
            "weight_kg": 0.06,
            "volume_m3": 0.0001,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "weight_g": 50,
                "coffee_type": "instant",
                "roast": "medium"
            }
        },
        {
            "sku_code": "FB003",
            "product_name": "Tata Tea Gold 250g",
            "category": "Beverages",
            "brand": "Tata Tea",
            "unit_price": 155.00,
            "weight_kg": 0.25,
            "volume_m3": 0.00025,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "weight_g": 250,
                "tea_type": "black",
                "blend": "premium"
            }
        },
        {
            "sku_code": "FB004",
            "product_name": "Kissan Mixed Fruit Jam 500g",
            "category": "Spreads",
            "brand": "Kissan",
            "unit_price": 185.00,
            "weight_kg": 0.5,
            "volume_m3": 0.0005,
            "temperature_requirement": "AMBIENT",
            "fragile": True,
            "product_attributes": {
                "weight_g": 500,
                "fruit_content": "mixed",
                "sugar_content": "high"
            }
        }
    ],
    "Baby Care": [
        {
            "sku_code": "BC001",
            "product_name": "Pampers Baby Dry Pants Medium 56pcs",
            "category": "Diapers",
            "brand": "Pampers",
            "unit_price": 899.00,
            "weight_kg": 1.8,
            "volume_m3": 0.008,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "size": "Medium",
                "count": 56,
                "age_range": "6-11 months"
            }
        },
        {
            "sku_code": "BC002",
            "product_name": "Johnson's Baby Shampoo 200ml",
            "category": "Baby Bath",
            "brand": "Johnson's",
            "unit_price": 165.00,
            "weight_kg": 0.22,
            "volume_m3": 0.0002,
            "temperature_requirement": "AMBIENT",
            "fragile": False,
            "product_attributes": {
                "volume_ml": 200,
                "tear_free": True,
                "hypoallergenic": True
            }
        }
    ]
}

# South India retailers data
SOUTH_INDIA_RETAILERS = [
    # Tamil Nadu
    {
        "retailer_code": "TN001",
        "name": "Chennai Supermart",
        "contact_person": "Rajesh Kumar",
        "phone": "+91-9876543210",
        "email": "rajesh@chennaisms.com",
        "address": "123 T.Nagar Main Road, Chennai, Tamil Nadu 600017",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "pincode": "600017",
        "latitude": 13.0435,
        "longitude": 80.2513,
        "business_type": "SUPERMARKET",
        "category": "PREMIUM"
    },
    {
        "retailer_code": "TN002", 
        "name": "Coimbatore Fresh Foods",
        "contact_person": "Meera Devi",
        "phone": "+91-9876543211",
        "email": "meera@cbefresh.com",
        "address": "456 Race Course Road, Coimbatore, Tamil Nadu 641018",
        "city": "Coimbatore",
        "state": "Tamil Nadu", 
        "pincode": "641018",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "business_type": "RETAIL_CHAIN",
        "category": "STANDARD"
    },
    {
        "retailer_code": "TN003",
        "name": "Madurai Grocery Hub",
        "contact_person": "Sundar Raj",
        "phone": "+91-9876543212", 
        "email": "sundar@maduragrocery.com",
        "address": "789 West Masi Street, Madurai, Tamil Nadu 625001",
        "city": "Madurai",
        "state": "Tamil Nadu",
        "pincode": "625001", 
        "latitude": 9.9252,
        "longitude": 78.1198,
        "business_type": "GROCERY_STORE",
        "category": "BUDGET"
    },
    {
        "retailer_code": "TN004",
        "name": "Salem Trade Center",
        "contact_person": "Kamala Krishnan",
        "phone": "+91-9876543213",
        "email": "kamala@salemtrade.com", 
        "address": "321 Junction Main Road, Salem, Tamil Nadu 636001",
        "city": "Salem",
        "state": "Tamil Nadu",
        "pincode": "636001",
        "latitude": 11.6643,
        "longitude": 78.1460,
        "business_type": "WHOLESALE",
        "category": "BULK"
    },
    {
        "retailer_code": "TN005",
        "name": "Trichy Modern Store",
        "contact_person": "Venkat Subramanian",
        "phone": "+91-9876543214",
        "email": "venkat@trichymodern.com",
        "address": "654 Bharathiar Salai, Tiruchirappalli, Tamil Nadu 620001", 
        "city": "Tiruchirappalli",
        "state": "Tamil Nadu",
        "pincode": "620001",
        "latitude": 10.7905,
        "longitude": 78.7047,
        "business_type": "SUPERMARKET",
        "category": "STANDARD"
    },
    
    # Karnataka
    {
        "retailer_code": "KA001",
        "name": "Bangalore Metro Mart",
        "contact_person": "Priya Sharma",
        "phone": "+91-9876543215",
        "email": "priya@blrmetro.com",
        "address": "100 Brigade Road, Bangalore, Karnataka 560001",
        "city": "Bangalore", 
        "state": "Karnataka",
        "pincode": "560001",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "business_type": "HYPERMARKET",
        "category": "PREMIUM"
    },
    {
        "retailer_code": "KA002",
        "name": "Mysore Heritage Foods",
        "contact_person": "Gopal Rao",
        "phone": "+91-9876543216",
        "email": "gopal@mysoreheritage.com",
        "address": "234 Sayyaji Rao Road, Mysore, Karnataka 570001",
        "city": "Mysore",
        "state": "Karnataka",
        "pincode": "570001", 
        "latitude": 12.2958,
        "longitude": 76.6394,
        "business_type": "SPECIALTY_STORE",
        "category": "PREMIUM"
    },
    {
        "retailer_code": "KA003", 
        "name": "Hubli Commerce Point",
        "contact_person": "Anita Kulkarni",
        "phone": "+91-9876543217",
        "email": "anita@hublicommerce.com",
        "address": "567 Station Road, Hubli, Karnataka 580020",
        "city": "Hubli",
        "state": "Karnataka",
        "pincode": "580020",
        "latitude": 15.3647,
        "longitude": 75.1240,
        "business_type": "RETAIL_CHAIN", 
        "category": "STANDARD"
    },
    {
        "retailer_code": "KA004",
        "name": "Mangalore Coastal Stores",
        "contact_person": "Suresh Pai",
        "phone": "+91-9876543218",
        "email": "suresh@mangalorecoastal.com",
        "address": "890 Falnir Road, Mangalore, Karnataka 575001",
        "city": "Mangalore",
        "state": "Karnataka", 
        "pincode": "575001",
        "latitude": 12.9141,
        "longitude": 74.8560,
        "business_type": "GROCERY_STORE",
        "category": "STANDARD"
    },
    
    # Andhra Pradesh & Telangana
    {
        "retailer_code": "AP001",
        "name": "Hyderabad Tech Mall",
        "contact_person": "Ramesh Reddy", 
        "phone": "+91-9876543219",
        "email": "ramesh@hydtechmall.com",
        "address": "200 HITEC City, Hyderabad, Telangana 500081",
        "city": "Hyderabad",
        "state": "Telangana",
        "pincode": "500081",
        "latitude": 17.4399,
        "longitude": 78.3908,
        "business_type": "HYPERMARKET",
        "category": "PREMIUM"
    },
    {
        "retailer_code": "AP002",
        "name": "Vijayawada Central Market",
        "contact_person": "Lakshmi Naidu",
        "phone": "+91-9876543220",
        "email": "lakshmi@vjwcentral.com",
        "address": "345 MG Road, Vijayawada, Andhra Pradesh 520001",
        "city": "Vijayawada",
        "state": "Andhra Pradesh",
        "pincode": "520001",
        "latitude": 16.5062,
        "longitude": 80.6480,
        "business_type": "WHOLESALE",
        "category": "BULK"
    },
    {
        "retailer_code": "AP003",
        "name": "Visakhapatnam Port Stores",
        "contact_person": "Krishna Murthy",
        "phone": "+91-9876543221",
        "email": "krishna@vskpport.com", 
        "address": "678 Beach Road, Visakhapatnam, Andhra Pradesh 530001",
        "city": "Visakhapatnam",
        "state": "Andhra Pradesh",
        "pincode": "530001",
        "latitude": 17.6868,
        "longitude": 83.2185,
        "business_type": "SUPERMARKET",
        "category": "STANDARD"
    },
    {
        "retailer_code": "AP004",
        "name": "Tirupati Temple Mart",
        "contact_person": "Sita Devi",
        "phone": "+91-9876543222", 
        "email": "sita@tirupatimart.com",
        "address": "901 Tirumala Hills Road, Tirupati, Andhra Pradesh 517501",
        "city": "Tirupati",
        "state": "Andhra Pradesh",
        "pincode": "517501",
        "latitude": 13.6288,
        "longitude": 79.4192,
        "business_type": "SPECIALTY_STORE",
        "category": "PREMIUM"
    },
    
    # Kerala
    {
        "retailer_code": "KL001",
        "name": "Kochi Marine Foods",
        "contact_person": "Mohanan Nair",
        "phone": "+91-9876543223",
        "email": "mohanan@kochimarine.com",
        "address": "150 Marine Drive, Kochi, Kerala 682031",
        "city": "Kochi",
        "state": "Kerala",
        "pincode": "682031",
        "latitude": 9.9312,
        "longitude": 76.2673,
        "business_type": "SEAFOOD_SPECIALIST",
        "category": "SPECIALTY"
    },
    {
        "retailer_code": "KL002",
        "name": "Trivandrum Capital Stores",
        "contact_person": "Radha Kumari",
        "phone": "+91-9876543224",
        "email": "radha@tvcapital.com",
        "address": "275 MG Road, Trivandrum, Kerala 695001",
        "city": "Trivandrum",
        "state": "Kerala", 
        "pincode": "695001",
        "latitude": 8.5241,
        "longitude": 76.9366,
        "business_type": "GROCERY_STORE",
        "category": "STANDARD"
    },
    {
        "retailer_code": "KL003",
        "name": "Calicut Spice Depot",
        "contact_person": "Basheer Ahmed",
        "phone": "+91-9876543225",
        "email": "basheer@calicutspice.com",
        "address": "400 SM Street, Calicut, Kerala 673001", 
        "city": "Calicut",
        "state": "Kerala",
        "pincode": "673001",
        "latitude": 11.2588,
        "longitude": 75.7804,
        "business_type": "SPICE_TRADER",
        "category": "SPECIALTY"
    },
    {
        "retailer_code": "KL004",
        "name": "Kottayam Rubber Mart",
        "contact_person": "Thomas Joseph",
        "phone": "+91-9876543226",
        "email": "thomas@kottayamrubber.com",
        "address": "525 Rubber Board Road, Kottayam, Kerala 686001",
        "city": "Kottayam",
        "state": "Kerala",
        "pincode": "686001",
        "latitude": 9.5916,
        "longitude": 76.5222, 
        "business_type": "INDUSTRIAL_SUPPLY",
        "category": "BULK"
    },
    
    # Puducherry
    {
        "retailer_code": "PY001",
        "name": "Pondicherry French Quarter",
        "contact_person": "Marie Claire",
        "phone": "+91-9876543227",
        "email": "marie@pondyfrench.com",
        "address": "50 Rue Suffren, Puducherry 605001",
        "city": "Puducherry", 
        "state": "Puducherry",
        "pincode": "605001",
        "latitude": 11.9416,
        "longitude": 79.8083,
        "business_type": "BOUTIQUE_STORE",
        "category": "PREMIUM"
    },
    
    # Lakshadweep  
    {
        "retailer_code": "LD001",
        "name": "Kavaratti Island Supplies",
        "contact_person": "Hassan Ali",
        "phone": "+91-9876543228",
        "email": "hassan@kavarattisupply.com",
        "address": "Beach Road, Kavaratti, Lakshadweep 682555",
        "city": "Kavaratti",
        "state": "Lakshadweep",
        "pincode": "682555",
        "latitude": 10.5669,
        "longitude": 72.6420,
        "business_type": "ISLAND_STORE", 
        "category": "REMOTE"
    }
]

# South India manufacturers data - Updated for FMCG products
SOUTH_INDIA_MANUFACTURERS = [
    {
        "manufacturer_code": "MFG001",
        "company_name": "South India Personal Care Ltd",
        "contact_person": "Dr. A. Selvakumar",
        "phone": "+91-9876540001",
        "email": "contact@sipcl.com",
        "address": "Industrial Estate, Ambattur, Chennai, Tamil Nadu 600058",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "pincode": "600058",
        "latitude": 13.1143,
        "longitude": 80.1548,
        "specialization": "Personal Care Products - Shampoo, Soap, Toothpaste",
        "product_categories": ["Hair Care", "Bath & Body", "Oral Care"],
        "capacity_tons_per_month": 5000,
        "certifications": ["ISO_22000", "FSSAI", "GMP"],
        "established_year": 1995
    },
    {
        "manufacturer_code": "MFG002", 
        "company_name": "Karnataka Household Products",
        "contact_person": "Suresh B. Patil",
        "phone": "+91-9876540002",
        "email": "info@khp.com",
        "address": "Electronic City, Hosur Road, Bangalore, Karnataka 560100",
        "city": "Bangalore",
        "state": "Karnataka",
        "pincode": "560100",
        "latitude": 12.8456,
        "longitude": 77.6632,
        "specialization": "Household Care Products - Detergents, Cleaners",
        "product_categories": ["Laundry", "Kitchen Care", "Bathroom Care"],
        "capacity_tons_per_month": 3500,
        "certifications": ["ISO_14001", "FSSAI", "BIS"],
        "established_year": 1988
    },
    {
        "manufacturer_code": "MFG003",
        "company_name": "Andhra Food Products Ltd",
        "contact_person": "Venkata Ramana",
        "phone": "+91-9876540003", 
        "email": "sales@afpl.com",
        "address": "APIIC Industrial Park, Guntur, Andhra Pradesh 522006",
        "city": "Guntur",
        "state": "Andhra Pradesh",
        "pincode": "522006",
        "latitude": 16.3067,
        "longitude": 80.4365,
        "specialization": "Food & Beverages - Instant Foods, Beverages",
        "product_categories": ["Instant Food", "Beverages", "Spreads"],
        "capacity_tons_per_month": 2000,
        "certifications": ["ISO_22000", "FSSAI", "HACCP"],
        "established_year": 1975
    },
    {
        "manufacturer_code": "MFG004",
        "company_name": "Kerala Baby Care Industries",
        "contact_person": "P.K. Radhakrishnan",
        "phone": "+91-9876540004",
        "email": "orders@kbci.com", 
        "address": "Industrial Park, Kochi, Kerala 682017",
        "city": "Kochi",
        "state": "Kerala",
        "pincode": "682017",
        "latitude": 9.9633,
        "longitude": 76.2439,
        "specialization": "Baby Care Products - Diapers, Baby Bath Products",
        "product_categories": ["Diapers", "Baby Bath", "Baby Food"],
        "capacity_tons_per_month": 1500,
        "certifications": ["ISO_22000", "FSSAI", "BIS"],
        "established_year": 1962
    },
    {
        "manufacturer_code": "MFG005",
        "company_name": "Hyderabad Multi-FMCG Corp",
        "contact_person": "Dr. Rajesh Kumar",
        "phone": "+91-9876540005",
        "email": "manufacturing@hmfc.com",
        "address": "Genome Valley, Shamirpet, Hyderabad, Telangana 500078",
        "city": "Hyderabad",
        "state": "Telangana", 
        "pincode": "500078",
        "latitude": 17.4435,
        "longitude": 78.4023,
        "specialization": "Multi-category FMCG - Personal Care, Household, Food",
        "product_categories": ["Hair Care", "Laundry", "Instant Food"],
        "capacity_tons_per_month": 800,
        "certifications": ["ISO_22000", "GMP", "FSSAI"],
        "established_year": 2005
    },
    {
        "manufacturer_code": "MFG006",
        "company_name": "Coimbatore Consumer Goods",
        "contact_person": "Meenakshi Sundaram",
        "phone": "+91-9876540006",
        "email": "production@ccgl.com",
        "address": "Textile Park, Tirupur Road, Coimbatore, Tamil Nadu 641604",
        "city": "Coimbatore",
        "state": "Tamil Nadu",
        "pincode": "641604",
        "latitude": 11.0510,
        "longitude": 76.9853,
        "specialization": "Personal Care & Household Products", 
        "product_categories": ["Bath & Body", "Kitchen Care", "Oral Care"],
        "capacity_tons_per_month": 1200,
        "certifications": ["ISO_22000", "FSSAI", "GMP"],
        "established_year": 1980
    },
    {
        "manufacturer_code": "MFG007",
        "company_name": "Mangalore Specialty Products",
        "contact_person": "Shivaram Kamath",
        "phone": "+91-9876540007",
        "email": "export@msp.com",
        "address": "Industrial Area, Baikampady, Mangalore, Karnataka 575011",
        "city": "Mangalore",
        "state": "Karnataka",
        "pincode": "575011",
        "latitude": 12.8832,
        "longitude": 74.9234,
        "specialization": "Premium Personal Care & Food Products",
        "product_categories": ["Hair Care", "Beverages", "Spreads"],
        "capacity_tons_per_month": 600,
        "certifications": ["ISO_22000", "FSSAI", "ORGANIC"],
        "established_year": 1971
    },
    {
        "manufacturer_code": "MFG008",
        "company_name": "Visakhapatnam FMCG Hub",
        "contact_person": "Srinivasa Rao",
        "phone": "+91-9876540008",
        "email": "business@vfh.com",
        "address": "Industrial Zone, Visakhapatnam, Andhra Pradesh 530012",
        "city": "Visakhapatnam", 
        "state": "Andhra Pradesh",
        "pincode": "530012",
        "latitude": 17.7231,
        "longitude": 83.3100,
        "specialization": "Multi-category FMCG Distribution Hub",
        "product_categories": ["Personal Care", "Household Care", "Food & Beverages"],
        "capacity_tons_per_month": 2500,
        "certifications": ["ISO_22000", "FSSAI", "BIS"],
        "established_year": 1992
    }
]

# Optimized truck routes with up to 4 retailers each
SOUTH_INDIA_ROUTES = [
    {
        "route_code": "SI_R001",
        "route_name": "Chennai Metro Circuit",
        "origin_manufacturer": "MFG001",  # Tamil Nadu Foods Ltd
        "route_type": "METRO_DELIVERY",
        "estimated_distance_km": 85,
        "estimated_duration_hours": 6,
        "vehicle_type": "MEDIUM_TRUCK",
        "retailers": ["TN001"],  # Chennai Supermart only (high volume)
        "delivery_frequency": "DAILY",
        "preferred_delivery_time": "08:00-12:00"
    },
    {
        "route_code": "SI_R002", 
        "route_name": "Tamil Nadu Western Loop",
        "origin_manufacturer": "MFG001",
        "route_type": "REGIONAL_CIRCUIT",
        "estimated_distance_km": 280,
        "estimated_duration_hours": 8,
        "vehicle_type": "LARGE_TRUCK",
        "retailers": ["TN002", "TN004", "TN005"],  # Coimbatore, Salem, Trichy
        "delivery_frequency": "TWICE_WEEKLY",
        "preferred_delivery_time": "06:00-18:00"
    },
    {
        "route_code": "SI_R003",
        "route_name": "Southern Tamil Nadu Route", 
        "origin_manufacturer": "MFG001",
        "route_type": "REGIONAL_CIRCUIT",
        "estimated_distance_km": 220,
        "estimated_duration_hours": 7,
        "vehicle_type": "MEDIUM_TRUCK",
        "retailers": ["TN003", "AP004"],  # Madurai, Tirupati
        "delivery_frequency": "WEEKLY",
        "preferred_delivery_time": "07:00-16:00"
    },
    {
        "route_code": "SI_R004",
        "route_name": "Bangalore Express",
        "origin_manufacturer": "MFG002",  # Karnataka Dairy Products
        "route_type": "METRO_DELIVERY", 
        "estimated_distance_km": 45,
        "estimated_duration_hours": 4,
        "vehicle_type": "REFRIGERATED_TRUCK",
        "retailers": ["KA001"],  # Bangalore Metro Mart only
        "delivery_frequency": "DAILY",
        "preferred_delivery_time": "05:00-09:00"
    },
    {
        "route_code": "SI_R005",
        "route_name": "Karnataka Heritage Circuit",
        "origin_manufacturer": "MFG002",
        "route_type": "HERITAGE_ROUTE",
        "estimated_distance_km": 195,
        "estimated_duration_hours": 6,
        "vehicle_type": "MEDIUM_TRUCK",
        "retailers": ["KA002", "KA004"],  # Mysore, Mangalore
        "delivery_frequency": "TWICE_WEEKLY", 
        "preferred_delivery_time": "08:00-15:00"
    },
    {
        "route_code": "SI_R006",
        "route_name": "North Karnataka Route",
        "origin_manufacturer": "MFG007",  # Mangalore Cashew Corporation  
        "route_type": "REGIONAL_CIRCUIT",
        "estimated_distance_km": 340,
        "estimated_duration_hours": 9,
        "vehicle_type": "LARGE_TRUCK",
        "retailers": ["KA003", "KA004"],  # Hubli, Mangalore
        "delivery_frequency": "WEEKLY",
        "preferred_delivery_time": "06:00-17:00"
    },
    {
        "route_code": "SI_R007",
        "route_name": "Andhra Pradesh Coastal",
        "origin_manufacturer": "MFG008",  # Visakhapatnam Steel Foods
        "route_type": "COASTAL_ROUTE",
        "estimated_distance_km": 450,
        "estimated_duration_hours": 10,
        "vehicle_type": "LARGE_TRUCK", 
        "retailers": ["AP003", "AP002", "AP001"],  # Visakhapatnam, Vijayawada, Hyderabad
        "delivery_frequency": "TWICE_WEEKLY",
        "preferred_delivery_time": "05:00-19:00"
    },
    {
        "route_code": "SI_R008",
        "route_name": "Guntur Spice Express",
        "origin_manufacturer": "MFG003",  # Andhra Spice Mills
        "route_type": "SPICE_DELIVERY",
        "estimated_distance_km": 180,
        "estimated_duration_hours": 5,
        "vehicle_type": "SPECIALIZED_TRUCK",
        "retailers": ["AP002", "AP004"],  # Vijayawada, Tirupati
        "delivery_frequency": "WEEKLY",
        "preferred_delivery_time": "09:00-16:00"
    },
    {
        "route_code": "SI_R009",
        "route_name": "Kerala Backwaters Circuit", 
        "origin_manufacturer": "MFG004",  # Kerala Coconut Industries
        "route_type": "SCENIC_ROUTE",
        "estimated_distance_km": 275,
        "estimated_duration_hours": 8,
        "vehicle_type": "MEDIUM_TRUCK",
        "retailers": ["KL001", "KL002", "KL004"],  # Kochi, Trivandrum, Kottayam
        "delivery_frequency": "TWICE_WEEKLY",
        "preferred_delivery_time": "07:00-17:00"
    },
    {
        "route_code": "SI_R010",
        "route_name": "Malabar Coast Route",
        "origin_manufacturer": "MFG004",
        "route_type": "COASTAL_ROUTE",
        "estimated_distance_km": 190,
        "estimated_duration_hours": 6,
        "vehicle_type": "MEDIUM_TRUCK",
        "retailers": ["KL001", "KL003"],  # Kochi, Calicut
        "delivery_frequency": "WEEKLY",
        "preferred_delivery_time": "08:00-16:00"
    },
    {
        "route_code": "SI_R011",
        "route_name": "Hyderabad Pharma Express",
        "origin_manufacturer": "MFG005",  # Hyderabad Pharma Foods
        "route_type": "PHARMA_DELIVERY",
        "estimated_distance_km": 120,
        "estimated_duration_hours": 4,
        "vehicle_type": "TEMPERATURE_CONTROLLED",
        "retailers": ["AP001", "KA001"],  # Hyderabad, Bangalore  
        "delivery_frequency": "DAILY",
        "preferred_delivery_time": "06:00-10:00"
    },
    {
        "route_code": "SI_R012",
        "route_name": "Cross-State Connector",
        "origin_manufacturer": "MFG006",  # Coimbatore Textile Mills
        "route_type": "INTER_STATE",
        "estimated_distance_km": 520,
        "estimated_duration_hours": 12,
        "vehicle_type": "LARGE_TRUCK",
        "retailers": ["TN002", "KA002", "KL003", "AP002"],  # Coimbatore, Mysore, Calicut, Vijayawada
        "delivery_frequency": "WEEKLY",
        "preferred_delivery_time": "04:00-20:00"
    },
    {
        "route_code": "SI_R013",
        "route_name": "Island & Union Territory Special",
        "origin_manufacturer": "MFG004",  # Kerala Coconut Industries  
        "route_type": "SPECIAL_DELIVERY",
        "estimated_distance_km": 850,
        "estimated_duration_hours": 24,
        "vehicle_type": "CONTAINER_TRUCK",
        "retailers": ["PY001", "LD001"],  # Puducherry, Lakshadweep
        "delivery_frequency": "MONTHLY",
        "preferred_delivery_time": "00:00-23:59"
    },
    {
        "route_code": "SI_R014",
        "route_name": "Southern Express Highway",
        "origin_manufacturer": "MFG001",  # Tamil Nadu Foods Ltd
        "route_type": "HIGHWAY_EXPRESS",
        "estimated_distance_km": 380,
        "estimated_duration_hours": 8,
        "vehicle_type": "LARGE_TRUCK",
        "retailers": ["TN001", "KA001", "AP001"],  # Chennai, Bangalore, Hyderabad
        "delivery_frequency": "TWICE_WEEKLY",
        "preferred_delivery_time": "05:00-15:00"
    },
    {
        "route_code": "SI_R015",
        "route_name": "Comprehensive South India",
        "origin_manufacturer": "MFG002",  # Karnataka Dairy Products
        "route_type": "MEGA_CIRCUIT",
        "estimated_distance_km": 980,
        "estimated_duration_hours": 20,
        "vehicle_type": "FLEET_CONVOY",
        "retailers": ["KA001", "TN001", "AP001", "KL001"],  # All major metros
        "delivery_frequency": "MONTHLY",
        "preferred_delivery_time": "00:00-23:59"
    }
]

async def initialize_south_india_data():
    """Initialize the database with South India FMCG data"""
    try:
        async with AsyncSessionLocal() as session:
            print("🚀 Starting South India FMCG data initialization...")
            
            # Clear existing data (routes first due to foreign key constraints)
            print("🧹 Clearing existing data...")
            await session.execute(text("DELETE FROM routes"))
            await session.execute(text("DELETE FROM retailers")) 
            await session.execute(text("DELETE FROM manufacturers"))
            await session.commit()
            
            # Create retailers
            print("🏪 Creating retailers...")
            retailer_objects = []
            for retailer_data in SOUTH_INDIA_RETAILERS:
                retailer = Retailer(
                    code=retailer_data["retailer_code"],
                    name=retailer_data["name"],
                    contact_email=retailer_data["email"],
                    contact_phone=retailer_data["phone"],
                    address=retailer_data["address"],
                    city=retailer_data["city"],
                    state=retailer_data["state"],
                    zip_code=retailer_data["pincode"],
                    country="India",
                    is_active=True,
                    notes=f"Business Type: {retailer_data['business_type']}, Category: {retailer_data['category']}"
                )
                retailer_objects.append(retailer)
                session.add(retailer)
            
            await session.commit()
            print(f"✅ Created {len(retailer_objects)} retailers")
            
            # Create manufacturers  
            print("🏭 Creating manufacturers...")
            manufacturer_objects = []
            for mfg_data in SOUTH_INDIA_MANUFACTURERS:
                manufacturer = Manufacturer(
                    code=mfg_data["manufacturer_code"],
                    name=mfg_data["company_name"],
                    contact_email=mfg_data["email"],
                    contact_phone=mfg_data["phone"],
                    address=mfg_data["address"],
                    city=mfg_data["city"],
                    state=mfg_data["state"],
                    zip_code=mfg_data["pincode"],
                    country="India",
                    is_active=True,
                    lead_time_days=7,
                    min_order_value=1000,
                    preferred_payment_terms="NET_30",
                    notes=f"Specializes in: {mfg_data['specialization']}"
                )
                manufacturer_objects.append(manufacturer)
                session.add(manufacturer)
            
            await session.commit()
            print(f"✅ Created {len(manufacturer_objects)} manufacturers")
            
            # Create retailer and manufacturer lookup dictionaries
            retailer_lookup = {r.code: r for r in retailer_objects}
            manufacturer_lookup = {m.code: m for m in manufacturer_objects}
            
            # Create routes
            print("� Creating routes...")
            route_objects = []
            for route_data in SOUTH_INDIA_ROUTES:
                # Find origin manufacturer
                origin_mfg = manufacturer_lookup.get(route_data["origin_manufacturer"])
                if not origin_mfg:
                    print(f"⚠️  Warning: Manufacturer {route_data['origin_manufacturer']} not found for route {route_data['route_code']}")
                    continue
                
                # Calculate approximate destination from first retailer
                first_retailer_code = route_data["retailers"][0] if route_data["retailers"] else None
                first_retailer = retailer_lookup.get(first_retailer_code) if first_retailer_code else None
                
                route = Route(
                    name=route_data["route_name"],
                    manufacturer_id=origin_mfg.id,
                    origin_city=origin_mfg.city,
                    origin_state=origin_mfg.state,
                    origin_country="India",
                    destination_city=first_retailer.city if first_retailer else "Multiple Cities",
                    destination_state=first_retailer.state if first_retailer else "Multiple States",
                    destination_country="India",
                    distance_km=route_data["estimated_distance_km"],
                    estimated_transit_days=max(1, route_data["estimated_duration_hours"] // 24),
                    transport_mode="truck",
                    cost_per_km=50,  # Default 50 rupees per km
                    max_weight_kg=route_data.get("max_weight_kg", 10000),
                    max_volume_m3=route_data.get("max_volume_m3", 50),
                    is_active=True,
                    notes=f"Vehicle: {route_data['vehicle_type']}, Frequency: {route_data['delivery_frequency']}, Retailers: {', '.join(route_data['retailers'])}"
                )
                route_objects.append(route)
                session.add(route)
                
            await session.commit()
            print(f"✅ Created {len(route_objects)} routes")
            
            # Create retailer-manufacturer associations based on routes
            print("🔗 Creating retailer-manufacturer associations...")
            associations_created = 0
            manufacturer_retailer_pairs = set()  # Track unique pairs to avoid duplicates
            
            for route_data in SOUTH_INDIA_ROUTES:
                # Find the manufacturer for this route
                manufacturer = manufacturer_lookup.get(route_data["origin_manufacturer"])
                if not manufacturer:
                    continue
                    
                # Associate retailers with this manufacturer
                for retailer_code in route_data["retailers"]:
                    retailer = retailer_lookup.get(retailer_code)
                    if retailer:
                        # Create unique pair to avoid duplicates
                        pair = (manufacturer.id, retailer.id)
                        if pair not in manufacturer_retailer_pairs:
                            # Insert directly into the association table to avoid lazy loading
                            await session.execute(text("""
                                INSERT INTO retailer_manufacturer_association (retailer_id, manufacturer_id)
                                VALUES (:retailer_id, :manufacturer_id)
                                ON CONFLICT (retailer_id, manufacturer_id) DO NOTHING
                            """), {
                                "retailer_id": retailer.id,
                                "manufacturer_id": manufacturer.id
                            })
                            manufacturer_retailer_pairs.add(pair)
                            associations_created += 1
            
            await session.commit()
            print(f"✅ Created {associations_created} retailer-manufacturer associations")
            
            # Print summary
            print("\n" + "="*60)
            print("🎉 SOUTH INDIA FMCG DATA INITIALIZATION COMPLETE!")
            print("="*60)
            print(f"📍 States Covered: Tamil Nadu, Karnataka, Andhra Pradesh, Telangana, Kerala, Puducherry, Lakshadweep")
            print(f"🏪 Total Retailers: {len(retailer_objects)}")
            print(f"🏭 Total Manufacturers: {len(manufacturer_objects)}")  
            print(f"🚛 Total Routes: {len(route_objects)}")
            print(f"🔗 Total Retailer-Manufacturer Links: {associations_created}")
            print(f"📦 Average Retailers per Route: {sum(len(r['retailers']) for r in SOUTH_INDIA_ROUTES) / len(SOUTH_INDIA_ROUTES):.1f}")
            
            print("\n💡 FMCG Product Categories Available:")
            for category, products in FMCG_PRODUCTS.items():
                print(f"   - {category}: {len(products)} products")
                for product in products[:2]:  # Show first 2 products as examples
                    print(f"     • {product['product_name']} ({product['brand']})")
            
            print("\n🚚 Vehicle Types Used:")
            vehicle_types = set(r["vehicle_type"] for r in SOUTH_INDIA_ROUTES)
            for vt in sorted(vehicle_types):
                count = sum(1 for r in SOUTH_INDIA_ROUTES if r["vehicle_type"] == vt)
                print(f"   - {vt}: {count} routes")
                
            print("\n📅 Delivery Frequencies:")
            frequencies = set(r["delivery_frequency"] for r in SOUTH_INDIA_ROUTES)
            for freq in sorted(frequencies):
                count = sum(1 for r in SOUTH_INDIA_ROUTES if r["delivery_frequency"] == freq)
                print(f"   - {freq}: {count} routes")
            
            print("\n✨ The FMCG system is now ready with comprehensive South India coverage!")
            print("✨ Routes are optimized for efficiency with up to 4 retailers per route.")
            print("✨ All major FMCG categories are represented in the product catalog.")
            print("✨ Manufacturers are specialized in different product categories.")
            
    except Exception as e:
        print(f"❌ Error during initialization: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

async def create_sample_fmcg_products():
    """Create sample FMCG product data for demonstration"""
    print("\n📦 Creating sample FMCG product data...")
    
    sample_products = []
    for category, products in FMCG_PRODUCTS.items():
        for product in products:
            sample_products.append(product)
    
    print(f"✅ Sample product catalog contains {len(sample_products)} FMCG products")
    print("📋 Product Categories:")
    for category, products in FMCG_PRODUCTS.items():
        print(f"   - {category}: {len(products)} products")
    
    return sample_products

def get_manufacturer_product_specialization():
    """Get the product specialization mapping for manufacturers"""
    return {
        "MFG001": ["Personal Care"],  # South India Personal Care Ltd
        "MFG002": ["Household Care"],  # Karnataka Household Products
        "MFG003": ["Food & Beverages"],  # Andhra Food Products Ltd
        "MFG004": ["Baby Care"],  # Kerala Baby Care Industries
        "MFG005": ["Personal Care", "Household Care", "Food & Beverages"],  # Hyderabad Multi-FMCG Corp
        "MFG006": ["Personal Care", "Household Care"],  # Coimbatore Consumer Goods
        "MFG007": ["Personal Care", "Food & Beverages"],  # Mangalore Specialty Products
        "MFG008": ["Personal Care", "Household Care", "Food & Beverages"]  # Visakhapatnam FMCG Hub
    }

if __name__ == "__main__":
    print("🌟 South India FMCG Data Initialization Script")
    print("🌟 Creating realistic retailers, manufacturers, and optimized routes")
    print("🌟 Including comprehensive FMCG product catalog")
    print("-" * 60)
    
    # Run the initialization
    asyncio.run(initialize_south_india_data())
    
    # Create sample products (demonstration)
    asyncio.run(create_sample_fmcg_products())
