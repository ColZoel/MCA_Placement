# -*- coding: utf-8 -*-
"""Econ 484 Project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15RUdQ5h1ZJYU8U9LAiLlvFXzUqO7hZfX

#1. Figure out your question

# 2. Obtain a labeled dataset (and explore its properties)
"""

# Commented out IPython magic to ensure Python compatibility.
#Import relevant libraries
from google.colab import drive
drive.mount('/content/gdrive')
# %matplotlib inline
import seaborn as sns
import pandas as pd
import numpy as np
import scipy.stats as stats
from sklearn import linear_model
from sklearn import metrics
from sklearn.model_selection import KFold
from sklearn.model_selection import GridSearchCV

#Read in the data in the spreadsheet 
#df=pd.read_csv('/content/gdrive/My Drive/Econ 484/Term Project/MCA Placement Data.csv')
df=pd.read_csv('/content/gdrive/My Drive/Colab Notebooks/Copy of MCA Placement Data.csv')
#print out the first few rows of data with the variable names
pd.set_option('display.max_columns', None)
print("Shape: {}".format(str(df.shape)))
#print out the number of observations and variables in the dataset
df.head()

# display the type of the columns in the data
pd.set_option('display.max_rows', None)
types = pd.DataFrame(df.dtypes[df.columns])
pd.DataFrame.transpose(types)

# get summary statistics on the numeric values in the dataset
df.describe()

#the location column is an object; get value counts for locations
for c in df.columns:
    if df[c].dtype == object:
      print(df[c].value_counts())
      print(sum(df[c].value_counts()))

#Determine the number of missing values for each column
missing = []
b = sum(df['ID'].value_counts())
for c in df.columns:
    a = sum(df[c].value_counts())
    z = b - a
    missing.append(z)
missingvars = pd.DataFrame(pd.DataFrame(np.array(missing)).transpose())
names = [s + 'Missing' for s in df.columns]
missingvars.columns=names
missingvars = missingvars.drop(columns=missingvars.columns[(missingvars == 0).any()])
missingvars

#plot the number of missing variables
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
missingvars.plot.bar(ax=ax)
ax.set_title("Missing variables in training data")
ax.set_ylabel("Number of missing variables")
ax.set_xlabel("")
 
ax.legend(bbox_to_anchor=(1.1, 1.05))

# impute indicators for columns with missing values
from sklearn.impute import MissingIndicator
indicator = MissingIndicator()
indicator.fit(df)
df1 = pd.DataFrame(indicator.transform(df))
df1.columns=missingvars.columns
df1.head()

#since I've now created an indicator for each missing value, I now replace all NA with 0
print('before', df.isnull().sum().sum(),' Nan values')
df.fillna(0, inplace=True)
print('after',df.isnull().sum().sum(),' Nan values')

#split into outcome variable and explanatory variables
#do not include ID variable (unnecessary)
y=df.loc[:,'Firm Category']
x=df.loc[:,[x for x in df.columns if x not in ('ID','Firm Category')]]

#explore the y variable distribution; 0 is "non-MBB", 1 is "MBB"
plt.figure(2); plt.title('Normal')
sns.distplot(y, kde=False)

#"Pre-process" quantitative features by standardizing them to have zero mean and unit variance
from sklearn.preprocessing import StandardScaler
xquant = df.loc[:,['ACT','GPA']]
scaler = StandardScaler()
scaler.fit(xquant)
xquant_scaled = pd.DataFrame(scaler.transform(xquant),columns=xquant.columns)
for c in xquant_scaled.columns:
  x[c] = xquant_scaled[c].values
x.head(1)

#turn years into an object variable to enable getting a dummy variable for each year to control for time-bound effects
x.astype({'Year': 'str'}).dtypes

#generate indicator variables for location
x = pd.get_dummies(x, columns=['Year','Location'])
print(x.shape)
x

#add in the indicators for missing variables
for c in df1.columns:
  #convert missing indicator boolean to integer
  df1[c] = df1[c]*1
  #add column to original dataframe
  x[c] = pd.Series(df1[c])
