import pandas as pd
import ijson
import json
from datetime import datetime
from collections import defaultdict
import time
import os


def get_all_sales_for_bfe_numbers(input_json_path, target_bfe_numbers, output_path=None):
    """
    Extract all sales (current and historical) for specific BFE numbers
    """
    print(f"🔍 Searching for all sales of {len(target_bfe_numbers)} BFE numbers...")
    
    # Convert to set for faster lookup
    target_bfe_set = set(target_bfe_numbers)
    
    VALID_SALE_TYPES = {'Almindelig fri handel'}
    
    # Step 1: Find all valid transactions for our target BFE numbers
    print("-> Pass 1/2: Finding all transactions for target BFE numbers...")
    sales_lookup = {}
    bfe_transactions = defaultdict(list)  # Group transactions by BFE number
    
    with open(input_json_path, 'rb') as f:
        ejerskifte_items = ijson.items(f, 'EjerskifteList.item')
        for ejerskifte in ejerskifte_items:
            bfe_nummer = ejerskifte.get("bestemtFastEjendomBFENr")
            
            # Only process if this BFE number is in our target list
            if bfe_nummer in target_bfe_set:
                is_valid_status = ejerskifte.get("status") in {"gældende", "historisk"}
                is_not_conditional = not ejerskifte.get("betinget")
                is_normal_sale_type = ejerskifte.get("overdragelsesmaade") in VALID_SALE_TYPES
                
                sale_date = ejerskifte.get("anmeldelsesdato") or ejerskifte.get("overtagelsesdato")
                
                if is_valid_status and is_not_conditional and is_normal_sale_type and sale_date:
                    hid = ejerskifte.get("handelsoplysningerLokalId")
                    if hid:
                        transaction_info = {
                            "bfe_nummer": bfe_nummer,
                            "handelsoplysninger_id": hid,
                            "dato": sale_date
                        }
                        
                        sales_lookup[hid] = transaction_info
                        bfe_transactions[bfe_nummer].append(transaction_info)
    
    print(f"-> Found {len(sales_lookup)} valid transactions across {len(bfe_transactions)} properties")
    
    # Step 2: Get price information for all transactions
    print("-> Pass 2/2: Getting price information...")
    all_sales = []
    
    with open(input_json_path, 'rb') as f:
        handelsoplysninger_items = ijson.items(f, 'HandelsoplysningerList.item')
        for handel in handelsoplysninger_items:
            handel_id = handel.get('id_lokalId')
            if handel_id in sales_lookup:
                # Get the samlet price and rename it to købesum
                samlet_pris = handel.get("samletKoebesum")
                kontant_pris = handel.get("kontantKoebesum")
                
                has_valid_price = (samlet_pris is not None and samlet_pris > 0)
                
                if has_valid_price:
                    sale_info = sales_lookup[handel_id]
                    complete_sale = {
                        "bfe_nummer": sale_info["bfe_nummer"],
                        "købesum": samlet_pris,  # Rename samlet to købesum
                        "samlet_koebesum": samlet_pris,  # Keep original for reference
                        "kontant_koebesum": kontant_pris,
                        "loesoeresum": handel.get("loesoeresum"),
                        "dato": sale_info["dato"]
                    }
                    all_sales.append(complete_sale)
    
    print(f"-> Retrieved {len(all_sales)} complete sales records")
    
    # Save to file if specified
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_sales, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved all sales to: {output_path}")
    
    return all_sales

