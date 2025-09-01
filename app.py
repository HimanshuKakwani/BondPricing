from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    return {"status": "API is running"}

@app.route("/price_bond", methods=["POST"])
def price_bond():
    data = request.get_json(force=True)

    bond_name = data.get("bond_name")
    face_value = float(data.get("face_value"))
    coupon_rate = float(data.get("coupon_rate"))  # e.g., 0.10 = 10%
    rating = data.get("rating")
    purchase_amount = float(data.get("purchase_amount"))
    maturity_years = int(data.get("maturity_years"))

    # --- Step 1: Base fraction setup ---
    fractions = 100
    fv_per_fraction = face_value / fractions
    coupon_per_fraction = fv_per_fraction * coupon_rate

    # --- Step 2: Pricing logic ---
    if rating in ["AAA", "AA", "A", "BBB+"]:
        # safer bonds → small markup for seller
        price_per_fraction = fv_per_fraction * 1.015
    else:
        # riskier bonds → seller takes reduced yield
        price_per_fraction = fv_per_fraction * 1.08

    # --- Step 3: ROI calculations ---
    roi_details = {}
    for years in [1, 3, 5]:
        total_interest = coupon_per_fraction * years
        final_value = fv_per_fraction + total_interest
        roi_percent = ((final_value - price_per_fraction) / price_per_fraction) * 100
        annualized_return = ((final_value / price_per_fraction) ** (1 / years) - 1) * 100

        roi_details[f"{years}_years"] = {
            "total_interest": round(total_interest, 2),
            "final_value": round(final_value, 2),
            "roi_percent": round(roi_percent, 2),
            "annualized_return": round(annualized_return, 2),
        }

    return jsonify({
        "bond_name": bond_name,
        "rating": rating,
        "face_value": face_value,
        "coupon_rate": coupon_rate,
        "fractions": fractions,
        "price_per_fraction": round(price_per_fraction, 2),
        "maturity_years": maturity_years,
        "buyer_returns": roi_details
    })

if __name__ == "__main__":
    app.run(debug=True, port=5012)





# from flask import Flask, jsonify, request

# app = Flask(__name__)

# # Rating categories
# HIGH_RATED = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB"]
# LOW_RATED = ["BBB-", "BB+", "BB", "BB-", "B+", "B", "B-", "CCC", "CC", "C", "D"]

# def calculate_fraction_price(face_value, coupon_rate, rating, purchase_amount, maturity_years):
#     fractions = 100
#     fv_per_unit = face_value / fractions

#     # Case 1: High-rated bonds
#     if rating in HIGH_RATED:
#         markup_rate = 0.02  # 2% markup
#         fraction_price = round(fv_per_unit * (1 + markup_rate), 2)
#         seller_total = fraction_price * fractions
#         buyer_yield = coupon_rate * (fv_per_unit / fraction_price) * 100

#     # Case 2: Riskier bonds
#     elif rating in LOW_RATED:
#         seller_effective_rate = coupon_rate * 0.75  # Seller gets 75% of stated rate
#         seller_total = face_value + (face_value * seller_effective_rate)
#         fraction_price = round(seller_total / fractions, 2)

#         # Buyer gets full coupon payments, so yield is boosted
#         buyer_yield = (coupon_rate * (fv_per_unit / fraction_price)) * 100

#         # Maturity adjustment (boost buyer yield slightly for longer term)
#         if maturity_years >= 3:
#             buyer_yield *= 1.1

#     else:
#         # Neutral pricing fallback
#         fraction_price = fv_per_unit
#         seller_total = fraction_price * fractions
#         buyer_yield = coupon_rate * 100

#     return {
#         "fraction_price": fraction_price,
#         "seller_total": round(seller_total, 2),
#         "buyer_expected_yield_%": round(buyer_yield, 2)
#     }


# @app.route("/")
# def home():
#     return {"status": "API is running"}

# @app.route('/price_bond', methods=['POST'])
# def price_bond():
#     data = request.json
#     bond_name = data.get("bond_name")
#     face_value = data.get("face_value")
#     coupon_rate = data.get("coupon_rate")  # e.g. 0.1 for 10%
#     rating = data.get("rating")
#     purchase_amount = data.get("purchase_amount")
#     maturity_years = data.get("maturity_years", 1)  # default 1 year if not given

#     result = calculate_fraction_price(face_value, coupon_rate, rating, purchase_amount, maturity_years)
#     result["bond_name"] = bond_name
#     result["rating"] = rating
#     result["maturity_years"] = maturity_years

#     return jsonify(result)

# if __name__ == "__main__":
#     # app.run()
#     app.run(debug=True, port=5012)