original_columns = x.columns
x.shape

# Get correct covariates (X) and variable of interest (d)
X = x.drop(['Business?'], axis=1)
d = x['Business?']

#generate polynomial features and interaction terms for all x variables
from sklearn.preprocessing import PolynomialFeatures
poly = PolynomialFeatures()
xpoly = poly.fit_transform(X)
column_names = poly.get_feature_names(X.columns)
X = pd.DataFrame(xpoly,columns=column_names, index=y.index)
X.shape

"""#3. Pick an appropriate method

##4. Divide into training and test sets
"""

from sklearn.model_selection import train_test_split
X_1, X_2, d_1, d_2, y_1, y_2 = train_test_split(X, d, y, test_size=0.2, random_state=42)

"""##5, 6. Choose regularization parameters via cross-validation on the training set and fit model on the whole training set using the cross-validated parameters"""

from sklearn.metrics import mean_squared_error # For comparing ML prediction methods
import statsmodels.api as sm # For outputting std errors, t-stats, and confidence intervals of final regression coefficients

"""# Post Double Selection"""

# Step 1: Lasso the outcome on X
lassoy = linear_model.Lasso(alpha=0.1, max_iter=100000,random_state=42).fit(X_1, y_1)
# print("Lassoy optimal alpha:", lassoy.alpha_)
print("CV lassoy alpha was ~0.01, which was too small. We set alpha=0.1 to remove enough covariates.")

# get MSE on test set
pds_test_preds_y = lassoy.predict(X_2)
print('Lassoy test MSE: %.2f' % mean_squared_error(y_2, pds_test_preds_y))

# Step 2: Lasso the treatment on X
lassod = linear_model.Lasso(alpha=0.1, max_iter=100000,random_state=42).fit(X_1, d_1)
# print("Lassod optimal alpha:", lassoy.alpha_)
print("CV lassod alpha was ~0.01, which was too small. We set alpha=0.1 to remove enough covariates.")

# get MSE on test set
pds_test_preds_d = lassod.predict(X_2)
print('Lassod test MSE: %.2f' % mean_squared_error(d_2, pds_test_preds_d))

# Step 3: Form the union of controls
Xunion = X_1.iloc[:,(lassod.coef_!=0) + (lassoy.coef_!=0)]

# Step 4: Concatenate treatment with union of controls and regress y on that
rhs=pd.concat([d_1,Xunion],axis=1)
fullreg=linear_model.LinearRegression().fit(rhs,y_1)
print("PDS regression effect of selective college: {:.3f}".format(fullreg.coef_[0]))

reg_obj = sm.OLS(y_1,sm.add_constant(rhs))
results = reg_obj.fit()
se_pds = results.bse[1]

print(results.summary())

"""## Double Debiased Machine Learning (Support Vector Machines)


"""

# Import the SVC package that allows for nonlinear decision boundaries and imperfect separation.
from sklearn.svm import SVC

from sklearn.model_selection import GridSearchCV
  # define grid for parameters
param_grid = {'C': [.01,.05,.1, .15,.2,.3,.4,.5,1],'gamma': [1,1.1,1.2,1.3,1.5,1.7,2,2.5],'kernel':['rbf','poly','linear']} #try every combo of these three parameters and see which is the best
grid_search = GridSearchCV(SVC(random_state=42),param_grid,cv=5,return_train_score=True)
best_SVCy=grid_search.fit(X_1,y_1)
best_SVCd=grid_search.fit(X_1,d_1)

print("Best C for y: ",best_SVCy.best_estimator_.get_params()['C'])
print("Best gamma for y: ",best_SVCy.best_estimator_.get_params()['gamma'])
print("Best kernel for y: ",best_SVCy.best_estimator_.get_params()['kernel'])