def create_comprehensive_dataframe(df_apartments_with_bfe, all_sales_data):
    """
    Create comprehensive DataFrame combining apartment info with all sales history
    """
    print("📊 Creating comprehensive DataFrame with apartment info and sales history...")
    
    # Convert all sales data to DataFrame
    df_all_sales = pd.DataFrame(all_sales_data)
    
    if df_all_sales.empty:
        print("❌ No sales data found!")
        return pd.DataFrame()
    
    # Debug: Check what columns we actually have
    print(f"-> Available columns in sales data: {list(df_all_sales.columns)}")
    
    # Make sure we have købesum column (create it if missing)
    if 'købesum' not in df_all_sales.columns:
        if 'samlet_koebesum' in df_all_sales.columns:
            df_all_sales['købesum'] = df_all_sales['samlet_koebesum']
            print("-> Created købesum from samlet_koebesum")
        elif 'kontant_koebesum' in df_all_sales.columns:
            df_all_sales['købesum'] = df_all_sales['kontant_koebesum']
            print("-> Created købesum from kontant_koebesum")
        else:
            print("❌ Neither købesum nor samlet_koebesum found in data!")
            return pd.DataFrame()
    
    # Fix datetime parsing with mixed timezones
    print("-> Converting dates...")
    df_all_sales['dato'] = pd.to_datetime(df_all_sales['dato'], utc=True)
    
    # Sort by BFE number and date
    df_all_sales = df_all_sales.sort_values(['bfe_nummer', 'dato'])
    
    # Add sequence number for each property (1 = oldest sale, highest = most recent)
    df_all_sales['sale_sequence'] = df_all_sales.groupby('bfe_nummer').cumcount() + 1
    df_all_sales['total_sales'] = df_all_sales.groupby('bfe_nummer')['bfe_nummer'].transform('count')
    
    # Mark the most recent sale for each property
    df_all_sales['is_most_recent'] = df_all_sales['sale_sequence'] == df_all_sales['total_sales']
    
    # Calculate price changes (using købesum as primary price)
    df_all_sales['prev_købesum'] = df_all_sales.groupby('bfe_nummer')['købesum'].shift(1)
    df_all_sales['price_change'] = df_all_sales['købesum'] - df_all_sales['prev_købesum']
    df_all_sales['price_change_pct'] = (df_all_sales['price_change'] / df_all_sales['prev_købesum']) * 100
    
    # Calculate years between sales
    df_all_sales['prev_sale_date'] = df_all_sales.groupby('bfe_nummer')['dato'].shift(1)
    df_all_sales['years_since_last_sale'] = (df_all_sales['dato'] - df_all_sales['prev_sale_date']).dt.days / 365.25
    
    print(f"✅ Created sales history with {len(df_all_sales)} total sales")
    
    # Fix the apartment data handling
    df_apartments = df_apartments_with_bfe.drop_duplicates(subset=['bfe_nummer'])
    
    print(f"📋 Apartment info shape: {df_apartments.shape}")
    
    # Merge sales history with apartment information
    df_comprehensive = df_all_sales.merge(
        df_apartments,
        on='bfe_nummer',
        how='left'
    )
    
    print(f"🏠 Comprehensive data shape: {df_comprehensive.shape}")
    print(f"🎯 Properties with apartment info: {df_comprehensive['addresse'].notna().sum()}")
    
    return df_comprehensive

def analyze_comprehensive_data(df_comprehensive):
    """
    Analyze the comprehensive dataset
    """
    print(f"\n📊 COMPREHENSIVE DATA ANALYSIS:")
    print(f"{'='*60}")
    
    # Overall statistics
    total_properties = df_comprehensive['bfe_nummer'].nunique()
    total_sales = len(df_comprehensive)
    properties_with_address = df_comprehensive['addresse'].notna().sum()
    
    print(f"Total unique properties: {total_properties:,}")
    print(f"Total sales transactions: {total_sales:,}")
    print(f"Properties with address info: {properties_with_address:,}")
    print(f"Average sales per property: {total_sales/total_properties:.1f}")
    
    # Properties with multiple sales
    multi_sale_props = df_comprehensive[df_comprehensive['total_sales'] > 1]['bfe_nummer'].nunique()
    print(f"Properties with multiple sales: {multi_sale_props:,} ({multi_sale_props/total_properties*100:.1f}%)")
    
    # Price change analysis
    price_changes = df_comprehensive[df_comprehensive['price_change'].notna()]
    if len(price_changes) > 0:
        print(f"\n💰 PRICE ANALYSIS ({len(price_changes)} repeat sales):")
        print(f"Average price change: {price_changes['price_change'].mean():,.0f} DKK")
        print(f"Median price change: {price_changes['price_change'].median():,.0f} DKK")
        print(f"Average price change %: {price_changes['price_change_pct'].mean():.1f}%")
        print(f"Median years between sales: {price_changes['years_since_last_sale'].median():.1f}")
    
    # Show apartment features analysis
    if 'Byggeår' in df_comprehensive.columns:
        print(f"\n🏠 APARTMENT FEATURES:")
        print(f"Building year range: {df_comprehensive['Byggeår'].min():.0f} - {df_comprehensive['Byggeår'].max():.0f}")
        print(f"Average size (m2): {df_comprehensive['m2'].mean():.1f}")
        print(f"Size range: {df_comprehensive['m2'].min():.0f} - {df_comprehensive['m2'].max():.0f} m2")
        print(f"Average rooms: {df_comprehensive['Vær.'].mean():.1f}")
        
        # Regional distribution
        print(f"\nRegional distribution:")
        print(df_comprehensive['region'].value_counts().head())
    
    # Show comprehensive sample with all key features
    print(f"\n📋 Sample of comprehensive data with apartment features:")
    sample_cols = [
        'bfe_nummer', 'addresse', 'postnummer', 'by', 'region',
        'Byggeår', 'm2', 'Vær.', 'btype', 
        'købesum', 'dato', 'sale_sequence', 'total_sales',
        'price_change', 'price_change_pct', 'years_since_last_sale', 'x', 'y'
    ]
    available_cols = [col for col in sample_cols if col in df_comprehensive.columns]
    
    # Show a few examples with all the rich apartment data
    sample_df = df_comprehensive[available_cols].head(10)
    
    # Format the display nicely
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 20)
    
    print(sample_df.to_string(index=False))
    
    # Show some interesting insights
    print(f"\n🎯 KEY INSIGHTS:")
    
    # Price per m2 analysis
    if 'm2' in df_comprehensive.columns:
        df_comprehensive['price_per_m2'] = df_comprehensive['købesum'] / df_comprehensive['m2']
        print(f"Average price per m2: {df_comprehensive['price_per_m2'].mean():,.0f} DKK")
        
        # Most expensive areas by price per m2
        if 'by' in df_comprehensive.columns:
            price_by_city = df_comprehensive.groupby('by')['price_per_m2'].mean().sort_values(ascending=False)
            print(f"\nTop 5 most expensive cities (price per m2):")
            for city, price in price_by_city.head().items():
                count = df_comprehensive[df_comprehensive['by'] == city]['bfe_nummer'].nunique()
                print(f"  {city}: {price:,.0f} DKK/m2 ({count} properties)")
    
    # Age vs price correlation
    if 'Byggeår' in df_comprehensive.columns:
        df_comprehensive['age'] = 2025 - df_comprehensive['Byggeår']
        age_price_corr = df_comprehensive[['age', 'købesum']].corr().iloc[0,1]
        print(f"\nAge vs Price correlation: {age_price_corr:.3f}")
        print(f"(Negative = newer buildings more expensive)")

    print(f"\n✅ Your dataset now includes:")
    print(f"   🏠 Full apartment details: address, postal code, city, region")
    print(f"   📏 Physical features: size (m2), rooms, building year")
    print(f"   📍 Location data: coordinates (x,y)")
    print(f"   💰 Complete sales history with price changes")
    print(f"   📈 Calculated metrics: price per m2, age, etc.")

