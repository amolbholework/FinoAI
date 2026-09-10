"""Model-fitting helpers. Kept separate from service.py so each model can be
unit tested (and swapped) independently of the forecast-assembly logic."""
import warnings
from dataclasses import dataclass

import pandas as pd

COLD_START_MIN_MONTHS = 3
BACKTEST_MIN_MONTHS = 4  # need one extra month beyond cold-start to hold out for error metrics


@dataclass(frozen=True)
class PointForecast:
    predicted: float
    lower: float
    upper: float


def _series_to_df(series: list[tuple[str, int]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ds": pd.to_datetime([f"{m}-01" for m, _ in series]),
            "y": [float(v) for _, v in series],
        }
    )


def average_fallback(series: list[tuple[str, int]]) -> PointForecast:
    """Cold-start model: plain average of whatever history exists. The interval
    is a fixed +/-30% band rather than a statistically derived one — with under
    3 months of data there isn't enough signal to estimate real uncertainty, so
    this is deliberately wide and labeled low-confidence by the caller."""
    values = [v for _, v in series]
    avg = sum(values) / len(values) if values else 0.0
    return PointForecast(predicted=avg, lower=avg * 0.7, upper=avg * 1.3)


def run_prophet(series: list[tuple[str, int]]) -> PointForecast:
    from prophet import Prophet

    df = _series_to_df(series)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
            interval_width=0.8,
        )
        model.fit(df)
        future = model.make_future_dataframe(periods=1, freq="MS")
        forecast = model.predict(future)

    last_row = forecast.iloc[-1]
    return PointForecast(
        predicted=max(0.0, float(last_row["yhat"])),
        lower=max(0.0, float(last_row["yhat_lower"])),
        upper=max(0.0, float(last_row["yhat_upper"])),
    )


def run_prophet_multi(series: list[tuple[str, int]], periods: int) -> list[PointForecast]:
    """Same fit as run_prophet, but returns one PointForecast per future month
    up to `periods` months out (a single Prophet fit, not one per horizon
    length) — powers the forecast page's 1/3/6-month horizon control."""
    from prophet import Prophet

    df = _series_to_df(series)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
            interval_width=0.8,
        )
        model.fit(df)
        future = model.make_future_dataframe(periods=periods, freq="MS")
        forecast = model.predict(future)

    future_rows = forecast.tail(periods)
    return [
        PointForecast(
            predicted=max(0.0, float(row.yhat)),
            lower=max(0.0, float(row.yhat_lower)),
            upper=max(0.0, float(row.yhat_upper)),
        )
        for row in future_rows.itertuples()
    ]


def run_arima(series: list[tuple[str, int]]) -> PointForecast | None:
    from statsmodels.tsa.arima.model import ARIMA

    values = [float(v) for _, v in series]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = ARIMA(values, order=(1, 1, 0))
            fitted = model.fit()
            result = fitted.get_forecast(steps=1)
            mean = float(result.predicted_mean[0])
            conf_int = result.conf_int(alpha=0.2)[0]
        return PointForecast(predicted=max(0.0, mean), lower=max(0.0, float(conf_int[0])), upper=max(0.0, float(conf_int[1])))
    except Exception:
        # Short/degenerate series can make ARIMA fail to converge — it's only
        # a comparison baseline, so we drop it rather than blocking the forecast.
        return None


def backtest_error(series: list[tuple[str, int]], fit_predict) -> tuple[float, float] | None:
    """Holds out the last month, fits on the rest, and compares. Returns
    (MAE, MAPE) in the series' native units, or None if there isn't enough
    history to hold a month out."""
    if len(series) < BACKTEST_MIN_MONTHS:
        return None

    train = series[:-1]
    actual = series[-1][1]

    try:
        prediction = fit_predict(train)
    except Exception:
        return None
    if prediction is None:
        return None

    mae = abs(prediction.predicted - actual)
    mape = (mae / actual * 100) if actual != 0 else None
    return mae, (mape if mape is not None else 0.0)
