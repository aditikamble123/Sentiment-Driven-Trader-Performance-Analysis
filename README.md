# Trader Performance vs Market Sentiment

This project analyzes how Bitcoin market sentiment, measured by the Fear & Greed Index, relates to Hyperliquid trader behavior and performance.

## Project Structure

- `src/analysis.py` - reproducible analysis pipeline
- `data/` - input CSVs
- `outputs/tables/` - generated CSV summaries
- `outputs/charts/` - generated visualizations
- `REPORT.md` - one-page findings and strategy recommendations

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas numpy matplotlib seaborn
```

The input files expected by the script are:

- `data/fear_greed_index.csv`
- `data/historical_data.csv`

## Run

```bash
python src/analysis.py
```

The script writes cleaned/merged data, summary tables, charts, and the final markdown report into `outputs/` and `REPORT.md`.

## Notes

The historical trader data does not include a direct leverage column. For the requested leverage-style analysis, this project uses a relative exposure proxy:

```text
abs(Start Position * Execution Price) / Size USD
```

This should be interpreted as a behavioral risk proxy, not true exchange leverage.
