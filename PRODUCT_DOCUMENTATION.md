# Financial Analyzer - Product Documentation

## Overview

**Financial Analyzer** is a comprehensive multi-entity financial intelligence platform designed to help finance teams manage, analyze, and report on financial data across multiple companies or entities. The system allows you to upload financial data from Excel files, standardize account codes, track transactions across different currencies, and generate insightful reports and analytics.

---

## Getting Started

### Login Page

When you first access the system, you'll see the **Login Page**. This is where you enter your username and password to access the platform.

**Key Features:**
- **Connection Status Indicator**: Shows whether the system is connected to the backend server (green = connected, red = connection issue)
- **Secure Authentication**: Your credentials are securely verified before granting access
- **Welcome Screen**: Displays information about the platform's capabilities

After successful login, you'll be automatically redirected to the **Dashboard**.

---

## Top Navigation Bar

The top bar appears on every page once you're logged in and provides quick access to important features:

### 1. **Forex Rates Button**
- Click this button to view and manage foreign exchange rates
- View all currencies with their initial and latest exchange rates
- Add new currency rates or edit existing ones
- Essential for converting transactions from different currencies to USD

### 2. **Notifications Bell**
- Displays alerts and important system notifications
- Red dot indicates new notifications

### 3. **User Menu** (Profile Icon)
- **Profile**: Access your user profile settings
- **Settings**: Navigate to system settings
- **Logout**: Safely exit the system

---

## Sidebar Navigation

The left sidebar provides access to all main sections of the application:

1. **Dashboard** - Overview and analytics
2. **Entities** - Manage companies/organizations
3. **Upload Data** - Upload Excel files
4. **Structured Data** - View processed financial data
5. **Code Master** - Manage standardized account codes
6. **Reports** - Generate analytical reports
7. **Settings** - System configuration

---

## Page-by-Page Guide

### 1. Dashboard

The **Dashboard** is your main control center, providing a comprehensive overview of your financial data.

**What You'll See:**

**Key Performance Indicators (KPIs):**
- **Total Entities**: Number of companies/organizations in the system
- **Total Records**: Total number of financial transactions processed
- **Total Amount**: Sum of all transaction amounts (displayed in local currency and USD)
- **Coverage**: Percentage of data that has been properly mapped with standardized codes

**Visual Analytics:**
- **Entity-wise Totals**: Bar chart showing total amounts by entity
- **Year-on-Year Trend**: Line chart displaying financial performance across years
- **Monthly Run-Rate**: Area chart showing monthly transaction trends
- **Category Mix**: Pie chart breaking down transactions by category
- **P&L vs Balance Sheet**: Distribution between Profit & Loss and Balance Sheet items
- **Currency Mix**: Breakdown of transactions by currency
- **Year-over-Year Variance**: Comparison of financial performance between years
- **Month-over-Month Variance**: Comparison of monthly performance
- **Concentration Analysis**: Top 5 accounts by transaction amount

**Data Tables:**
- **Top Accounts**: List of accounts with highest transaction amounts, showing:
  - Account name (Particular)
  - Standardized code
  - Category and sub-category classifications
  - Total amount
- **Bottom Accounts**: Accounts with lowest transaction amounts

**Data Quality Section:**
- **Alerts**: System-generated warnings about data quality issues
- **FX Gaps**: List of currencies missing foreign exchange rates
- **Unmapped Particulars**: Accounts that haven't been assigned standardized codes yet

**Filter Options:**
- Filter by **Entity** (specific company or "All Entities")
- Filter by **Financial Year** (specific year or "All Years")
- **Refresh Button**: Reload the latest data

**Use Cases:**
- Get a quick overview of financial health across all entities
- Identify trends and patterns in financial data
- Spot data quality issues that need attention
- Compare performance across entities and time periods

---

### 2. Entities

The **Entities** page allows you to manage all the companies or organizations in your system.

**What You Can Do:**

**View All Entities:**
- See a complete list of all entities with:
  - Entity Code (short identifier)
  - Entity Name (full company name)
  - Local Currency (e.g., INR, USD, AED)
  - City and Country (if available)

**Add New Entity:**
- Click "Add New Entity" button
- Fill in the required information:
  - **Entity Name**: Full name of the company
  - **Entity Code**: Short code identifier (e.g., "RADSINC")
  - **Local Currency**: 3-letter currency code (e.g., "AED" for UAE Dirham)
  - **City** and **Country**: Optional location information

