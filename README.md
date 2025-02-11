Amazon Sponsored Products Bid Optimizer

This guide will help you set up and use the bid optimization script for your Amazon Sponsored Products campaigns. Don't worry if you're new to coding - we'll go through this step by step!

 🚀 Getting Started

Step 1: Install Required Software

1. Download and install VSCode (Visual Studio Code):
   - Go to https://code.visualstudio.com/
   - Click the big blue "Download" button
   - Run the installer you downloaded
   - Follow the installation prompts (just click "Next" for default settings)

2. Install Python:
   - Go to https://www.python.org/downloads/
   - Click "Download Python" (get the latest version)
   - Run the installer
   - **Important**: Check the box that says "Add Python to PATH" during installation
   - Click Install Now

Step 2: Set Up Your Project

1. Create a new folder on your computer:
   - Right-click on your desktop or in your Documents folder
   - Select "New" → "Folder"
   - Name it "AmazonBidOptimizer"

2. Open VSCode and set up your workspace:
   - Open VSCode
   - Go to File → Open Folder
   - Select your "AmazonBidOptimizer" folder
   - Click "Select Folder"

3. Install required Python packages:
   - In VSCode, click View → Terminal or you can do it via CMD
   - In the terminal that appears, type these commands one at a time:
     
     pip install pandas
     pip install numpy
     

Step 3: Create Your Files

1. Create the Python script:
   - In VSCode, click the "New File" icon
   - Name it `bid_optimizer.py`
   - Copy and paste the provided code into this file

2. Prepare your input file:
   - Export your bulksheet(whatever date range u want)
   - Select Sponsored Products Campaigns  , and filter for Entity keyword and product targeting
   - Exclude whatever campaigns u dont want to optimize or do bid changes on , also exclude paused campaigns and paused keywords/targets
   - Copy this file into your "AmazonBidOptimizer" folder
   - Rename it to yourinput_file.csv ( make sure its csv or the code wont read it)

 📝 How to Use

1. Place your Amazon bulksheet CSV file in the same folder as the script
2. Update the input and output filenames in the code:
   - Find these lines in the code:
     input_file = r'yourinput_file.csv'
     output_file = r'youroutput_file.csv'
   - Change them to match your actual file names

3. Run the script:
   - In VSCode's terminal, type:
     python bid_optimizer.py

4. Output file
   It would create an output file , make sure u look into it what are the changes made , then remove those additional filters and upload it to Amazon
   Important note - New Bid after Bids is your calculated bid.
     

## 🔧 Customizing the Filters

The script uses different filters to adjust bids. Here's how to modify them:

### Current Filters:

1. No Revenue Filter (Decreases bids for keywords with clicks but no orders)
   # To change the spend thresholds:
   mask_opt1_high = mask_opt1 & (optimized_df['Spend'] > 20)     # Change 20 to your desired amount
   mask_opt1_medium = mask_opt1 & (optimized_df['Spend'] >= 5)   # Change 5 to your desired amount
   

2. High ACOS Filter(Decreases bids for high ACOS keywords)
   # To change the ROAS threshold:
   mask_opt3 = (optimized_df['ROAS'] < 3)   # Change 3 to your desired ROAS

3. High Performance Filter (Increases bids for well-performing keywords)
   # To change the criteria:
   mask_opt4 = (
       (optimized_df['ROAS'] > 4) &          # Change 4 to your desired ROAS
       (optimized_df['Orders'] > 1) &        # Change 1 to your desired order count
       (optimized_df['Clicks'] > 10)         # Change 10 to your desired click count
   )

 Adding New Filters

To add a new filter, copy this template and modify it:
# Create your filter condition
mask_new = (
    (optimized_df['YourMetric'] > YourValue) &
    (optimized_df['AnotherMetric'] < AnotherValue)
)
# Apply bid changes
optimized_df.loc[mask_new, 'New Bid'] = optimized_df.loc[mask_new, 'Bid'] + 0.10  # Add/subtract your amount
optimized_df.loc[mask_new, 'Why'] = 'Your reason for the change'
optimized_df.loc[mask_new, 'Goal'] = 'Your goal'
optimized_df.loc[mask_new, 'How much'] = 'Changed bids by X cents'
optimized_df.loc[mask_new, 'Increase or decrease'] = 'Increase or Decrease'


⚠️ Important Notes

- Always backup your data before running the script
- The script will not modify your Amazon campaign directly - it creates a new file
- Minimum bid is set to $0.02 and maximum to $5.00
- Make small changes first and monitor results

🆘 Need Help?

If you get an error:
1. Make sure your CSV file is in the same folder as the script
2. Check that the file names match exactly
3. Verify that all required columns exist in your CSV file
4. Make sure you've installed all required packages

📊 Required CSV Columns

Your input CSV must have these columns:
- Bid
- Ad Group Default Bid (Informational only)
- Spend
- Sales
- Orders
- Clicks
- ROAS
- Impressions

🔄 Updates and Maintenance

Remember to:
- Regularly update your input data
- Monitor the performance of bid changes
- Adjust thresholds based on your campaign's performance
- Keep Python and required packages updated