print("Best C for d: ",best_SVCd.best_estimator_.get_params()['C'])
print("Best gamma for d: ",best_SVCd.best_estimator_.get_params()['gamma'])
print("Best kernel for d: ",best_SVCd.best_estimator_.get_params()['kernel'])

SVCy = SVC(C=0.1,kernel='linear',gamma=1)
SVCd = SVC(C=0.1,kernel='linear',gamma=1)

# create our sample splitting "object"
kf = KFold(n_splits=5,shuffle=True,random_state=42)

# apply the splits to our Xs
kf.get_n_splits(X_1)

# initialize array to hold each fold's regression coefficient
coeffs=np.zeros(5)

# initialize arrays to hold each fold's MSEs
SVM_mse_y=np.zeros(5)
SVM_mse_d=np.zeros(5)

# Now loop through each fold
ii=0 # counter that keeps track of what fold we're on
total_variance = 0 # keep track of total variance to get std err of averaged coefficient
for train_index, test_index in kf.split(X_1):
  X_train, X_test = X_1.iloc[train_index,:], X_1.iloc[test_index,:] # using iloc to pick which obs. we want
  y_train, y_test = y_1.iloc[train_index], y_1.iloc[test_index]
  d_train, d_test = d_1.iloc[train_index], d_1.iloc[test_index]
  # Do DDML thing
  # SVC y on training folds:
  SVCy.fit(X_train,y_train)

  # get residuals in test set
  yresid=y_test-SVCy.predict(X_test)

  # get MSE on test set
  SVM_mse_y[ii] = mean_squared_error(y_2, SVCy.predict(X_2))
  
  #SVC d on training folds
  SVCd.fit(X_train,y_train)

  # get residuals in test set
  dresid=d_test-SVCd.predict(X_test)

  # get MSE on test set
  SVM_mse_d[ii] = mean_squared_error(d_2, SVCd.predict(X_2))

  # regress resids on resids
  reg_obj = sm.OLS(yresid,dresid)
  results = reg_obj.fit()
  # print(results.bse)
  total_variance += results.bse ** 2

  # save coefficient in a vector
  coeffs[ii]=results.params[0]
  ii+=1

# calculate the standard errors
stande_svc=np.sqrt(total_variance / 5)

# Take the average of the regression coefficients
coeffs_svc = np.mean(coeffs)
print("Double-Debiased Machine Learning effect of being a business major: {:.3f}".format(coeffs_svc))
print('coefficients:', coeffs)
print("Standard Error of mean coefficient:", np.sqrt(total_variance / 5)) # avg std err = add up variances, divide by 5, take square root

"""# Double Debiased Random Forests"""

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV

#parameters grid for cross-validation of the regression of y on x
parameters_y = {'max_depth':range(2,6),'min_samples_leaf':range(1,4),
              'criterion': ["gini", "entropy"]} 
#reg y_train subsample on X_train
rfcv_y= GridSearchCV(RandomForestClassifier(random_state=42), 
                     parameters_y, n_jobs=5).fit(X=X_train,y=y_train)

#unpacked cross-validated parameters 
rfy = RandomForestClassifier(random_state=42,**rfcv_y.best_params_)
print("RF_y optimal parameters", rfcv_y.best_params_)

#parameters grid for cross-validation of the regression of d on x
parameters_d = {'max_depth':range(2,6),'min_samples_leaf':range(1,4),
              'criterion': ["gini", "entropy"]} 
rfcv_d= GridSearchCV(RandomForestClassifier(random_state=42), 
                     parameters_d, n_jobs=5).fit(X=X_train,y=d_train)
rfd = RandomForestClassifier(random_state=42,**rfcv_d.best_params_)  

print("RF_d optimal parameters", rfcv_d.best_params_)

"""Evaluate using Sample Splitting"""

# initialize arrays to hold each fold's MSEs
RF_mse_y=np.zeros(5)
RF_mse_d=np.zeros(5)

