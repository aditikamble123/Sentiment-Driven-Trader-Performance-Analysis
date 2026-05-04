# Trader Performance vs Market Sentiment

## Methodology

I cleaned and aligned the Bitcoin Fear & Greed index with Hyperliquid trade history at daily granularity. Trader performance is measured with realized `Closed PnL`, net PnL after fees, realized win rate on non-zero-PnL trades, PnL per trade, and a drawdown proxy based on negative daily PnL. Behavior is measured with trade count, average trade size, long/short ratio, and an exposure proxy derived from `abs(Start Position * Execution Price) / Size USD`. The raw trader file does not include a direct leverage field, so the exposure proxy is used only as a relative risk indicator.

## Data Quality

- Fear & Greed: 2,644 rows, 4 columns, no missing values or duplicates.
- Historical trades: 211,224 rows, 16 columns, no missing values or duplicates.
- Merged trade-level table: 211,224 rows. Daily sentiment coverage matched all trade dates in this dataset.

## Key Insights

1. Greed days generated the strongest total PnL: 4,865,300.58 gross PnL across 90,295 trades.
2. Fear days had a slightly higher realized win rate: 84.42% versus 82.45% on Greed days, but Greed still produced more aggregate PnL.
3. Average daily PnL was highest during Fear conditions at 39,012.05 per day.
4. Behavior shifts with sentiment: median long/short ratio was 1.38 on Fear days and 0.68 on Greed days.
5. The best segment by gross PnL was `Frequent traders / High exposure proxy / Consistent/top winners`, producing 5,323,999.35 gross PnL.
6. PnL is concentrated: the top 5 accounts contributed 6,360,279.33 gross PnL, so trader-level risk controls matter as much as aggregate sentiment.
7. Fear days had larger average trade size at trade level (7,182.01) than Greed days (4,574.42), suggesting traders sized up in stressed conditions.
8. Greed had the broadest sample coverage with 307 active sentiment days, while Fear had 105; this matters when comparing total versus per-day performance.
9. Frequent high-exposure winners were the strongest archetype, but their average win rate (80.59%) was lower than some lower-exposure winning groups, implying size and activity drove much of the PnL.

## Visual Evidence

![Average daily PnL by sentiment](outputs/charts/avg_daily_pnl_by_sentiment.png)

![Realized win rate by sentiment](outputs/charts/win_rate_by_sentiment.png)

![PnL per trade distribution](outputs/charts/pnl_per_trade_distribution.png)

![Behavior metrics by sentiment](outputs/charts/behavior_metrics_by_sentiment.png)

![Daily PnL over time](outputs/charts/daily_pnl_timeseries.png)

![Trader segment performance](outputs/charts/segment_performance.png)

![Account activity vs PnL](outputs/charts/account_activity_vs_pnl.png)

## Strategy Recommendations

1. Use sentiment-aware risk sizing: when the market is in Fear, reduce exposure for weaker or low-win-rate accounts and require stronger confirmation before increasing trade frequency.
2. Let proven high-activity winners trade through Greed regimes, but cap exposure proxy outliers because aggregate PnL is concentrated in a small number of accounts.
3. Monitor the long/short ratio alongside sentiment. A sharp directional bias during Fear should trigger stricter loss limits, while the lower long/short ratio observed during Greed appears more favorable in this sample.

## Deliverable Files

- `outputs/tables/sentiment_daily_summary.csv`
- `outputs/tables/sentiment_trade_summary.csv`
- `outputs/tables/account_segments.csv`
- `outputs/tables/segment_performance.csv`
- `outputs/charts/*.png`
