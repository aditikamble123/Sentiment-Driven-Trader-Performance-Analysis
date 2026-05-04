# Sentiment-Driven Trader Performance Analysis

This project analyzes how Bitcoin market sentiment, measured through the Fear & Greed Index, relates to Hyperliquid trader behavior and performance. The goal is to identify patterns in profitability, trade sizing, win rate, activity, and directional bias across Fear, Neutral, and Greed market regimes.

## Objective

The analysis answers the assignment questions:

- Does trader performance differ between Fear and Greed days?
- Do traders change behavior based on sentiment?
- Which trader segments perform better or worse?
- What actionable trading rules can be derived from the findings?

## Datasets

The project uses two CSV files:

- `data/fear_greed_index.csv` - Bitcoin Fear & Greed sentiment data
- `data/historical_data.csv` - Hyperliquid historical trader data

Main trader fields used include account, coin, execution price, size, side, timestamp, direction, closed PnL, fee, and trade ID.

## Methodology

1. Loaded both datasets and checked rows, columns, missing values, and duplicate rows.
2. Converted timestamps and aligned both datasets at daily level.
3. Merged trader activity with daily sentiment labels.
4. Built daily and trader-level performance metrics:
   - Gross PnL and net PnL after fees
   - Realized win rate
   - PnL per trade
   - Average trade size
   - Number of trades
   - Long/short ratio
   - Drawdown proxy from negative daily PnL
5. Created trader segments:
   - Frequent vs infrequent traders
   - High vs low exposure proxy traders
   - Top winners, middle performers, and low/negative performers
6. Generated output tables, charts, and a final markdown report.

## Project Structure

```text
.
├── README.md
├── REPORT.md
├── Task Details.pdf
├── data/
│   ├── fear_greed_index.csv
│   └── historical_data.csv
├── src/
│   └── analysis.py
└── outputs/
    ├── charts/
    │   ├── account_activity_vs_pnl.png
    │   ├── avg_daily_pnl_by_sentiment.png
    │   ├── behavior_metrics_by_sentiment.png
    │   ├── daily_pnl_timeseries.png
    │   ├── pnl_per_trade_distribution.png
    │   ├── segment_performance.png
    │   └── win_rate_by_sentiment.png
    └── tables/
        ├── account_day_metrics.csv
        ├── account_segments.csv
        ├── account_sentiment_summary.csv
        ├── daily_metrics.csv
        ├── data_quality_summary.csv
        ├── segment_performance.csv
        ├── sentiment_daily_summary.csv
        ├── sentiment_trade_summary.csv
        └── top_accounts.csv
```

## How to Run

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install pandas numpy matplotlib seaborn
```

Run the analysis:

```bash
python src/analysis.py
```

The script regenerates all charts, tables, the merged analysis output, and `REPORT.md`.

## Outputs

### Final Report

- `REPORT.md` contains the methodology, data-quality summary, key insights, embedded chart references, and strategy recommendations.

### Charts

The generated plots are stored in `outputs/charts/`:

- `avg_daily_pnl_by_sentiment.png` - compares average daily PnL across Fear, Neutral, and Greed days.
- `win_rate_by_sentiment.png` - compares realized win rate by sentiment regime.
- `pnl_per_trade_distribution.png` - shows how daily PnL per trade differs by sentiment.
- `behavior_metrics_by_sentiment.png` - compares trade count, trade size, long/short ratio, and exposure proxy.
- `daily_pnl_timeseries.png` - shows daily PnL movement over time with sentiment labels.
- `segment_performance.png` - compares PnL across trader behavior segments.
- `account_activity_vs_pnl.png` - visualizes account-level activity versus PnL.

### Tables

The generated CSV summaries are stored in `outputs/tables/`:

- `data_quality_summary.csv` - rows, columns, missing values, and duplicates.
- `sentiment_daily_summary.csv` - daily performance aggregated by sentiment.
- `sentiment_trade_summary.csv` - trade-level performance aggregated by sentiment.
- `daily_metrics.csv` - date-level metrics after sentiment alignment.
- `account_day_metrics.csv` - account-date level performance metrics.
- `account_segments.csv` - trader segmentation output.
- `segment_performance.csv` - performance by trader segment.
- `account_sentiment_summary.csv` - account performance split by sentiment.
- `top_accounts.csv` - highest-PnL trader accounts.

## Key Findings

- Greed days produced the highest total gross PnL.
- Fear days had a slightly higher realized win rate, but Greed still generated more aggregate PnL.
- Average daily PnL was highest during Fear conditions in this sample.
- Long/short behavior changed meaningfully by sentiment.
- Frequent high-exposure top winners were the strongest-performing trader segment.
- PnL was concentrated among a small number of accounts, making account-level risk controls important.

## Strategy Recommendations

- Apply sentiment-aware risk sizing, especially during Fear periods.
- Allow proven high-activity winners to trade more actively during favorable regimes, but cap exposure outliers.
- Monitor long/short ratio shifts together with sentiment to identify when stricter loss limits are needed.

## Important Note on Leverage

The historical trader dataset does not include a direct leverage column. To support the requested leverage-style analysis, this project uses a relative exposure proxy:

```text
abs(Start Position * Execution Price) / Size USD
```

This is used only as a behavioral risk indicator and should not be interpreted as true exchange leverage.

## Submission Contents

For GitHub submission, include:

- `README.md`
- `REPORT.md`
- `src/analysis.py`
- `data/`
- `outputs/charts/`
- `outputs/tables/`
- `Task Details.pdf` if required by the reviewer
