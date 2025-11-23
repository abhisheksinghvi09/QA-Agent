# Product Specifications: E-Shop Checkout

## Discount Logic
1. **Coupon Codes**:
    - The code `SAVE15` applies a **15% discount** to the item subtotal.
    - Any other code is considered invalid and should display "Invalid Code".
    - Discounts do not apply to shipping costs.

## Shipping Rules
1. **Standard Shipping**:
    - Cost: $0 (Free).
    - Default selection.
2. **Express Shipping**:
    - Cost: $10 flat fee.
    - Added to the total after discount calculation.

## Cart Behavior
- The initial cart contains items worth $150.
- Users can increase quantity (logic handled by backend, but frontend inputs exist).