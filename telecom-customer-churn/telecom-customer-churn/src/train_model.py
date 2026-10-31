"""
train_model.py
---------------
Trains and compares classification models for Telecom Customer Churn
Prediction, picks the best one, tunes it, and saves the final trained
pipeline (preprocessing + model bundled together) to the models/ folder.

Run this file directly:
    python src/train_model.py
"""

import os
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

from preprocessing import (
    load_and_clean_data,
    split_features_target,
    build_preprocessor,
    FEATURE_COLUMNS,
)

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
# Built from this file's own location so the script works no matter
# where it is run from (VS Code "Run" button, terminal in src/, or
# terminal in project root all work the same way).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, "dataset", "Telco-Customer-Churn.csv")
MODEL_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "models", "churn_model.pkl")
RESULTS_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "models", "model_comparison_results.csv")
RANDOM_STATE = 42


def get_candidate_models():
    """
    Returns the models we will train and compare.

    Why these three:
      - Logistic Regression: simple, fast, highly interpretable baseline.
        Works well because many churn signals (contract type, tenure) are
        fairly linearly related to churn risk.
      - Random Forest: handles non-linear relationships and feature
        interactions (e.g. contract type + tenure combos) without much
        tuning, and is robust to outliers.
      - Gradient Boosting: usually squeezes out the best predictive
        performance on tabular data like this by building trees
        sequentially to correct previous errors.

    class_weight="balanced" (or equivalent) is used where available since
    the target is imbalanced (~73% No churn / ~27% Churn).
    """
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, class_weight="balanced", random_state=RANDOM_STATE
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            random_state=RANDOM_STATE
        ),
    }


def evaluate_model(name, pipeline, X_test, y_test):
    """Computes and prints all required evaluation metrics for one model."""
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)

    print(f"\n--- {name} ---")
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall   : {rec:.4f}")
    print(f"F1-score : {f1:.4f}")
    print(f"ROC-AUC  : {auc:.4f}")
    print("Confusion Matrix:")
    print(cm)
    print(classification_report(y_test, y_pred, target_names=["No Churn", "Churn"]))

    return {
        "Model": name,
        "Accuracy": acc,
        "Precision": prec,
        "Recall": rec,
        "F1": f1,
        "ROC-AUC": auc,
    }


def main():
    # -----------------------------------------------------------------
    # 1. Load and clean data
    # -----------------------------------------------------------------
    print("Loading and cleaning data...")
    df = load_and_clean_data(DATA_PATH)
    X, y = split_features_target(df)
    print(f"Data ready: {X.shape[0]} rows, {X.shape[1]} features")
    print(f"Target balance:\n{y.value_counts(normalize=True)}")

    # -----------------------------------------------------------------
    # 2. Train/test split (stratified because target is imbalanced)
    # -----------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    print(f"\nTrain size: {X_train.shape[0]}, Test size: {X_test.shape[0]}")

    # -----------------------------------------------------------------
    # 3. Train + evaluate each candidate model
    #    Each model gets its OWN preprocessor fitted only on training data
    #    (fit_transform on train, transform on test) -> avoids data leakage.
    # -----------------------------------------------------------------
    results = []
    fitted_pipelines = {}

    for name, model in get_candidate_models().items():
        pipeline = Pipeline(steps=[
            ("preprocessor", build_preprocessor()),
            ("classifier", model),
        ])
        pipeline.fit(X_train, y_train)
        fitted_pipelines[name] = pipeline
        results.append(evaluate_model(name, pipeline, X_test, y_test))

    results_df = pd.DataFrame(results).sort_values(by="F1", ascending=False)
    print("\n=========== MODEL COMPARISON (sorted by F1-score) ===========")
    print(results_df.to_string(index=False))

    # -----------------------------------------------------------------
    # 4. Select best model
    #    We use F1-score as the primary metric (not accuracy) because the
    #    dataset is imbalanced -> accuracy can look good while missing
    #    most actual churners. F1 balances precision and recall.
    # -----------------------------------------------------------------
    best_model_name = results_df.iloc[0]["Model"]
    print(f"\nBest model based on F1-score: {best_model_name}")
    best_pipeline = fitted_pipelines[best_model_name]

    # -----------------------------------------------------------------
    # 5. Hyperparameter tuning on the best model
    # -----------------------------------------------------------------
    print(f"\nRunning hyperparameter tuning for {best_model_name}...")
    param_grids = {
        "Logistic Regression": {
            "classifier__C": [0.01, 0.1, 1, 10],
        },
        "Random Forest": {
            "classifier__n_estimators": [200, 400],
            "classifier__max_depth": [None, 10, 20],
            "classifier__min_samples_leaf": [1, 2, 4],
        },
        "Gradient Boosting": {
            "classifier__n_estimators": [100, 200],
            "classifier__learning_rate": [0.05, 0.1],
            "classifier__max_depth": [2, 3, 4],
        },
    }

    grid = GridSearchCV(
        estimator=Pipeline(steps=[
            ("preprocessor", build_preprocessor()),
            ("classifier", get_candidate_models()[best_model_name]),
        ]),
        param_grid=param_grids[best_model_name],
        scoring="f1",
        cv=5,
        n_jobs=-1,
    )
    grid.fit(X_train, y_train)
    print(f"Best params: {grid.best_params_}")
    print(f"Best CV F1-score: {grid.best_score_:.4f}")

    tuned_pipeline = grid.best_estimator_
    tuned_metrics = evaluate_model(f"{best_model_name} (Tuned)", tuned_pipeline, X_test, y_test)

    # Only keep the tuned version if it's actually better on the test set
    if tuned_metrics["F1"] >= results_df.iloc[0]["F1"]:
        final_pipeline = tuned_pipeline
        print("\nTuned model performs better (or equal) -> using tuned model as final.")
    else:
        final_pipeline = best_pipeline
        print("\nTuned model did not improve F1 on test set -> keeping original best model.")

    # -----------------------------------------------------------------
    # 6. Feature importance (for tree-based models) / coefficients (for LR)
    # -----------------------------------------------------------------
    print("\n=========== FEATURE IMPORTANCE / INTERPRETABILITY ===========")
    try:
        preprocessor = final_pipeline.named_steps["preprocessor"]
        classifier = final_pipeline.named_steps["classifier"]
        feature_names = preprocessor.get_feature_names_out()

        if hasattr(classifier, "feature_importances_"):
            importances = classifier.feature_importances_
            imp_df = pd.DataFrame({
                "feature": feature_names,
                "importance": importances,
            }).sort_values(by="importance", ascending=False)
            print(imp_df.head(15).to_string(index=False))
        elif hasattr(classifier, "coef_"):
            coefs = classifier.coef_[0]
            imp_df = pd.DataFrame({
                "feature": feature_names,
                "coefficient": coefs,
            }).sort_values(by="coefficient", key=abs, ascending=False)
            print(imp_df.head(15).to_string(index=False))
    except Exception as e:
        print(f"Could not extract feature importance: {e}")

    # -----------------------------------------------------------------
    # 7. Save the final trained pipeline (preprocessing + model together)
    # -----------------------------------------------------------------
    os.makedirs(os.path.join(PROJECT_ROOT, "models"), exist_ok=True)
    joblib.dump(final_pipeline, MODEL_OUTPUT_PATH)
    print(f"\nFinal model pipeline saved to: {MODEL_OUTPUT_PATH}")

    # Also save the results table for reference
    results_df.to_csv(RESULTS_OUTPUT_PATH, index=False)
    print(f"Model comparison results saved to: {RESULTS_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
