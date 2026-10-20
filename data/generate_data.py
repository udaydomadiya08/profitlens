"""
Deterministic synthetic retail data generator for ProfitLens.
Generates realistic multi-item retail orders across 2023-2024 with embedded business trends.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_retail_dataset(
    num_orders: int = 5000,
    seed: int = 42,
    output_path: str = "data/sample_retail_data.csv"
) -> pd.DataFrame:
    """
    Generate synthetic retail transaction dataset with realistic financial distributions,
    seasonality, regional variation, and an embedded business anomaly for root-cause analysis.
    """
    random.seed(seed)
    np.random.seed(seed)

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range_days = (end_date - start_date).days

    regions = ["North", "South", "East", "West"]
    region_weights = [0.30, 0.25, 0.25, 0.20]

    categories = {
        "Electronics": {
            "items": [
                ("Noise-Cancelling Headphones", 149.99, 85.00),
                ("Wireless Ergonomic Keyboard", 69.99, 32.00),
                ("Ultra-HD 4K Monitor", 349.99, 210.00),
                ("Smart Home Hub Speaker", 99.99, 52.00),
                ("Portable Power Bank 20k", 39.99, 16.00),
                ("Smart Fitness Watch", 199.99, 115.00)
            ],
            "base_return_rate": 0.06,
            "base_discount_pct": 0.08
        },
        "Apparel": {
            "items": [
                ("Performance Running Shoes", 120.00, 48.00),
                ("Merino Wool Crewneck", 85.00, 30.00),
                ("Water-Resistant Windbreaker", 95.00, 36.00),
                ("Everyday Chino Pants", 55.00, 18.00),
                ("Moisture-Wicking Athletic Tee", 28.00, 8.50),
                ("Fleece Zip Hoodie", 65.00, 22.00)
            ],
            "base_return_rate": 0.12,
            "base_discount_pct": 0.15
        },
        "Home & Kitchen": {
            "items": [
                ("Stainless Steel Cookware Set", 219.99, 105.00),
                ("Precision Pour-Over Kettle", 59.99, 24.00),
                ("Cast Iron Skillet 12-inch", 44.99, 18.00),
                ("Air Fryer Deluxe 6Qt", 119.99, 58.00),
                ("Organic Bamboo Cutting Board", 29.99, 10.50),
                ("HEPA Air Purifier Compact", 129.99, 62.00)
            ],
            "base_return_rate": 0.05,
            "base_discount_pct": 0.10
        },
        "Beauty": {
            "items": [
                ("Hydrating Facial Serum 50ml", 48.00, 11.00),
                ("Vitamin C Glow Moisturizer", 38.00, 8.50),
                ("Botanical Exfoliating Cleanser", 26.00, 5.50),
                ("Mineral UV Sunscreen SPF50", 32.00, 7.00),
                ("Restorative Night Eye Cream", 42.00, 9.50)
            ],
            "base_return_rate": 0.03,
            "base_discount_pct": 0.07
        },
        "Sports": {
            "items": [
                ("Non-Slip Pro Yoga Mat", 45.00, 16.00),
                ("Adjustable Dumbbell Pair 25lb", 179.99, 88.00),
                ("Insulated Stainless Water Bottle", 30.00, 9.00),
                ("Carbon Fiber Trekking Poles", 75.00, 28.00),
                ("High-Density Foam Roller", 24.99, 7.50)
            ],
            "base_return_rate": 0.04,
            "base_discount_pct": 0.09
        }
    }

    category_names = list(categories.keys())
    category_weights = [0.28, 0.24, 0.20, 0.15, 0.13]

    rows = []
    line_item_counter = 1

    # Generate customer pool
    customer_ids = [f"CUST-{i:05d}" for i in range(1, 2001)]

    for order_num in range(1, num_orders + 1):
        order_id = f"ORD-{order_num:06d}"
        
        # Order date generation with monthly trend and Q4 holiday bump
        day_offset = random.randint(0, date_range_days)
        order_date = start_date + timedelta(days=day_offset)
        month = order_date.month
        year = order_date.year

        customer_id = random.choice(customer_ids)
        region = np.random.choice(regions, p=region_weights)

        # Multi-item orders (1 to 4 items per order)
        num_items = np.random.choice([1, 2, 3, 4], p=[0.55, 0.28, 0.12, 0.05])
        
        # Order-level base logistics & acquisition expense to allocate
        # Order shipping baseline: $6 - $15 based on items
        order_shipping_base = 5.0 + (num_items * 2.2) + random.uniform(0.5, 3.5)
        # Order marketing attribution baseline: $3 - $12
        order_marketing_base = random.uniform(2.5, 9.5)

        # Temporary buffer for order lines
        order_lines = []

        for _ in range(num_items):
            cat_name = np.random.choice(category_names, p=category_weights)
            cat_meta = categories[cat_name]
            item_name, list_price, base_cost = random.choice(cat_meta["items"])
            
            # Small random variation in price & cost
            price = round(list_price * random.uniform(0.96, 1.04), 2)
            cost = round(base_cost * random.uniform(0.97, 1.05), 2)
            
            # Quantity (usually 1, occasionally 2-3)
            qty = int(np.random.choice([1, 2, 3], p=[0.78, 0.18, 0.04]))

            # Base discount logic
            disc_rate = cat_meta["base_discount_pct"]
            
            # Embedded business anomaly:
            # In Q3 & Q4 of 2024, the South region launched an overly aggressive discount campaign
            # on Electronics and Apparel, but return rates surged and shipping logistics costs skyrocketed.
            if year == 2024 and month >= 7 and region == "South":
                if cat_name in ["Electronics", "Apparel"]:
                    disc_rate += 0.18  # heavy promotional cuts
            
            # Holiday promotional bump in November/December
            if month in [11, 12]:
                disc_rate += 0.06

            actual_disc_pct = max(0.0, min(0.45, np.random.normal(disc_rate, 0.04)))
            discount_per_unit = round(price * actual_disc_pct, 2)
            if discount_per_unit >= price:
                discount_per_unit = round(price * 0.5, 2)

            # Return probability
            return_prob = cat_meta["base_return_rate"]
            if year == 2024 and month >= 7 and region == "South" and cat_name == "Apparel":
                return_prob = 0.26 # Anomaly in South Apparel returns

            is_returned = 1 if (random.random() < return_prob) else 0

            order_lines.append({
                "order_id": order_id,
                "line_item_id": f"LINE-{line_item_counter:07d}",
                "order_date": order_date.strftime("%Y-%m-%d"),
                "customer_id": customer_id,
                "region": region,
                "product_category": cat_name,
                "product_name": item_name,
                "quantity": qty,
                "unit_price": price,
                "unit_cost": cost,
                "discount": discount_per_unit,
                "returned": is_returned,
                "order_status": "Returned" if is_returned == 1 else "Completed"
            })
            line_item_counter += 1

        # Allocate order-level shipping & marketing across lines proportionally
        total_order_gross = sum(l["quantity"] * l["unit_price"] for l in order_lines)
        for line in order_lines:
            line_gross = line["quantity"] * line["unit_price"]
            ratio = (line_gross / total_order_gross) if total_order_gross > 0 else (1.0 / num_items)
            
            # Logistics inflation in 2024 H2 for South
            shipping_multiplier = 1.35 if (year == 2024 and month >= 7 and region == "South") else 1.0
            
            line["marketing_cost"] = round(order_marketing_base * ratio, 2)
            line["shipping_cost"] = round(order_shipping_base * ratio * shipping_multiplier, 2)
            rows.append(line)

    df = pd.DataFrame(rows)
    # Sort chronologically
    df = df.sort_values(by=["order_date", "order_id", "line_item_id"]).reset_index(drop=True)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Generated {len(df)} records across {num_orders} orders saved to {output_path}")

    return df

if __name__ == "__main__":
    generate_retail_dataset()
