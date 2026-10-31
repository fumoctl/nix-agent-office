# Invoice Template — Document Structure

## Layout

```
+----------------------------------------------------------+
|  [LOGO]                                    INVOICE        |
|  Company Name                              #INV-XXXX      |
|  Street Address                            Date: XXXX     |
|  City, State ZIP                           Due: XXXX      |
|  Phone | Email                                            |
+----------------------------------------------------------+
|                                                           |
|  BILL TO:                      SHIP TO: (if applicable)   |
|  Client Name                   Delivery Address            |
|  Client Address                                           |
|  Client Email                                             |
|                                                           |
+------+--------------------------+-------+--------+--------+
| #    | Description              | Qty   | Rate   | Amount |
+------+--------------------------+-------+--------+--------+
| 1    | Service/Product A        | 10    | $50.00 | $500   |
| 2    | Service/Product B        | 5     | $75.00 | $375   |
| 3    | Service/Product C        | 1     | $200   | $200   |
+------+--------------------------+-------+--------+--------+
|                                         Subtotal | $1,075 |
|                                        Tax (10%) | $107.50|
|                                    Discount (5%) | -$53.75|
|                                     TOTAL DUE    |$1,128.75|
+----------------------------------------------------------+
|                                                           |
|  Payment Terms:                                           |
|  Bank: XXXX | Account: XXXX | Routing: XXXX              |
|  Or pay via: [PayPal/Stripe link]                         |
|                                                           |
|  Notes: Thank you for your business!                      |
+----------------------------------------------------------+
```

## Implementation Notes

1. Use invisible table for header layout (logo left, invoice details right)
2. Use Table Grid for line items
3. Right-align all number columns
4. Bold the TOTAL row, use larger font
5. Color scheme: header row navy (#1A365D), text white
6. Subtotal/tax/total section: right-aligned in last two columns, merge left columns
7. Add company logo if provided (width: 1.5 inches)
8. Footer: payment terms in smaller font, muted color
