# Amazon Sponsored Products Bid Optimizer - Version with Input Validation & PDF Output
# This script optimizes Amazon Sponsored Products bids, includes input validation,
# and now automatically generates a PDF instruction file along with the CSV output.
# This script can be used for US ,UK AND EU.

import pandas as pd # Import pandas for data manipulation
import numpy as np # Import numpy for numerical operations
from fpdf import FPDF  # Import the FPDF class from the fpdf2 library

def optimize_bids(input_file):
    """
    Main function to optimize Amazon Sponsored Products bids and generate output.
    Performs input validation, data loading, cleaning, applies bid optimization filters,
    and prepares the output DataFrame.

    Args:
        input_file (str): Path to the CSV file containing campaign data

    Returns:
        pandas.DataFrame: Optimized data with new bid recommendations

    Raises:
        ValueError: If the input CSV file is missing any of the required columns.
        FileNotFoundError: If the input file specified by input_file is not found.
        Exception: For any other errors during processing, with a general error message.
    """
    try: # Start of a try block to catch potential errors during the process
        #  Input Validation: Check for required columns 
        # --------------------------------------------------
        required_columns = [
            'Bid',                                      # Current bid amount - REQUIRED
            'Ad Group Default Bid (Informational only)', # Default ad group bid - REQUIRED
            'Spend',                                    # Amount spent on advertising - REQUIRED
            'Sales',                                    # Revenue generated - REQUIRED
            'Orders',                                   # Number of orders received - REQUIRED
            'Clicks',                                   # Number of clicks on the ad - REQUIRED
            'ROAS',                                     # Return on Ad Spend - REQUIRED
            'Impressions',                             # Number of times ad was shown - REQUIRED
        ]
        # List comprehension to find columns from required_columns that are NOT in the DataFrame's columns
        missing_columns = [col for col in required_columns if col not in pd.read_csv(input_file, nrows=0).columns] # Read only headers to efficiently check columns

        if missing_columns: # Check if the list of missing columns is not empty (i.e., if there are missing columns)
            missing_cols_str = ", ".join(missing_columns) # Create a comma-separated string of missing column names for the error message
            error_message = f"Error: Input CSV is missing the following required columns: {missing_cols_str}. \nPlease ensure your bulksheet export includes these columns and that the column names are correct." # Construct user-friendly error message
            raise ValueError(error_message) # Raise a ValueError exception, stopping the script and displaying the error message

        # Step 1: Load and prepare the data
        #-----------------------------------------

        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(input_file, keep_default_na=False) # keep_default_na=False to treat empty cells as empty strings, not NaN

        # Make a copy of the data to work with (leaves original data unchanged)
        optimized_df = df.copy()

        # List of columns that should contain numbers (re-declared for clarity, already used in input validation)
        numeric_columns = [
            'Bid',
            'Ad Group Default Bid (Informational only)',
            'Spend',
            'Sales',
            'Orders',
            'Clicks',
            'ROAS',
            'Impressions',
        ]

        # Step 2: Clean up the numeric data
        #-----------------------------------------

        # Convert all numeric columns to proper number format
        for col in numeric_columns:
            if col in optimized_df.columns: # Check if the column exists in the DataFrame (for robustness)
                # Replace empty strings with '0' before converting to numeric
                optimized_df[col] = optimized_df[col].replace('', '0')
                # Convert to numeric, errors='coerce' will turn invalid parsing into NaN, then fillna(0) replaces NaN with 0
                optimized_df[col] = pd.to_numeric(optimized_df[col], errors='coerce').fillna(0)

        # If Bid is 0, use the Ad Group Default Bid instead
        mask = (optimized_df['Bid'] == 0) # Create a boolean mask for rows where 'Bid' is 0
        optimized_df.loc[mask, 'Bid'] = optimized_df.loc[mask, 'Ad Group Default Bid (Informational only)'] # Use .loc to safely modify 'Bid' based on the mask

        # Step 3: Set up new columns for our analysis
        #-----------------------------------------

        optimized_df['New Bid'] = optimized_df['Bid']          # Column to store our recommended bid, initially set to current bid
        optimized_df['Increase or decrease'] = ''              # Column to indicate if bid is increased or decreased
        optimized_df['Why'] = ''                              # Column to explain the reason for bid change
        optimized_df['Goal'] = ''                             # Column to state the optimization goal
        optimized_df['How much'] = ''                         # Column to show the amount of bid change
        optimized_df['Operation'] = 'Update'                  # Column set to 'Update' for bulksheet operation type

        # Step 4: Calculate performance metrics
        #-----------------------------------------

        # Get total spend and sales across all keywords for percentage calculations
        total_spend = optimized_df['Spend'].sum()
        total_sales = optimized_df['Sales'].sum()

        # Calculate what percentage each keyword represents of total spend
        if total_spend > 0: # Avoid division by zero if total_spend is 0
            optimized_df['Spend%'] = (optimized_df['Spend'] / total_spend * 100).round(2) # Calculate percentage, round to 2 decimal places
        else:
            optimized_df['Spend%'] = 0 # Set to 0 if total spend is 0

        # Calculate what percentage each keyword represents of total sales
        if total_sales > 0: # Avoid division by zero if total_sales is 0
            optimized_df['Sale%'] = (optimized_df['Sales'] / total_sales * 100).round(2) # Calculate percentage, round to 2 decimal places
        else:
            optimized_df['Sale%'] = 0 # Set to 0 if total sales is 0

        # Dynamically find column names (case-insensitive matching) - for robustness if column names in CSV vary slightly
        campaign_name_col = next(col for col in optimized_df.columns if col.lower() == "campaign name (informational only)")
        portfolioname_col = next(col for col in optimized_df.columns if col.lower() == "portfolio name (informational only)")
        campaignstate_col = next(col for col in optimized_df.columns if col.lower() == "campaign state (informational only)")

        # Step 5: Apply Different Optimization Filters
        #-----------------------------------------

        # FILTER 1: Keywords that get clicks but no sales (Cost but No Revenue)
        #----------------------------------------------
        mask_opt1 = (
            (optimized_df['Clicks'] > 0) &    # Condition: Has received clicks
            (optimized_df['Orders'] == 0)      # Condition: But no orders
        )

        # Different bid reductions based on how much we're spending
        mask_opt1_high = mask_opt1 & (optimized_df['Spend'] > 20)                                        # High spenders: over $20
        mask_opt1_medium = mask_opt1 & (optimized_df['Spend'] >= 5) & (optimized_df['Spend'] <= 20)      # Medium spenders: $5-$20
        mask_opt1_low = mask_opt1 & (optimized_df['Spend'] < 5)                                          # Low spenders: under $5

        # Apply bid reductions
        optimized_df.loc[mask_opt1_high, 'New Bid'] = optimized_df.loc[mask_opt1_high, 'Bid'] - 0.10    # Reduce by 10 cents
        optimized_df.loc[mask_opt1_medium, 'New Bid'] = optimized_df.loc[mask_opt1_medium, 'Bid'] - 0.05 # Reduce by 5 cents
        optimized_df.loc[mask_opt1_low, 'New Bid'] = optimized_df.loc[mask_opt1_low, 'Bid'] - 0.03      # Reduce by 3 cents

        # Add explanations for these changes
        optimized_df.loc[mask_opt1, 'Why'] = 'Cost but No Revenue'
        optimized_df.loc[mask_opt1, 'Goal'] = 'To Decrease Acos'
        optimized_df.loc[mask_opt1_high, 'How much'] = 'Decreased bids by 0.10 cents'
        optimized_df.loc[mask_opt1_medium, 'How much'] = 'Decreased bids by 0.05 cents'
        optimized_df.loc[mask_opt1_low, 'How much'] = 'Decreased bids by 0.03 cents'
        optimized_df.loc[mask_opt1, 'Increase or decrease'] = 'Decrease'

        # FILTER 2: Keywords with high ACOS (low ROAS)
        #----------------------------------------------
        mask_opt3 = (
            (optimized_df['ROAS'] < 3) &     # Return on ad spend less than 3x
            (optimized_df['Orders'] > 0)      # Has generated orders
        )

        # Different bid reductions based on spend
        mask_opt3_high = mask_opt3 & (optimized_df['Spend'] > 20)
        mask_opt3_medium = mask_opt3 & (optimized_df['Spend'] >= 5) & (optimized_df['Spend'] <= 20)
        mask_opt3_low = mask_opt3 & (optimized_df['Spend'] < 5)

        # Apply bid reductions
        optimized_df.loc[mask_opt3_high, 'New Bid'] = optimized_df.loc[mask_opt3_high, 'Bid'] - 0.15    # Reduce by 15 cents
        optimized_df.loc[mask_opt3_medium, 'New Bid'] = optimized_df.loc[mask_opt3_medium, 'Bid'] - 0.10 # Reduce by 10 cents
        optimized_df.loc[mask_opt3_low, 'New Bid'] = optimized_df.loc[mask_opt3_low, 'Bid'] - 0.07      # Reduce by 7 cents

        # Add explanations
        optimized_df.loc[mask_opt3, 'Why'] = 'High ACOS but Overspending'
        optimized_df.loc[mask_opt3, 'Goal'] = 'To Decrease Acos'
        optimized_df.loc[mask_opt3_high, 'How much'] = 'Decreased bids by 0.15 cents'
        optimized_df.loc[mask_opt3_medium, 'How much'] = 'Decreased bids by 0.10 cents'
        optimized_df.loc[mask_opt3, 'Increase or decrease'] = 'Decrease'

        # FILTER 3: High performing keywords
        #----------------------------------------------
        mask_opt4 = (
            (optimized_df['ROAS'] > 4) &     # Good return on ad spend
            (optimized_df['Orders'] > 1) &    # Multiple orders
            (optimized_df['Clicks'] > 10)     # Good number of clicks
        )

        # Different increases based on sales volume
        mask_opt4_high = mask_opt4 & (optimized_df['Sales'] >= 100)                                     # High sales: $100+
        mask_opt4_medium = mask_opt4 & (optimized_df['Sales'] >= 50) & (optimized_df['Sales'] < 100)    # Medium sales: $50-$100
        mask_opt4_low = mask_opt4 & (optimized_df['Sales'] >= 30) & (optimized_df['Sales'] < 50)        # Lower sales: $30-$50
        mask_opt4_low1 = mask_opt4 & (optimized_df['Sales'] < 30)                                       # Lowest sales: under $30

        # Apply bid increases
        optimized_df.loc[mask_opt4_high, 'New Bid'] = optimized_df.loc[mask_opt4_high, 'Bid'] + 0.15    # Increase by 15 cents
        optimized_df.loc[mask_opt4_medium, 'New Bid'] = optimized_df.loc[mask_opt4_medium, 'Bid'] + 0.12 # Increase by 12 cents
        optimized_df.loc[mask_opt4_low, 'New Bid'] = optimized_df.loc[mask_opt4_low, 'Bid'] + 0.10      # Increase by 10 cents
        optimized_df.loc[mask_opt4_low1, 'New Bid'] = optimized_df.loc[mask_opt4_low1, 'Bid'] + 0.07    # Increase by 7 cents

        # Add explanations
        optimized_df.loc[mask_opt4, 'Why'] = 'ROAS > 4, Orders > 1, Clicks > 10'
        optimized_df.loc[mask_opt4, 'Goal'] = 'To Increase Sales'
        optimized_df.loc[mask_opt4_high, 'How much'] = 'Increased bids by 0.15 cents'
        optimized_df.loc[mask_opt4_medium, 'How much'] = 'Increased bids by 0.12 cents'
        optimized_df.loc[mask_opt4_low, 'How much'] = 'Increased bids by 0.10 cents'
        optimized_df.loc[mask_opt4_low1, 'How much'] = 'Increased bids by 0.07 cents'
        optimized_df.loc[mask_opt4, 'Increase or decrease'] = 'Increase'

        # FILTER 4: Keywords with good ROAS but not captured in Filter 3
        #----------------------------------------------
        mask_opt5 = (
            (optimized_df['ROAS'] >= 3) &    # Good return on ad spend
            ~mask_opt4                        # Not already caught by Filter 3
        )

        # Different increases based on sales volume
        mask_opt5_high = mask_opt5 & (optimized_df['Sales'] >= 100)
        mask_opt5_medium = mask_opt5 & (optimized_df['Sales'] >= 50) & (optimized_df['Sales'] < 100)
        mask_opt5_low = mask_opt5 & (optimized_df['Sales'] >= 30) & (optimized_df['Sales'] < 50)
        mask_opt5_low1 = mask_opt5 & (optimized_df['Sales'] < 30)

        # Apply bid increases
        optimized_df.loc[mask_opt5_high, 'New Bid'] = optimized_df.loc[mask_opt5_high, 'Bid'] + 0.12
        optimized_df.loc[mask_opt5_medium, 'New Bid'] = optimized_df.loc[mask_opt5_medium, 'Bid'] + 0.10
        optimized_df.loc[mask_opt5_low, 'New Bid'] = optimized_df.loc[mask_opt5_low, 'Bid'] + 0.08
        optimized_df.loc[mask_opt5_low1, 'New Bid'] = optimized_df.loc[mask_opt5_low1, 'Bid'] + 0.05

        # Add explanations
        optimized_df.loc[mask_opt5, 'Why'] = 'ROAS > 3 (Low ACOS)'
        optimized_df.loc[mask_opt5, 'Goal'] = 'To Increase Sales'
        optimized_df.loc[mask_opt5_high, 'How much'] = 'Increased bids by 0.12 cents'
        optimized_df.loc[mask_opt5_medium, 'How much'] = 'Increased bids by 0.10 cents'
        optimized_df.loc[mask_opt5_low, 'How much'] = 'Increased bids by 0.08 cents'
        optimized_df.loc[mask_opt5_low1, 'How much'] = 'Increased bids by 0.05 cents'
        optimized_df.loc[mask_opt5, 'Increase or decrease'] = 'Increase'

        # FILTER 5: Keywords with no spend
        #----------------------------------------------
        mask_opt6 = (optimized_df['Spend'] == 0)

        # Split between those with impressions and those without
        mask_opt6_impressions = mask_opt6 & (optimized_df['Impressions'] > 0)     # No spend but some impressions
        mask_opt6_noimpressions = mask_opt6 & (optimized_df['Impressions'] == 0)  # No spend and no impressions

        # Apply small bid increases
        optimized_df.loc[mask_opt6_impressions, 'New Bid'] = optimized_df.loc[mask_opt6_impressions, 'Bid'] + 0.02
        optimized_df.loc[mask_opt6_noimpressions, 'New Bid'] = optimized_df.loc[mask_opt6_noimpressions, 'Bid'] + 0.03

        # Add explanations
        optimized_df.loc[mask_opt6_impressions, 'Why'] = 'No Spend but have Impressions'
        optimized_df.loc[mask_opt6_noimpressions, 'Why'] = 'No Spend and No Impressions'
        optimized_df.loc[mask_opt6, 'Goal'] = 'To Increase Sales'
        optimized_df.loc[mask_opt6_impressions, 'How much'] = 'Increased bids by 0.02 cents'
        optimized_df.loc[mask_opt6_noimpressions, 'How much'] = 'Increased bids by 0.03 cents'
        optimized_df.loc[mask_opt6, 'Increase or decrease'] = 'Increase'

        # Step 6: Apply Safety Limits and Format Results
        #----------------------------------------------

        # Make sure all new bids stay within Amazon's allowed range
        # No bid can be lower than $0.02 or higher than $5.00
        optimized_df['New Bid'] = optimized_df['New Bid'].clip(lower=0.02, upper=5.00)

        # Calculate how much each bid changed
        optimized_df['Changes'] = optimized_df['New Bid'] - optimized_df['Bid']
        optimized_df['% changes'] = ((optimized_df['New Bid'] / optimized_df['Bid']) - 1) * 100

        # Step 7: Format Numbers for Better Readability
        #----------------------------------------------

        optimized_df['Spend%'] = optimized_df['Spend%'].round(2).apply(lambda x: f"{x}%")
        optimized_df['Sale%'] = optimized_df['Sale%'].round(2).apply(lambda x: f"{x}%")
        optimized_df['Changes'] = optimized_df['Changes'].round(2).apply(lambda x: f"${x:+.2f}")
        optimized_df['% changes'] = optimized_df['% changes'].round(2).apply(lambda x: f"{x:+.2f}%")

        # Step 8: Organize Columns in a Logical Order
        #----------------------------------------------

        columns = list(optimized_df.columns)
        bid_index = columns.index('Bid')
        new_bid_index = columns.index('New Bid')
        columns.pop(new_bid_index)
        columns.insert(bid_index + 1, 'New Bid')
        optimized_df = optimized_df[columns]

        return optimized_df

    except FileNotFoundError:
        print("Error: Input file not found. Please check the file path and ensure the file exists.")
        return None
    except ValueError as ve:
        print(f"An error occurred: {str(ve)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during script execution: {str(e)}")
        return None


