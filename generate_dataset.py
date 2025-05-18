import csv
import random

def generate_demo_data(num_products=10):
    """Generates demo product data."""
    header = [
        'product_id',
        'sellers_price',
        'avg_revenue_monday', 'avg_revenue_tuesday', 'avg_revenue_wednesday',
        'avg_revenue_thursday', 'avg_revenue_friday', 'avg_revenue_saturday', 'avg_revenue_sunday',
        
        'avg_demand_monday_perc', 'avg_demand_tuesday_perc', 'avg_demand_wednesday_perc',
        'avg_demand_thursday_perc', 'avg_demand_friday_perc', 'avg_demand_saturday_perc', 'avg_demand_sunday_perc',
        
        'seasonal_price_increase_perc',
        'seller_trust_increase_perc',
        'price_elasticity',
        'p'
    ]
    data = [header]

    # adjust parameters as needed
    for i in range(1, num_products + 1):
        product_id = i
        sellers_price = round(random.uniform(0, 20), 2)
        revenues = [round(random.uniform(50.0, 1000.0), 2) for _ in range(7)]
        demands = [round(random.uniform(0.5, 1.5), 2) for _ in range(7)]
        seasonal_increase = round(random.uniform(0.0, 0.25), 2)
        trust_increase = round(random.uniform(0.0, 0.15), 2)
        elasticity = round(random.uniform(0, 1.0), 2)
        p = round(random.uniform(-0.05, 0.05), 2)

        row = [product_id, sellers_price] + revenues + demands + [seasonal_increase, trust_increase, elasticity, p]
        data.append(row)
    return data

def write_to_csv(filename, data):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data)
    print(f"Data successfully written to {filename}")

if __name__ == "__main__":
    dataset = generate_demo_data(num_products=50)
    csv_filename = 'dataset/group_a.csv'
    write_to_csv(csv_filename, dataset)

    dataset_2 = generate_demo_data(num_products=50)
    csv_filename = 'dataset/group_b.csv'
    write_to_csv(csv_filename, dataset_2)
