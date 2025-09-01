def bond_returns(face_value=100, coupon_rate=0.1, price_paid=108, maturity_years=5):
    
    # Total coupon payments over maturity
    total_coupons = face_value * coupon_rate * maturity_years
    
    # Redemption at face value
    redemption = face_value
    
    # Total cash received by buyer
    total_cash = total_coupons + redemption
    
    # Profit
    profit = total_cash - price_paid
    
    # ROI total percentage
    roi_total = (profit / price_paid) * 100
    
    # Annualized yield (CAGR)
    annualized_yield = ((total_cash / price_paid) ** (1 / maturity_years) - 1) * 100
    
    return {
        "Total Cash Received": total_cash,
        "Profit": profit,
        "ROI % (Total)": roi_total,
        "Annualized Yield %": annualized_yield
    }

# Example usage:
for years in [1, 3, 5]:
    result = bond_returns(face_value=100, coupon_rate=0.10, price_paid=108, maturity_years=years)
    print(f"Maturity: {years} years -> {result}")