#loop through each fold
ii=0 #keeps track of what fold we're on
total_variance = 0 #to get std err of averaged coefficient
for train_index, test_index in kf.split(X_1):
  X_train, X_test = X_1.iloc[train_index,:], X_1.iloc[test_index,:] # using iloc to pick which obs. we want
  y_train, y_test = y_1.iloc[train_index], y_1.iloc[test_index]
  d_train, d_test = d_1.iloc[train_index], d_1.iloc[test_index]
  
  # DDML
  rfy.fit(X_train, y_train)
  #y residuals in test
  yresidrf = y_test - rfy.predict(X_test)

  # get residuals in test set
  test_preds_y_rf = rfy.predict(X_2)
 
  #MSE on test set
  RF_mse_y[ii] = mean_squared_error(y_2, test_preds_y_rf)

  #Random Forest d on training folds
  rfd.fit(X_train, d_train)
  
  #d residuals in test set
  dresidrf = d_test - rfd.predict(X_test)
  #MSE
  test_preds_drf = rfd.predict(X_2)
  RF_mse_d[ii] = mean_squared_error(d_2, test_preds_drf)

#OLS residuals on residuals
  ddmlregrf = linear_model.LinearRegression().fit(dresidrf.values.reshape(-1,1),yresidrf)

  reg_obj = sm.OLS(yresidrf,dresidrf)
  results = reg_obj.fit()
  total_variance += results.bse ** 2 

  # save coefficient in a vector
  coeffs[ii]=ddmlregrf.coef_[0]
  ii+=1
#average coefficient among all estimations for use in aggregated table
coeffs_rf = np.mean(coeffs)

#standard error
se_rf = np.sqrt(total_variance / 5)

print("DDML Random Forests effect of business major: {:.3f}".format(np.mean(coeffs)))
print("Standard Error of mean coefficient:", np.sqrt(total_variance / 5))

"""# Causal Forest for Determining Heterogeneous Effects

The following describe feature importances indicating the level of heterogeneity created by the treatment Business Major, showing relative importance to the given subclass. Larger numbers indicate more significance. In this case, Having a business major creates greater heterogeneity between years some on those with a minor, and less among those with an internship. This does not imply magnitude of the effect.
"""

#specific library for Causal Forest
!pip install econml

from econml.dml import CausalForestDML as CausalForest
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

#establishing a list of potentially hetergenous variables
feature_names = ['Gender',
                 'Year',
                 'Double Major?','Minor?',
                    'Internship?']
#adding the controls follows an assumption of uncoundedness and removes two
#                     variables from being scored as affected by the business major
controls = ['ACT','GPA']

train, test = train_test_split(df,test_size=0.2)

#Run the estimator using the Random Forest Classifier to create a Propensity Tree
#since the goal is to check for heterogeneity rahter than identify specific effect, 
#default parameters are used.
estimator = CausalForest(n_estimators=1000,
                         cv = 5,
                         discrete_treatment = True,
                         model_t=RandomForestClassifier(random_state = 42),
                         model_y=RandomForestClassifier(random_state = 42),
                         )
#Fitting tree to the response
estimator.fit(train['Firm Category'],
              train['Business?'], #treatment: whether in business major 
              X = train[feature_names],
              inference='blb', #bootstrap of little bags inference
              W = train[controls])
effects_train = estimator.effect(train[feature_names]) #effects on training model
effects_test = estimator.effect(test[feature_names]) #effects on test model
conf_intrvl = estimator.effect_interval(test[feature_names]) #confidence interval 
#for all coefficient estimations

#prints the scores on level of heterogeneity created by the business major among 
#each feature in the order of the feature list. 
print(estimator.feature_importances())
print("creates higher heterogeneity among those with a minor and between years")

"""The second feature, year, has a significantly higher level of heterogeneity than all other features.

Identify the relative magnitudes of heterogeneity for "minor?" to determine if effect corroborates with other methods.
"""

#effect of business major for those with a minor
minorfx_train=effects_train[train['Double Major?'].values==1]
minorbusi_train=train['Business?'].iloc[train['Double Major?'].values==1] 
print('Training effect of business major for those with a minor', minorfx_train.mean())

