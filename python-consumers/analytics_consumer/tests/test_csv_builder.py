import pytest

from analytics_consumer.main import build_csv_from_events

def test_build_csv_from_events_customer_and_inventory():
    events = [
        {
            "type": "customer_update",
            "customer": {"id": "c1", "status": "active"},
            "inventory_summary": {"total_products": 2, "low_stock_count": 1},
        },
        {
            "type": "inventory_update",
            "product": {"product_id": "p1", "sku": "SKU-001", "qty": 5},
            "customer_summary": {"total_customers": 3},
        },
    ]

    csv_text = build_csv_from_events(events)
    lines = [ln for ln in csv_text.splitlines() if ln.strip()]

    # header + 2 data rows
    assert len(lines) == 3

    header = lines[0].split(",")
    assert header == [
        "type",
        "customer_id",
        "product_id",
        "status",
        "sku",
        "qty",
        "total_products",
        "low_stock_count",
        "total_customers",
    ]

    # customer row
    c = lines[1].split(",")
    assert c[0] == "customer_update"
    assert c[1] == "c1"
    assert c[3] == "active"
    assert c[6] == "2"
    assert c[7] == "1"

    # inventory row
    i = lines[2].split(",")
    assert i[0] == "inventory_update"
    assert i[2] == "p1"
    assert i[4] == "SKU-001"
    assert i[5] == "5"
    assert i[8] == "3"
