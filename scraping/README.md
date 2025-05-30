# Danish residential house prices (1992-2024)

## About the dataset

The dataset contains approximately 1,5 million residential household sales from Denmark during the periode from 1992 to 2024. 

The dataset has been scraped and cleaned (to some extent). Cleaned files are located in: \Housing_data_cleaned \ named DKHousingprices_1 and 2. Saved in parquet format (and saved as two files due to size). Note some cleaning might still be nessesary, see notebook under code on Kaggle (https://www.kaggle.com/datasets/martinfrederiksen/danish-residential-housing-prices-1992-2024/code).

Cleaning from raw files to above cleaned files is outlined in BoligsalgConcatCleanigGit.ipynb. (done in Python version: 2.6.3)

Webscraping script: Webscrape_script.ipynb (done in Python version: 2.6.3)

Provided you want to clean raw files from scratch yourself:

Uncleaned scraped files (81 in total) are located in \Housing_data_raw \ Housing_data_batch1 and 2. Saved in .csv format and compressed as 7-zip files.

Additional files added/appended to the Cleaned files are located in \Addtional_data and named DK_inflation_rates, DK_interest_rates, DK_morgage_rates and DK_regions_zip_codes. Saved in .xlsx format.

## Content
Each row in the dataset contains a residential household sale during the period 1992 - 2024.

“Cleaned files” columns:

#### 0 'date': is the transaction date.

#### 1 'quarter': is the quarter based on a standard calendar year.

#### 2 'house_id': unique house id (could be dropped)

#### 3 'house_type': can be 'Villa', 'Farm', 'Summerhouse', 'Apartment', 'Townhouse'

#### 4 'sales_type': can be 'regular_sale', 'family_sale', 'other_sale', 'auction', '-' (“-“ could be dropped)

#### 5 'year_build': range 1000 to 2024 (could be narrowed more)

#### 6 'purchase_price': is purchase price in DKK

#### 7 '%_change_between_offer_and_purchase': could differ negatively, be zero or positive

#### 8 'no_rooms': number of rooms

#### 9 'sqm': number of square meters

#### 10 'sqm_price': 'purchase_price' divided by 'sqm_price'

#### 11 'address': is the address

#### 12 'zip_code': is the zip code

#### 13 'city': is the city

#### 14 'area': 'East & mid jutland', 'North jutland', 'Other islands', 'Capital, Copenhagen', 'South jutland', 'North Zealand', 'Fyn & islands', 'Bornholm'

#### 15 'region': 'Jutland', 'Zealand', 'Fyn & islands', 'Bornholm'

#### 16 'nom_interest_rate%': Danish nominal interest rate show pr. quarter however actual rate is not converted from annualized to quarterly

#### 17 'dk_ann_infl_rate%': Danish annual inflation rate show pr. quarter however actual rate is not converted from annualized to quarterly 

#### 18 'yield_on_mortgage_credit_bonds%': 30 year mortgage bond rate (without spread)

*************************************

## Uses

Various (statistical) analysis, visualisation and I assume machine learning as well. 

Practice exercises etc. 

Uncleaned scraped files are great to practice cleaning, especially string cleaning. I’m not an expect as seen in the coding ;-).

*************************************

## Disclaimer
The data and information in the data set provided here are intended to be used primarily for educational purposes only. I do not own any data, and all rights are reserved to the respective owners as outlined in “Acknowledgements/sources”. The accuracy of the dataset is not guaranteed accordingly any analysis and/or conclusions is solely at the user's own responsibly and accountability.

*************************************

## Acknowledgements/sources 

All data is publicly available on:

Boliga: https://www.boliga.dk/

Finans Danmark: https://finansdanmark.dk/

Danmarks Statistik: https://www.dst.dk/da

Statistikbanken: https://statistikbanken.dk/statbank5a/default.asp?w=2560

Macrotrends: https://www.macrotrends.net/

PostNord: https://www.postnord.dk/

World Data: https://www.worlddata.info/

*************************************

Have fun… :-)