**Summary Cards:**
- **Total Entities**: Count of all entities in the system
- **Active Entities**: Number of entities with recent activity
- **Recent Updates**: Information about latest entity changes

**Use Cases:**
- Set up new companies before uploading their financial data
- View all entities in one place
- Ensure proper currency codes are assigned to each entity

---

### 3. Upload Data

The **Upload Data** page is where you import financial data from Excel files into the system.

**How to Upload:**

1. **Select Entity**: Choose which company/organization this data belongs to
2. **Enter Financial Year**: Type the financial year (e.g., 2024)
3. **Select Month**: Choose the month from the dropdown (April through March in fiscal order)
4. **Choose File**: 
   - Click the upload area or drag and drop your Excel file
   - Supported formats: .xlsx, .xls, or .csv
5. **Upload & Process**: Click the button to start the upload process

**During Upload:**
- Progress bar shows upload status
- System processes the file and validates data
- You'll see messages like "Uploading file..." and "Processing..."
- Final confirmation shows how many rows were processed and inserted

**What Happens After Upload:**
- The system automatically processes the Excel file
- Data is standardized and stored in the database
- Transactions are linked to the selected entity, month, and financial year
- You can then view this data in the "Structured Data" page

**Important Notes:**
- Make sure your Excel file follows the required format (see documentation)
- Each upload should be for a specific entity, month, and year combination
- The system will show warnings if there are any data quality issues

**Use Cases:**
- Import monthly financial statements
- Upload balance sheet data
- Add transaction-level detail from accounting systems
- Bulk import historical financial data

---

### 4. Structured Data

The **Structured Data** page displays all processed financial transactions in a detailed table format.

**What You'll See:**

**Summary Cards:**
- **Total Assets**: Sum of all asset values in the filtered data
- **Missing Rows**: Count of rows with incomplete or missing information

**Main Data Table:**
The table shows all financial records with columns such as:
- **Particular**: Account name or transaction description
- **Entity Name**: Which company the transaction belongs to
- **Local Currency Code**: Currency of the transaction
- **Standardized Code**: Mapped account code
- **Category 1-5**: Hierarchical classification of accounts
- **Month** and **Year**: Time period
- **Transaction Amount**: Amount in local currency
- **Avg Fx Rt**: Average foreign exchange rate used
- **Transaction Amount USD**: Amount converted to US Dollars

**Features:**

**Filtering:**
- Filter by **Entity** (specific company or all)
- Filter by **Financial Year** (specific year or all)
- **Column Filters**: Click on any column header to filter by specific values
- **Clear Filters**: Remove all active filters at once

**Data Quality Indicators:**
- Rows with missing data are highlighted in light red
- Hover over highlighted rows to see an "Add Data" button
- Click "Add Data" to fill in missing standardized codes or categories

**Add Missing Data:**
- When you click "Add Data" on a row, a dialog opens
- You can enter:
  - **Raw Particulars**: The account name as it appears
  - **Standardized Code**: Assign a standard code
  - **Category 1-5**: Classify the account into categories
- This information is saved to the Code Master and automatically updates all matching records

**Export to Excel:**
- Click "Export Excel" button to download the filtered data
- Useful for further analysis in Excel or sharing with stakeholders

**Column Management:**
- Hide columns you don't need by clicking the X button on column headers
- Drag and drop column headers to reorder them

**Use Cases:**
- Review all financial transactions in detail
- Identify and fix missing or incomplete data
- Export data for external reporting
- Verify that transactions are properly classified
- Check currency conversions are correct

---

### 5. Code Master

The **Code Master** is a reference library that maps account names (particulars) to standardized codes and categories.

**Purpose:**
When you upload financial data, account names might vary (e.g., "Bank Charges", "Banking Fees", "Bank Fee"). The Code Master creates a standard mapping so all similar accounts are classified consistently.

**What You'll See:**

**Code Master Table:**
- **ID**: Unique identifier for each code mapping
- **Raw Particulars**: The original account name as it appears in uploaded files
- **Standardized Code**: The standard code assigned to this account
- **Category 1-5**: Hierarchical classification levels

