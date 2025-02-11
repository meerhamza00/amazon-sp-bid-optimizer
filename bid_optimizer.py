# Amazon Sponsored Products Bid Optimizer
# This script helps optimize bids for Amazon advertising campaigns
# It reads campaign data from a CSV file and does bid adjustments based on filters
# Some basic filters applied
# This script can be used for US ,UK AND EU.


import pandas as pd   # pandas is used for handling data in table format
import numpy as np    # numpy is used for numerical operations

def optimize_bids(input_file):
    """
    Main function to optimize Amazon Sponsored Products bids.
    Args:
        input_file (str): Path to the CSV file containing campaign data
    Returns:
        pandas.DataFrame: Optimized data with new bid recommendations
    """
    # Step 1: Load and prepare the data
    #-----------------------------------------
    
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(input_file, keep_default_na=False)
    
    # Make a copy of the data to work with (leaves original data unchanged)
    optimized_df = df.copy()
    
    # List of columns that should contain numbers
    numeric_columns = [
        'Bid',                                      # Current bid amount
        'Ad Group Default Bid (Informational only)', # Default bid for the ad group
        'Spend',                                    # Amount spent on advertising
        'Sales',                                    # Revenue generated
        'Orders',                                   # Number of orders received
        'Clicks',                                   # Number of clicks on the ad
        'ROAS',                                     # Return on Ad Spend
        'Impressions',                             # Number of times ad was shown
    ]

    # Step 2: Clean up the numeric data
    #-----------------------------------------
    
    # Convert all numeric columns to proper number format
    for col in numeric_columns:
        if col in optimized_df.columns:
            # Replace empty strings with '0'
            optimized_df[col] = optimized_df[col].replace('', '0')
            # Convert to numbers, replace any errors with 0
            optimized_df[col] = pd.to_numeric(optimized_df[col], errors='coerce').fillna(0)
    
    # If Bid is 0, use the Ad Group Default Bid instead
    mask = (optimized_df['Bid'] == 0)
    optimized_df.loc[mask, 'Bid'] = optimized_df.loc[mask, 'Ad Group Default Bid (Informational only)']
    
    # Step 3: Set up new columns for our analysis
    #-----------------------------------------
    
    optimized_df['New Bid'] = optimized_df['Bid']          # Will store our recommended bid
    optimized_df['Increase or decrease'] = ''              # Will show if we're increasing or decreasing
    optimized_df['Why'] = ''                              # Will explain reason for change
    optimized_df['Goal'] = ''                             # Will state our optimization goal
    optimized_df['How much'] = ''                         # Will show amount of change
    optimized_df['Operation'] = 'Update'                  # Always set to Update
    
    # Step 4: Calculate performance metrics
    #-----------------------------------------
    
    # Get total spend and sales across all keywords
    total_spend = optimized_df['Spend'].sum()
    total_sales = optimized_df['Sales'].sum()
    
    # Calculate what percentage each keyword represents of total spend
    if total_spend > 0:
        optimized_df['Spend%'] = (optimized_df['Spend'] / total_spend * 100).round(2)
    else:
        optimized_df['Spend%'] = 0
    
    # Calculate what percentage each keyword represents of total sales    
    if total_sales > 0:
        optimized_df['Sale%'] = (optimized_df['Sales'] / total_sales * 100).round(2)
    else:
        optimized_df['Sale%'] = 0
    
    # Find the correct column names in the CSV (they might vary slightly)
    campaign_name_col = next(col for col in optimized_df.columns if col.lower() == "campaign name (informational only)")
    portfolioname_col = next(col for col in optimized_df.columns if col.lower() == "portfolio name (informational only)")
    campaignstate_col = next(col for col in optimized_df.columns if col.lower() == "campaign state (informational only)")

    # Step 5: Apply Different Optimization Filters
    #-----------------------------------------
    
    # FILTER 1: Keywords that get clicks but no sales
    #----------------------------------------------
    # These keywords are costing money but not generating revenue
    mask_opt1 = (
        (optimized_df['Clicks'] > 0) &    # Has received clicks
        (optimized_df['Orders'] == 0)      # But no orders
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
    # These keywords are generating sales but at too high a cost
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
    optimized_df.loc[mask_opt3_low, 'How much'] = 'Decreased bids by 0.07 cents'
    optimized_df.loc[mask_opt3, 'Increase or decrease'] = 'Decrease'

    # FILTER 3: High performing keywords
    #----------------------------------------------
    # These keywords are performing very well and could benefit from higher bids
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
    # These keywords are performing well but don't meet all criteria of Filter 3
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
    # These keywords haven't spent any money yet
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
    optimized_df['Changes'] = optimized_df['New Bid'] - optimized_df['Bid']           # Dollar amount change
    optimized_df['% changes'] = ((optimized_df['New Bid'] / optimized_df['Bid']) - 1) * 100  # Percentage change
    
    # Step 7: Format Numbers for Better Readability
    #----------------------------------------------
    
    # Add % symbol to Spend% and Sale% columns
    # round(2) keeps 2 decimal places
    # f"{x}%" adds the % symbol to the number
    optimized_df['Spend%'] = optimized_df['Spend%'].round(2).apply(lambda x: f"{x}%")
    optimized_df['Sale%'] = optimized_df['Sale%'].round(2).apply(lambda x: f"{x}%")
    
    # Format the Changes column to show dollar signs and +/- signs
    # Example: +$0.10 for increases, -$0.05 for decreases
    optimized_df['Changes'] = optimized_df['Changes'].round(2).apply(lambda x: f"${x:+.2f}")
    
    # Format the % changes column to show +/- signs and % symbol
    # Example: +10.00% for increases, -5.00% for decreases
    optimized_df['% changes'] = optimized_df['% changes'].round(2).apply(lambda x: f"{x:+.2f}%")
    
    # Step 8: Organize Columns in a Logical Order
    #----------------------------------------------
    
    # Get list of all columns
    columns = list(optimized_df.columns)
    
    # Find where 'Bid' and 'New Bid' columns are currently located
    bid_index = columns.index('Bid')
    new_bid_index = columns.index('New Bid')
    
    # Remove 'New Bid' from its current position
    columns.pop(new_bid_index)
    
    # Insert 'New Bid' right after 'Bid' column
    columns.insert(bid_index + 1, 'New Bid')
    
    # Rearrange columns in the DataFrame
    optimized_df = optimized_df[columns]
    
    # Return the final optimized DataFrame
    return optimized_df

def main():
    """
    Main function that runs the entire optimization process.
    This handles loading the input file and saving the results.
    """
    try:
        # Define input file path
        # The 'r' prefix makes this a raw string, which is useful for Windows file paths
        input_file = r'yourinput_file.csv'   
        
        # Run the optimization function
        result_df = optimize_bids(input_file)
        
        # Define output file path
        output_file = r'youroutput_file.csv'
        
        # Save the results to a new CSV file
        # index=False prevents adding row numbers to the output
        result_df.to_csv(output_file, index=False)
        
        # Print success message
        print(f"Successfully processed the data!")
        print(f"Output file saved to: {output_file}")
        
    except FileNotFoundError:
        # This error occurs if the input file doesn't exist
        print("Error: Input file not found. Please check the file path.")
    except Exception as e:
        # This catches any other errors that might occur
        print(f"An error occurred: {str(e)}")

# This is the standard Python way to check if this file is being run directly
# (versus being imported as a module into another file)
if __name__ == "__main__":
    main()
