from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score
from sklearn.linear_model import SGDClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import warnings
warnings.simplefilter("ignore")

np.random.seed(47)

data = pd.read_csv('data/adult.csv')
data['ones'] = 1
columns = list(data)
target = 'income'

print(columns)

X, y = data[[col for col in columns if col != target]], data[target]
label_enc = LabelEncoder()
y_enc = label_enc.fit_transform(y)
X_train, X_test, y_train, y_test = train_test_split(X, y_enc, stratify=y_enc,
                                                    test_size=.1)

categorical_cols = ['workclass', 'occupation', 'marital_status']
numeric_cols = ['hours_per_week', 'age']

feature_transformation = ColumnTransformer(transformers=[
    ('cat_features', OneHotEncoder(handle_unknown='ignore'), categorical_cols),
    ('scaled_numeric', StandardScaler(), numeric_cols)
])

pipeline = Pipeline([
    ('features', feature_transformation),
    ('learner', SGDClassifier(max_iter=1000, tol=1e-3))])

param_grid = {
    'learner__loss': ['log'],
    'learner__penalty': ['l2', 'l1', 'elasticnet'],
    'learner__alpha': [0.0001, 0.001, 0.01, 0.1]
}

search = GridSearchCV(pipeline, param_grid, cv=5)
model = search.fit(X_train, y_train)

predicted = model.predict(X_test)
acc = accuracy_score(y_test, predicted)
print("TRAIN.  accuracy: %.4f" % (acc))