#effect of business major for those without a minor
nominorfx_train=effects_train[train['Minor?'].values==0]
nominorbusi_train=train['Business?'].iloc[train['Minor?'].values==0] 
print('Training effect of business major for those without a minor', nominorfx_train.mean())

"""Effect seems very small, especially in comparison to other methods (though it is unkown if statstically significant or not). """

#MSE of estimator to compare to the other models 
print('Causal Forest MSE:', estimator.score(test['Firm Category'], test['Business?'], X = test[feature_names], W = test[controls]))

"""# Double Debiased Machine Learning (LASSO)"""

'''Without Sample Splitting first'''

# Lasso y on x
lassoy = linear_model.LassoCV(max_iter=100000,random_state=42).fit(X_1, y_1)
print("Lasso_y optimal alpha:", lassoy.alpha_)
# Obtain residuals
yresid = y_1 - lassoy.predict(X_1)
# Get test set MSE of predicting y
test_preds_y = lassoy.predict(X_2)
print('Lasso_y test MSE: %.2f' % mean_squared_error(y_2, test_preds_y))

# Lasso d on x
lassod = linear_model.LassoCV(max_iter=100000,random_state=42).fit(X_1, d_1)
print("Lasso_d optimal alpha:", lassod.alpha_)
# Obtain residuals
dresid = d_1 - lassod.predict(X_1)
# Get test set MSE of predicting d 
test_preds_d = lassod.predict(X_2)
print('Lasso_d test MSE: %.2f' % mean_squared_error(d_2, test_preds_d))

# Regress y residuals on d residuals
ddmlreg_lasso = linear_model.LinearRegression().fit(dresid.values.reshape(-1,1), yresid)
print("Double-Debiased Machine Learning (LASSO) effect of business major:", ddmlreg_lasso.coef_[0])

# Same thing but with statsmodel for regression table summary
reg_obj = sm.OLS(yresid,sm.add_constant(dresid))
results = reg_obj.fit()

print(results.summary())

'''With sample splitting'''
import statsmodels.api as sm

# create our sample splitting "object"
kf = KFold(n_splits=5,shuffle=True,random_state=42)

# apply the splits to our Xs
kf.get_n_splits(X_1)

# initialize array to hold each fold's regression coefficient
coeffs=np.zeros(5)
mse_y=np.zeros(5)
mse_d=np.zeros(5)

lassoy = linear_model.Lasso(alpha=lassoy.alpha_, max_iter=100000)
lassod = linear_model.Lasso(alpha=lassod.alpha_,max_iter=100000)

# Now loop through each fold
ii=0
total_variance = 0 # keep track of total variance to get std err of averaged coefficient
for train_index, test_index in kf.split(X_1):
  X_train, X_test = pd.DataFrame(X_1).iloc[train_index,:], pd.DataFrame(X_1).iloc[test_index,:]
  y_train, y_test = y_1.iloc[train_index], y_1.iloc[test_index]
  d_train, d_test = d_1.iloc[train_index], d_1.iloc[test_index]
  # Do DDML thing
  # Lasso y on training folds:
  lassoy.fit(X_train, y_train)

  # but get residuals in test set
  yresid = y_test - lassoy.predict(X_test)

  # get MSE on held-out set
  test_preds_y = lassoy.predict(X_2)
  mse_y[ii] = mean_squared_error(y_2, test_preds_y)
  
  # Lasso d on training folds
  lassod.fit(X_train, d_train)

  #but get residuals in test set
  dresid = d_test - lassod.predict(X_test)

  # get MSE on held-out set
  test_preds_d = lassod.predict(X_2)
  mse_d[ii] = mean_squared_error(d_2, test_preds_d)

  # regress resids on resids
  ddmlreg = linear_model.LinearRegression().fit(dresid.values.reshape(-1,1),yresid)

  reg_obj = sm.OLS(yresid,dresid)
  results = reg_obj.fit()
  # print(results.bse)
  total_variance += results.bse ** 2

  # save coefficient in a vector
  coeffs[ii]=ddmlreg.coef_[0]
  ii+=1

