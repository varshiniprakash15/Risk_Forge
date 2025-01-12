import streamlit as st
import stTools as tools
import portfolio_page_components
from datetime import datetime
import sqlite3
import json

# Database connection for users
user_conn = sqlite3.connect("users.db", check_same_thread=False)
user_cursor = user_conn.cursor()

# Database connection for portfolios
portfolio_conn = sqlite3.connect("portfolios.db", check_same_thread=False)
portfolio_cursor = portfolio_conn.cursor()

# Create portfolios table if it does not exist
portfolio_cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolios (
        username TEXT,
        portfolio_name TEXT,
        portfolio_data TEXT,
        PRIMARY KEY (username, portfolio_name)
    )
""")
portfolio_conn.commit()

def load_page():
    no_stocks = st.session_state.no_investment

    # Load portfolio performance
    my_portfolio = tools.build_portfolio(no_stocks=no_stocks)
    my_portfolio.update_market_value()

    portfolio_book_amount = my_portfolio.book_amount
    portfolio_market_value = my_portfolio.market_value
    diff_amount = portfolio_market_value - portfolio_book_amount
    pct_change = (diff_amount) / portfolio_book_amount * 100

    # Save my_portfolio to session state
    st.session_state.my_portfolio = my_portfolio

    # Create 2 columns for summary and pie chart
    col1_summary, col2_pie = st.columns(2)

    with col1_summary:
        portfolio_page_components.load_portfolio_performance_cards(
            portfolio_book_amount=portfolio_book_amount,
            portfolio_market_value=portfolio_market_value,
            diff_amount=diff_amount,
            pct_change=pct_change
        )

    with col2_pie:
        pie_chart_path = portfolio_page_components.load_portfolio_summary_pie()

    # Load investment preview
    st.subheader("Investment Performance Summary - Since Purchase")
    portfolio_page_components.load_portfolio_preview(no_stocks=no_stocks)

    # Input for saving the portfolio
    portfolio_name = st.text_input("Enter a name for your portfolio:", key="portfolio_name")
    
    if st.button("Save Portfolio"):
        if portfolio_name.strip():
            save_portfolio(my_portfolio, portfolio_name, portfolio_book_amount, portfolio_market_value, diff_amount, pct_change)
            st.success(f"Portfolio '{portfolio_name}' saved successfully!")
        else:
            st.error("Please enter a valid name for your portfolio.")

    # Button to view saved portfolios
    if st.button("View Saved Portfolios"):
        view_saved_portfolios()


def save_portfolio(portfolio, portfolio_name, book_amount, market_value, diff_amount, pct_change):
    """Save the user's portfolio data into the separate database."""
    
    # Prepare the data to be saved in the database
    saved_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Prepare the JSON data for storage (including name)
    portfolio_data = json.dumps({
        "name": portfolio_name,  # Include the name here
        "book_amount": book_amount,
        "market_value": market_value,
        "diff_amount": diff_amount,
        "pct_change": pct_change,
        "saved_date": saved_date,
        "username": st.session_state.username  # Associate with logged-in user
    })

    try:
        portfolio_cursor.execute("""
            INSERT INTO portfolios (username, portfolio_name, portfolio_data) 
            VALUES (?, ?, ?)
        """, (st.session_state.username, portfolio_name, portfolio_data))
        portfolio_conn.commit()
    except sqlite3.IntegrityError:
        st.error(f"Portfolio '{portfolio_name}' already exists. Please choose a different name.")


def view_saved_portfolios():
    """Display all saved portfolios for the logged-in user."""
    
    portfolio_cursor.execute("""
        SELECT portfolio_name FROM portfolios 
        WHERE username=?
    """, (st.session_state.username,))
    
    portfolios = portfolio_cursor.fetchall()
    
    if not portfolios:
        st.warning("No saved portfolios found.")
        return
    
    selected_file = st.selectbox("Select a portfolio to view:", [p[0] for p in portfolios])

    if selected_file:
        portfolio_cursor.execute("""
            SELECT portfolio_data FROM portfolios 
            WHERE username=? AND portfolio_name=?
        """, (st.session_state.username, selected_file))
        
        result = portfolio_cursor.fetchone()
        
        if result:
            display_portfolio_details(json.loads(result[0]), selected_file)  # Pass selected_file


def display_portfolio_details(portfolio_data, selected_file):
    """Display the details of a selected portfolio."""
    
    st.markdown(f"### Portfolio Details")
    
    st.markdown(f"**Title:** {portfolio_data.get('name', 'Unnamed Portfolio')}")
    st.markdown(f"**Saved Date:** {portfolio_data.get('saved_date', 'N/A')}")

    book_amount = portfolio_data.get('book_amount', 'Data Missing')
    market_value = portfolio_data.get('market_value', 'Data Missing')
    diff_amount = portfolio_data.get('diff_amount', 'Data Missing')
    pct_change = portfolio_data.get('pct_change', 'Data Missing')

    st.markdown(f"**Book Amount:** {tools.format_currency(book_amount) if book_amount != 'Data Missing' else 'Data Missing'}")
    st.markdown(f"**Market Value:** {tools.format_currency(market_value) if market_value != 'Data Missing' else 'Data Missing'}")

    # Check if pct_change is a number (int or float), and format accordingly
    pct_change_display = f"{pct_change:.2f}%" if isinstance(pct_change, (int, float)) else "Data Missing"
    
    st.markdown(f"**Gain/Loss:** {tools.format_currency(diff_amount) if diff_amount != 'Data Missing' else 'Data Missing'} "
                f"({pct_change_display})")

     # Option to delete the selected portfolio
    if st.button(f"Delete {selected_file}"):
         delete_portfolio(selected_file)


def delete_portfolio(portfolio_name):
   """Delete a specific user's saved portfolio."""
   portfolio_cursor.execute("""
       DELETE FROM portfolios 
       WHERE username=? AND portfolio_name=?
   """, (st.session_state.username, portfolio_name))
   portfolio_conn.commit()
   st.success(f"Portfolio '{portfolio_name}' has been deleted.")

# Close connections when done (optional based on your app lifecycle)
# user_conn.close()
# portfolio_conn.close()
