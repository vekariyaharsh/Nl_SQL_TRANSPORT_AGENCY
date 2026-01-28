# SQL Logistics Pipeline - Quick Guide

## 🚛 What This Does

This pipeline converts your **logistics business questions** to **SQL queries** for your transport management system, executes them on **MySQL**, and stores successful queries in **Neo4j** for continuous learning.

## 📊 Your Database Schema

Table: `lr_dump` (LR = Lorry Receipt / Consignment Note data)

**Key Fields:**
- **CN Info**: `CN No`, `CN Date`, `CN Type`, `CN DOE`
- **Billing**: `Billing Party`, `Billing Office`, `Bill No`, `Bill Date`
- **Route**: `Route`, `Origin`, `Destination`, `LR Office`
- **Vehicle**: `Vehicle No`, `Vehicle Type`, `Load Type`
- **Weight**: `No of Pieces`, `Actual Weight`, `Charge Weight`
- **Financial**: `Total Freight`, `Basic Freight`, `Detention`, `Other Charges`, `Service Tax`
- **Payments**: `Payment Received`, `Deduction LR`, `Balance`
- **Hire Charges**: `Hire Chargers`, `Detention HC`, `Unload HC`, `Other HC`, `Misc1 HC`, `Misc2 HC`, `PenaltyHC`, `ClaimsHC`
- **Profit**: `LR Profit`, `Extra Cost of LR`
- **Parties**: `Consignor`, `Consignee`, `Broker`, `Hire Vehicle Party`
- **Dates**: `MRNo`, `Expected Date`, `Reach Date`, `Unload Date`, `POD Date`, `Submission Date`
- **POD**: `POD Receipt No`, `POD Receipt Date`
- **HM**: `No Of HM`, `HM No`, `HM Bal Pymt Office`

## 🚀 Setup

### 1. Configure `.env`

```env
# MySQL Configuration (your lr_dump data)
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DATABASE=test_harsh

# Neo4j (for storing query examples)
NEO4J_PASSWORD=your_neo4j_password

# OpenAI
OPENAI_API_KEY=sk-your_api_key

# Query Type
QUERY_TYPE=SQL
```

### 2. Run

```bash
python app_sql.py
```

## 💼 Logistics Business Questions You Can Ask

### Revenue & Billing Queries
- "What was the revenue from billing party XYZ from Jan 2021 to Dec 2021?"
- "Total revenue for 2021"
- "Top 5 billing parties based on revenue in 2022"
- "Show billing party revenue breakdown by month for 2023"
- "Find billing parties with revenue over 100000 in 2022"

### Consignment Queries
- "How many consignments for ABC billing party in March 2022?"
- "How many consignments in March 2021?"
- "Compare revenue year over year (2021 vs 2022)"

### Route Analytics
- "Most used route in 2022"
- "Profit analysis by route in 2022"
- "Origin to destination route analysis"

### Financial Analysis
- "Pending payments by billing party"
- "Average hire charges per consignment in Q1 2023"
- "Detention charges breakdown by billing party"

### Vehicle Analysis
- "Vehicle utilization report for 2022"

## 📊 Example Session

```bash
$ python app_sql.py

💬 Your question: Top 5 billing parties based on revenue in 2022

🔄 [Node 1] Generating SQL query...
✅ Generated SQL query:
SELECT 
    `Billing Party`,
    SUM(`Total Freight`) as total_revenue,
    COUNT(`CN No`) as consignment_count,
    AVG(`Total Freight`) as avg_freight_per_consignment,
    SUM(`Actual Weight`) as total_weight
FROM lr_dump
WHERE YEAR(`CN Date`) = 2022
GROUP BY `Billing Party`
ORDER BY total_revenue DESC
LIMIT 5

🔍 [Node 2] Validating SQL query...
✅ Validation PASSED

⚡ [Node 4] Executing SQL query on MySQL...
✅ Query executed successfully!
📊 Returned 5 result(s)

💾 Stored SQL query example in Neo4j

📊 RESULTS
Result 1:
  Billing Party: ABC Logistics
  total_revenue: 2500000.00
  consignment_count: 450
  avg_freight_per_consignment: 5555.56
  total_weight: 125000.50
...
```

