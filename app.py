import math

from flask import Flask, jsonify, request

app = Flask(__name__)

# --- Rating Categories ---
# Bonds are classified into high-rated (safe) and low-rated (risky) categories.
HIGH_RATED = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB"]
LOW_RATED = ["BBB-", "BB+", "BB", "BB-", "B+", "B", "B-", "CCC", "CC", "C", "D"]


# --- Bond Pricing Utilities ---

def pv_price(face_value: float, coupon_rate: float, yield_rate: float, years: int) -> float:
    """
    Compute bond price as PV (present value) of all coupons + PV of face value.
    Coupons are assumed to be annual and equal to face_value * coupon_rate.
    """
    c = face_value * coupon_rate
    y = yield_rate
    n = max(int(math.ceil(years)), 0)

    if n == 0:
        # Immediate maturity → principal + coupon
        return face_value + c

    # PV of all coupons
    pv_coupons = sum(c / ((1 + y) ** t) for t in range(1, n + 1))
    # PV of principal repayment
    pv_face = face_value / ((1 + y) ** n)
    return pv_coupons + pv_face


def implied_yield_for_price(face_value: float, coupon_rate: float, price: float, years: int,
                            lo=1e-8, hi=1.0, eps=1e-8, max_iter=200):
    """
    Solve for implied yield Y such that pv_price(...) == price.
    Uses the bisection method between [lo, hi].
    """
    a, b = lo, hi
    fa = pv_price(face_value, coupon_rate, a, years) - price
    fb = pv_price(face_value, coupon_rate, b, years) - price

    if fa * fb > 0:
        # If solution not bracketed, expand the search space
        b = 10.0
        fb = pv_price(face_value, coupon_rate, b, years) - price
        if fa * fb > 0:
            return None  # No solution found

    for _ in range(max_iter):
        m = 0.5 * (a + b)
        fm = pv_price(face_value, coupon_rate, m, years) - price
        if abs(fm) < eps:
            return m
        if fa * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return 0.5 * (a + b)


# --- Fractional Bond Pricing Logic ---

def calculate_fraction_price(face_value, coupon_rate, rating, purchase_amount,
                             maturity_years, fractions=100,
                             use_pv_forward=True, force_seller_target=False):
    """
    Calculates price per fraction of bond along with yield and projections.
    :param face_value: Total bond face value
    :param coupon_rate: Annual coupon rate (decimal, e.g., 0.10 = 10%)
    :param rating: Bond rating (AAA, AA, BBB-, etc.)
    :param purchase_amount: Amount invested (not used currently, kept for future extension)
    :param maturity_years: Years until maturity
    :param fractions: Number of parts bond is divided into (default 100)
    :param use_pv_forward: Whether to use PV forward pricing
    :param force_seller_target: Whether seller enforces target proceeds
    :return: Pricing details dict
    """

    fv_per_unit = face_value / fractions

    # Smooth yield adjustment for high-rated bonds
    def target_yield_for_time(t):
        delta = 0.01  # Max reduction (1%) up to 5 years
        t_capped = min(max(t, 0.0), 5.0)
        return coupon_rate - delta * (t_capped / 5.0)

    if rating in HIGH_RATED:
        if use_pv_forward and not force_seller_target:
            # Forward PV pricing (based on target yield curve)
            Y = target_yield_for_time(maturity_years)
            seller_total = pv_price(face_value, coupon_rate, Y, maturity_years)
            fraction_price = round(seller_total / fractions, 2)
            buyer_cost = fraction_price * fractions
            buyer_yield = (coupon_rate * face_value / buyer_cost) * 100

        elif force_seller_target:
            # Seller enforces target recovery
            base_recovery = face_value * (1 + coupon_rate)
            time_scale = 0.95 + 0.07 * (min(max(maturity_years, 0.0), 5.0) / 5.0)
            seller_total = base_recovery * time_scale
            fraction_price = round(seller_total / fractions, 2)
            buyer_cost = fraction_price * fractions
            implied = implied_yield_for_price(face_value, coupon_rate, seller_total, maturity_years)
            buyer_yield = (implied * 100) if implied is not None else None
            Y = implied

        else:
            # Fallback simple rule
            seller_total = face_value * (1 + coupon_rate) * 0.98
            fraction_price = round(seller_total / fractions, 2)
            buyer_cost = fraction_price * fractions
            buyer_yield = (coupon_rate * face_value / buyer_cost) * 100
            Y = None

    elif rating in LOW_RATED:
        # Lower recovery assumption for risky bonds
        seller_effective_rate = coupon_rate * 0.75
        seller_total = face_value * (1 + seller_effective_rate)
        fraction_price = round(seller_total / fractions, 2)
        buyer_cost = fraction_price * fractions
        buyer_yield = (coupon_rate * face_value / buyer_cost) * 100
        Y = None

    else:
        # Neutral fallback
        fraction_price = fv_per_unit
        seller_total = fraction_price * fractions
        buyer_cost = seller_total
        buyer_yield = coupon_rate * 100
        Y = None

    # Buyer interest projections
    def proj(years):
        held_years = min(years, max(maturity_years, 0))
        interest_amt = coupon_rate * face_value * held_years
        return {
            "absolute_interest": round(interest_amt, 2),
            "return_pct_of_cost": round((interest_amt / buyer_cost) * 100, 2) if buyer_cost else 0
        }

    interest_projections = {
        "1_year": proj(1),
        "3_year": proj(3),
        "5_year": proj(5),
    }

    return {
        "fraction_price": fraction_price,
        "seller_total": round(seller_total, 2),
        "buyer_expected_yield_%": round(buyer_yield, 2) if buyer_yield else None,
        "buyer_interest_projection": interest_projections,
        "pricing_mode": "pv_forward" if use_pv_forward and not force_seller_target else (
            "force_seller" if force_seller_target else "fallback"
        ),
        "used_yield": round(Y, 6) if Y else None
    }


# --- Flask Routes ---

@app.route("/")
def home():
    """Health check endpoint"""
    return {"status": "API is running"}


@app.route('/price_bond', methods=['POST'])
def price_bond():
    """
    Endpoint to calculate bond fraction pricing.
    Expects JSON with: bond_name, face_value, coupon_rate, rating, purchase_amount, maturity_years
    """
    data = request.json
    bond_name = data.get("bond_name")
    face_value = data.get("face_value")
    coupon_rate = data.get("coupon_rate")   # e.g. 0.10 for 10%
    rating = data.get("rating")
    purchase_amount = data.get("purchase_amount")
    maturity_years = data.get("maturity_years", 1)

    # Default: PV forward mode
    result = calculate_fraction_price(face_value, coupon_rate, rating,
                                      purchase_amount, maturity_years,
                                      use_pv_forward=True, force_seller_target=False)

    result["bond_name"] = bond_name
    result["rating"] = rating
    result["maturity_years"] = maturity_years

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5012)
