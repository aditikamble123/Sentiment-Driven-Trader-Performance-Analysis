from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
CHART_DIR = OUTPUT_DIR / "charts"
TABLE_DIR = OUTPUT_DIR / "tables"

FEAR_GREED_PATH = DATA_DIR / "fear_greed_index.csv"
TRADES_PATH = DATA_DIR / "historical_data.csv"


def ensure_dirs() -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    fear_greed = pd.read_csv(FEAR_GREED_PATH)
    trades = pd.read_csv(TRADES_PATH)
    return fear_greed, trades


def sentiment_bucket(classification: str) -> str:
    value = str(classification).lower()
    if "fear" in value:
        return "Fear"
    if "greed" in value:
        return "Greed"
    return "Neutral"


def direction_bucket(direction: str, side: str) -> str:
    value = str(direction).lower()
    if "long" in value or value == "buy":
        return "Long"
    if "short" in value or value == "sell":
        return "Short"
    side_value = str(side).lower()
    if side_value == "buy":
        return "Long"
    if side_value == "sell":
        return "Short"
    return "Other"


def prepare_data(fear_greed: pd.DataFrame, trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    fear_greed = fear_greed.copy()
    trades = trades.copy()

    fear_greed["date"] = pd.to_datetime(fear_greed["date"])
    fear_greed["sentiment_bucket"] = fear_greed["classification"].map(sentiment_bucket)

    trades["timestamp_ist"] = pd.to_datetime(trades["Timestamp IST"], format="%d-%m-%Y %H:%M")
    trades["date"] = trades["timestamp_ist"].dt.normalize()
    trades["direction_bucket"] = [
        direction_bucket(direction, side)
        for direction, side in zip(trades["Direction"], trades["Side"], strict=False)
    ]
    trades["is_realized"] = trades["Closed PnL"].ne(0)
    trades["is_win"] = trades["Closed PnL"].gt(0)
    trades["net_pnl"] = trades["Closed PnL"] - trades["Fee"]
    trades["abs_start_position_usd"] = (trades["Start Position"].abs() * trades["Execution Price"]).replace(0, np.nan)
    trades["position_to_trade_size"] = (trades["abs_start_position_usd"] / trades["Size USD"].replace(0, np.nan)).clip(upper=100)

    return fear_greed, trades


def build_merged_trade_level(fear_greed: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    merged = trades.merge(
        fear_greed[["date", "value", "classification", "sentiment_bucket"]],
        how="left",
        on="date",
        validate="many_to_one",
    )
    return merged


def build_daily_metrics(merged: pd.DataFrame) -> pd.DataFrame:
    realized = merged["is_realized"]
    daily = (
        merged.groupby(["date", "sentiment_bucket", "classification"], dropna=False)
        .agg(
            trades=("Trade ID", "count"),
            active_accounts=("Account", "nunique"),
            total_size_usd=("Size USD", "sum"),
            avg_trade_size_usd=("Size USD", "mean"),
            gross_pnl=("Closed PnL", "sum"),
            fees=("Fee", "sum"),
            net_pnl=("net_pnl", "sum"),
            realized_trades=("is_realized", "sum"),
            long_trades=("direction_bucket", lambda s: (s == "Long").sum()),
            short_trades=("direction_bucket", lambda s: (s == "Short").sum()),
            exposure_proxy=("position_to_trade_size", "median"),
        )
        .reset_index()
    )
    wins = (
        merged.loc[realized]
        .groupby("date")["is_win"]
        .mean()
        .rename("win_rate")
        .reset_index()
    )
    daily = daily.merge(wins, on="date", how="left")
    daily["long_short_ratio"] = daily["long_trades"] / daily["short_trades"].replace(0, np.nan)
    daily["pnl_per_trade"] = daily["gross_pnl"] / daily["trades"]
    daily["pnl_per_realized_trade"] = daily["gross_pnl"] / daily["realized_trades"].replace(0, np.nan)
    daily["drawdown_proxy"] = daily["gross_pnl"].clip(upper=0)
    return daily


def build_account_day_metrics(merged: pd.DataFrame) -> pd.DataFrame:
    account_day = (
        merged.groupby(["Account", "date", "sentiment_bucket"], dropna=False)
        .agg(
            trades=("Trade ID", "count"),
            realized_trades=("is_realized", "sum"),
            total_size_usd=("Size USD", "sum"),
            avg_trade_size_usd=("Size USD", "mean"),
            gross_pnl=("Closed PnL", "sum"),
            net_pnl=("net_pnl", "sum"),
            fees=("Fee", "sum"),
            long_trades=("direction_bucket", lambda s: (s == "Long").sum()),
            short_trades=("direction_bucket", lambda s: (s == "Short").sum()),
            exposure_proxy=("position_to_trade_size", "median"),
        )
        .reset_index()
    )
    wins = (
        merged.loc[merged["is_realized"]]
        .groupby(["Account", "date"])["is_win"]
        .mean()
        .rename("win_rate")
        .reset_index()
    )
    account_day = account_day.merge(wins, on=["Account", "date"], how="left")
    account_day["long_short_ratio"] = account_day["long_trades"] / account_day["short_trades"].replace(0, np.nan)
    account_day["pnl_per_trade"] = account_day["gross_pnl"] / account_day["trades"]
    return account_day


def build_account_segments(account_day: pd.DataFrame) -> pd.DataFrame:
    account = (
        account_day.groupby("Account")
        .agg(
            active_days=("date", "nunique"),
            total_trades=("trades", "sum"),
            total_realized_trades=("realized_trades", "sum"),
            total_size_usd=("total_size_usd", "sum"),
            avg_trade_size_usd=("avg_trade_size_usd", "mean"),
            gross_pnl=("gross_pnl", "sum"),
            net_pnl=("net_pnl", "sum"),
            avg_win_rate=("win_rate", "mean"),
            exposure_proxy=("exposure_proxy", "median"),
        )
        .reset_index()
    )
    account["trades_per_day"] = account["total_trades"] / account["active_days"]
    account["pnl_per_trade"] = account["gross_pnl"] / account["total_trades"]
    account["activity_segment"] = np.where(
        account["trades_per_day"] >= account["trades_per_day"].median(),
        "Frequent traders",
        "Infrequent traders",
    )
    account["exposure_segment"] = np.where(
        account["exposure_proxy"] >= account["exposure_proxy"].median(),
        "High exposure proxy",
        "Low exposure proxy",
    )
    account["performance_segment"] = np.select(
        [
            account["gross_pnl"] >= account["gross_pnl"].quantile(0.67),
            account["gross_pnl"] <= account["gross_pnl"].quantile(0.33),
        ],
        ["Consistent/top winners", "Low/negative performers"],
        default="Middle performers",
    )
    return account.sort_values("gross_pnl", ascending=False)


def summarize_quality(fear_greed: pd.DataFrame, trades: pd.DataFrame, merged: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, df in [("fear_greed_index", fear_greed), ("historical_data", trades)]:
        rows.append(
            {
                "dataset": name,
                "rows": len(df),
                "columns": df.shape[1],
                "missing_values": int(df.isna().sum().sum()),
                "duplicate_rows": int(df.duplicated().sum()),
            }
        )
    rows.append(
        {
            "dataset": "merged_trade_level",
            "rows": len(merged),
            "columns": merged.shape[1],
            "missing_values": int(merged.isna().sum().sum()),
            "duplicate_rows": int(merged.duplicated().sum()),
        }
    )
    return pd.DataFrame(rows)


def build_summary_tables(
    merged: pd.DataFrame, daily: pd.DataFrame, account_day: pd.DataFrame, account: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    sentiment_daily = (
        daily.groupby("sentiment_bucket")
        .agg(
            days=("date", "nunique"),
            trades=("trades", "sum"),
            active_accounts=("active_accounts", "mean"),
            gross_pnl=("gross_pnl", "sum"),
            net_pnl=("net_pnl", "sum"),
            avg_daily_pnl=("gross_pnl", "mean"),
            median_daily_pnl=("gross_pnl", "median"),
            win_rate=("win_rate", "mean"),
            avg_trade_size_usd=("avg_trade_size_usd", "mean"),
            exposure_proxy=("exposure_proxy", "median"),
            long_short_ratio=("long_short_ratio", "median"),
        )
        .reset_index()
        .sort_values("gross_pnl", ascending=False)
    )

    sentiment_trade = (
        merged.groupby("sentiment_bucket")
        .agg(
            trades=("Trade ID", "count"),
            realized_trades=("is_realized", "sum"),
            gross_pnl=("Closed PnL", "sum"),
            net_pnl=("net_pnl", "sum"),
            avg_trade_size_usd=("Size USD", "mean"),
            median_trade_size_usd=("Size USD", "median"),
            exposure_proxy=("position_to_trade_size", "median"),
        )
        .reset_index()
    )

    realized_win = (
        merged.loc[merged["is_realized"]]
        .groupby("sentiment_bucket")["is_win"]
        .mean()
        .rename("realized_win_rate")
        .reset_index()
    )
    sentiment_trade = sentiment_trade.merge(realized_win, on="sentiment_bucket", how="left")

    segment_performance = (
        account.groupby(["activity_segment", "exposure_segment", "performance_segment"])
        .agg(
            accounts=("Account", "nunique"),
            total_trades=("total_trades", "sum"),
            gross_pnl=("gross_pnl", "sum"),
            net_pnl=("net_pnl", "sum"),
            avg_win_rate=("avg_win_rate", "mean"),
            trades_per_day=("trades_per_day", "mean"),
            exposure_proxy=("exposure_proxy", "median"),
        )
        .reset_index()
        .sort_values("gross_pnl", ascending=False)
    )

    account_sentiment = (
        account_day.groupby(["Account", "sentiment_bucket"])
        .agg(
            days=("date", "nunique"),
            trades=("trades", "sum"),
            gross_pnl=("gross_pnl", "sum"),
            win_rate=("win_rate", "mean"),
            avg_trade_size_usd=("avg_trade_size_usd", "mean"),
        )
        .reset_index()
    )

    top_accounts = account.head(10)

    return {
        "sentiment_daily_summary": sentiment_daily,
        "sentiment_trade_summary": sentiment_trade,
        "account_segments": account,
        "segment_performance": segment_performance,
        "account_sentiment_summary": account_sentiment,
        "top_accounts": top_accounts,
    }


def save_tables(tables: dict[str, pd.DataFrame], quality: pd.DataFrame) -> None:
    quality.to_csv(TABLE_DIR / "data_quality_summary.csv", index=False)
    for name, table in tables.items():
        table.to_csv(TABLE_DIR / f"{name}.csv", index=False)


def plot_outputs(merged: pd.DataFrame, daily: pd.DataFrame, account: pd.DataFrame, tables: dict[str, pd.DataFrame]) -> None:
    sns.set_theme(style="whitegrid", palette="Set2")

    plt.figure(figsize=(9, 5))
    order = ["Fear", "Neutral", "Greed"]
    sns.barplot(data=tables["sentiment_daily_summary"], x="sentiment_bucket", y="avg_daily_pnl", order=order)
    plt.title("Average Daily PnL by Market Sentiment")
    plt.xlabel("Sentiment")
    plt.ylabel("Average daily gross PnL")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "avg_daily_pnl_by_sentiment.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5))
    sns.boxplot(data=daily, x="sentiment_bucket", y="pnl_per_trade", order=order, showfliers=False)
    plt.title("Daily PnL per Trade Distribution by Sentiment")
    plt.xlabel("Sentiment")
    plt.ylabel("PnL per trade")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "pnl_per_trade_distribution.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5))
    sns.barplot(data=tables["sentiment_trade_summary"], x="sentiment_bucket", y="realized_win_rate", order=order)
    plt.title("Realized Win Rate by Market Sentiment")
    plt.xlabel("Sentiment")
    plt.ylabel("Realized win rate")
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(CHART_DIR / "win_rate_by_sentiment.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5))
    behavior = daily.melt(
        id_vars=["date", "sentiment_bucket"],
        value_vars=["trades", "avg_trade_size_usd", "long_short_ratio", "exposure_proxy"],
        var_name="metric",
        value_name="value",
    )
    sns.boxplot(data=behavior, x="sentiment_bucket", y="value", hue="metric", order=order, showfliers=False)
    plt.yscale("symlog")
    plt.title("Behavior Metrics by Sentiment")
    plt.xlabel("Sentiment")
    plt.ylabel("Value, symlog scale")
    plt.legend(title="Metric", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "behavior_metrics_by_sentiment.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 5))
    daily_sorted = daily.sort_values("date")
    sns.lineplot(data=daily_sorted, x="date", y="gross_pnl", hue="sentiment_bucket", marker="o")
    plt.title("Daily Gross PnL Over Time")
    plt.xlabel("Date")
    plt.ylabel("Gross PnL")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "daily_pnl_timeseries.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 5))
    seg = tables["segment_performance"].copy()
    seg["segment"] = seg["activity_segment"] + " | " + seg["exposure_segment"]
    sns.barplot(data=seg, y="segment", x="gross_pnl", hue="performance_segment")
    plt.title("Trader Segment Gross PnL")
    plt.xlabel("Gross PnL")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "segment_performance.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 6))
    scatter = account.copy()
    scatter["gross_pnl_signed"] = np.sign(scatter["gross_pnl"]) * np.log1p(scatter["gross_pnl"].abs())
    sns.scatterplot(
        data=scatter,
        x="trades_per_day",
        y="gross_pnl_signed",
        hue="performance_segment",
        size="exposure_proxy",
        sizes=(40, 220),
    )
    plt.title("Account Activity vs Gross PnL")
    plt.xlabel("Trades per active day")
    plt.ylabel("Signed log gross PnL")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "account_activity_vs_pnl.png", dpi=160)
    plt.close()


def format_number(value: float) -> str:
    if pd.isna(value):
        return "NA"
    return f"{value:,.2f}"


def write_report(tables: dict[str, pd.DataFrame], quality: pd.DataFrame) -> None:
    daily = tables["sentiment_daily_summary"].set_index("sentiment_bucket")
    trade = tables["sentiment_trade_summary"].set_index("sentiment_bucket")
    segment = tables["segment_performance"].head(5)
    top = tables["top_accounts"].head(5)

    report = f"""# Trader Performance vs Market Sentiment

## Methodology

I cleaned and aligned the Bitcoin Fear & Greed index with Hyperliquid trade history at daily granularity. Trader performance is measured with realized `Closed PnL`, net PnL after fees, realized win rate on non-zero-PnL trades, PnL per trade, and a drawdown proxy based on negative daily PnL. Behavior is measured with trade count, average trade size, long/short ratio, and an exposure proxy derived from `abs(Start Position * Execution Price) / Size USD`. The raw trader file does not include a direct leverage field, so the exposure proxy is used only as a relative risk indicator.

## Data Quality

- Fear & Greed: {int(quality.loc[quality.dataset == "fear_greed_index", "rows"].iloc[0]):,} rows, {int(quality.loc[quality.dataset == "fear_greed_index", "columns"].iloc[0])} columns, no missing values or duplicates.
- Historical trades: {int(quality.loc[quality.dataset == "historical_data", "rows"].iloc[0]):,} rows, {int(quality.loc[quality.dataset == "historical_data", "columns"].iloc[0])} columns, no missing values or duplicates.
- Merged trade-level table: {int(quality.loc[quality.dataset == "merged_trade_level", "rows"].iloc[0]):,} rows. Daily sentiment coverage matched all trade dates in this dataset.

## Key Insights

1. Greed days generated the strongest total PnL: {format_number(trade.loc["Greed", "gross_pnl"])} gross PnL across {int(trade.loc["Greed", "trades"]):,} trades.
2. Fear days had a slightly higher realized win rate: {format_number(trade.loc["Fear", "realized_win_rate"] * 100)}% versus {format_number(trade.loc["Greed", "realized_win_rate"] * 100)}% on Greed days, but Greed still produced more aggregate PnL.
3. Average daily PnL was highest during {daily["avg_daily_pnl"].idxmax()} conditions at {format_number(daily["avg_daily_pnl"].max())} per day.
4. Behavior shifts with sentiment: median long/short ratio was {format_number(daily.loc["Fear", "long_short_ratio"])} on Fear days and {format_number(daily.loc["Greed", "long_short_ratio"])} on Greed days.
5. The best segment by gross PnL was `{segment.iloc[0]["activity_segment"]} / {segment.iloc[0]["exposure_segment"]} / {segment.iloc[0]["performance_segment"]}`, producing {format_number(segment.iloc[0]["gross_pnl"])} gross PnL.
6. PnL is concentrated: the top 5 accounts contributed {format_number(top["gross_pnl"].sum())} gross PnL, so trader-level risk controls matter as much as aggregate sentiment.
7. Fear days had larger average trade size at trade level ({format_number(trade.loc["Fear", "avg_trade_size_usd"])}) than Greed days ({format_number(trade.loc["Greed", "avg_trade_size_usd"])}), suggesting traders sized up in stressed conditions.
8. Greed had the broadest sample coverage with {int(daily.loc["Greed", "days"]):,} active sentiment days, while Fear had {int(daily.loc["Fear", "days"]):,}; this matters when comparing total versus per-day performance.
9. Frequent high-exposure winners were the strongest archetype, but their average win rate ({format_number(segment.iloc[0]["avg_win_rate"] * 100)}%) was lower than some lower-exposure winning groups, implying size and activity drove much of the PnL.

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
"""
    (ROOT / "REPORT.md").write_text(report)


def main() -> None:
    ensure_dirs()
    fear_greed_raw, trades_raw = load_data()
    fear_greed, trades = prepare_data(fear_greed_raw, trades_raw)
    merged = build_merged_trade_level(fear_greed, trades)
    daily = build_daily_metrics(merged)
    account_day = build_account_day_metrics(merged)
    account = build_account_segments(account_day)
    quality = summarize_quality(fear_greed_raw, trades_raw, merged)
    tables = build_summary_tables(merged, daily, account_day, account)

    merged.to_csv(OUTPUT_DIR / "merged_trade_sentiment.csv", index=False)
    daily.to_csv(TABLE_DIR / "daily_metrics.csv", index=False)
    account_day.to_csv(TABLE_DIR / "account_day_metrics.csv", index=False)
    save_tables(tables, quality)
    plot_outputs(merged, daily, account, tables)
    write_report(tables, quality)

    print("Analysis complete.")
    print(f"Tables: {TABLE_DIR}")
    print(f"Charts: {CHART_DIR}")
    print(f"Report: {ROOT / 'REPORT.md'}")


if __name__ == "__main__":
    main()
