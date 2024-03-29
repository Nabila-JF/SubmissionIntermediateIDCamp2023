# -*- coding: utf-8 -*-
"""Submission2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1G9KJCAsUqB_y3HtpLCmYdgLMoLReiYPj

# Machine Learning Development Project: Submission 2
## Gold price forecasting
- Nama: Nabila Jauza Firjatullah
- Email: nabila060695@gmail.com
- Id Dicoding: billa_firza

#### Link to Google Drive
"""

from google.colab import drive
drive.mount('/content/drive')

"""#### Install Library"""

import numpy as np
import pandas as pd
from keras.layers import Dense, LSTM
import matplotlib.pyplot as plt
import tensorflow as tf

"""#### EDA"""

df = pd.read_csv('/content/drive/MyDrive/IDCamp2023/Pengembangan ML/Gold Price/gold_price_data.csv')
df.head()

df.isnull().sum()

print(f"{df.duplicated().sum()}")

plt.figure(figsize=(15,5))
plt.plot(df['Date'], df['Value'])
plt.title('Gold Price 1970-2020', fontsize=20);

"""#### Preprocessing Data"""

data = pd.DataFrame(list(df['Value']), index=df['Date'], columns=['Value'])

data.info()

data.head()

from sklearn.preprocessing import MinMaxScaler
scalar = MinMaxScaler(feature_range=(-1,1))
data_scaled=scalar.fit_transform(data)

data['Value_Scaled']= data_scaled
data.head()

from sklearn.model_selection import train_test_split

X = data.index
y = data['Value_Scaled'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

print("Jumlah data training:", X_train.shape[0])
print("Jumlah data testing:", X_test.shape[0])

max_data_scale = data_scaled.max()
min_data_scale = data_scaled.min()
threshold_mae = (max_data_scale - min_data_scale) * 10/100
print("Max Value: ", max_data_scale)
print("Min Value: ", min_data_scale)
print("Threshold MAE: ", threshold_mae)

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[-1:]))
    return ds.batch(batch_size).prefetch(1)

train_set = windowed_dataset(y_train, window_size=30, batch_size=32, shuffle_buffer=5000)
val_set = windowed_dataset(y_test, window_size=30, batch_size=32, shuffle_buffer=5000)

"""#### Model Train"""

model = tf.keras.models.Sequential([
  tf.keras.layers.LSTM(256, return_sequences=True),
  tf.keras.layers.LSTM(128),
  tf.keras.layers.Dense(64, activation="relu"),
  tf.keras.layers.Dense(1),
])

optimizer = tf.keras.optimizers.SGD(learning_rate=0.001, momentum=0.9)

model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=["mae"])

class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('mae') < 0.2 and  logs.get('val_mae') < 0.2):
      print("\nMAE telah mencapai < 10% skala data!")
      self.model.stop_training = True
callbacks = myCallback()

history = model.fit(
  train_set,
  validation_data=val_set,
  epochs=100,
  batch_size=256,
  callbacks=[callbacks]
)

"""#### History Train Plot"""

history_dict = history.history
loss = history_dict['loss']
val_loss = history_dict['val_loss']

mae = history_dict['mae']
val_mae = history_dict['val_mae']

epochs = range(1, len(loss) + 1)

fig, ax = plt.subplots()

ax.plot(epochs, loss, label='Training Loss')
ax.plot(epochs, val_loss, label='Validation Loss')
ax.plot(epochs, mae, label='Training MAE')
ax.plot(epochs, val_mae, label='Validation MAE')

ax.set_title('Training and Validation Metric')
ax.legend()

plt.show()

"""#### Test Predict"""

window_size = 30

forecast = []

for time in range(len(y_test) - window_size):
    series_window = np.array([y_test[time:time + window_size]])

    series_window = series_window.reshape((series_window.shape[0], series_window.shape[1], 1))

    prediction = model.predict(series_window)

    forecast.append(prediction[0, 0])

time_labels = np.arange(len(y_test))

plt.figure(figsize=(10, 6))

plt.plot(time_labels[window_size:], y_test[window_size:], label='Actual')

plt.plot(time_labels[window_size:], forecast, label='Predicted', linestyle='dashed')

plt.title('Time Series Prediction')
plt.xlabel('Time')
plt.ylabel('Values')

plt.legend()

plt.show()