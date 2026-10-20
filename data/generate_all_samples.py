"""
Generator for 5 diverse, realistic retail/commercial datasets for ProfitLens.
Each dataset captures unique operational realities:
1. Omnichannel Retail Benchmark (data/sample_retail_data.csv)
2. Global Superstore - Tech, Office & Furniture (data/global_superstore.csv)
3. Fashion & Apparel E-Commerce (data/fashion_apparel.csv)
4. D2C Health, Beauty & Cosmetics (data/d2c_beauty_wellness.csv)
5. B2B Hardware & SaaS Subscriptions (data/b2b_saas_hardware.csv)
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

def random_date(start_date: datetime, end_date: datetime) -> datetime:
    delta_days = (end_date - start_date).days
    day_offset = random.randint(0, delta_days)
    hour = random.randint(8, 22)
    minute = random.randint(0, 59)
    return start_date + timedelta(days=day_offset, hours=hour, minutes=minute)


def generate_global_superstore(num_orders: int = 2500, seed: int = 101) -> pd.DataFrame:
    """Classic multi-category superstore: Furniture, Technology, Office Supplies."""
    random.seed(seed)
    np.random.seed(seed)
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    regions = ["East", "West", "Central", "South"]
    catalog = {
        "Technology": [
            ("Pro UltraBook 15\"", 1199.99, 780.00, 0.05, 18.0),
            ("Wireless Laser Printer", 279.99, 160.00, 0.08, 14.0),
            ("Smartphone Dock Station", 89.99, 42.00, 0.10, 6.5),
            ("External 4TB SSD", 179.99, 105.00, 0.05, 5.0),
            ("Noise-Canceling Headset", 149.99, 75.00, 0.08, 5.5),
        ],
        "Furniture": [
            ("Ergonomic Mesh Office Chair", 289.99, 180.00, 0.15, 32.0),
            ("Motorized Standing Desk", 499.99, 310.00, 0.18, 48.0),
            ("Modular 4-Shelf Bookcase", 189.99, 115.00, 0.20, 28.0),
            ("Conference Room Credenza", 650.00, 420.00, 0.22, 55.0),
            ("Mobile File Storage Cart", 119.99, 68.00, 0.15, 19.0),
        ],
        "Office Supplies": [
            ("Heavy-Duty Lever Arch Binder (Pack)", 34.99, 14.00, 0.05, 4.5),
            ("Premium Recycled Copy Paper 10 Reams", 52.99, 28.00, 0.05, 9.0),
            ("Desktop Gel Pen Tub (60 ct)", 24.99, 8.50, 0.08, 3.0),
            ("Mesh Desk Organizer Set", 29.99, 12.00, 0.10, 4.0),
            ("Heavy-Duty Electric Stapler", 45.99, 20.00, 0.08, 4.5),
        ],
    }
    
    rows = []
    line_counter = 1
    for order_num in range(1, num_orders + 1):
        order_id = f"GSS-{order_num:06d}"
        order_dt = random_date(start_date, end_date)
        region = random.choices(regions, weights=[0.32, 0.28, 0.22, 0.18])[0]
        customer_id = f"CUST-SS-{random.randint(100, 999)}"
        num_items = random.choices([1, 2, 3, 4], weights=[0.45, 0.35, 0.15, 0.05])[0]
        
        for _ in range(num_items):
            category = random.choices(["Technology", "Furniture", "Office Supplies"], weights=[0.35, 0.25, 0.40])[0]
            item_name, base_price, unit_cost, def_disc, base_ship = random.choice(catalog[category])
            
            # Furniture in Central/South often had unprofitable deep discounts in 2024
            disc_rate = def_disc
            if category == "Furniture" and region in ["Central", "South"] and order_dt.year == 2024:
                disc_rate += random.uniform(0.10, 0.25)
            else:
                disc_rate += random.uniform(-0.03, 0.08)
            disc_rate = max(0.0, min(0.45, disc_rate))
            
            unit_price = round(base_price * (1.0 + random.uniform(-0.04, 0.04)), 2)
            discount_amount = round(unit_price * disc_rate, 2)
            quantity = random.choices([1, 2, 3, 5, 8], weights=[0.60, 0.22, 0.10, 0.05, 0.03])[0]
            if category == "Office Supplies":
                quantity = random.choices([1, 2, 4, 8, 12], weights=[0.40, 0.25, 0.15, 0.12, 0.08])[0]
            
            shipping_cost = round(base_ship * (1.0 + random.uniform(-0.15, 0.25)), 2)
            marketing_cost = round(random.uniform(2.50, 9.00), 2)
            
            # Return rate: Furniture has higher return rates
            ret_prob = 0.04 if category == "Office Supplies" else (0.12 if category == "Furniture" else 0.07)
            returned = 1 if random.random() < ret_prob else 0
            
            rows.append({
                "order_id": order_id,
                "line_item_id": f"LINE-SS-{line_counter:07d}",
                "order_date": order_dt.strftime("%Y-%m-%d"),
                "customer_id": customer_id,
                "region": region,
                "product_category": category,
                "product_name": item_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "unit_cost": unit_cost,
                "discount": discount_amount,
                "shipping_cost": shipping_cost,
                "marketing_cost": marketing_cost,
                "returned": returned,
                "order_status": "Returned" if returned == 1 else "Completed"
            })
            line_counter += 1
            
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA_DIR, "global_superstore.csv"), index=False)
    return df


def generate_fashion_apparel(num_orders: int = 2800, seed: int = 202) -> pd.DataFrame:
    """Fashion e-commerce: high return rates, steep seasonality, size/fit dynamics."""
    random.seed(seed)
    np.random.seed(seed)
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    regions = ["Northeast", "Midwest", "Southeast", "West Coast"]
    catalog = {
        "Footwear": [
            ("Pro Marathon Running Shoes", 135.00, 48.00, 0.22),
            ("Leather Chelsea Boots", 165.00, 62.00, 0.24),
            ("Minimalist White Sneakers", 88.00, 28.00, 0.18),
            ("Trail Hiking Lows", 115.00, 42.00, 0.20),
        ],
        "Dresses & Outerwear": [
            ("Tailored Wool Overcoat", 220.00, 85.00, 0.20),
            ("Silk Midi Wrap Dress", 145.00, 42.00, 0.25),
            ("Waterproof Technical Parka", 195.00, 72.00, 0.16),
            ("Ribbed Knit Sweater Dress", 98.00, 32.00, 0.22),
        ],
        "Activewear": [
            ("High-Rise Compression Leggings", 68.00, 18.00, 0.12),
            ("Seamless Tech Sports Bra", 42.00, 11.50, 0.10),
            ("Breathable Running Shorts", 45.00, 13.00, 0.14),
            ("Polartec Thermal Zip Top", 78.00, 24.00, 0.12),
        ],
        "Casual Tops & Bottoms": [
            ("Organic Cotton Heavyweight Tee", 34.00, 8.50, 0.08),
            ("Slim Selvedge Denim Jeans", 110.00, 38.00, 0.18),
            ("Garment-Dyed French Terry Hoodie", 75.00, 22.00, 0.12),
            ("Pleated Linen Trouser", 85.00, 27.00, 0.19),
        ],
        "Accessories": [
            ("Full-Grain Leather Belt", 48.00, 14.00, 0.05),
            ("Merino Beanie & Scarf Set", 55.00, 16.00, 0.08),
            ("Canvas Travel Duffel", 95.00, 32.00, 0.06),
            ("UV-Polarized Aviator Sunglasses", 65.00, 18.00, 0.07),
        ]
    }
    
    rows = []
    line_counter = 1
    for order_num in range(1, num_orders + 1):
        order_id = f"FSH-{order_num:06d}"
        order_dt = random_date(start_date, end_date)
        region = random.choices(regions, weights=[0.35, 0.20, 0.22, 0.23])[0]
        customer_id = f"CUST-FSH-{random.randint(1000, 9999)}"
        num_items = random.choices([1, 2, 3], weights=[0.50, 0.35, 0.15])[0]
        
        # Holiday / Black Friday surge in discounts (Nov-Dec)
        is_holiday_sale = order_dt.month in [11, 12]
        
        for _ in range(num_items):
            category = random.choices(
                ["Footwear", "Dresses & Outerwear", "Activewear", "Casual Tops & Bottoms", "Accessories"],
                weights=[0.25, 0.25, 0.22, 0.20, 0.08]
            )[0]
            item_name, base_price, unit_cost, ret_prob = random.choice(catalog[category])
            
            disc_rate = random.uniform(0.05, 0.22)
            if is_holiday_sale:
                disc_rate += random.uniform(0.10, 0.20)
            disc_rate = min(0.50, disc_rate)
            
            unit_price = round(base_price * (1.0 + random.uniform(-0.03, 0.03)), 2)
            discount_amount = round(unit_price * disc_rate, 2)
            quantity = random.choices([1, 2, 3], weights=[0.82, 0.15, 0.03])[0]
            
            shipping_cost = round(random.uniform(4.50, 9.50), 2)
            marketing_cost = round(random.uniform(5.00, 14.00), 2)
            
            # High return rate in fashion
            returned = 1 if random.random() < ret_prob else 0
            
            rows.append({
                "order_id": order_id,
                "line_item_id": f"LINE-FSH-{line_counter:07d}",
                "order_date": order_dt.strftime("%Y-%m-%d"),
                "customer_id": customer_id,
                "region": region,
                "product_category": category,
                "product_name": item_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "unit_cost": unit_cost,
                "discount": discount_amount,
                "shipping_cost": shipping_cost,
                "marketing_cost": marketing_cost,
                "returned": returned,
                "order_status": "Returned" if returned == 1 else "Completed"
            })
            line_counter += 1
            
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA_DIR, "fashion_apparel.csv"), index=False)
    return df


def generate_d2c_beauty_wellness(num_orders: int = 2600, seed: int = 303) -> pd.DataFrame:
    """Direct-to-consumer cosmetics: high gross margins (70%+), significant CAC."""
    random.seed(seed)
    np.random.seed(seed)
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    regions = ["East Coast", "West Coast", "South", "Central"]
    catalog = {
        "Skincare": [
            ("Vitamin C Brightening Serum 30ml", 58.00, 8.50),
            ("Hydrating Hyaluronic Acid Cream", 44.00, 6.20),
            ("Gentle Cleansing Oil & Foam", 32.00, 4.50),
            ("Multi-Peptide Night Renewal Balm", 68.00, 10.50),
            ("Broad Spectrum Mineral Sunscreen SPF 50", 36.00, 5.80),
        ],
        "Haircare": [
            ("Bond Repair Treatment Mask 250ml", 42.00, 7.00),
            ("Scalp Detox Exfoliating Shampoo", 28.00, 4.20),
            ("Botanical Leave-In Hair Oil", 34.00, 5.20),
            ("Volumizing Biotin Conditioner", 28.00, 4.10),
        ],
        "Supplements & Wellness": [
            ("Marine Collagen Peptide Powder 300g", 49.00, 12.00),
            ("Sleep Support Magnesium Elixir", 38.00, 8.00),
            ("Daily Probiotic & Digestive Enzymes", 35.00, 7.20),
            ("Stress Relief Ashwagandha Drops", 30.00, 6.00),
        ],
        "Cosmetics": [
            ("Weightless Matte Foundation 30ml", 42.00, 7.20),
            ("Dewy Multi-Stick Blush & Lip", 26.00, 3.80),
            ("Tubing Lengthening Mascara", 24.00, 3.20),
            ("Hydra-Glaze Tinted Lip Oil", 22.00, 2.80),
        ]
    }
    
    rows = []
    line_counter = 1
    for order_num in range(1, num_orders + 1):
        order_id = f"D2C-{order_num:06d}"
        order_dt = random_date(start_date, end_date)
        region = random.choices(regions, weights=[0.38, 0.32, 0.18, 0.12])[0]
        customer_id = f"CUST-D2C-{random.randint(100, 1500)}"
        num_items = random.choices([1, 2, 3, 4], weights=[0.40, 0.35, 0.18, 0.07])[0]
        
        # Rising ad CAC inflation in 2024
        ad_inflation = 1.35 if order_dt.year == 2024 else 1.0
        
        for _ in range(num_items):
            category = random.choices(
                ["Skincare", "Haircare", "Supplements & Wellness", "Cosmetics"],
                weights=[0.42, 0.22, 0.20, 0.16]
            )[0]
            item_name, base_price, unit_cost = random.choice(catalog[category])
            
            disc_rate = random.choices([0.0, 0.10, 0.15, 0.20], weights=[0.45, 0.30, 0.15, 0.10])[0]
            unit_price = round(base_price * (1.0 + random.uniform(-0.02, 0.02)), 2)
            discount_amount = round(unit_price * disc_rate, 2)
            quantity = random.choices([1, 2, 3], weights=[0.75, 0.20, 0.05])[0]
            
            shipping_cost = round(random.uniform(3.50, 6.50), 2)
            # High digital marketing acquisition cost per order item
            marketing_cost = round(random.uniform(9.00, 22.00) * ad_inflation, 2)
            
            # Low return rate in consumables
            returned = 1 if random.random() < 0.025 else 0
            
            rows.append({
                "order_id": order_id,
                "line_item_id": f"LINE-D2C-{line_counter:07d}",
                "order_date": order_dt.strftime("%Y-%m-%d"),
                "customer_id": customer_id,
                "region": region,
                "product_category": category,
                "product_name": item_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "unit_cost": unit_cost,
                "discount": discount_amount,
                "shipping_cost": shipping_cost,
                "marketing_cost": marketing_cost,
                "returned": returned,
                "order_status": "Returned" if returned == 1 else "Completed"
            })
            line_counter += 1
            
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA_DIR, "d2c_beauty_wellness.csv"), index=False)
    return df


def generate_b2b_saas_hardware(num_orders: int = 1800, seed: int = 404) -> pd.DataFrame:
    """B2B Technology & Subscriptions: high order values, contract discounts, low returns."""
    random.seed(seed)
    np.random.seed(seed)
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    regions = ["North America - East", "North America - West", "EMEA", "APAC"]
    catalog = {
        "Cloud Subscriptions": [
            ("Enterprise Analytics Seat (Annual)", 1200.00, 180.00),
            ("Cloud Data Warehouse Tier 2 (Mo)", 850.00, 240.00),
            ("Security & SSO Add-on Module", 450.00, 60.00),
            ("Developer API Tier (Annual)", 2400.00, 320.00),
        ],
        "Network Infrastructure": [
            ("Managed 48-Port PoE Switch", 1450.00, 920.00),
            ("Next-Gen Hardware Firewall Appliance", 2200.00, 1400.00),
            ("Wi-Fi 7 Enterprise Access Point (3-Pack)", 890.00, 540.00),
            ("Rackmount Uninterruptible Power Supply 3kVA", 1100.00, 710.00),
        ],
        "Professional Services": [
            ("Implementation & Migration Package (40 hrs)", 4000.00, 2200.00),
            ("Custom Data Integration Workflow", 2500.00, 1300.00),
            ("Onsite Security Assessment", 3200.00, 1600.00),
        ],
        "Hardware Accessories": [
            ("Optical Transceiver SFP+ 10G (Pack of 4)", 260.00, 110.00),
            ("Cat6A Shielded Patch Cable Bundle 50m", 120.00, 35.00),
            ("Enterprise PDU Vertical Rack Mount", 340.00, 175.00),
        ]
    }
    
    rows = []
    line_counter = 1
    for order_num in range(1, num_orders + 1):
        order_id = f"B2B-{order_num:05d}"
        order_dt = random_date(start_date, end_date)
        region = random.choices(regions, weights=[0.40, 0.30, 0.20, 0.10])[0]
        customer_id = f"ORG-{random.randint(100, 600)}"
        num_items = random.choices([1, 2, 3], weights=[0.60, 0.30, 0.10])[0]
        
        for _ in range(num_items):
            category = random.choices(
                ["Cloud Subscriptions", "Network Infrastructure", "Professional Services", "Hardware Accessories"],
                weights=[0.45, 0.30, 0.15, 0.10]
            )[0]
            item_name, base_price, unit_cost = random.choice(catalog[category])
            
            # Enterprise contract discounts (0% up to 25%)
            disc_rate = random.choices([0.0, 0.08, 0.15, 0.22], weights=[0.30, 0.35, 0.25, 0.10])[0]
            unit_price = round(base_price * (1.0 + random.uniform(-0.02, 0.05)), 2)
            discount_amount = round(unit_price * disc_rate, 2)
            quantity = random.choices([1, 2, 5, 10], weights=[0.70, 0.18, 0.08, 0.04])[0]
            
            # Services and software have 0 shipping; physical hardware has freight
            is_physical = category in ["Network Infrastructure", "Hardware Accessories"]
            shipping_cost = round(random.uniform(25.00, 95.00), 2) if is_physical else 0.0
            
            # B2B enterprise sales acquisition / SDR cost
            marketing_cost = round(random.uniform(40.00, 180.00), 2)
            
            returned = 1 if (is_physical and random.random() < 0.015) else 0
            
            rows.append({
                "order_id": order_id,
                "line_item_id": f"LINE-B2B-{line_counter:06d}",
                "order_date": order_dt.strftime("%Y-%m-%d"),
                "customer_id": customer_id,
                "region": region,
                "product_category": category,
                "product_name": item_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "unit_cost": unit_cost,
                "discount": discount_amount,
                "shipping_cost": shipping_cost,
                "marketing_cost": marketing_cost,
                "returned": returned,
                "order_status": "Returned" if returned == 1 else "Completed"
            })
            line_counter += 1
            
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA_DIR, "b2b_saas_hardware.csv"), index=False)
    return df


if __name__ == "__main__":
    print("Generating Global Superstore...")
    df1 = generate_global_superstore()
    print(f"Generated {len(df1)} rows.")
    
    print("Generating Fashion Apparel...")
    df2 = generate_fashion_apparel()
    print(f"Generated {len(df2)} rows.")
    
    print("Generating D2C Beauty & Wellness...")
    df3 = generate_d2c_beauty_wellness()
    print(f"Generated {len(df3)} rows.")
    
    print("Generating B2B SaaS & Hardware...")
    df4 = generate_b2b_saas_hardware()
    print(f"Generated {len(df4)} rows.")
    
    print("All 4 supplementary realistic datasets generated successfully in data/!")
