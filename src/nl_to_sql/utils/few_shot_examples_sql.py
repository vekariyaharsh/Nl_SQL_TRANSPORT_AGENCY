"""
Few-shot examples for Natural Language to SQL query generation
Logistics & Transport Management System
"""
from typing import List, Dict


class LogisticsSQLExamples:
    """Repository of SQL examples for logistics/transport business analytics"""
    
    # Logistics Business Analytics Examples
    LOGISTICS_EXAMPLES = [
        {
            "question": "What was the revenue from billing party XYZ from Jan 2021 to Dec 2021?",
            "sql": """SELECT 
    billing_party,
    SUM(total_freight) as total_revenue,
    COUNT(cn_no) as total_consignments,
    AVG(total_freight) as avg_freight,
    SUM(actual_weight) as total_weight
FROM reg_dump
WHERE billing_party = 'XYZ'
  AND cn_date BETWEEN '2021-01-01' AND '2021-12-31'
GROUP BY billing_party""",
            "explanation": "Calculate total revenue for specific billing party within date range"
        },
        {
            "question": "How many consignments for ABC billing party in March 2022?",
            "sql": """SELECT 
    billing_party,
    COUNT(cn_no) as consignment_count,
    SUM(total_freight) as total_freight,
    SUM(actual_weight) as total_weight,
    COUNT(DISTINCT vehicle_no) as vehicles_used
FROM reg_dump
WHERE billing_party = 'ABC'
  AND cn_date LIKE '2022-03%'
GROUP BY billing_party""",
            "explanation": "Count consignments for specific billing party in given month and year using LIKE for text dates"
        },
        {
            "question": "Total revenue for 2021",
            "sql": """SELECT 
    '2021' as year,
    SUM(total_freight) as total_revenue,
    COUNT(cn_no) as total_consignments,
    AVG(total_freight) as average_freight,
    SUM(actual_weight) as total_weight
FROM reg_dump
WHERE cn_date LIKE '2021%'""",
            "explanation": "Calculate total revenue for entire year using LIKE for text date filtering"
        },
        {
            "question": "How many consignments in March 2021?",
            "sql": """SELECT 
    COUNT(cn_no) as consignment_count,
    SUM(total_freight) as total_revenue,
    AVG(total_freight) as average_freight,
    SUM(actual_weight) as total_weight,
    COUNT(DISTINCT billing_party) as unique_billing_parties
FROM reg_dump
WHERE cn_date LIKE '2021-03%'""",
            "explanation": "Count consignments in specific month with freight metrics"
        },
        {
            "question": "Top 5 billing parties based on revenue in 2022",
            "sql": """SELECT 
    billing_party,
    SUM(total_freight) as total_revenue,
    COUNT(cn_no) as consignment_count,
    AVG(total_freight) as avg_freight_per_consignment,
    SUM(actual_weight) as total_weight
FROM reg_dump
WHERE cn_date LIKE '2022%'
GROUP BY billing_party
ORDER BY total_revenue DESC
LIMIT 5""",
            "explanation": "Find top billing parties by revenue with rankings"
        },
        {
            "question": "Most used route in 2022",
            "sql": """SELECT 
    route,
    COUNT(cn_no) as usage_count,
    COUNT(DISTINCT billing_party) as unique_customers,
    SUM(total_freight) as total_revenue,
    SUM(actual_weight) as total_weight
FROM reg_dump
WHERE cn_date LIKE '2022%'
GROUP BY route
ORDER BY usage_count DESC
LIMIT 1""",
            "explanation": "Find most frequently used route by consignment count"
        },
        {
            "question": "Show billing party revenue breakdown by month for 2023",
            "sql": """SELECT 
    billing_party,
    SUBSTRING(cn_date, 1, 7) as year_month,
    SUM(total_freight) as monthly_revenue,
    COUNT(cn_no) as consignment_count,
    SUM(actual_weight) as total_weight
FROM reg_dump
WHERE cn_date LIKE '2023%'
GROUP BY billing_party, SUBSTRING(cn_date, 1, 7)
ORDER BY billing_party, year_month""",
            "explanation": "Monthly revenue breakdown using SUBSTRING for text dates"
        },
        {
            "question": "Find billing parties with revenue over 100000 in 2022",
            "sql": """SELECT 
    billing_party,
    SUM(total_freight) as total_revenue,
    COUNT(cn_no) as total_consignments,
    AVG(total_freight) as avg_freight
FROM reg_dump
WHERE cn_date LIKE '2022%'
GROUP BY billing_party
HAVING SUM(total_freight) > 100000
ORDER BY total_revenue DESC""",
            "explanation": "Filter billing parties by revenue threshold using HAVING clause"
        },
        {
            "question": "Average hire charges per consignment in Q1 2023",
            "sql": """SELECT 
    billing_party,
    COUNT(cn_no) as consignment_count,
    SUM(hire_charges) as total_hire_charges,
    AVG(hire_charges) as avg_hire_charges,
    SUM(total_freight) as total_revenue
FROM reg_dump
WHERE cn_date BETWEEN '2023-01-01' AND '2023-03-31'
GROUP BY billing_party
ORDER BY avg_hire_charges DESC""",
            "explanation": "Calculate average hire charges for a quarter"
        },
        {
            "question": "Compare revenue year over year (2021 vs 2022)",
            "sql": """SELECT 
    SUBSTRING(cn_date, 1, 4) as year,
    SUM(total_freight) as total_revenue,
    COUNT(cn_no) as consignment_count,
    AVG(total_freight) as avg_freight,
    SUM(actual_weight) as total_weight
FROM reg_dump
WHERE cn_date LIKE '2021%' OR cn_date LIKE '2022%'
GROUP BY SUBSTRING(cn_date, 1, 4)
ORDER BY year""",
            "explanation": "Year-over-year revenue comparison using SUBSTRING for text dates"
        },
        {
            "question": "Profit analysis by route in 2022",
            "sql": """SELECT 
    route,
    COUNT(cn_no) as consignment_count,
    SUM(total_freight) as total_revenue,
    SUM(hire_charges) as total_hire_charges,
    SUM(lr_profit) as total_profit,
    AVG(lr_profit) as avg_profit_per_consignment
FROM reg_dump
WHERE cn_date LIKE '2022%'
GROUP BY route
ORDER BY total_profit DESC""",
            "explanation": "Analyze profitability by route"
        },
        {
            "question": "Pending payments by billing party",
            "sql": """SELECT 
    billing_party,
    COUNT(cn_no) as consignment_count,
    SUM(total_freight) as total_billed,
    SUM(payment_received) as total_received,
    SUM(balance) as pending_amount,
    ROUND((SUM(balance) / SUM(total_freight)) * 100, 2) as pending_percentage
FROM reg_dump
WHERE balance > 0
GROUP BY billing_party
ORDER BY pending_amount DESC""",
            "explanation": "Track outstanding payments from billing parties"
        },
        {
            "question": "Vehicle utilization report for 2022",
            "sql": """SELECT 
    vehicle_no,
    vehicle_type,
    COUNT(cn_no) as trips_count,
    SUM(actual_weight) as total_weight_carried,
    SUM(total_freight) as total_revenue,
    AVG(actual_weight) as avg_weight_per_trip
FROM reg_dump
WHERE cn_date LIKE '2022%'
  AND vehicle_no IS NOT NULL
  AND vehicle_no != ''
GROUP BY vehicle_no, vehicle_type
ORDER BY trips_count DESC""",
            "explanation": "Analyze vehicle usage and revenue generation"
        },
        {
            "question": "Detention charges breakdown by billing party",
            "sql": """SELECT 
    billing_party,
    COUNT(cn_no) as consignments_with_detention,
    SUM(detention) as total_detention_charges,
    AVG(detention) as avg_detention_per_consignment,
    SUM(total_freight) as total_revenue
FROM reg_dump
WHERE detention > 0
  AND cn_date LIKE '2022%'
GROUP BY billing_party
ORDER BY total_detention_charges DESC""",
            "explanation": "Analyze detention charges billed to customers"
        },
        {
            "question": "Origin to destination route analysis",
            "sql": """SELECT 
    origin,
    destination,
    COUNT(cn_no) as consignment_count,
    SUM(total_freight) as total_revenue,
    AVG(actual_weight) as avg_weight
FROM reg_dump
WHERE origin IS NOT NULL 
  AND destination IS NOT NULL
  AND cn_date LIKE '2022%'
GROUP BY origin, destination
ORDER BY consignment_count DESC
LIMIT 10""",
            "explanation": "Top routes with performance metrics"
        }
    ]
    
    @classmethod
    def get_all_examples(cls) -> List[Dict[str, str]]:
        """Get all logistics SQL examples"""
        return cls.LOGISTICS_EXAMPLES
    
    @classmethod
    def get_examples_as_text(cls, max_examples: int = 10) -> str:
        """
        Format examples as text for LLM prompt
        
        Args:
            max_examples: Maximum number of examples to include
        
        Returns:
            Formatted examples string
        """
        examples = cls.LOGISTICS_EXAMPLES[:max_examples]
        
        lines = []
        for i, example in enumerate(examples, 1):
            lines.append(f"Example {i}:")
            lines.append(f"Question: {example['question']}")
            lines.append(f"SQL Query:\n{example['sql']}")
            lines.append(f"Explanation: {example['explanation']}")
            lines.append("")
        
        return "\n".join(lines)
    
    @classmethod
    def add_custom_example(
        cls, 
        question: str, 
        sql: str, 
        explanation: str
    ):
        """Add a custom example"""
        cls.LOGISTICS_EXAMPLES.append({
            "question": question,
            "sql": sql,
            "explanation": explanation
        })
    
    @classmethod
    def get_example_count(cls) -> int:
        """Get total number of examples"""
        return len(cls.LOGISTICS_EXAMPLES)


# For backward compatibility
SQLFewShotExamples = LogisticsSQLExamples


if __name__ == "__main__":
    # Test logistics SQL examples
    print("Testing Logistics SQL Examples...")
    
    print(f"\nTotal examples: {LogisticsSQLExamples.get_example_count()}")
    
    print("\n" + "="*80)
    print("LOGISTICS & TRANSPORT EXAMPLES")
    print("="*80)
    print(LogisticsSQLExamples.get_examples_as_text(max_examples=3))
    print("="*80)