**Add New Code:**
1. Click "Add Code" button
2. Fill in the form:
   - **Raw Particulars** (Required): The account name you want to map
   - **Standardized Code** (Required): The standard code to assign
   - **Category 1-5** (Optional): Classification categories
3. The system provides autocomplete suggestions based on existing codes
4. You can type new values to create new codes or categories

**How It Works:**
- When you add a code mapping, the system automatically updates all matching records in Structured Data
- If the same "Raw Particulars" appears in future uploads, it will automatically get the standardized code and categories
- This ensures consistency across all your financial data

**Use Cases:**
- Standardize account names across different entities
- Create a consistent chart of accounts
- Map vendor-specific account names to standard codes
- Ensure proper categorization for reporting
- Maintain data quality and consistency

---

### 6. Reports

The **Reports** page provides advanced analytics and cross-entity comparisons.

**Report Configuration:**
- **Select Metric**: Choose what to analyze (e.g., Total Amount, Revenue, Expenses)
- **Period**: Select a financial year for the report
- **Report Type**: Currently supports "Cross-Entity Comparison"

**Comparison Results:**
When you generate a comparison report, you'll see:

**Summary Statistics:**
- **Entities**: Number of entities included
- **Total Amount**: Combined total across all entities
- **Total (USD)**: Combined total in US Dollars
- **Average**: Average amount per entity

**Comparison Table:**
Shows side-by-side comparison of:
- Entity Code and Name
- Total Amount (in local currency)
- Total Amount in USD
- Record Count (number of transactions)

**Red Flags & Alerts:**
The system automatically identifies potential issues:
- **Warnings**: Medium-priority alerts (yellow)
- **Errors**: High-priority issues (red)
- **Info**: Informational messages (blue)

Each alert shows:
- Which entity it relates to
- What the issue is
- The metric and value that triggered the alert

**Export Report:**
- Click "Export Report" to download the comparison data as a CSV file
- Useful for sharing with management or further analysis

**Use Cases:**
- Compare financial performance across multiple entities
- Identify entities that need attention
- Generate reports for management review
- Spot anomalies or outliers in financial data
- Prepare consolidated financial statements

---

### 7. Settings

The **Settings** page allows you to configure system preferences and defaults.

**General Settings:**
- **Company Information**: Set default company name
- **Default Currency**: Choose the primary currency (INR, USD, EUR)
- **Financial Year Start**: Set when your financial year begins (January, April, or July)

**User Management:**
- **Admin Users**: Users with full access to all features
- **Analyst Users**: Users who can view and analyze data
- **Viewer Users**: Users with read-only access
- **Add New User**: Create new user accounts

**Data Processing Configuration:**
- **Default Account Mapping**: Choose accounting standard (Indian GAAP, IFRS, or Custom)
- **Strict Validation**: Toggle to reject files with validation errors
- **Auto-process Uploads**: Automatically process files after upload
- **Overwrite Existing Data**: Replace data for duplicate periods

**Notification Preferences:**
- **Email Notifications**: Receive alerts via email
- **System Alerts**: Important system notifications
- **Processing Failures**: Alerts when file processing fails

**Use Cases:**
- Configure system defaults for your organization
- Manage user access and permissions
- Set up notification preferences
- Customize data processing rules

---

## Workflow Example

Here's a typical workflow for using the system:

1. **Set Up Entities**: Go to Entities page and add all companies you'll be managing
2. **Configure Codes**: Use Code Master to set up your standardized account codes
3. **Upload Data**: Upload Excel files for each entity, month, and year
4. **Review Data**: Check Structured Data page to verify uploads and fix any missing information
5. **Analyze**: Use Dashboard to see overview and trends
6. **Report**: Generate comparison reports in Reports page
7. **Maintain**: Periodically update Code Master as new account names appear

---

## Key Benefits

- **Multi-Entity Management**: Handle multiple companies from one platform
- **Data Standardization**: Consistent account codes across all entities
- **Currency Conversion**: Automatic conversion to USD using forex rates
- **Real-Time Analytics**: Instant insights and visualizations
- **Data Quality Tracking**: Identify and fix data issues proactively
- **Flexible Reporting**: Generate custom reports and comparisons
- **Excel Integration**: Easy import and export of data

---

## Support

For questions or issues, please contact your system administrator or refer to the technical documentation.

---

*This documentation is designed for business users. For technical implementation details, please refer to the developer documentation.*


