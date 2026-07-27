# ML Training Report

## Classification: Placement Disruption Prediction
- Samples: 384
- Class balance: {0: 0.865, 1: 0.135}

### Deep Learning Justification Check
Dataset has 384 samples, below the ~1000 generally recommended before deep learning offers a real advantage over classical ML on tabular data. A small MLP is still trained below for comparison purposes, but classical models are expected to match or outperform it here — that is itself the finding worth reporting, not a limitation to hide.

### Deep Learning (MLP)
*Skipped: TensorFlow is not installed in this environment.*

### Random Forest Hyperparameter Tuning (GridSearchCV, 5-fold, scoring=f1)
- Best params: `{'max_depth': 6, 'min_samples_split': 2, 'n_estimators': 100}`
- Best CV F1: 0.6104

### Model Comparison (sorted by F1 score)
| model               |   accuracy |   precision |   recall |     f1 |   roc_auc |   cv_accuracy_mean |
|:--------------------|-----------:|------------:|---------:|-------:|----------:|-------------------:|
| Random Forest       |     0.9221 |      0.75   |      0.6 | 0.6667 |    0.9007 |             0.8729 |
| XGBoost             |     0.8831 |      0.5455 |      0.6 | 0.5714 |    0.8806 |             0.8567 |
| SVM (RBF kernel)    |     0.8442 |      0.4444 |      0.8 | 0.5714 |    0.8746 |             0.7917 |
| Logistic Regression |     0.8571 |      0.4667 |      0.7 | 0.56   |    0.9418 |             0.8275 |
| Gradient Boosting   |     0.9091 |      0.8    |      0.4 | 0.5333 |    0.8299 |             0.8762 |
| Decision Tree       |     0.7792 |      0.3478 |      0.8 | 0.4848 |    0.8022 |             0.8241 |
| K-Nearest Neighbors |     0.8831 |      1      |      0.1 | 0.1818 |    0.8791 |             0.8567 |

**Selected model: Random Forest** (highest F1 — chosen over raw accuracy because the disruption class is a minority class; accuracy alone would favor a model that just predicts 'not disrupted' for everyone).

**Note on deep learning**: MLP training was skipped because TensorFlow is not installed in this environment.

## Regression: Time-in-Care Prediction (months)
| model                       |   mae |   rmse |     r2 |
|:----------------------------|------:|-------:|-------:|
| Linear Regression           | 6.305 |  8.831 | 0.3961 |
| Gradient Boosting Regressor | 6.65  |  9.259 | 0.3361 |
| Random Forest Regressor     | 7.004 |  9.475 | 0.3048 |
| Decision Tree Regressor     | 7.03  |  9.57  | 0.2908 |
