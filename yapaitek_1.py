# -*- coding: utf-8 -*-
"""yapaitek_1.ipynb

Automatically generated by Colaboratory.
my vm works fine on github
commit
Original file is located at
    https://colab.research.google.com/drive/1lilJdAMtXwKKjSei2VtXFfFbGBRomkcl
"""

# downloading files
# import requests
import urllib.request as urlrq
names = ['data.csv','test.csv']
urls =['https://www.dropbox.com/s/xvmakmcx51cos54/data.csv?dl=1',
       'https://www.dropbox.com/s/3xw7hw4qp6l0nnf/test.csv?dl=1']
for i in range(2):
  urlrq.urlretrieve(urls[i],names[i])

dp = '/content/data.csv'
dt = '/content/test.csv'

import sklearn.metrics as sklm
from sklearn.model_selection import train_test_split,cross_val_score,GridSearchCV
from xgboost import XGBRegressor
import xgboost as xgb
import pandas as pd
import numpy as np
import multiprocessing
from sklearn import preprocessing
from tqdm import trange
from IPython.display import clear_output
from sklearn.preprocessing import LabelEncoder

nthread = multiprocessing.cpu_count()
print('pool counts: ', nthread)
train = pd.read_csv(dp, na_values="?", low_memory=False)
test = pd.read_csv(dt, na_values="?", low_memory=False)

train_proned =train.drop(columns=['Year','Date','Start_time','End_time','Market Share_total','Name of episode','Unnamed: 0'])
categoricals = train_proned.drop(columns=["Length","Temperature in Montreal during episode"])
scalars = train_proned[["Length","Temperature in Montreal during episode"]]
Ground_truth = train["Market Share_total"].to_numpy()

# date manu...
date_time = pd.to_datetime(train["Start_time"])
date = pd.to_datetime(train["Date"])
datebuf = np.zeros(date.count())
time = np.zeros(date.count())

for i in trange(date.count()):
  # clear_output()
  if date[i] is pd.NaT:
    datebuf[i] = datebuf[i-1]
  elif date_time[i] is pd.NaT:
    time[i] = time[i-1]
  else:
    datebuf[i] = np.array(((date[i].year-2000)*365 + date[i].day + date[i].month*30))
    time[i]=np.array((date_time[i].time().hour*60+date_time[i].time().minute))

p=categoricals.columns
trainlist = pd.DataFrame()
encoder=[]
for i in trange(len(p)):
  encoder.append(LabelEncoder())
  categoricals[p[i]] = encoder[i].fit_transform(categoricals[p[i]])
clear_output()
categoricals.insert(1,column="time", value=time)
categoricals.insert(1,column="datebuf", value=datebuf)
categoricals=categoricals.join(scalars, how='right')
trainset = categoricals.to_numpy()

X_train, X_test, y_train, y_test = train_test_split(trainset, Ground_truth, test_size=0.3)

generalmodel = XGBRegressor(max_depth = 20,booster ="dart", tree_method='gpu_hist', gpu_id=0, 
                   nthread = nthread, nrounds = 3000, objective = "reg:squarederror")    # reg:tweedie / reg:squarederror
generalmodel.fit(X_train, y_train)
print('generalmodel: trained')

y_pred = generalmodel.predict(X_train)
corr = np.corrcoef(np.transpose(y_pred), y_train)
print('train correlation:',corr[0,0])
print('R-squared for train-set: ',sklm.r2_score(y_train,y_pred))
print('mean_absolute_error for train-set: ',sklm.mean_absolute_error(y_train,y_pred))
print('\n')
y_pred = generalmodel.predict(X_test)
corr = np.corrcoef(y_pred, y_test)
print('test correlation:',corr[0,0])
print('R-squared for test-set: ',sklm.r2_score(y_test,y_pred))
print('mean_absolute_error for test-set: ',sklm.mean_absolute_error(y_test,y_pred))