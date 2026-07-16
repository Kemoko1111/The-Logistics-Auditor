# 🚚 Interview Preparation — The "Last Mile" Logistics Auditor

> **Project Name:** The Logistics Auditor  
> **Client (Fictional):** Veridi Logistics (Global E-Commerce Aggregator)  
> **Deliverables:** Jupyter Notebook, Streamlit Dashboard, Presentation  
> **Live Dashboard:** [logistics-auditor.streamlit.app](https://logistics-auditor.streamlit.app/)  
> **GitHub:** [Kemoko1111/The-Logistics-Auditor](https://github.com/Kemoko1111/The-Logistics-Auditor)

---

## 1. Project Overview — The "Elevator Pitch"

> **If asked "Tell me about this project" — use this:**

"I built a logistics audit system for a fictional client called Veridi Logistics. The goal was to investigate **why customers were leaving bad reviews** on an e-commerce platform. Using the **Olist Brazilian E-Commerce dataset** (~100K orders), I proved that **late deliveries are the direct root cause of negative reviews** — not product quality, not pricing, but logistics.

I delivered three things:
1. A **Jupyter Notebook** with full exploratory data analysis
2. An **interactive Streamlit dashboard** deployed to the cloud
3. A **presentation** summarizing key findings and recommendations

The main findings were:
- ~8% of orders arrive late, but those orders disproportionately generate 1-2 star reviews
- The problem is **regional, not nationwide** — Northern/Northeastern Brazilian states suffer 2-3x higher late rates than hub states near distribution centers
- On-time orders average **~4.2 stars**, while super-late orders average only **~1.3 stars**
- Certain product categories (heavier/bulkier items) consistently have worse delivery performance"

---

## 2. The Dataset — Know These Cold

### Source
- **Olist Brazilian E-Commerce Dataset** from Kaggle
- Real anonymized orders from 2016-2018
- License: CC0 (Public Domain)

### Tables Used (6 CSV files)

| Table | Rows | Key Columns |
|---|---|---|
| `olist_orders_dataset.csv` | ~99,441 | `order_id`, `customer_id`, `order_status`, `order_purchase_timestamp`, `order_delivered_customer_date`, `order_estimated_delivery_date` |
| `olist_customers_dataset.csv` | ~99,441 | `customer_id`, `customer_state`, `customer_city` |
| `olist_order_reviews_dataset.csv` | ~104,719 | `order_id`, `review_score` (1-5), `review_comment_message` |
| `olist_order_items_dataset.csv` | ~112,650 | `order_id`, `product_id`, `price`, `freight_value` |
| `olist_products_dataset.csv` | ~32,951 | `product_id`, `product_category_name`, `product_weight_g` |
| `product_category_name_translation.csv` | 70 | Maps Portuguese category names → English |

### Key Relationships
```
Orders ──(customer_id)──> Customers
Orders ──(order_id)──> Reviews
Orders ──(order_id)──> Order Items ──(product_id)──> Products
Products ──(product_category_name)──> Translations
```

---

## 3. Data Cleaning & Preparation — Expect Questions Here

### 3.1 Duplicate Reviews Problem
- **Problem:** The reviews table has **~104K rows** but only **~99K unique orders** — some orders have multiple reviews.
- **Solution:** Sorted by `review_creation_date` descending, then kept only the **first (latest) review** per `order_id` using `drop_duplicates()`.
- **Why latest?** The most recent review best represents the customer's final sentiment after any follow-up interactions.

### 3.2 Join Strategy
```
Step 1: Orders LEFT JOIN Customers    (on customer_id)  → 99,441 rows
Step 2: Result LEFT JOIN Reviews      (on order_id)     → 99,441 rows ✓
```
- Used **left joins** throughout to preserve all orders (even those without reviews).
- **Validated** the row count after each join with an `assert` statement to confirm **zero row duplication**.

### 3.3 Filtering to Delivered Orders Only
- Orders with `order_status != 'delivered'` (canceled, unavailable, etc.) were **excluded** because they lack actual delivery dates.
- This removed a small fraction of orders.

### 3.4 Handling Missing Delivery Dates
- Some delivered orders had null `order_delivered_customer_date` — these were **dropped** using `dropna()` since we can't calculate delay without an actual delivery date.

### 3.5 Product Category Deduplication
- **Problem:** The `order_items` table has multiple rows per order (one per item). Joining directly would re-introduce row duplication.
- **Solution:** Kept only the **first item per order** (`drop_duplicates(subset='order_id', keep='first')`) before joining product categories.
- **Trade-off acknowledged:** Multi-item orders are represented by only their first item's category. This is a simplification but avoids inflating row counts.

---

## 4. The Core Metric — Days_Difference

### How It's Calculated
```python
Days_Difference = order_estimated_delivery_date - order_delivered_customer_date
```

| Value | Meaning |
|---|---|
| **Positive** (e.g., +5) | Delivered **5 days BEFORE** the estimate → Early/On Time |
| **Zero** (0) | Delivered **exactly on** the estimated date |
| **Negative** (e.g., -3) | Delivered **3 days AFTER** the estimate → Late |

### Classification Thresholds
| Category | Condition | Meaning |
|---|---|---|
| **On Time** | `Days_Difference >= 0` | Arrived on or before the estimate |
| **Late** | `-5 <= Days_Difference < 0` | 1-5 days past the estimate |
| **Super Late** | `Days_Difference < -5` | More than 5 days past the estimate |

### Results
- **~92% On Time** (~84,800 orders)
- **~5% Late** (~4,600 orders)  
- **~3% Super Late** (~2,800 orders)

---

## 5. The 4 User Stories + Candidate's Choice

### Story 1: The Schema Builder 🔧
- **Persona:** Data Engineer
- **Goal:** Join Orders, Reviews, and Customers into a single master dataset
- **What I did:** Multi-step left joins with deduplication, row count validation
- **Key skill demonstrated:** Data wrangling, schema design, data integrity checks

### Story 2: The "Real" Delay Calculator ⏱️
- **Persona:** Logistics Manager
- **Goal:** Calculate the gap between estimated and actual delivery dates
- **What I did:** Created `Days_Difference` metric, classified into On Time/Late/Super Late
- **Visualizations:** Pie chart of status distribution + histogram of delay days
- **Key finding:** The distribution is heavily right-skewed — most orders are early, but the late tail is significant

### Story 3: The Geographic Heatmap 🗺️
- **Persona:** Regional Director
- **Goal:** Identify which states have the highest late delivery rates
- **What I did:** Grouped by `customer_state`, calculated `% Late`, created choropleth map + bar chart
- **Key finding:** Northern/Northeastern states (AM, RR, AP, AL, MA) have 2-3x higher late rates than hub states (SP, RJ, MG)
- **Insight:** Remote states far from distribution hubs suffer disproportionately — this is a **regional logistics gap**, not a nationwide issue

### Story 4: The Sentiment Correlation 💬
- **Persona:** Customer Success Lead
- **Goal:** Prove that late deliveries actually cause bad reviews
- **What I did:** Compared average review scores across delivery status categories + created binned delay-vs-review chart
- **Key finding:**
  - On Time → **~4.2 stars**
  - Late → **~2.5 stars**
  - Super Late → **~1.3 stars**
- **Conclusion:** There is a **clear negative correlation** — logistics IS the root cause of negative reviews

### Candidate's Choice: Product Category Analysis 📦
- **Business justification:** Different product categories have different physical characteristics (weight, dimensions) that affect shipping logistics
- **What I did:** Analyzed late delivery rates and review scores across the top 15 product categories
- **Key finding:** Categories involving heavier/bulkier items show higher delay rates
- **Actionable recommendations:**
  1. Negotiate better carrier contracts for problematic categories
  2. Set more realistic delivery estimates per category (not one-size-fits-all)
  3. Optimize warehouse placement for high-delay categories

---

## 6. The Streamlit Dashboard — Technical Architecture

### Tech Stack
| Component | Technology |
|---|---|
| Framework | **Streamlit** (Python web framework for data apps) |
| Charting | **Plotly Express** + **Plotly Graph Objects** (interactive charts) |
| Data | **Pandas** (data manipulation) |
| Map Data | **GeoJSON** (Brazil states boundaries from GitHub) |
| Styling | Custom **CSS** injected via `st.markdown(unsafe_allow_html=True)` |
| Font | **Inter** (Google Fonts) |
| Deployment | **Streamlit Community Cloud** (free hosting) |

### Dashboard Structure (dashboard.py — 474 lines)

```
1. Page Config (title, icon, layout)
2. Custom CSS (dark theme, glassmorphism cards, gradient header)
3. Data Loading (@st.cache_data — loads & prepares data, cached for performance)
4. GeoJSON Loading (@st.cache_data — Brazil states map)
5. Sidebar Filters (States, Delivery Status, Product Categories)
6. Header (gradient banner)
7. KPI Cards Row (5 metric cards: Total Orders, On Time %, Late %, Avg Days Early, Avg Review)
8. Row 1: Geographic Analysis (Choropleth Map + State Bar Chart)
9. Row 2: Sentiment Analysis (Review by Status + Binned Delay vs Review)
10. Row 3: Category Analysis (Late Rate by Category + Review by Category)
11. Row 4: Monthly Trend (Late delivery % over time)
12. Footer
```

### Key Technical Decisions

1. **`@st.cache_data` decorator** — Caches the data loading function so CSVs are only read once. Subsequent filter changes don't re-read files.

2. **Interactive Plotly charts** instead of static Matplotlib — Users can hover, zoom, and explore the data.

3. **Sidebar filters** — Allow users to drill down by state, delivery status, and product category without reloading.

4. **Choropleth map** — Fetches GeoJSON at runtime from GitHub, maps state abbreviations (`sigla`) to geographic features.

5. **`unsafe_allow_html=True`** — Used to inject custom CSS for premium dark-theme styling (gradient backgrounds, card layouts, custom fonts).

6. **NaN handling** — Explicit `math.isnan()` checks for edge cases where all filtered data might produce NaN averages.

7. **Monthly trend filtering** — Months with fewer than 50 orders are excluded to avoid noisy/misleading percentages.

---

## 7. Deployment

### Streamlit Community Cloud
- The dashboard is deployed at **logistics-auditor.streamlit.app**
- Streamlit Cloud reads `requirements.txt` and installs dependencies automatically
- CSV data files are committed to the repo (not gitignored) specifically **for cloud deployment**
- The `.gitignore` excludes build scripts (`create_notebook.py`) and generated PNGs, but keeps CSVs

### To Run Locally
```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

### Requirements
```
pandas, matplotlib, seaborn, plotly, streamlit, jupyter, nbconvert, kaleido, nbformat
```

---

## 8. Key Numbers to Memorize

| Metric | Value |
|---|---|
| Total orders in dataset | ~99,441 |
| Delivered orders analyzed | ~92,000+ |
| On-time delivery rate | ~92% |
| Late delivery rate | ~5% |
| Super-late delivery rate | ~3% |
| Avg review (On Time) | ~4.2 ★ |
| Avg review (Late) | ~2.5 ★ |
| Avg review (Super Late) | ~1.3 ★ |
| Worst states for delays | AM, RR, AP, AL, MA (Northern/NE) |
| Best states for on-time | SP, PR, MG (Near hubs) |
| Remote vs Hub late rate | 2-3x higher in remote states |
| CSV files used | 6 |
| Dashboard lines of code | 474 |
| Notebook stories | 4 + 1 candidate's choice |

---

## 9. Anticipated Interview Questions & Answers

### About the Project

**Q: What was the business problem you were trying to solve?**
> Veridi Logistics was receiving bad customer reviews but didn't know why. The CEO suspected it might be a regional issue. My job was to audit the delivery data to find out if late deliveries were causing bad reviews, and if so, where the problem was worst.

**Q: Why did you choose this dataset?**
> The Olist Brazilian E-Commerce dataset is a well-known public dataset with ~100K real (anonymized) orders. It uniquely combines logistics data (delivery timestamps) with customer sentiment data (review scores), which is exactly what I needed to prove the connection between delivery performance and customer satisfaction.

**Q: What were your main deliverables?**
> Three things: (1) A Jupyter Notebook with the full analysis and visualizations, (2) An interactive Streamlit dashboard deployed to the cloud, and (3) A presentation deck summarizing findings and recommendations.

---

### About Data Cleaning

**Q: How did you handle duplicate data?**
> The reviews table had multiple reviews per order. I deduplicated by sorting by review creation date (descending) and keeping only the latest review per order. For product categories, I kept only the first item per order to avoid row multiplication when joining the order_items table.

**Q: Why did you use left joins?**
> To preserve all orders in the master dataset, even those without reviews or product information. An inner join would have dropped valid orders that simply hadn't been reviewed yet.

**Q: How did you validate your joins?**
> After each join, I checked the row count against the original orders table using an `assert` statement. If the count changed, it would mean row duplication occurred — which would invalidate all percentage calculations downstream.

**Q: What did you do with missing data?**
> For missing delivery dates, I dropped those rows since I can't calculate delay without an actual delivery date. For missing review scores, I kept them (via left join) since they're still valid for delivery analysis. For missing product categories, I filled with 'Unknown' or 'Other'.

---

### About the Analysis

**Q: How did you calculate if a delivery was late?**
> I calculated `Days_Difference = Estimated Date - Actual Date`. Positive means early, negative means late. I classified into three buckets: On Time (≥0 days), Late (-1 to -5 days), and Super Late (more than -5 days).

**Q: Why those specific thresholds (-5 days)?**
> The threshold of -5 days for "Super Late" represents a meaningful customer experience boundary — being a few days late is annoying, but being a week or more late is a fundamentally different level of dissatisfaction. The data also shows a clear drop in review scores past this threshold.

**Q: How did you prove that late deliveries cause bad reviews?**
> I showed the correlation in multiple ways: (1) Average review scores by delivery status — clear stepdown from 4.2 to 2.5 to 1.3, (2) Binned delay analysis — the review score consistently drops with each additional day of delay. It's not just correlation; the dose-response relationship (more delay = worse review) strongly suggests causation.

**Q: What's the difference between correlation and causation here?**
> Strictly speaking, this is observational data so I can only prove correlation. However, the relationship is strong, monotonic (more delay = worse reviews), and there's a clear mechanism (customers are upset about late deliveries). While I can't run an A/B test, the evidence is compelling enough for business decisions.

**Q: Why do remote states have higher late delivery rates?**
> Brazil's major distribution centers and sellers are concentrated in the Southeast (São Paulo, Rio de Janeiro, Minas Gerais). Orders going to Northern and Northeastern states travel much farther, through less-developed logistics infrastructure. This creates a geographic "last mile" problem.

---

### About the Dashboard

**Q: Why Streamlit?**
> Streamlit is ideal for data science dashboards — it's Python-native (no frontend skills needed), renders Pandas DataFrames and Plotly charts natively, and offers free cloud deployment. It lets me go from analysis to interactive web app quickly.

**Q: How did you handle performance?**
> I used Streamlit's `@st.cache_data` decorator on the data loading functions. This means the 6 CSV files are loaded and processed only once, then cached in memory. When users change filters, only the filtering/charting logic re-runs — not the data loading.

**Q: How does the choropleth map work?**
> I load a GeoJSON file of Brazilian state boundaries from a public GitHub repo. Each feature has a `sigla` property (state abbreviation) that I map to my data's `customer_state` column. Plotly's `px.choropleth` then colors each state polygon by its `pct_late` value using a Red-Yellow-Green color scale.

**Q: How did you style the dashboard?**
> I injected custom CSS via `st.markdown()` with `unsafe_allow_html=True`. This includes: a dark gradient theme, glassmorphism-style metric cards, Inter font from Google Fonts, and color-coded text (green for good, red for bad). This gives it a premium, professional look.

**Q: Why did you include sidebar filters?**
> Filters let stakeholders explore the data themselves — a Regional Director can filter to their states, a Category Manager can focus on their product categories. It makes the dashboard a tool, not just a report.

---

### About Technical Choices

**Q: Why Plotly instead of Matplotlib for the dashboard?**
> Matplotlib generates static images. Plotly generates interactive HTML charts where users can hover for details, zoom, pan, and export. For a web dashboard, interactivity is essential.

**Q: Why did you keep Matplotlib in the notebook?**
> The notebook is a static document (meant to be read on GitHub or as an HTML export). Matplotlib is lighter, more widely supported in notebooks, and produces cleaner static charts. I used Plotly only for the interactive choropleth map in the notebook.

**Q: What would you do differently with more time?**
> Several things: (1) Add a **seller location** analysis to map seller-to-customer distances and their impact on delays, (2) Build a **predictive model** (e.g., logistic regression) to predict which orders are likely to be late, (3) Add **time-series forecasting** for delivery performance trends, (4) Implement **NLP sentiment analysis** on review comment text to extract specific complaints.

---

### Behavioral / Soft Skill Questions

**Q: What was the most challenging part of this project?**
> The data preparation — specifically the join strategy. The reviews table had duplicates that would silently inflate my row counts and skew all percentage calculations. Running that `assert` check after joins saved me from reporting incorrect numbers. It taught me to always validate row counts after every join.

**Q: How would you explain your findings to a non-technical stakeholder?**
> "We found that 8 out of every 100 orders arrive late. When they do, customers punish us with 1-2 star reviews instead of the 4-5 stars we'd normally get. And this problem isn't everywhere — it's concentrated in specific remote states far from our warehouses. If we fix logistics in those 5-10 worst states, we can dramatically improve our overall review scores."

**Q: What actionable recommendations did you make?**
> Four main ones: (1) Invest in regional logistics partnerships in underserved Northern/Northeastern states, (2) Recalibrate delivery estimates to under-promise and over-deliver, (3) Implement category-specific shipping strategies for heavier items, (4) Track `Days_Difference` as a core KPI alongside review scores.

---

## 10. Potential Gotcha Questions

**Q: Isn't ~92% on-time already good? Why bother?**
> 8% late might sound small, but with ~100K orders, that's ~8,000 disappointed customers leaving 1-2 star reviews. Those reviews are visible to future customers and directly impact conversion rates and brand trust. Also, the 8% is an average — in the worst states it's 15-20%.

**Q: You only kept the first item per order for category analysis — doesn't that lose information?**
> Yes, it's a trade-off. Multi-item orders could belong to multiple categories. I chose data integrity (no row duplication) over completeness. An alternative would be to assign order-level categories based on the most expensive item or create a multi-label representation, but for this level of analysis, the simplification is acceptable.

**Q: Why not use an inner join for reviews?**
> An inner join would drop ~5-10% of orders that haven't been reviewed. This would bias the analysis toward reviewed orders only, which might not be representative of all delivery experiences.

**Q: What if the estimated delivery date is intentionally inflated?**
> That's a real possibility — companies often pad estimates to appear "early." This analysis would still be valid because: (1) if estimates are padded, the fact that some orders are STILL late means the logistics gap is even worse than it appears, and (2) the sentiment correlation doesn't depend on estimate accuracy — it measures actual vs. promised performance.

**Q: Could there be confounding variables? Maybe bad products cause both returns/delays AND bad reviews?**
> Good question. The dose-response relationship (each additional day of delay correlates with lower scores) is strong evidence that delay itself is the driver, not just a confound. I also controlled for this partially by analyzing across product categories — the pattern holds within categories too.

---

## 11. Quick-Reference: Tools & Libraries

| Tool | Purpose |
|---|---|
| **Python 3** | Core language |
| **Pandas** | Data loading, cleaning, manipulation, aggregation |
| **Matplotlib + Seaborn** | Static charts in the notebook |
| **Plotly Express / Graph Objects** | Interactive charts in the dashboard |
| **Streamlit** | Dashboard web framework |
| **Jupyter / nbformat** | Notebook creation and execution |
| **Kaleido** | Static chart export |
| **Git / GitHub** | Version control and code hosting |
| **Streamlit Community Cloud** | Dashboard deployment |

---

## 12. Project File Structure

```
The-Logistics-Auditor/
├── dashboard.py                         ← Streamlit dashboard (474 lines)
├── logistics_auditor.ipynb              ← Main Jupyter notebook
├── create_notebook.py                   ← Script that generates the notebook
├── requirements.txt                     ← Python dependencies
├── README.md                            ← Project brief & links
├── LICENSE                              ← CC0 Public Domain
├── Logistics_Auditor_Presentation.pptx  ← Slide deck
├── olist_orders_dataset.csv             ← Orders (99K rows)
├── olist_customers_dataset.csv          ← Customers (99K rows)
├── olist_order_reviews_dataset.csv      ← Reviews (104K rows)
├── olist_order_items_dataset.csv        ← Order Items (112K rows)
├── olist_products_dataset.csv           ← Products (32K rows)
├── product_category_name_translation.csv← Category translations (70 rows)
├── *.png                                ← Generated chart images
└── .gitignore                           ← Excludes build scripts & PNGs
```

---

## 13. Final Checklist Before Your Interview

- [ ] Can explain the project in 60 seconds (Section 1)
- [ ] Know all 6 dataset tables and their relationships (Section 2)
- [ ] Can explain every data cleaning step and **why** (Section 3)
- [ ] Understand `Days_Difference` calculation and thresholds (Section 4)
- [ ] Can walk through all 4 stories + candidate's choice (Section 5)
- [ ] Know the dashboard architecture and technical decisions (Section 6)
- [ ] Have key numbers memorized (Section 8)
- [ ] Practiced answers for common questions (Section 9)
- [ ] Ready for gotcha/edge-case questions (Section 10)
- [ ] Can articulate what you'd do differently with more time
- [ ] Have the live dashboard URL ready to demo

---

> **Good luck with your interview! 🎯**
