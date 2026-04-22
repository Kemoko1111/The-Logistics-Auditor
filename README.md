# Project Brief: The "Last Mile" Logistics Auditor

**Client:** Veridi Logistics (Global E-Commerce Aggregator)  
**Deliverable:** Public Dashboard, Code Notebook & Insight Presentation

---

## A. Executive Summary

Veridi Logistics' delivery data reveals that **~8% of orders are delivered late**, with a significant regional disparity: **Northern and Northeastern Brazilian states** (e.g., AM, RR, AP, MA, AL) experience late delivery rates **2-3x higher** than hub states near distribution centers (SP, RJ, MG). This confirms the CEO's suspicion — the problem is **regional, not nationwide**. Furthermore, we established a **clear negative correlation between delivery delays and customer review scores**: on-time orders average ~4.2 stars while super-late orders (>7 days) average ~1.3 stars, proving that logistics performance is the **direct root cause** of negative customer reviews. We also identified that certain product categories (likely bulkier/heavier items like electronics and furniture) suffer systematically worse delays, presenting an opportunity for category-specific shipping optimizations.

## B. Project Links

- **Link to Notebook:** [logistics_auditor.ipynb on GitHub](https://github.com/Kemoko1111/The-Logistics-Auditor/blob/main/logistics_auditor.ipynb)
- **Link to Dashboard:** [https://logistics-auditor.streamlit.app](https://logistics-auditor.streamlit.app/)
- **Link to Presentation:** [Logistics_Auditor_Presentation on Google Drive](https://docs.google.com/presentation/d/1jB9LBVPcRFWKX33SCCeK2U-ImForl5VY/edit?usp=sharing&ouid=114393768506535582100&rtpof=true&sd=true)

> **How to run the dashboard locally:**
> ```bash
> pip install -r requirements.txt
> streamlit run dashboard.py
> ```

## C. Technical Explanation

### Data Cleaning
1. **Duplicate Reviews:** The `olist_order_reviews_dataset.csv` contains multiple reviews per order. We deduplicated by keeping the **latest review** per `order_id` (sorted by `review_creation_date`), reducing from ~100k to ~99k unique reviews.
2. **Join Strategy:** We used left joins — Orders → Customers (on `customer_id`) → Reviews (on `order_id`). Post-join row count was validated against the original Orders table to ensure **zero row duplication**.
3. **Undelivered Orders:** Orders with `order_status` != `delivered` (canceled, unavailable, etc.) were **excluded** from delay calculations since they lack actual delivery dates.
4. **Missing Delivery Dates:** A small number of delivered orders had null `order_delivered_customer_date` — these were dropped from analysis.
5. **Product Category Dedup:** When joining product data via `order_items`, we kept only the **first item per order** to avoid re-introducing row duplication in multi-item orders.

### Candidate's Choice: Delivery Performance by Product Category
**Why this matters:** Different product categories have different physical characteristics (weight, dimensions) that directly impact shipping logistics. By analyzing which categories consistently suffer the worst delays, Veridi Logistics can:
- **Negotiate better carrier contracts** for problematic categories
- **Set more realistic delivery estimates** per category instead of a one-size-fits-all approach
- **Optimize warehouse placement** for high-delay categories

The analysis revealed meaningful variation in late delivery rates across categories, suggesting that a category-aware shipping strategy could significantly reduce overall late deliveries.

---
