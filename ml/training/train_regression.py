"""
ml.training.train_regression

Trains regression models on the time_in_care_months target (see
feature_engineering.build_regression_features() docstring for why this is
a meaningful continuous target rather than a forced regression). Uses the
same multi-model comparison approach as classification for consistency.
"""

from __future__ import annotations

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor

RANDOM_STATE = 42


def get_candidate_regressors() -> dict:
    return {
        "Linear Regression": LinearRegression(),
        "Decision Tree Regressor": DecisionTreeRegressor(max_depth=6, random_state=RANDOM_STATE),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE),
        "Gradient Boosting Regressor": GradientBoostingRegressor(random_state=RANDOM_STATE),
    }


def train_and_evaluate_regressors(X, y, test_size: float = 0.2) -> dict:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_STATE,
    )

    results = {}
    for name, model in get_candidate_regressors().items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        metrics = {
            "mae": mean_absolute_error(y_test, y_pred),
            "rmse": mean_squared_error(y_test, y_pred) ** 0.5,
            "r2": r2_score(y_test, y_pred),
        }
        results[name] = {"model": model, "metrics": metrics, "y_test": y_test, "y_pred": y_pred}

    results["_split"] = {"X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test}
    return results
