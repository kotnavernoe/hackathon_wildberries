from flask import Flask, jsonify, request
from flasgger import Swagger
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
swagger_config = Swagger.DEFAULT_CONFIG.copy()
Swagger(app, config=swagger_config)



def get_weekday_name(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return date_obj.strftime('%A').lower()



@app.route('/api/calculate_price/<int:product_id>', methods=['GET'])
def get_ideal_price_api(product_id):
    """
    Calculates the ideal price for a given product ID.
    The calculation can be based on a specific date and seasonality.
    If 'date' is not provided, the current date is used.
    ---
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: The ID of the product for which to calculate the price.
      - name: date
        in: query
        type: string
        format: date
        required: false
        description: The date for the price calculation (YYYY-MM-DD). Defaults to today if not provided.
      - name: seasonal
        in: query
        type: boolean
        required: false
        default: false
        description: Whether to consider seasonal price adjustments.
    responses:
      200:
        description: Ideal price calculation successful.
        schema:
          type: object
          properties:
            product_id:
              type: integer
              description: The ID of the product.
            sellers_price:
              type: number
              format: float
              description: The original seller's price.
            ideal_price:
              type: number
              format: float
              description: The calculated ideal price.
            adjustment_parameters:
              type: object
              description: Breakdown of adjustments made to the price.
              properties:
                day_of_the_week_demand:
                  type: number
                  format: float
                seasonal_demand:
                  type: number
                  format: float
                elasticity:
                  type: number
                  format: float
                seller_trust:
                  type: number
                  format: float
                a_b_testing:
                  type: number
                  format: float
      400:
        description: Invalid input (e.g., missing or invalid date format if provided).
      404:
        description: Product ID not found or data missing for calculation.
      500:
        description: Internal server error (e.g., dataset file not found, missing columns in data).
    """
    calculation_date_str = request.args.get('date')
    if not calculation_date_str:
        calculation_date_str = datetime.today().strftime('%Y-%m-%d')

    is_seasonal_str = request.args.get('seasonal', 'false')
    is_seasonal = is_seasonal_str.lower() == 'true'

    try:
        weekday_name = get_weekday_name(calculation_date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

    try:
        df_a = pd.read_csv('demo_dataset/group_a.csv')
        df_b = pd.read_csv('demo_dataset/group_b.csv')
    except FileNotFoundError:
        return jsonify({"error": "Dataset file not found."}), 500

    product_a_data = df_a[df_a['product_id'] == product_id]
    product_b_data = df_b[df_b['product_id'] == product_id]

    if product_a_data.empty and product_b_data.empty:
        return jsonify({"error": f"Product ID {product_id} not found in any dataset."}), 404

    revenue_cols = [f'avg_revenue_{day}' for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']]
    
    total_revenue_a = 0
    if not product_a_data.empty:
        if all(col in product_a_data.columns for col in revenue_cols):
            total_revenue_a = product_a_data[revenue_cols].fillna(0).sum(axis=1).iloc[0]

    total_revenue_b = 0
    if not product_b_data.empty:
        if all(col in product_b_data.columns for col in revenue_cols):
            total_revenue_b = product_b_data[revenue_cols].fillna(0).sum(axis=1).iloc[0]
            
    selected_df = None
    selected_data_source_name = None

    if total_revenue_a >= total_revenue_b:
        if not product_a_data.empty:
            selected_df = product_a_data
            selected_data_source_name = "group_a"
        elif not product_b_data.empty:
            selected_df = product_b_data
            selected_data_source_name = "group_b"
    else:
        if not product_b_data.empty:
            selected_df = product_b_data
            selected_data_source_name = "group_b"
        elif not product_a_data.empty:
            selected_df = product_a_data
            selected_data_source_name = "group_a"

    if selected_df is None or selected_df.empty:
        return jsonify({"error": f"No valid data found for Product ID {product_id} to make a selection."}), 404

    try:
        sellers_price = selected_df['sellers_price'].iloc[0]
        if pd.isna(sellers_price):
            return jsonify({"error": f"sellers_price is missing for Product ID {product_id} in {selected_data_source_name}."}), 500

        avg_demand_perc_col = f'avg_demand_{weekday_name}_perc'
        if avg_demand_perc_col not in selected_df.columns:
            return jsonify({"error": f"Column {avg_demand_perc_col} not found in {selected_data_source_name} for product {product_id}."}), 500
        
        avg_demand_weekday_raw_perc = selected_df[avg_demand_perc_col].iloc[0]
        if pd.isna(avg_demand_weekday_raw_perc):
            return jsonify({"error": f"{avg_demand_perc_col} is missing for Product ID {product_id} in {selected_data_source_name}."}), 500
        actual_day_of_week_perc_change = avg_demand_weekday_raw_perc - 1
        
        p_perc = selected_df['p'].fillna(0).iloc[0]
        seller_trust_perc = selected_df['seller_trust_increase_perc'].fillna(0).iloc[0]
        
        seasonal_perc = 0
        if is_seasonal:
            seasonal_perc_raw = selected_df['seasonal_price_increase_perc'].fillna(0).iloc[0]
            seasonal_perc = seasonal_perc_raw
            
        price_elasticity = selected_df['price_elasticity'].fillna(0).iloc[0]

    except IndexError:
        return jsonify({"error": f"Data missing for Product ID {product_id} in selected dataset '{selected_data_source_name}'."}), 404
    except KeyError as e:
        return jsonify({"error": f"Missing expected column {str(e)} in dataset '{selected_data_source_name}'."}), 500



    
    increase = (actual_day_of_week_perc_change + p_perc + seller_trust_perc + seasonal_perc) * sellers_price
    total_increase = increase * price_elasticity
    ideal_price = sellers_price + total_increase

    adjustment_details = {
        "day_of_the_week_demand": round(actual_day_of_week_perc_change, 2),
        "seasonal_demand": round(seasonal_perc, 2),
        "elasticity": round(price_elasticity, 2),
        "seller_trust": round(seller_trust_perc, 2),
        "a_b_testing": round(p_perc, 2)
    }

    response = {
        "product_id": product_id,
        "sellers_price": round(sellers_price, 2),
        "ideal_price": round(ideal_price, 2),
        "adjustment_parameters": adjustment_details
    }

    return jsonify(response)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
