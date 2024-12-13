import streamlit as st
import stTools as tools
import side_bar_components
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import yfinance as yf  # Import yfinance for stock data
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler

def load_sidebar() -> None:
    tools.create_side_bar_width()
    st.sidebar.title("Control Panel")

    if "load_portfolio" not in st.session_state:
        st.session_state["load_portfolio"] = False

    if "run_simulation" not in st.session_state:
        st.session_state["run_simulation"] = False

    portfo_tab, model_tab, pred_tab = st.sidebar.tabs(
        ["📈 Create Portfolio", " Build Risk Model", "Prediction"]
    )

    # Portfolio tab
    portfo_tab.title("Portfolio Building")
    side_bar_components.load_sidebar_dropdown_stocks(portfo_tab)
    side_bar_components.load_sidebar_stocks(portfo_tab,
                                            st.session_state.no_investment)
    st.session_state["load_portfolio"] = portfo_tab.button("Load Portfolio",
                                                           key="side_bar_load_portfolio",
                                                           on_click=tools.click_button_port)

    portfo_tab.markdown("""You can create a portfolio with a maximum of :green[10] investments.""")

    # Model tab
    model_tab.title("Risk Model Building")
    side_bar_components.load_sidebar_risk_model(model_tab)
    st.session_state["run_simulation"] = model_tab.button("Run Simulation",
                                                         key="main_page_run_simulation",
                                                         on_click=tools.click_button_sim)

    model_tab.markdown(""" :green[VaR (Value at Risk)]: Think of VaR as a safety net, indicating the maximum potential loss within a confidence level.""")

    # Prediction Tab
    pred_tab.title("Stock Prediction")

    stock_ticker = pred_tab.text_input("Enter stock ticker (e.g., AAPL)")

    if stock_ticker:
        pred_tab.write(f"Predicting for: {stock_ticker}")

        if pred_tab.button("Train Model and Predict"):
            # Call the function to train the model and predict
            predictions, df_predictions = train_predict_stock(stock_ticker)
            
            # Show results in a popup with a close button
            with st.expander(f"Prediction Results for {stock_ticker}", expanded=True):
                st.write("### Predicted Prices (Next 15 days):")
                st.write(df_predictions)  # Show prediction dataframe
                
                # Plotting graph with Plotly
                fig = plot_prediction_graph(df_predictions)
                st.plotly_chart(fig, use_container_width=True)

                # Option to close the expanded section by clicking the cross icon
                st.write("\n")
                st.write("### Hover over the graph to see prices.")

def train_predict_stock(ticker: str):
    # Fetch stock data using yfinance
    data = yf.download(ticker, period="1y", interval="1d")

    # Preprocessing data for LSTM model
    data = data[['Close']]
    
    # Normalize the data (scaling between 0 and 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data['Close'].values.reshape(-1, 1))
    
    # Prepare data for LSTM
    def create_dataset(data, time_step=1):
        x, y = [], []
        for i in range(len(data) - time_step - 1):
            x.append(data[i:(i + time_step), 0])
            y.append(data[i + time_step, 0])
        return np.array(x), np.array(y)

    time_step = 100
    x, y = create_dataset(scaled_data, time_step)
    x = x.reshape(x.shape[0], x.shape[1], 1)

    # Build and train LSTM model
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(x.shape[1], 1)))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dense(units=1))
    model.compile(optimizer='adam', loss='mean_squared_error')

    model.fit(x, y, epochs=1, batch_size=1, verbose=2)

    # Predict next 15 days
    last_100_days = scaled_data[-100:]
    x_input = last_100_days.reshape(1, -1)
    x_input = x_input.reshape((x_input.shape[0], x_input.shape[1], 1))
    
    predictions = []
    for i in range(15):
        pred_price = model.predict(x_input)
        predictions.append(pred_price)
        x_input = np.append(x_input[:, 1:, :], pred_price.reshape(1, 1, 1), axis=1)
    
    # Inverse transform predictions to original scale
    predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1))

    # Create dataframe for predictions
    future_dates = pd.date_range(start=data.index[-1], periods=16, freq='D')[1:]
    df_predictions = pd.DataFrame(predictions, columns=['Predicted Price'], index=future_dates)
    
    return predictions, df_predictions

def plot_prediction_graph(df_predictions):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_predictions.index, y=df_predictions['Predicted Price'],
                             mode='lines+markers', name='Predicted Price'))
    fig.update_layout(title="Stock Price Prediction for Next 15 Days",
                      xaxis_title="Date",
                      yaxis_title="Price (USD)",
                      hovermode="x unified")
    return fig