LASSO_mse_y = mse_y
LASSO_mse_d = mse_d
# Take average
print("Double-Debiased Machine Learning (LASSO) effect of business major: {:.3f}".format(np.mean(coeffs)))
coef_lasso = np.mean(coeffs)
print("Standard Error of mean coefficient:", np.sqrt(total_variance / 5)) # avg std err = add up variances, divide by 5, take square root
se_lasso = np.sqrt(total_variance / 5)
print("coeffs:", coeffs)
print("MSE_y", mse_y)
print("Avg:", np.mean(mse_y))
print("MSE_d", mse_d)
print("Avg:", np.mean(mse_d))

"""# Double Debiased Machine Learning (Logit)"""

'''Without Sample Splitting first'''

from sklearn.linear_model import LogisticRegression

# Logistic regression of y on x
logity = linear_model.LogisticRegressionCV(max_iter=1000,random_state=42).fit(X_1, y_1)
print("Logit optimal C:", logity.C_)
# Obtain residuals
yresid = y_1 - logity.predict(X_1)
# Get test set MSE of predicting y
logit_test_preds_y = logity.predict(X_2)
print('Logity test MSE: %.2f' % mean_squared_error(y_2, logit_test_preds_y))

# Logistic regression of d on x
logitd = linear_model.LogisticRegressionCV(max_iter=1000,random_state=42).fit(X_1, d_1)
print("Logit optimal C:", logitd.C_)
# Obtain residuals
dresid = d_1 - logitd.predict(X_1)
# Get test set MSE of predicting d 
logit_test_preds_d = logitd.predict(X_2)
print('Logitd test MSE: %.2f' % mean_squared_error(d_2, logit_test_preds_d))

# Regress y residuals on d residuals
ddmlreg_logit = linear_model.LinearRegression().fit(dresid.values.reshape(-1,1), yresid)
print("Double-Debiased Machine Learning (Logit) effect of business major:", ddmlreg_logit.coef_[0])

# Same thing but with statsmodel for regression table summary
import statsmodels.api as sm
reg_obj = sm.OLS(yresid,sm.add_constant(dresid))
results = reg_obj.fit()

print(results.summary())

'''With sample splitting'''
import statsmodels.api as sm

# create our sample splitting "object"
kf = KFold(n_splits=5,shuffle=True,random_state=42)

# apply the splits to our Xs
kf.get_n_splits(X_1)

# initialize array to hold each fold's regression coefficient
coeffs=np.zeros(5)
mse_y=np.zeros(5)
mse_d=np.zeros(5)

logity = linear_model.LogisticRegression(C=logity.C_[0], max_iter=1000)
logitd = linear_model.LogisticRegression(C=logitd.C_[0], max_iter=1000)

# Now loop through each fold
ii=0
total_variance = 0 # keep track of total variance to get std err of averaged coefficient
for train_index, test_index in kf.split(X_1):
  X_train, X_test = pd.DataFrame(X_1).iloc[train_index,:], pd.DataFrame(X_1).iloc[test_index,:]
  y_train, y_test = y_1.iloc[train_index], y_1.iloc[test_index]
  d_train, d_test = d_1.iloc[train_index], d_1.iloc[test_index]
  # Do DDML thing
  # Lasso y on training folds:
  logity.fit(X_train, y_train)

  # but get residuals in test set
  yresid = y_test - logity.predict(X_test)

  # get MSE on held-out set
  test_preds_y = logity.predict(X_2)
  mse_y[ii] = mean_squared_error(y_2, test_preds_y)
  
  # Lasso d on training folds
  logitd.fit(X_train, d_train)

  #but get residuals in test set
  dresid = d_test - logitd.predict(X_test)

  # get MSE on held-out set
  test_preds_d = logitd.predict(X_2)
  mse_d[ii] = mean_squared_error(d_2, test_preds_d)

  # regress resids on resids
  ddmlreg = linear_model.LinearRegression().fit(dresid.values.reshape(-1,1),yresid)

  reg_obj = sm.OLS(yresid,dresid)
  results = reg_obj.fit()
  # print(results.bse)
  total_variance += results.bse ** 2

  # save coefficient in a vector
  coeffs[ii]=ddmlreg.coef_[0]
  ii+=1