def generate_ppc_manager_pdf(output_csv_filename, pdf_output_filename):
    """
    Generates a PDF instruction file for PPC managers, explaining the output CSV file.
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)

        pdf_content = """Amazon Sponsored Products Bid Optimizer - Actionable Guide for PPC Managers

        Congratulations! You've used the Bid Optimizer to get data-driven bid suggestions. Now, let's turn those suggestions into real results for your Amazon campaigns!

        This guide is designed to help PPC managers like you quickly understand and implement the recommendations from the `youroutput_file.csv` output file.

        1. Understanding Your Output File (`youroutput_file.csv`) - Your Action Plan

        After running the Bid Optimizer script, you've generated `youroutput_file.csv`. This file is your action plan for bid optimization!  Open this file in a spreadsheet program like Excel or Google Sheets.

        Key Columns to Focus On:

        *   "New Bid" Column - Your Suggested Bids: This column contains the most important information for you. It shows the script's recommended new bid for each keyword and product target in your Amazon campaigns.  This is what you will be implementing in Amazon.

        *   "Increase or decrease" Column - Direction of Change:  This column simply indicates whether the script is suggesting an "Increase" or "Decrease" in your current bid.

        *   "Why" Column - Reason for Suggestion - Understand the Logic:  This is crucial for informed decision-making!  The "Why" column explains the reason behind each bid change suggestion.  Understanding the "Why" helps you evaluate if the suggestion makes sense for your specific campaign goals and strategy.  Common reasons you'll see:

            *   "Cost but No Revenue":  Keywords costing money (Spend) but not generating sales.  *Action: The script suggests lowering bids to reduce wasted spend.*
            *   "High ACOS but Overspending": Keywords making sales, but at an inefficient cost (high ACOS, low ROAS). *Action: The script suggests lowering bids to improve profitability.*
            *   "ROAS > 4, Orders > 1, Clicks > 10": High-performing keywords with excellent ROAS, orders, and clicks. *Action: The script suggests increasing bids to capture more sales volume.*
            *   "ROAS > 3 (Low ACOS)": Keywords performing well with good ROAS, but potentially with room for growth. *Action: The script suggests a moderate bid increase to explore further potential.*
            *   "No Spend but have Impressions" / "No Spend and No Impressions": Keywords that haven't spent money yet. *Action: The script suggests a small bid increase to test their performance.*

        *   "Goal" Column - Optimization Objective:  States the overall objective behind the bid change, such as "To Decrease Acos" or "To Increase Sales."

        *   "How much" Column - Magnitude of Change:  Indicates the amount of the bid change in cents.

        2. Implementing Bid Changes in Amazon - Applying Your Action Plan

        Now that you understand the output file, let's apply the suggested bid changes in Amazon Advertising:

        *   Review `youroutput_file.csv` First! Before uploading, carefully review the "New Bid" column and the "Why" explanations.  Ask yourself:
            *   Do these suggestions make sense for my campaigns and current strategy?
            *   Are there any specific keywords or targets where I disagree with the suggestion based on my expert knowledge (e.g., ongoing promotions, inventory constraints, competitor actions)?

        *   Manually Adjust "New Bids" in the CSV (If Needed):  If you disagree with any "New Bid" suggestion, you can directly edit the "New Bid" value in the `youroutput_file.csv` file using your spreadsheet program. Your judgment is always the final step!

        *   Save the Modified `youroutput_file.csv`:  After reviewing and making any manual adjustments, save the CSV file.

        *   Upload to Amazon Bulksheets:
            1.  Go to your Amazon Advertising Dashboard.
            2.  Navigate to the "Bulksheets" section.
            3.  Start the "Upload bulksheet" process.
            4.  Upload your `youroutput_file.csv` file.
            5.  Follow Amazon's on-screen instructions to complete the upload and apply the bid changes.

        3. When to Implement Bid Changes - Timing is Key

        *   Implement Changes Promptly After Review: Once you've reviewed and are satisfied with the `youroutput_file.csv`, upload it to Amazon to apply the bid changes.  The sooner you implement, the sooner you can start seeing potential improvements.
        *   Avoid Overly Frequent Changes:  Resist the urge to re-run the script and upload new bid changes too frequently (e.g., daily).  Amazon's advertising data needs time to reflect the impact of bid changes.  A good cadence is typically weekly or bi-weekly. This allows enough data to accumulate for the script to make informed decisions.

        4. Tracking Performance After Bid Changes - Measure Your Success

        After implementing the bid changes, monitoring your campaign performance is crucial to see if the optimization is working and to guide future adjustments.

        Key Metrics to Track (PPC Manager Focus):

        *   ROAS (Return on Ad Spend) & ACOS (Advertising Cost of Sales): Your primary profitability metrics!  Are these improving? Aim for higher ROAS and lower ACOS over time.
        *   Sales & Revenue: Are your sales and revenue from Sponsored Products campaigns increasing or at least stable at a profitable level?
        *   Impressions:  Are you maintaining or increasing your ad visibility (impressions)?  A significant drop in impressions could indicate bids are now too low.
        *   Clicks: Are you getting sufficient traffic to your product pages (clicks)? A drop in clicks might also indicate bids are too low.
        *   Conversion Rate: Is your conversion rate (percentage of clicks that turn into sales) being maintained or improving?
        *   Spend:  Are you staying within your advertising budget? Is your spend being used efficiently?

        How to Track Performance in Amazon Ads:

        *   Amazon Advertising Dashboard (Campaign Manager):  You can monitor campaign performance directly in the Amazon Advertising Campaign Manager. Look at the "Performance Summary" and campaign-level metrics over time.
        *   Amazon Advertising Reports:  For more detailed analysis, use Amazon Advertising reports. You can generate performance reports (e.g., Campaign Performance Reports, Search Term Reports) to track metrics over specific time periods.

        Monitoring Frequency:

        *   Initial Days (Daily): For the first few days after implementing bid changes, check your key metrics daily to quickly identify any immediate negative impacts or unexpected results.
        *   Weekly Monitoring: After the initial days, switch to weekly monitoring. Track your metrics week-over-week to see the longer-term trends and impact of the bid optimizations.

        5. Interpreting Results & Iteration - Continuous Improvement

        *   Signs of Success (Positive Outcomes):
            *   Improved ROAS and/or Lower ACOS: Your ads are becoming more profitable!
            *   Stable or Increasing Sales with Improved Profitability: You are driving sales efficiently.
            *   Healthy Impression and Click Volume: You are maintaining good ad visibility and traffic.

        *   Signs of Potential Issues (Negative Outcomes):
            *   Worsening ROAS and/or Higher ACOS: Your ad profitability is declining. You may need to re-evaluate your bid strategy or filter settings.
            *   Sales Decline: Sales are decreasing significantly after bid changes. Bids might be too low, limiting visibility.
            *   Significant Drop in Impressions and/or Clicks: Your ads are not being shown enough. Bids might be too low to compete in auctions.
            *   Budget Overspending or Underspending: Are you hitting your budget limits too quickly or not spending your budget effectively?

        *   Bid Optimization is an Iterative Process!  The first run of the script is just the beginning.  Based on your performance monitoring, you will likely need to:
            *   Re-run the script regularly with updated Amazon data (weekly or bi-weekly).
            *   Fine-tune the filters and bid adjustment settings in the `bid_optimizer.py` code over time to optimize for your specific campaign goals and market conditions.
            *   Continuously Learn and Adapt:  Amazon's advertising landscape is dynamic.  Stay informed about changes and be prepared to adjust your strategies and the script's settings as needed."""

        pdf.multi_cell(0, 5, text=pdf_content)

        pdf.output(pdf_output_filename)
        print(f"PDF instruction file saved to: {pdf_output_filename}")
    except Exception as e:
        print(f"Error generating PDF instruction file: {str(e)}")


def main():
    """
    Main function that runs the entire bid optimization process and saves both CSV and PDF outputs.
    """
    try:
        input_file = r'yourinput_file.csv'
        result_df = optimize_bids(input_file)

        if result_df is not None:
            output_file = r'youroutput_file.csv'
            result_df.to_csv(output_file, index=False)
            print(f"Successfully processed the data!")
            print(f"Output file saved to: {output_file}")

            #  Generate PDF instruction file after successful CSV output 
            pdf_output_file = r'ppc_manager_guide.pdf'
            generate_ppc_manager_pdf(output_file, pdf_output_file)

        else:
            print("Data processing failed. Please check the error messages above.")

    except FileNotFoundError:
        print("Error: Input file not found. Please check the file path and ensure the file exists.")
    except ValueError as ve:
        print(f"An error occurred: {str(ve)}")
    except Exception as e:
        print(f"A critical error occurred in the main function: {str(e)}")


if __name__ == "__main__":
    main()