## 🎯 Common Use Cases

### 1. Revenue Analysis
```
"What was the revenue from billing party [NAME] in [MONTH] [YEAR]?"
"Total revenue for [YEAR]"
"Monthly revenue breakdown for [YEAR]"
```

### 2. Party Performance
```
"Top 10 billing parties by revenue"
"Billing parties with pending payments"
"Consignments from billing party [NAME]"
```

### 3. Route Optimization
```
"Most profitable routes in [YEAR]"
"Route usage statistics"
"Average delivery time by route"
```

### 4. Financial Tracking
```
"Outstanding balance from all parties"
"Detention charges by party"
"Hire charges breakdown"
"Profit margin by route"
```

### 5. Operational Metrics
```
"Vehicle utilization report"
"Average weight per consignment"
"Delivery performance by route"
```

## 📋 New Features for Logistics Domain

### 15 Business Analytics Examples
1. Revenue by billing party (date range)
2. Consignment count by party/month
3. Total revenue by year
4. Monthly consignments
5. Top billing parties ranking
6. Most used routes
7. Monthly revenue breakdown
8. High-value parties (revenue threshold)
9. Hire charges analysis
10. Year-over-year comparison
11. Route profitability analysis
12. Pending payments tracking
13. Vehicle utilization report
14. Detention charges breakdown
15. Origin-destination analysis

### Key Metrics Supported
- ✅ Revenue (`Total Freight`)
- ✅ Profit (`LR Profit`)
- ✅ Weights (`Actual Weight`, `Charge Weight`)
- ✅ Charges (Detention, Hire, Other)
- ✅ Payments & Balance
- ✅ Consignment counts
- ✅ Route usage
- ✅ Vehicle utilization
- ✅ Delivery performance

## 🛠️ Important Notes

### Column Names with Spaces
Your table uses column names with spaces (e.g., `Billing Party`). The system automatically handles this by wrapping them in backticks:
```sql
SELECT `Billing Party`, `Total Freight` FROM lr_dump
```

### Date Fields
Primary date field: `CN Date`
Other dates: `Bill Date`, `Expected Date`, `Reach Date`, `Unload Date`, `POD Date`

### Financial Calculations
- **Total Revenue** = SUM(`Total Freight`)
- **Profit** = `LR Profit`
- **Balance** = `Total Freight` - `Payment Received`
- **Hire Charges** = Multiple HC columns

## 🎓 Tips for Better Results

1. **Be specific with dates**: "March 2022" or "2021-01-01 to 2021-12-31"
2. **Use exact party names**: System will find them in your database
3. **Specify year for trends**: "in 2022", "during 2021"
4. **Ask for top/bottom N**: "Top 5", "Bottom 10"
5. **Combine metrics**: "revenue and profit by route"

## ⚡ Quick Test

```bash
# Test with your actual data
python app_sql.py

💬 Your question: How many consignments in March 2021?
```

## 🔄 How It Learns

1. **First query**: "Revenue from billing party ABC in 2022"
   - Uses 15 built-in logistics examples
   
2. **System stores**: Successful query as embedding in Neo4j

3. **Future queries**: "Show ABC party revenue"
   - Finds similar past query
   - Generates better SQL faster
   - Improves over time

## 📊 Expected Table Structure

The system expects one main table: `lr_dump` with all consignment/LR data.

If you have multiple tables (e.g., separate `parties`, `vehicles`, `routes` tables), you can:
1. Update examples in `few_shot_examples_sql.py` with JOIN queries
2. System will adapt to your schema automatically

## 🎉 Ready to Use!

Your **Logistics SQL Pipeline** is configured for:
- ✅ Billing party revenue analysis
- ✅ Consignment tracking
- ✅ Route performance
- ✅ Profit analysis
- ✅ Payment tracking
- ✅ Vehicle utilization
- ✅ Detention/hire charges

Ask your business questions in natural language!