# Take average
print("Double-Debiased Machine Learning (Logit) effect of business major: {:.3f}".format(np.mean(coeffs)))
coef_logit = np.mean(coeffs)
print("Standard Error of mean coefficient:", np.sqrt(total_variance / 5)) # avg std err = add up variances, divide by 5, take square root
se_logit = np.sqrt(total_variance / 5)
print("coeffs:", coeffs)
print("MSE_y", mse_y)
print("Avg:", np.mean(mse_y))
logit_mse_y = np.mean(mse_y)
print("MSE_d", mse_d)
print("Avg:", np.mean(mse_d))
logit_mse_d = np.mean(mse_d)

"""# Choose a model of best fit

Compare the results of each method
"""

# Gather all test MSES for predicting y and d
SVM_y = np.mean(SVM_mse_y)
SVM_d = np.mean(SVM_mse_d)
logit_y = logit_mse_y
logit_d = logit_mse_d
PDSlasso_y = mean_squared_error(y_2, pds_test_preds_y)
PDSlasso_d = mean_squared_error(d_2, pds_test_preds_d)
lasso_y = np.mean(LASSO_mse_y)
lasso_d = np.mean(LASSO_mse_d)
rf_y = np.mean(RF_mse_y)
rf_d = np.mean(RF_mse_d)

# Gather coefficient results
coeffs_pds = fullreg.coef_[0]
coeffs_logit = coef_logit
coeffs_lasso = coef_lasso

#convert all se from series into scalers
se_svc = stande_svc.tolist()
se_logit = se_logit.tolist()
se_lasso = se_lasso.tolist()
se_rf = se_rf.tolist()
se_pds = np.mean(se_pds.tolist())

# Generate table of results
data = {'Model': ['DDB SVC', 'DDB Logit',
                  'DDB LASSO', 'DDB Random Forests', 
                  'PDS LASSO'],
        'MSE_y': [SVM_y, logit_y, lasso_y, rf_y, PDSlasso_y ],
        'MSE_d': [SVM_d,logit_d, lasso_d,rf_d, PDSlasso_d],
        
        'Coefficient Effect': [coeffs_svc, coeffs_logit, 
                               coeffs_lasso, coeffs_rf, coeffs_pds],
        'Coeff SE': [se_svc, se_logit, se_lasso,se_rf, se_pds]}

method_comp = pd.DataFrame(data = data)
method_comp

method_comp.to_excel('/content/gdrive/My Drive/Colab Notebooks/output.xlsx')

"""Select the models of best fit for both y and d"""

# Predict y using LASSO
lasso_y = linear_model.LassoCV(max_iter=100000,random_state=42).fit(X_1, y_1)
print("Lasso  y optimal alpha:", lasso_y.alpha_)
yresid = y_1 - lasso_y.predict(X_1)
logit_test_preds_y = lasso_y.predict(X_2)
print('Lasso y MSE: %.2f' % mean_squared_error(y_2, logit_test_preds_y))

# Predict d using LASSO
lassod = linear_model.LassoCV(max_iter=100000,random_state=42).fit(X_1, d_1)
print("Lasso optimal alpha:", lassod.alpha_)
lasso_test_preds_d = lassod.predict(X_2)
dresid = d_1 - lassod.predict(X_1)
print('LASSO test MSE: %.2f' % mean_squared_error(d_2, lasso_test_preds_d))

#Regress residuals from the logit regression on residuals from LASSO
reg_obj = sm.OLS(yresid,dresid)
results = reg_obj.fit()

print(results.summary())