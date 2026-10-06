TASKS = {

"Task 1 — Stock Overview": """
SELECT 'Bajaj Auto' AS stock, COUNT(*) AS rows, MIN(date) AS start_date, MAX(date) AS end_date
FROM bajaj_auto
UNION ALL
SELECT 'Eicher Motors', COUNT(*), MIN(date), MAX(date)
FROM eicher_motors
UNION ALL
SELECT 'Hero Motocorp', COUNT(*), MIN(date), MAX(date)
FROM hero_motocorp
UNION ALL
SELECT 'Infosys', COUNT(*), MIN(date), MAX(date)
FROM infosys
UNION ALL
SELECT 'TCS', COUNT(*), MIN(date), MAX(date)
FROM tcs
UNION ALL
SELECT 'TVS Motors', COUNT(*), MIN(date), MAX(date)
FROM tvs_motors;
""",

"Task 2 — Eicher Top 5 Closing Prices": """
SELECT
    date(date) AS date,
    close_price
FROM eicher_motors
ORDER BY close_price DESC
LIMIT 5;
""",

"Task 3 — TCS Yearly Average Close": """
SELECT
    strftime('%Y', date) AS year,
    ROUND(AVG(close_price), 2) AS average_close
FROM tcs
GROUP BY strftime('%Y', date)
ORDER BY year;
""",

"Task 4 — NULL Deliverable Quantity": """
SELECT
    'Bajaj Auto' AS stock,
    COUNT(*) AS null_count
FROM bajaj_auto
WHERE deliverable_quantity IS NULL

UNION ALL

SELECT
    'Eicher Motors',
    COUNT(*)
FROM eicher_motors
WHERE deliverable_quantity IS NULL

UNION ALL

SELECT
    'Hero Motocorp',
    COUNT(*)
FROM hero_motocorp
WHERE deliverable_quantity IS NULL

UNION ALL

SELECT
    'Infosys',
    COUNT(*)
FROM infosys
WHERE deliverable_quantity IS NULL

UNION ALL

SELECT
    'TCS',
    COUNT(*)
FROM tcs
WHERE deliverable_quantity IS NULL

UNION ALL

SELECT
    'TVS Motors',
    COUNT(*)
FROM tvs_motors
WHERE deliverable_quantity IS NULL;
""",

"Task 5 — 20/50 Day Moving Averages": """
WITH moving_average AS (
    SELECT
        date,
        close_price,

        AVG(close_price) OVER (
            ORDER BY date
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) AS ma20,

        AVG(close_price) OVER (
            ORDER BY date
            ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
        ) AS ma50

    FROM bajaj_auto
)

SELECT
    date(date) AS date,
    ROUND(close_price, 2) AS close_price,
    ROUND(ma20, 2) AS ma20,
    ROUND(ma50, 2) AS ma50
FROM moving_average
ORDER BY date;
""",

"Task 6 — Master Table": """
SELECT
    date(b.date) AS date,
    b.close_price AS bajaj_close,
    e.close_price AS eicher_close,
    h.close_price AS hero_close,
    i.close_price AS infosys_close,
    t.close_price AS tcs_close,
    v.close_price AS tvs_close

FROM bajaj_auto b

INNER JOIN eicher_motors e
    ON date(b.date) = date(e.date)

INNER JOIN hero_motocorp h
    ON date(b.date) = date(h.date)

INNER JOIN infosys i
    ON date(b.date) = date(i.date)

INNER JOIN tcs t
    ON date(b.date) = date(t.date)

INNER JOIN tvs_motors v
    ON date(b.date) = date(v.date)

ORDER BY date;
""",

"Task 7 — Buy/Sell/Hold Signals": """
WITH moving_average AS (
    SELECT
        date,
        close_price,

        AVG(close_price) OVER (
            ORDER BY date
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) AS ma20,

        AVG(close_price) OVER (
            ORDER BY date
            ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
        ) AS ma50

    FROM bajaj_auto
),

previous_values AS (
    SELECT
        date,
        close_price,
        ma20,
        ma50,

        LAG(ma20) OVER (
            ORDER BY date
        ) AS previous_ma20,

        LAG(ma50) OVER (
            ORDER BY date
        ) AS previous_ma50

    FROM moving_average
)

SELECT
    date(date) AS date,
    ROUND(close_price, 2) AS close_price,
    ROUND(ma20, 2) AS ma20,
    ROUND(ma50, 2) AS ma50,

    CASE
        WHEN previous_ma20 <= previous_ma50
             AND ma20 > ma50
            THEN 'Buy'

        WHEN previous_ma20 >= previous_ma50
             AND ma20 < ma50
            THEN 'Sell'

        ELSE 'Hold'
    END AS signal

FROM previous_values

WHERE ma20 IS NOT NULL
AND ma50 IS NOT NULL

ORDER BY date;
""",

"Task 8 — Signal Counts": """
WITH moving_average AS (
    SELECT
        date,

        AVG(close_price) OVER (
            ORDER BY date
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) AS ma20,

        AVG(close_price) OVER (
            ORDER BY date
            ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
        ) AS ma50

    FROM bajaj_auto
),

signals AS (
    SELECT
        date,
        ma20,
        ma50,

        LAG(ma20) OVER (
            ORDER BY date
        ) AS previous_ma20,

        LAG(ma50) OVER (
            ORDER BY date
        ) AS previous_ma50

    FROM moving_average
),

classified AS (
    SELECT
        CASE
            WHEN previous_ma20 <= previous_ma50
                 AND ma20 > ma50
                THEN 'Buy'

            WHEN previous_ma20 >= previous_ma50
                 AND ma20 < ma50
                THEN 'Sell'

            ELSE 'Hold'
        END AS signal

    FROM signals

    WHERE ma20 IS NOT NULL
    AND ma50 IS NOT NULL
)

SELECT
    signal,
    COUNT(*) AS signal_count
FROM classified
GROUP BY signal
ORDER BY signal;
""",

"Task 9 — Signal on 2018-06-21": """
WITH moving_average AS (
    SELECT
        date,
        ma20,
        ma50,

        LAG(ma20) OVER (
            ORDER BY date
        ) AS previous_ma20,

        LAG(ma50) OVER (
            ORDER BY date
        ) AS previous_ma50

    FROM (
        SELECT
            date,

            AVG(close_price) OVER (
                ORDER BY date
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) AS ma20,

            AVG(close_price) OVER (
                ORDER BY date
                ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
            ) AS ma50

        FROM bajaj_auto
    )
)

SELECT
    date(date) AS date,
    ROUND(ma20, 2) AS ma20,
    ROUND(ma50, 2) AS ma50,

    CASE
        WHEN previous_ma20 <= previous_ma50
             AND ma20 > ma50
            THEN 'Buy'

        WHEN previous_ma20 >= previous_ma50
             AND ma20 < ma50
            THEN 'Sell'

        ELSE 'Hold'
    END AS signal

FROM moving_average

WHERE date(date) = '2018-06-21';
""",

"Task 10 — Signals Across All Stocks": """
WITH all_stocks AS (

    SELECT 'Bajaj Auto' AS stock, date, close_price
    FROM bajaj_auto

    UNION ALL

    SELECT 'Eicher Motors', date, close_price
    FROM eicher_motors

    UNION ALL

    SELECT 'Hero Motocorp', date, close_price
    FROM hero_motocorp

    UNION ALL

    SELECT 'Infosys', date, close_price
    FROM infosys

    UNION ALL

    SELECT 'TCS', date, close_price
    FROM tcs

    UNION ALL

    SELECT 'TVS Motors', date, close_price
    FROM tvs_motors
),

moving_average AS (

    SELECT
        stock,
        date,

        AVG(close_price) OVER (
            PARTITION BY stock
            ORDER BY date
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) AS ma20,

        AVG(close_price) OVER (
            PARTITION BY stock
            ORDER BY date
            ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
        ) AS ma50

    FROM all_stocks
),

signals AS (

    SELECT
        stock,
        date,
        ma20,
        ma50,

        LAG(ma20) OVER (
            PARTITION BY stock
            ORDER BY date
        ) AS previous_ma20,

        LAG(ma50) OVER (
            PARTITION BY stock
            ORDER BY date
        ) AS previous_ma50

    FROM moving_average
)

SELECT
    stock,

    SUM(
        CASE
            WHEN previous_ma20 <= previous_ma50
                 AND ma20 > ma50
            THEN 1
            ELSE 0
        END
    ) AS buy_signals,

    SUM(
        CASE
            WHEN previous_ma20 >= previous_ma50
                 AND ma20 < ma50
            THEN 1
            ELSE 0
        END
    ) AS sell_signals

FROM signals

WHERE ma20 IS NOT NULL
AND ma50 IS NOT NULL

GROUP BY stock
ORDER BY stock;
""",

"Task 11 — First-to-Last Return": """
WITH stock_returns AS (

    SELECT
        'Bajaj Auto' AS stock,
        (SELECT close_price FROM bajaj_auto ORDER BY date LIMIT 1) AS first_price,
        (SELECT close_price FROM bajaj_auto ORDER BY date DESC LIMIT 1) AS last_price

    UNION ALL

    SELECT
        'Eicher Motors',
        (SELECT close_price FROM eicher_motors ORDER BY date LIMIT 1),
        (SELECT close_price FROM eicher_motors ORDER BY date DESC LIMIT 1)

    UNION ALL

    SELECT
        'Hero Motocorp',
        (SELECT close_price FROM hero_motocorp ORDER BY date LIMIT 1),
        (SELECT close_price FROM hero_motocorp ORDER BY date DESC LIMIT 1)

    UNION ALL

    SELECT
        'Infosys',
        (SELECT close_price FROM infosys ORDER BY date LIMIT 1),
        (SELECT close_price FROM infosys ORDER BY date DESC LIMIT 1)

    UNION ALL

    SELECT
        'TCS',
        (SELECT close_price FROM tcs ORDER BY date LIMIT 1),
        (SELECT close_price FROM tcs ORDER BY date DESC LIMIT 1)

    UNION ALL

    SELECT
        'TVS Motors',
        (SELECT close_price FROM tvs_motors ORDER BY date LIMIT 1),
        (SELECT close_price FROM tvs_motors ORDER BY date DESC LIMIT 1)
)

SELECT
    stock,
    ROUND(first_price, 2) AS first_price,
    ROUND(last_price, 2) AS last_price,
    ROUND(
        ((last_price - first_price) / first_price) * 100,
        2
    ) AS return_pct

FROM stock_returns

ORDER BY return_pct DESC;
""",

"Task 12 — Worst Daily Drops": """
WITH all_daily_data AS (

    SELECT
        'Bajaj Auto' AS stock,
        date,
        close_price
    FROM bajaj_auto

    UNION ALL

    SELECT
        'Eicher Motors',
        date,
        close_price
    FROM eicher_motors

    UNION ALL

    SELECT
        'Hero Motocorp',
        date,
        close_price
    FROM hero_motocorp

    UNION ALL

    SELECT
        'Infosys',
        date,
        close_price
    FROM infosys

    UNION ALL

    SELECT
        'TCS',
        date,
        close_price
    FROM tcs

    UNION ALL

    SELECT
        'TVS Motors',
        date,
        close_price
    FROM tvs_motors
),

daily_returns AS (

    SELECT
        stock,
        date,
        close_price,

        LAG(close_price) OVER (
            PARTITION BY stock
            ORDER BY date
        ) AS previous_close

    FROM all_daily_data
)

SELECT
    stock,
    date(date) AS date,

    ROUND(
        ((close_price - previous_close) / previous_close) * 100,
        2
    ) AS daily_change_pct

FROM daily_returns

WHERE previous_close IS NOT NULL

ORDER BY daily_change_pct ASC

LIMIT 10;
""",

"Task 13 — Corporate Action Analysis": """
WITH all_prices AS (

    SELECT
        'TCS' AS stock,
        date,
        close_price
    FROM tcs

    UNION ALL

    SELECT
        'Infosys' AS stock,
        date,
        close_price
    FROM infosys
),

daily_changes AS (

    SELECT
        stock,
        date,
        close_price,

        LAG(close_price) OVER (
            PARTITION BY stock
            ORDER BY date
        ) AS previous_close

    FROM all_prices
),

corporate_events AS (

    SELECT
        stock,
        MIN(date) AS event_date

    FROM daily_changes

    WHERE previous_close IS NOT NULL

    AND (
        ((close_price - previous_close) / previous_close) <= -0.40
    )

    GROUP BY stock
),

adjusted_prices AS (

    SELECT
        p.stock,
        p.date,
        p.close_price,

        CASE
            WHEN p.date < e.event_date
                THEN p.close_price / 2.0
            ELSE p.close_price
        END AS adjusted_close

    FROM all_prices p

    INNER JOIN corporate_events e
        ON p.stock = e.stock
)

SELECT
    stock,
    MIN(date(date)) AS start_date,
    MAX(date(date)) AS end_date,

    ROUND(
        MIN(CASE
            WHEN date = (
                SELECT MIN(ap2.date)
                FROM adjusted_prices ap2
                WHERE ap2.stock = adjusted_prices.stock
            )
            THEN adjusted_close
        END),
        2
    ) AS adjusted_first_price,

    ROUND(
        MAX(CASE
            WHEN date = (
                SELECT MAX(ap3.date)
                FROM adjusted_prices ap3
                WHERE ap3.stock = adjusted_prices.stock
            )
            THEN adjusted_close
        END),
        2
    ) AS adjusted_last_price,

    ROUND(
        (
            (
                MAX(CASE
                    WHEN date = (
                        SELECT MAX(ap4.date)
                        FROM adjusted_prices ap4
                        WHERE ap4.stock = adjusted_prices.stock
                    )
                    THEN adjusted_close
                END)
                -
                MIN(CASE
                    WHEN date = (
                        SELECT MIN(ap5.date)
                        FROM adjusted_prices ap5
                        WHERE ap5.stock = adjusted_prices.stock
                    )
                    THEN adjusted_close
                END)
            )
            /
            MIN(CASE
                WHEN date = (
                    SELECT MIN(ap6.date)
                    FROM adjusted_prices ap6
                    WHERE ap6.stock = adjusted_prices.stock
                )
                THEN adjusted_close
            END)
        ) * 100,
        2
    ) AS adjusted_return_pct

FROM adjusted_prices

GROUP BY stock

ORDER BY adjusted_return_pct DESC;
"""

}