def main():
    """
    Main function to create comprehensive apartment sales dataset
    """
    print("🏠 Creating comprehensive apartment sales dataset...")
    
    json_output_path = './all_apartment_sales_history.json'
    
    if not os.path.exists(json_output_path):
        print("📖 Loading apartment checkpoint data...")
        df_checkpoint = pd.read_csv('bfe_checkpoint_lejligheder.csv', index_col=0)
    
        # Filter to only apartments that have BFE numbers
        df_apartments_with_bfe = df_checkpoint[df_checkpoint['bfe_nummer'].notna()].copy()
        df_apartments_with_bfe['bfe_nummer'] = df_apartments_with_bfe['bfe_nummer'].astype(int)
        
        print(f"Total apartments in checkpoint: {len(df_checkpoint):,}")
        print(f"Apartments with BFE numbers: {len(df_apartments_with_bfe):,}")
        print(f"Success rate: {len(df_apartments_with_bfe)/len(df_checkpoint)*100:.1f}%")
        
        # Get unique BFE numbers
        unique_bfe_numbers = df_apartments_with_bfe['bfe_nummer'].unique().tolist()
        print(f"🎯 Will search for ALL sales of these {len(unique_bfe_numbers)} unique BFE numbers")
        
        # Extract all sales (current + historical) for these BFE numbers
        json_input_path = './test_tdyt_1__20250627184206.json'
        
        all_sales_data = get_all_sales_for_bfe_numbers(
            json_input_path, 
            unique_bfe_numbers,
            json_output_path
        )
        
        if not all_sales_data:
            print("❌ No sales data found!")
            return
        
        # Create comprehensive DataFrame
        df_comprehensive = create_comprehensive_dataframe(df_apartments_with_bfe, all_sales_data)
        
    else:
        print("📖 Loading existing sales data from JSON...")
        # Load the JSON file and recreate the comprehensive DataFrame
        with open(json_output_path, 'r', encoding='utf-8') as f:
            all_sales_data = json.load(f)
        
        # Still need apartment data for the comprehensive DataFrame
        df_checkpoint = pd.read_csv('bfe_checkpoint_lejligheder.csv', index_col=0)
        df_apartments_with_bfe = df_checkpoint[df_checkpoint['bfe_nummer'].notna()].copy()
        df_apartments_with_bfe['bfe_nummer'] = df_apartments_with_bfe['bfe_nummer'].astype(int)
        
        df_comprehensive = create_comprehensive_dataframe(df_apartments_with_bfe, all_sales_data)

    if df_comprehensive.empty:
        print("❌ Failed to create comprehensive DataFrame!")
        return
    
    # Save the comprehensive dataset as CSV
    output_csv = 'comprehensive_apartment_sales.csv'
    df_comprehensive.to_csv(output_csv, index=False)
    print(f"💾 Saved comprehensive apartment sales data to: {output_csv}")
    
    # Analyze the data
    analyze_comprehensive_data(df_comprehensive)
    
    print(f"\n✅ SUCCESS! You now have a complete dataset with:")
    print(f"   🏠 Apartment addresses, postal codes, etc. from checkpoint file")
    print(f"   📈 All historical sales for each apartment")
    print(f"   💰 Price changes between sales")
    print(f"   📅 Time intervals between sales")
    print(f"   🔢 Sale sequence numbers")

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"\n⏱️ Total execution time: {end_time - start_time:.2f} seconds")