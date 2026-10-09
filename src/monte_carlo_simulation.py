import matplotlib.pyplot as plt
import numpy as np
import numpy_financial as npf

# 1. Base Deal Constants (Heathrow Hub)
area = 150000
base_rent_sqft = 12.50
purchase_price = 25000000
gross_basis = purchase_price * 1.045
senior_debt = purchase_price * 0.65
equity_invested = gross_basis - senior_debt  # ~£9.875M
debt_rate = 0.0525
exit_debt_payoff = 15210558

# Amortizing debt service years 3-5
debt_service = [
    senior_debt * debt_rate,
    senior_debt * debt_rate,
    1182036,
    1182036,
    1182036,
]

# 2. Monte Carlo Setup
n_simulations = 10000
np.random.seed(42)

# Stochastic Distributions
rent_growths = np.random.normal(0.035, 0.010, n_simulations)
exit_cap_rates = np.random.normal(0.050, 0.004, n_simulations)
vacancies = np.random.uniform(0.02, 0.06, n_simulations)

levered_irrs = []

# 3. Simulation Engine
for i in range(n_simulations):
    g = rent_growths[i]
    cap = max(exit_cap_rates[i], 0.035)  # floor cap rate
    vac = vacancies[i]

    # 5-Year Operating Pro-Forma Cash Flows
    cash_flows = [-equity_invested]
    cur_rent = base_rent_sqft

    # Years 1 to 5 Cash Flow
    for yr in range(5):
        cur_rent *= 1.0 + g if yr > 0 else 1.0
        pgi = area * cur_rent
        egi = pgi * (1 - vac)
        opex = egi * 0.05
        capex = 37500
        noi = egi - opex - capex
        tenant_capex = 150000 if yr == 3 else 0

        unlevered_cf = noi - tenant_capex
        levered_cf = unlevered_cf - debt_service[yr]

        # Year 5 Terminal Disposition
        if yr == 4:
            fwd_rent = cur_rent * (1 + g)
            fwd_noi = (
                (area * fwd_rent * (1 - vac)) * 0.95
            ) - 37500  # Year 6 Forward NOI
            gross_exit = fwd_noi / cap
            net_exit = gross_exit * 0.98
            equity_proceeds = net_exit - exit_debt_payoff
            levered_cf += equity_proceeds

        cash_flows.append(levered_cf)

    # Compute Levered IRR
    irr = npf.irr(cash_flows)
    if not np.isnan(irr):
        levered_irrs.append(irr)

levered_irrs = np.array(levered_irrs)

# 4. Key Metrics & Output
prob_hurdle = np.mean(levered_irrs >= 0.18) * 100
var_5 = np.percentile(levered_irrs, 5) * 100
median_irr = np.median(levered_irrs) * 100

print(f"--- MONTE CARLO SIMULATION RESULTS ({n_simulations:,} Trials) ---")
print(f"Median Expected Levered IRR: {median_irr:.2f}%")
print(f"Probability of Beating 18% Hurdle: {prob_hurdle:.1f}%")
print(f"Downside 5th Percentile (Value at Risk): {var_5:.2f}%")

# 5. Visual Plot
plt.figure(figsize=(9, 5))
plt.hist(
    levered_irrs * 100,
    bins=60,
    color="#1f4e78",
    edgecolor="white",
    alpha=0.85,
    density=True,
)
plt.axvline(
    18.0,
    color="crimson",
    linestyle="--",
    linewidth=2,
    label="Fund Hurdle (18.0%)",
)
plt.axvline(
    median_irr,
    color="gold",
    linestyle="-",
    linewidth=2,
    label=f"Median IRR ({median_irr:.1f}%)",
)
plt.title(
    "Heathrow Logistics Hub — Levered IRR Monte Carlo Distribution",
    fontsize=12,
    weight="bold",
)
plt.xlabel("Levered IRR (%)", fontsize=10)
plt.ylabel("Probability Density", fontsize=10)
plt.legend()
plt.grid(axis="y", linestyle=":", alpha=0.6)
plt.tight_layout()
plt.savefig("monte_carlo_irr_distribution.png", dpi=300)
plt.savefig("assets/monte_carlo_irr_distribution.png", dpi=300)
plt.show()