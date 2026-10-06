# Figures

Every row behind the dossier. `As shown` is the value after rounding, which is the value later formulas use.

| ID | Figure | As shown | Kind | Basis |
|---|---|---|---|---|
| `revenue_fy0` | Revenue, year just ended | $1,500.0 million | assumption | assumption A1: see assumptions-table.md |
| `aftermarket_share` | Replacement parts and service, share of revenue | 25.0% | assumption | assumption A2: see assumptions-table.md |
| `aftermarket_revenue_fy0` | Replacement parts and service revenue, year just ended | $375.0 million | derived | derived D1: revenue_fy0 * aftermarket_share |
| `headcount_total` | Employees, end of year just ended | 3,310 | derived | derived D2: revenue_fy0 / ind_rev_per_emp |
| `plant_count` | Number of plants | 6 | assumption | assumption A3: see assumptions-table.md |
| `plant_1_no` | Plant number, Great Lakes | 1 | assumption | assumption A4: see assumptions-table.md |
| `plant_2_no` | Plant number, Ohio Valley | 2 | assumption | assumption A5: see assumptions-table.md |
| `plant_3_no` | Plant number, Upper Midwest | 3 | assumption | assumption A6: see assumptions-table.md |
| `plant_4_no` | Plant number, Southeast | 4 | assumption | assumption A7: see assumptions-table.md |
| `plant_5_no` | Plant number, South Central | 5 | assumption | assumption A8: see assumptions-table.md |
| `plant_6_no` | Plant number, Great Plains | 6 | assumption | assumption A9: see assumptions-table.md |
| `revenue_fy2` | Revenue, two years ago | $1,456.6 million | derived | derived D3: revenue_fy1 / (1 + rev_growth_fy1) |
| `revenue_fy1` | Revenue, prior year | $1,449.3 million | derived | derived D4: revenue_fy0 / (1 + rev_growth_fy0) |
| `rev_growth_fy1` | Revenue growth, prior year | -0.5% | derived | derived D5: aies_rev_2024 / aies_rev_2023 - 1. Note: The Company's revenue is taken to have moved with the industry's (AIES, all employer firms, 2023 to 2024). |
| `rev_growth_fy0` | Revenue growth, year just ended | 3.5% | derived | derived D6: price_change_fy0 + volume_change_fy0 |
| `gross_profit_fy2` | Gross profit, two years ago | $517.1 million | derived | derived D7: revenue_fy2 * ind_gm_fy2 |
| `ind_gm_fy2` | Industry gross margin, two years ago | 35.5% | sourced | Damodaran 2024 margins: Machinery, Gross Margin; read as 0.35540162 |
| `gross_profit_fy1` | Gross profit, prior year | $537.7 million | derived | derived D8: revenue_fy1 * ind_gm_fy1 |
| `ind_gm_fy1` | Industry gross margin, prior year | 37.1% | sourced | Damodaran 2025 margins: Machinery, Gross Margin; read as 0.37078192 |
| `gross_profit_fy0` | Gross profit, year just ended | $562.5 million | derived | derived D9: revenue_fy0 * ind_gm_fy0 |
| `ind_gm_fy0` | Industry gross margin, year just ended | 37.5% | sourced | Damodaran 2026 margins: Machinery, Gross Margin; read as 0.3747335 |
| `op_income_fy2` | Operating income, two years ago | $212.7 million | derived | derived D10: revenue_fy2 * (ind_gm_fy2 - ind_sga_fy2 - ind_rnd_fy2) |
| `op_income_fy1` | Operating income, prior year | $227.5 million | derived | derived D11: revenue_fy1 * (ind_gm_fy1 - ind_sga_fy1 - ind_rnd_fy1) |
| `op_income_fy0` | Operating income, year just ended | $238.5 million | derived | derived D12: gross_profit_fy0 - sga_fy0 - rnd_fy0. Note: Gross margin less SG&A and R&D. Damodaran's own pre-tax operating margin for the year is 15.86%; the rounded line items (37.5% less 19.6% less 2.0%) give 15.9%, and the statement adds up from its own lines. |
| `net_income_fy2` | Net income, two years ago | $142.7 million | derived | derived D13: revenue_fy2 * ind_net_margin_fy2 |
| `net_income_fy1` | Net income, prior year | $144.9 million | derived | derived D14: revenue_fy1 * ind_net_margin_fy1 |
| `net_income_fy0` | Net income, year just ended | $162.4 million | derived | derived D15: pretax_income_fy0 - tax_fy0 |
| `price_change_fy1` | Industry producer price change, prior year | 3.3% | derived | derived D16: ppi_2024 / ppi_2023 - 1 |
| `price_change_fy0` | Industry producer price change, year just ended | 3.5% | derived | derived D17: ppi_2025 / ppi_2024 - 1 |
| `volume_change_fy0` | Change in the Company's unit volume, year just ended | 0.0% | assumption | assumption A10: see assumptions-table.md |
| `sga_fy0` | Selling, general and administrative expense, year just ended | $294.0 million | derived | derived D18: revenue_fy0 * ind_sga_fy0 |
| `rnd_fy0` | Research and development expense, year just ended | $30.0 million | derived | derived D19: revenue_fy0 * ind_rnd_fy0 |
| `op_margin_fy0` | Operating margin, year just ended | 15.9% | derived | derived D20: op_income_fy0 / revenue_fy0 |
| `interest_fy0` | Interest expense, year just ended | $32.1 million | derived | derived D21: debt * ind_book_rate |
| `pretax_income_fy0` | Income before tax, year just ended | $206.4 million | derived | derived D22: op_income_fy0 - interest_fy0 |
| `tax_fy0` | Income tax, year just ended | $44.0 million | derived | derived D23: pretax_income_fy0 * ind_tax_rate |
| `net_margin_fy0` | Net margin, year just ended | 10.8% | derived | derived D24: net_income_fy0 / revenue_fy0 |
| `da_fy0` | Depreciation and amortization, year just ended | $52.5 million | derived | derived D25: revenue_fy0 * ind_da_share |
| `ebitda_fy0` | EBITDA, year just ended | $291.0 million | derived | derived D26: op_income_fy0 + da_fy0 |
| `cash` | Cash, end of year just ended | $144.9 million | derived | derived D27: enterprise_value * ind_cash_fv / (1 - ind_cash_fv). Note: Damodaran's cash to firm value, where firm value is enterprise value plus cash; solving cash = r x (EV + cash) gives cash = EV x r / (1 - r). |
| `receivables` | Receivables, end of year just ended | $285.0 million | derived | derived D28: revenue_fy0 * ind_ar_sales |
| `inventory` | Inventory, end of year just ended | $249.0 million | derived | derived D29: revenue_fy0 * ind_inv_sales |
| `payables` | Payables, end of year just ended | $148.5 million | derived | derived D30: revenue_fy0 * ind_ap_sales |
| `debt` | Total debt, end of year just ended | $669.3 million | derived | derived D31: ebitda_fy0 * ind_debt_ebitda. Note: Set at the industry's debt to EBITDA. |
| `equity_book` | Shareholders' equity (book), end of year just ended | $1,033.8 million | derived | derived D32: debt * (1 - ind_book_dc) / ind_book_dc. Note: At the industry's book debt to capital, where capital is book debt plus book equity. |
| `ind_debt_ebitda` | Industry debt to EBITDA | 2.30 | sourced | Damodaran 2026 debt ratios: Machinery, Debt to EBITDA; read as 2.3039265 |
| `interest_coverage` | Interest coverage (operating income to interest) | 7.43 | derived | derived D33: op_income_fy0 / interest_fy0 |
| `credit_facility` | Revolving credit facility, undrawn | $300.0 million | assumption | assumption A11: see assumptions-table.md |
| `liquidity` | Available liquidity (cash plus the undrawn facility) | $444.9 million | derived | derived D34: cash + credit_facility |
| `min_cash_months` | Minimum operating cash, in months of cash operating costs | 1 | assumption | assumption A12: see assumptions-table.md |
| `cash_costs_fy0` | Cash operating costs, year just ended (revenue less EBITDA) | $1,209.0 million | derived | derived D35: revenue_fy0 - ebitda_fy0 |
| `min_operating_cash` | Minimum operating cash | $100.8 million | derived | derived D36: cash_costs_fy0 / 12 * min_cash_months |
| `cash_above_min` | Cash above the minimum operating level | $44.1 million | derived | derived D37: cash - min_operating_cash |
| `wc_increase_fy0` | Increase in working capital, year just ended | $12.4 million | derived | derived D38: (revenue_fy0 - revenue_fy1) * ind_nwc_sales. Note: Working capital held at the industry's share of revenue, so it grows with revenue. |
| `operating_cash_flow_fy0` | Cash from operations, year just ended | $202.5 million | derived | derived D39: net_income_fy0 + da_fy0 - wc_increase_fy0 |
| `capex_fy0` | Capital spending, year just ended | $36.0 million | derived | derived D40: revenue_fy0 * ind_capex_share. Note: Below depreciation and amortization, as for the industry (Damodaran's Cap Ex/Deprecn for Machinery is 0.68); amortization of acquired intangibles is part of the gap. |
| `free_cash_flow_fy0` | Free cash flow (cash from operations less capital spending), year just ended | $166.5 million | derived | derived D41: operating_cash_flow_fy0 - capex_fy0 |
| `dividends_fy0` | Dividends paid, year just ended | $54.2 million | derived | derived D42: net_income_fy0 * ind_payout |
| `repurchases_fy0` | Share repurchases, year just ended | $91.9 million | derived | derived D43: net_income_fy0 * (ind_cash_return - ind_payout) |
| `uncommitted_cash_flow` | Cash flow after capital spending, dividends and repurchases, year just ended | $20.4 million | derived | derived D44: free_cash_flow_fy0 - dividends_fy0 - repurchases_fy0. Note: The uncommitted cash a year produces at the current plans (the R&D scenario's annual amount draws on this row). |
| `ind_payout` | Industry dividend payout ratio | 33.4% | sourced | Damodaran 2026 dividends: Machinery, Dividend Payout; read as 0.33425684 |
| `shareholder_returns_fy0` | Dividends and repurchases, year just ended | $146.1 million | derived | derived D45: dividends_fy0 + repurchases_fy0 |
| `ind_cash_return` | Industry dividends plus buybacks as a share of net income | 90.0% | sourced | Damodaran 2026 cash returns: Machinery, Cash Return as % of Net Income; read as 0.90040863 |
| `market_cap` | Market value of equity | $4,325.6 million | derived | derived D46: enterprise_value - debt + cash |
| `pe_ratio` | Market value of equity over net income | 26.64 | derived | derived D47: market_cap / net_income_fy0 |
| `dividend_yield` | Dividend yield (dividends over the market value of equity) | 1.3% | derived | derived D48: dividends_fy0 / market_cap |
| `roe_fy0` | Return on equity (net income over book equity), year just ended | 15.7% | derived | derived D49: net_income_fy0 / equity_book |
| `plant_workforce` | Employees at the plants (production, maintenance and warehouse) | 1,900 | derived | derived D50: hc_prod + hc_maint + hc_logistics |
| `office_workforce` | Employees at the headquarters, engineering center and sales offices | 1,410 | derived | derived D51: headcount_total - plant_workforce |
| `hc_prod` | Employees, production | 1,560 | derived | derived D52: headcount_total * oews_emp_prod / oews_emp_all |
| `oews_wage_prod` | Mean annual wage, production occupations | $54,570 | sourced | OEWS May 2025: NAICS 333000, 51-0000 Production Occupations, A_MEAN; read as 54,570 |
| `payroll_prod` | Payroll, production | $85.1 million | derived | derived D53: hc_prod * oews_wage_prod |
| `hc_maint` | Employees, maintenance, repair and field service | 180 | derived | derived D54: headcount_total * oews_emp_maint / oews_emp_all |
| `oews_wage_maint` | Mean annual wage, installation, maintenance and repair occupations | $67,030 | sourced | OEWS May 2025: NAICS 333000, 49-0000 Installation, Maintenance, and Repair Occupations, A_MEAN; read as 67,030 |
| `payroll_maint` | Payroll, maintenance, repair and field service | $12.1 million | derived | derived D55: hc_maint * oews_wage_maint |
| `hc_logistics` | Employees, warehouse and shipping | 160 | derived | derived D56: headcount_total * oews_emp_logistics / oews_emp_all |
| `oews_wage_logistics` | Mean annual wage, transportation and material moving occupations | $47,970 | sourced | OEWS May 2025: NAICS 333000, 53-0000 Transportation and Material Moving Occupations, A_MEAN; read as 47,970 |
| `payroll_logistics` | Payroll, warehouse and shipping | $7.7 million | derived | derived D57: hc_logistics * oews_wage_logistics |
| `hc_eng` | Employees, engineering | 350 | derived | derived D58: headcount_total * oews_emp_eng / oews_emp_all |
| `oews_wage_eng` | Mean annual wage, architecture and engineering occupations | $97,280 | sourced | OEWS May 2025: NAICS 333000, 17-0000 Architecture and Engineering Occupations, A_MEAN; read as 97,280 |
| `payroll_eng` | Payroll, engineering | $34.0 million | derived | derived D59: hc_eng * oews_wage_eng |
| `hc_it` | Employees, information technology | 90 | derived | derived D60: headcount_total * oews_emp_it / oews_emp_all |
| `oews_wage_it` | Mean annual wage, computer and mathematical occupations | $108,070 | sourced | OEWS May 2025: NAICS 333000, 15-0000 Computer and Mathematical Occupations, A_MEAN; read as 108,070 |
| `payroll_it` | Payroll, information technology | $9.7 million | derived | derived D61: hc_it * oews_wage_it |
| `hc_sales` | Employees, sales | 120 | derived | derived D62: headcount_total * oews_emp_sales / oews_emp_all |
| `oews_wage_sales` | Mean annual wage, sales occupations | $92,830 | sourced | OEWS May 2025: NAICS 333000, 41-0000 Sales and Related Occupations, A_MEAN; read as 92,830 |
| `payroll_sales` | Payroll, sales | $11.1 million | derived | derived D63: hc_sales * oews_wage_sales |
| `hc_office` | Employees, office and administrative support | 280 | derived | derived D64: headcount_total * oews_emp_office / oews_emp_all |
| `oews_wage_office` | Mean annual wage, office and administrative support occupations | $56,050 | sourced | OEWS May 2025: NAICS 333000, 43-0000 Office and Administrative Support Occupations, A_MEAN; read as 56,050 |
| `payroll_office` | Payroll, office and administrative support | $15.7 million | derived | derived D65: hc_office * oews_wage_office |
| `hc_business` | Employees, business and financial operations | 220 | derived | derived D66: headcount_total * oews_emp_business / oews_emp_all |
| `oews_wage_business` | Mean annual wage, business and financial operations occupations | $91,780 | sourced | OEWS May 2025: NAICS 333000, 13-0000 Business and Financial Operations Occupations, A_MEAN; read as 91,780 |
| `payroll_business` | Payroll, business and financial operations | $20.2 million | derived | derived D67: hc_business * oews_wage_business |
| `hc_mgmt` | Employees, management | 280 | derived | derived D68: headcount_total * oews_emp_mgmt / oews_emp_all |
| `oews_wage_mgmt` | Mean annual wage, management occupations | $156,950 | sourced | OEWS May 2025: NAICS 333000, 11-0000 Management Occupations, A_MEAN; read as 156,950 |
| `payroll_mgmt` | Payroll, management | $43.9 million | derived | derived D69: hc_mgmt * oews_wage_mgmt |
| `hc_other` | Employees, all other occupations | 70 | derived | derived D70: headcount_total - hc_prod - hc_maint - hc_logistics - hc_eng - hc_it - hc_sales - hc_office - hc_business - hc_mgmt. Note: The remainder, so the functions add up to the total. |
| `pay_other` | Average pay, all other occupations | $68,571 | derived | derived D71: payroll_other / hc_other |
| `payroll_other` | Payroll, all other occupations | $4.8 million | derived | derived D72: payroll_total - payroll_prod - payroll_maint - payroll_logistics - payroll_eng - payroll_it - payroll_sales - payroll_office - payroll_business - payroll_mgmt. Note: The remainder, so payroll by function adds up to the total. |
| `oews_wage_all` | Industry mean annual wage, all occupations | $73,820 | sourced | OEWS May 2025: NAICS 333000, 00-0000 All Occupations, A_MEAN; read as 73,820 |
| `payroll_total` | Payroll, total | $244.3 million | derived | derived D73: headcount_total * oews_wage_all. Note: Headcount times the industry's mean wage across all occupations (OEWS). AIES's payroll share of revenue (17.8%, 2024) is higher than this gives (about 16.3%); the two surveys differ in what pay they count and in year, and pay by occupation needs OEWS, so OEWS is used throughout. |
| `benefits_ratio` | Benefits cost as a share of payroll | 26.8% | derived | derived D74: aies_fringe_2024 / aies_payroll_2024 |
| `benefits_total` | Benefits cost, year just ended | $65.5 million | derived | derived D75: payroll_total * benefits_ratio |
| `employment_cost` | Payroll and benefits, year just ended | $309.8 million | derived | derived D76: payroll_total + benefits_total |
| `hc_assemblers` | Employees, assemblers and fabricators | 430 | derived | derived D77: headcount_total * oews_emp_assemblers / oews_emp_all |
| `oews_wage_assemblers` | Mean annual wage, assemblers and fabricators | $48,510 | sourced | OEWS May 2025: NAICS 333000, 51-2090 Miscellaneous Assemblers and Fabricators, A_MEAN; read as 48,510 |
| `hc_welders` | Employees, welders | 190 | derived | derived D78: headcount_total * oews_emp_welders / oews_emp_all |
| `oews_wage_welders` | Mean annual wage, welders | $54,710 | sourced | OEWS May 2025: NAICS 333000, 51-4121 Welders, Cutters, Solderers, and Brazers, A_MEAN; read as 54,710 |
| `hc_machinists` | Employees, machinists | 180 | derived | derived D79: headcount_total * oews_emp_machinists / oews_emp_all |
| `oews_wage_machinists` | Mean annual wage, machinists | $58,740 | sourced | OEWS May 2025: NAICS 333000, 51-4041 Machinists, A_MEAN; read as 58,740 |
| `hc_mech_eng` | Employees, mechanical engineers | 130 | derived | derived D80: headcount_total * oews_emp_mech_eng / oews_emp_all |
| `oews_wage_mech_eng` | Mean annual wage, mechanical engineers | $102,010 | sourced | OEWS May 2025: NAICS 333000, 17-2141 Mechanical Engineers, A_MEAN; read as 102,010 |
| `hc_mechanics` | Employees, industrial machinery mechanics | 70 | derived | derived D81: headcount_total * oews_emp_mechanics / oews_emp_all |
| `oews_wage_mechanics` | Mean annual wage, industrial machinery mechanics | $67,310 | sourced | OEWS May 2025: NAICS 333000, 49-9041 Industrial Machinery Mechanics, A_MEAN; read as 67,310 |
| `plant_avg_pay` | Average pay at the plants | $55,211 | derived | derived D82: (payroll_prod + payroll_maint + payroll_logistics) / plant_workforce |
| `rev_p1` | Plant 1 revenue | $360.0 million | derived | derived D83: revenue_fy0 * share_p1 |
| `share_p1` | Plant 1 share of revenue | 24.0% | assumption | assumption A13: see assumptions-table.md |
| `hc_p1` | Plant 1 employees | 450 | derived | derived D84: plant_workforce - hc_p2 - hc_p3 - hc_p4 - hc_p5 - hc_p6. Note: The remainder, so the plants add up to the plant workforce. |
| `result_p1` | Plant 1 operating result | $70.3 million | derived | derived D85: op_income_fy0 - result_p2 - result_p3 - result_p4 - result_p5 - result_p6. Note: The remainder, so the plants add up to the Company's operating income. |
| `margin_p1` | Plant 1 operating margin, after allocated corporate costs | 19.5% | derived | derived D86: result_p1 / rev_p1 |
| `rev_p2` | Plant 2 revenue | $300.0 million | derived | derived D87: revenue_fy0 * share_p2 |
| `share_p2` | Plant 2 share of revenue | 20.0% | assumption | assumption A14: see assumptions-table.md |
| `hc_p2` | Plant 2 employees | 380 | derived | derived D88: plant_workforce * share_p2. Note: Plant employees are spread in proportion to plant revenue (an assumption with no further source). |
| `result_p2` | Plant 2 operating result | $57.0 million | derived | derived D89: rev_p2 * margin_p2 |
| `margin_p2` | Plant 2 operating margin, after allocated corporate costs | 19.0% | assumption | assumption A15: see assumptions-table.md |
| `rev_p3` | Plant 3 revenue | $270.0 million | derived | derived D90: revenue_fy0 * share_p3 |
| `share_p3` | Plant 3 share of revenue | 18.0% | assumption | assumption A16: see assumptions-table.md |
| `hc_p3` | Plant 3 employees | 340 | derived | derived D91: plant_workforce * share_p3 |
| `result_p3` | Plant 3 operating result | $45.9 million | derived | derived D92: rev_p3 * margin_p3 |
| `margin_p3` | Plant 3 operating margin, after allocated corporate costs | 17.0% | assumption | assumption A17: see assumptions-table.md |
| `rev_p4` | Plant 4 revenue | $225.0 million | derived | derived D93: revenue_fy0 * share_p4 |
| `share_p4` | Plant 4 share of revenue | 15.0% | assumption | assumption A18: see assumptions-table.md |
| `hc_p4` | Plant 4 employees | 290 | derived | derived D94: plant_workforce * share_p4 |
| `result_p4` | Plant 4 operating result | $45.0 million | derived | derived D95: rev_p4 * margin_p4 |
| `margin_p4` | Plant 4 operating margin, after allocated corporate costs | 20.0% | assumption | assumption A19: see assumptions-table.md |
| `rev_p5` | Plant 5 revenue | $195.0 million | derived | derived D96: revenue_fy0 * share_p5 |
| `share_p5` | Plant 5 share of revenue | 13.0% | assumption | assumption A20: see assumptions-table.md |
| `hc_p5` | Plant 5 employees | 250 | derived | derived D97: plant_workforce * share_p5 |
| `result_p5` | Plant 5 operating result | $29.3 million | derived | derived D98: rev_p5 * margin_p5 |
| `margin_p5` | Plant 5 operating margin, after allocated corporate costs | 15.0% | assumption | assumption A21: see assumptions-table.md |
| `rev_p6` | Plant 6 revenue | $150.0 million | derived | derived D99: revenue_fy0 * share_p6 |
| `share_p6` | Plant 6 share of revenue | 10.0% | derived | derived D100: 1 - share_p1 - share_p2 - share_p3 - share_p4 - share_p5. Note: The remainder: the smallest plant, about a tenth of revenue. |
| `hc_p6` | Plant 6 employees | 190 | derived | derived D101: plant_workforce * share_p6 |
| `result_p6` | Plant 6 operating result | -$9.0 million | derived | derived D102: rev_p6 * margin_p6 |
| `margin_p6` | Plant 6 operating margin, after allocated corporate costs | -6.0% | assumption | assumption A22: see assumptions-table.md |
| `payroll_p6` | Plant 6 payroll | $10.5 million | derived | derived D103: hc_p6 * plant_avg_pay |
| `price_change_fy2` | Industry producer price change, two years ago | 6.9% | derived | derived D104: ppi_2023 / ppi_2022 - 1 |
| `max_price_increase` | Price increase customers would accept in the coming year, at most | 3.5% | assumption | assumption A23: see assumptions-table.md |
| `price_cap` | Revenue from the largest price increase customers would accept | $52.5 million | derived | derived D105: revenue_fy0 * max_price_increase |
| `supplier_spend` | Spending with suppliers, year just ended | $753.0 million | derived | derived D106: revenue_fy0 * materials_share |
| `materials_share` | Purchased materials, parts and services as a share of revenue | 50.2% | derived | derived D107: aies_materials_2024 / aies_rev_2024 |
| `payment_days` | Days taken to pay suppliers | 72 | derived | derived D108: payables / supplier_spend * 365 |
| `renegotiable_share` | Supplier spending under agreements that come up for renewal in the coming year | 30.0% | assumption | assumption A24: see assumptions-table.md |
| `max_supplier_reduction` | Price reduction obtainable on renewing supplier agreements, at most | 4.0% | assumption | assumption A25: see assumptions-table.md |
| `supplier_cap` | Annual saving from pressing suppliers, at most | $9.0 million | derived | derived D109: supplier_spend * renegotiable_share * max_supplier_reduction |
| `energy_spend` | Spending on fuel and electricity, year just ended | $8.9 million | derived | derived D110: revenue_fy0 * (aies_fuel_2024 + aies_elec_2024) / aies_rev_2024 |
| `env_total` | Environmental spending, year just ended | $7.5 million | derived | derived D111: env_compliance + env_projects |
| `env_compliance` | Environmental compliance spending (permits, monitoring, waste handling), year just ended | $3.0 million | assumption | assumption A26: see assumptions-table.md |
| `env_projects` | Environmental projects budget (energy efficiency, emissions reduction), year just ended | $4.5 million | assumption | assumption A27: see assumptions-table.md |
| `plant_hires` | People hired from outside into plant roles, year just ended | 500 | derived | derived D112: plant_workforce * jolts_hires_rate. Note: The Company's plants are taken to hire at the durable goods rate. These are the openings a retrained employee could fill. |
| `retraining_cost_pp` | Retraining cost per person (instruction and paid training time) | $15,000 | assumption | assumption A28: see assumptions-table.md |
| `retraining_months` | Months of training before a retrained person works independently | 6 | assumption | assumption A29: see assumptions-table.md |
| `retraining_payback` | Years until retraining pays back, against hiring from outside | 2 | assumption | assumption A30: see assumptions-table.md |
| `max_wage_cut` | Reduction in wages or hours the Company can make within a year, at most, as a share of payroll | 10.0% | assumption | assumption A31: see assumptions-table.md |
| `wage_cut_cap` | Payroll saving from cutting wages or hours, at most | $24.4 million | derived | derived D113: payroll_total * max_wage_cut |
| `ind_sga_fy0` | Industry SG&A as a share of revenue, year just ended | 19.6% | sourced | Damodaran 2026 margins: Machinery, SG&A/ Sales; read as 0.19649988 |
| `ind_rnd_fy0` | Industry R&D as a share of revenue, year just ended | 2.0% | sourced | Damodaran 2026 margins: Machinery, R&D/Sales; read as 0.020329465 |
| `ind_net_margin_fy0` | Industry net margin, year just ended | 10.6% | sourced | Damodaran 2026 margins: Machinery, Net Margin; read as 0.10578747. Note: Used only to back out the industry's aggregate revenue; the Company's own net income is built from its operating income, interest and tax. |
| `ind_sga_fy1` | Industry SG&A as a share of revenue, prior year | 19.2% | sourced | Damodaran 2025 margins: Machinery, SG&A/ Sales; read as 0.19248441 |
| `ind_rnd_fy1` | Industry R&D as a share of revenue, prior year | 2.2% | sourced | Damodaran 2025 margins: Machinery, R&D/Sales; read as 0.021636323 |
| `ind_net_margin_fy1` | Industry net margin, prior year | 10.0% | sourced | Damodaran 2025 margins: Machinery, Net Margin; read as 0.100392 |
| `ind_sga_fy2` | Industry SG&A as a share of revenue, two years ago | 18.8% | sourced | Damodaran 2024 margins: Machinery, SG&A/ Sales; read as 0.18827063 |
| `ind_rnd_fy2` | Industry R&D as a share of revenue, two years ago | 2.1% | sourced | Damodaran 2024 margins: Machinery, R&D/Sales; read as 0.021220999 |
| `ind_net_margin_fy2` | Industry net margin, two years ago | 9.8% | sourced | Damodaran 2024 margins: Machinery, Net Margin; read as 0.097724728 |
| `ind_ni_total` | Industry aggregate net income (105 firms) | $20,804.5 million | sourced | Damodaran 2026 cash returns: Machinery, Net Income (US $ millions) 20804.484, in dollars; read as 20,804,484,000 |
| `ind_revenue_total` | Industry aggregate revenue (105 firms) | $196,268.9 million | derived | derived D114: ind_ni_total / ind_net_margin_fy0. Note: Damodaran's files used here do not state the industry's revenue; it is backed out of his aggregate net income and net margin, both computed over the same 105 firms. |
| `ind_capex_total` | Industry aggregate capital expenditures (105 firms) | $4,700.9 million | sourced | Damodaran 2026 capex: Machinery, Capital Expenditures (US $ millions) 4700.863, in dollars; read as 4,700,863,000 |
| `ind_da_total` | Industry aggregate depreciation and amortization (105 firms) | $6,927.6 million | sourced | Damodaran 2026 capex: Machinery, Depreciation & Amort (US $ millions) 6927.636, in dollars; read as 6,927,636,000 |
| `ppi_2022` | Producer price index, machinery manufacturing, annual average, two years before fy2 (2022) | 166.86 | sourced | BLS PPI: PCU333---333---, 2022, mean of the twelve monthly values; read as 166.86417 |
| `ppi_2023` | Producer price index, machinery manufacturing, annual average, fy2 (2023) | 178.39 | sourced | BLS PPI: PCU333---333---, 2023, mean of the twelve monthly values; read as 178.39433 |
| `ppi_2024` | Producer price index, machinery manufacturing, annual average, fy1 (2024) | 184.19 | sourced | BLS PPI: PCU333---333---, 2024, mean of the twelve monthly values; read as 184.18967 |
| `ppi_2025` | Producer price index, machinery manufacturing, annual average, fy0 (2025) | 190.55 | sourced | BLS PPI: PCU333---333---, 2025, mean of the twelve monthly values; read as 190.54667 |
| `aies_rev_2023` | Industry revenue, NAICS 333, 2023 | $476,234.7 million | sourced | AIES 2023: NAICS 333, U.S., RCPT_TOT_VAL ($1,000) 476234673, in dollars; read as 476,234,673,000 |
| `aies_rev_2024` | Industry revenue, NAICS 333, 2024 | $473,891.5 million | sourced | AIES 2024: NAICS 333, U.S., RCPT_TOT_VAL ($1,000) 473891483, in dollars; read as 473,891,483,000 |
| `ind_da_share` | Industry depreciation and amortization as a share of revenue | 3.5% | derived | derived D115: ind_da_total / ind_revenue_total |
| `ind_book_rate` | Industry book interest rate | 4.8% | sourced | Damodaran 2026 debt detail: Machinery, Book interest rate; read as 0.047970758 |
| `ind_tax_rate` | Industry effective tax rate, aggregate | 21.3% | sourced | Damodaran 2026 tax rates: Machinery, Effective Tax Rates: Aggregate tax rate (the first of the two columns so named; the second is the cash rate); read as 0.21294562 |
| `ind_ar_sales` | Industry receivables as a share of revenue | 19.0% | sourced | Damodaran 2026 working capital: Machinery, Acc Rec/ Sales; read as 0.19032645 |
| `ind_inv_sales` | Industry inventory as a share of revenue | 16.6% | sourced | Damodaran 2026 working capital: Machinery, Inventory/Sales; read as 0.16618568 |
| `ind_ap_sales` | Industry payables as a share of revenue | 9.9% | sourced | Damodaran 2026 working capital: Machinery, Acc Pay/ Sales; read as 0.099265724 |
| `ind_nwc_sales` | Industry non-cash working capital as a share of revenue | 24.4% | sourced | Damodaran 2026 working capital: Machinery, Non-cash WC/ Sales; read as 0.24421936 |
| `ind_ebitda_ev` | Industry EBITDA to enterprise value | 6.0% | sourced | Damodaran 2026 debt ratios: Machinery, EBITDA/EV; read as 0.060369518 |
| `ind_cash_fv` | Industry cash to firm value | 2.9% | sourced | Damodaran 2026 cash returns: Machinery, Cash/ Firm Value; read as 0.029141915 |
| `ind_book_dc` | Industry book debt to capital | 39.3% | sourced | Damodaran 2026 debt ratios: Machinery, Book Debt to Capital; read as 0.39328982 |
| `enterprise_value` | Enterprise value | $4,850.0 million | derived | derived D116: ebitda_fy0 / ind_ebitda_ev. Note: At the industry's EBITDA to enterprise value. |
| `ind_capex_share` | Industry capital expenditures as a share of revenue | 2.4% | derived | derived D117: ind_capex_total / ind_revenue_total |
| `aies_emp_2024` | Industry employees, NAICS 333, 2024 | 1,046,464 | sourced | AIES 2024: NAICS 333, U.S., EMP_MAR12_NUM; read as 1,046,464 |
| `aies_payroll_2024` | Industry annual payroll, NAICS 333, 2024 | $84,347.8 million | sourced | AIES 2024: NAICS 333, U.S., PAY_ANN_VAL ($1,000) 84347756, in dollars; read as 84,347,756,000 |
| `aies_fringe_2024` | Industry employer cost of fringe benefits, NAICS 333, 2024 | $22,566.7 million | sourced | AIES 2024: NAICS 333, U.S., EXPS_FRNG_BENEFIT_VAL ($1,000) 22566734, in dollars; read as 22,566,734,000 |
| `ind_rev_per_emp` | Industry revenue per employee | $452,850 | derived | derived D118: aies_rev_2024 / aies_emp_2024 |
| `oews_emp_all` | Industry jobs, all occupations | 1,092,170 | sourced | OEWS May 2025: NAICS 333000, 00-0000 All Occupations, TOT_EMP; read as 1,092,170 |
| `oews_emp_prod` | Industry jobs, production occupations | 516,150 | sourced | OEWS May 2025: NAICS 333000, 51-0000 Production Occupations, TOT_EMP; read as 516,150 |
| `oews_emp_maint` | Industry jobs, installation, maintenance and repair occupations | 59,060 | sourced | OEWS May 2025: NAICS 333000, 49-0000 Installation, Maintenance, and Repair Occupations, TOT_EMP; read as 59,060 |
| `oews_emp_logistics` | Industry jobs, transportation and material moving occupations | 52,110 | sourced | OEWS May 2025: NAICS 333000, 53-0000 Transportation and Material Moving Occupations, TOT_EMP; read as 52,110 |
| `oews_emp_eng` | Industry jobs, architecture and engineering occupations | 116,640 | sourced | OEWS May 2025: NAICS 333000, 17-0000 Architecture and Engineering Occupations, TOT_EMP; read as 116,640 |
| `oews_emp_it` | Industry jobs, computer and mathematical occupations | 29,780 | sourced | OEWS May 2025: NAICS 333000, 15-0000 Computer and Mathematical Occupations, TOT_EMP; read as 29,780 |
| `oews_emp_sales` | Industry jobs, sales occupations | 38,040 | sourced | OEWS May 2025: NAICS 333000, 41-0000 Sales and Related Occupations, TOT_EMP; read as 38,040 |
| `oews_emp_office` | Industry jobs, office and administrative support occupations | 91,270 | sourced | OEWS May 2025: NAICS 333000, 43-0000 Office and Administrative Support Occupations, TOT_EMP; read as 91,270 |
| `oews_emp_business` | Industry jobs, business and financial operations occupations | 71,240 | sourced | OEWS May 2025: NAICS 333000, 13-0000 Business and Financial Operations Occupations, TOT_EMP; read as 71,240 |
| `oews_emp_mgmt` | Industry jobs, management occupations | 92,110 | sourced | OEWS May 2025: NAICS 333000, 11-0000 Management Occupations, TOT_EMP; read as 92,110 |
| `oews_emp_assemblers` | Industry jobs, miscellaneous assemblers and fabricators | 143,310 | sourced | OEWS May 2025: NAICS 333000, 51-2090 Miscellaneous Assemblers and Fabricators, TOT_EMP; read as 143,310 |
| `oews_emp_welders` | Industry jobs, welders, cutters, solderers and brazers | 63,880 | sourced | OEWS May 2025: NAICS 333000, 51-4121 Welders, Cutters, Solderers, and Brazers, TOT_EMP; read as 63,880 |
| `oews_emp_machinists` | Industry jobs, machinists | 59,550 | sourced | OEWS May 2025: NAICS 333000, 51-4041 Machinists, TOT_EMP; read as 59,550 |
| `oews_emp_mech_eng` | Industry jobs, mechanical engineers | 41,730 | sourced | OEWS May 2025: NAICS 333000, 17-2141 Mechanical Engineers, TOT_EMP; read as 41,730 |
| `oews_emp_mechanics` | Industry jobs, industrial machinery mechanics | 24,740 | sourced | OEWS May 2025: NAICS 333000, 49-9041 Industrial Machinery Mechanics, TOT_EMP; read as 24,740 |
| `aies_materials_2024` | Industry cost of materials, NAICS 333, 2024 | $237,904.5 million | sourced | AIES 2024: NAICS 333, U.S., EXPS_CSTMTOT_DVAL ($1,000) 237904461, in dollars (materials, parts, resale, contract work, fuel and electricity); read as 237,904,461,000 |
| `aies_fuel_2024` | Industry purchased fuels, NAICS 333, 2024 | $543.2 million | sourced | AIES 2024: NAICS 333, U.S., EXPS_FUEL_VAL ($1,000) 543209, in dollars; read as 543,209,000 |
| `aies_elec_2024` | Industry purchased electricity, NAICS 333, 2024 | $2,267.8 million | sourced | AIES 2024: NAICS 333, U.S., EXPS_ELEC_VAL ($1,000) 2267798, in dollars; read as 2,267,798,000 |
| `jolts_hires_rate` | Hires as a share of employment, durable goods manufacturing, 2025 | 26.4% | sourced | BLS JOLTS: JTU320000000000000HIR, 2025, sum of the twelve monthly rates, 26.4 (percent), as a fraction; read as 0.264 |
