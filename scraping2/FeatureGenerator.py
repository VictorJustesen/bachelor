import os
import pandas as pd
import numpy as np
import requests
from sklearn.neighbors import BallTree
from typing import Dict, Any, Optional

# --- Configuration ---
# It's recommended to load these from environment variables or a config file
DATA_FORDELER_USERNAME = os.environ.get("DATAFORDELER_USERNAME", "XEVPPQIYSU")
DATA_FORDELER_PASSWORD = os.environ.get("DATAFORDELER_PASSWORD", "Luffygear3!")

class FeatureGenerator:
    """
    A high-performance service to generate a rich feature vector for a Danish real estate property.

    This class is designed to be instantiated once at application startup. It pre-loads
    and pre-processes all necessary historical data to ensure low-latency feature
    generation for individual addresses on-demand.
    """

    def __init__(self, data_path: str):
        """
        Initializes the service by loading data and pre-computing indices.

        Args:
            data_path (str): The file path to the 'cleaned_data_with_bfe_coords.csv' dataset.
        """
        print("Initializing FeatureGenerator...")
        self.main_df = self._load_and_prepare_data(data_path)
        self.spatial_index = self._build_spatial_index()
        print("Initialization complete. Service is ready.")

    def _load_and_prepare_data(self, data_path: str) -> pd.DataFrame:
        """
        Loads the historical sales data from a CSV file into a pandas DataFrame,
        performing necessary type conversions and optimizations.
        """
        print(f"Loading data from {data_path}...")
        dtype_map = {
            'bfe_nummer': 'int64',
            'postnummer': 'int32',
            'Vær.': 'int16',
            'område_Bornholm': 'int8',
            'område_Fyn og øer': 'int8',
            '"område_Hovedstaden, København"': 'int8',
            'område_Nordjylland': 'int8',
            'område_Nordsjælland': 'int8',
            'område_Sydjylland': 'int8',
            'område_Øst- og Midtjylland': 'int8',
        }
        df = pd.read_csv(data_path, dtype=dtype_map, low_memory=False)
        # Filter for postnummer 2960 and date range
        df_filtered = df[
        (df['postnummer'] == 2960) & 
        (pd.to_datetime(df['dato']) >= '2024-01-01') & 
        (pd.to_datetime(df['dato']) <= '2025-08-18')
        ]

        print(f"Properties from postnummer 2960 sold between 2024-01-01 and 2025-08-18: {len(df_filtered)}")
        df['dato'] = pd.to_datetime(df['dato'])
        # The column name from the CSV has quotes, we rename it for easier access
        df.rename(columns={'\"område_Hovedstaden, København\"': 'område_Hovedstaden_København'}, inplace=True)
        # Assuming 'by' can be inferred from postnummer name if not present
        # This is a placeholder; in a real scenario, a proper city mapping would be needed.
       
        print("Data loaded and prepared.")
        return df

    def _build_spatial_index(self) -> BallTree:
        """
        Constructs a BallTree spatial index for efficient nearest-neighbor searches.
        The coordinates are converted to radians as required by the Haversine metric.
        """
        print("Building spatial index...")
        # Haversine metric requires coordinates in [latitude, longitude] order in radians
        coords_radians = np.radians(self.main_df[['y', 'x']].values)
        tree = BallTree(coords_radians, metric='haversine')
        print("Spatial index built successfully.")
        return tree

    def _get_dawa_data(self, full_address_query: str) -> Optional[Dict[str, Any]]:
        """
        Queries the Danmarks Adressers Web API (DAWA) to resolve an address string.

        Args:
            full_address_query (str): The address to search for.

        Returns:
            A dictionary containing key address information, or None if not found.
        """
        dawa_url = "https://api.dataforsyningen.dk/adresser"
        try:
            dawa_resp = requests.get(dawa_url, params={'q': full_address_query}, timeout=30)
            dawa_resp.raise_for_status()
            dawa_data = dawa_resp.json()

            if not dawa_data:
                print(f"DAWA API: No address found for query: {full_address_query}")
                return None

            address_info = dawa_data[0]
            adgangsadresse = address_info.get('adgangsadresse', {})

            coords = None
            # The coordinates are stored in a list: [x, y]
            coords_list = adgangsadresse.get('adgangspunkt', {}).get('koordinater')
            if coords_list and len(coords_list) == 2:
                coords = {'x': coords_list[0], 'y': coords_list[1]}
        
            
            return {
                'adresseId': address_info.get('id'),
                'husnummer_id': adgangsadresse.get('id'),
                'postnummer': int(adgangsadresse.get('postnummer', {}).get('nr')),
                'by': adgangsadresse.get('postnummer', {}).get('navn'),
               'x': coords['x'] if coords else None,
            'y': coords['y'] if coords else None
            }
        except requests.RequestException as e:
            print(f"Error calling DAWA API: {e}")
            return None
        
    def _get_bbr_data(self, address_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Gets building/unit data from BBR following the official API documentation.
        """
        # First try to get apartment/unit data if we have an address ID
        if address_info.get('adresseId'):
            unit_data = self._get_apartment_data(address_info['adresseId'])
            if unit_data:
                print(unit_data)
                return self._parse_unit_data(unit_data)
    
        # Fallback to building data using husnummer_id
        if address_info.get('husnummer_id'):
            building_data = self._get_building_data(address_info['husnummer_id'])
            if building_data:
                return self._parse_building_data(building_data)
    
        return None
    def _map_bbr_unit_to_btype(self, anvendelse_kode: str) -> str:
        return "Villa"
    def _get_apartment_data(self, apartment_id: str) -> Optional[Dict]:
        """
        Gets apartment/unit data using the same approach as your working code.
        """
        enhed_endpoint = "https://services.datafordeler.dk/BBR/BBRPublic/1/rest/enhed"
        params = {
            "AdresseIdentificerer": apartment_id,
            "username": DATA_FORDELER_USERNAME,
            "password": DATA_FORDELER_PASSWORD
        }
        
        try:
            response = requests.get(enhed_endpoint, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data[0] if isinstance(data, list) and data else data
        except requests.RequestException as e:
            print(f"Error getting apartment data: {e}")
        return None

    def _get_building_data(self, adgangsadresse_id: str) -> Optional[Dict]:
        """
        Gets building data using the same approach as your working code.
        """
        bygning_endpoint = "https://services.datafordeler.dk/BBR/BBRPublic/1/rest/bygning"
        params = {
            "Husnummer": adgangsadresse_id,
            "username": DATA_FORDELER_USERNAME,
            "password": DATA_FORDELER_PASSWORD
        }
        
        try:
            response = requests.get(bygning_endpoint, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data[0] if isinstance(data, list) and data else data
        except requests.RequestException as e:
            print(f"Error getting building data: {e}")
        return None

    def _parse_unit_data(self, unit_data: Dict) -> Dict[str, Any]:
        """
        Parses apartment/unit data from BBR response.
        """
        # Get unit area (apartment size)
        unit_areal = unit_data.get('EnhedAreal', {})
        m2_value = unit_areal.get('value') if isinstance(unit_areal, dict) else unit_areal
        
        # Get floor information
        etage = unit_data.get('enh031AntalVærelser', {})
        etage_value = etage.get('value', 1) if isinstance(etage, dict) else (etage or 1)
        
        # Get unit use code
        anvendelse = unit_data.get('EnhedAnvendelse', {})
        anvendelse_kode = anvendelse.get('kode') if isinstance(anvendelse, dict) else anvendelse
    
        return {
            'btype': self._map_bbr_unit_to_btype(anvendelse_kode),
            'm2': m2_value,
            'Vær.': etage_value,  # Floor number for apartments
            'byggeaar': unit_data.get('OpfoerelsesAar', {}).get('value') if isinstance(unit_data.get('OpfoerelsesAar', {}), dict) else unit_data.get('OpfoerelsesAar')
        }

    def _parse_building_data(self, building_data: Dict) -> Dict[str, Any]:
        """
        Parses building data from BBR response.
        """
        # Get total building area
        samlet_areal = building_data.get('SamletBygningsareal', {})
        m2_value = samlet_areal.get('value') if isinstance(samlet_areal, dict) else samlet_areal
    
        # Get number of floors
        antal_etager = building_data.get('AntalEtager', {})
        etager_value = antal_etager.get('value', 1) if isinstance(antal_etager, dict) else (antal_etager or 1)
        
        # Get building use code
        anvendelse = building_data.get('BygAnvendelse', {})
        anvendelse_kode = anvendelse.get('kode') if isinstance(anvendelse, dict) else anvendelse
    
        return {
            'btype': self._map_bbr_to_btype(anvendelse_kode),
            'm2': m2_value,
            'Vær.': etager_value,  # Number of floors for houses
            'byggeaar': building_data.get('OpfoerelsesAar', {}).get('value') if isinstance(building_data.get('OpfoerelsesAar', {}), dict) else building_data.get('OpfoerelsesAar')
        }
    
    def _get_bfe_number(self, address_info: Dict[str, Any]) -> Optional[int]:
        """
        Retrieves the BFE number using a try-fallback strategy for apartments vs. houses.

        Args:
            address_info: The dictionary returned by _get_dawa_data.

        Returns:
            The BFE number as an integer, or None if not found.
        """
        auth = (DATA_FORDELER_USERNAME, DATA_FORDELER_PASSWORD)
        
        # 1. Primary Attempt (for apartments/units)
        if address_info.get('adresseId'):
            unit_url = "https://services.datafordeler.dk/DAR/DAR_BFE_Public/1/rest/adresseTilEnhedBfe"
            params = {"adresseId": address_info['adresseId'], "username": DATA_FORDELER_USERNAME,
                "password": DATA_FORDELER_PASSWORD
            }
            try:
                resp = requests.get(unit_url, params=params,  timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"Unit API response: {data}")  # Debug print
                    
                    # Handle different response formats
                    if isinstance(data, list) and data:
                        # Response is a list of objects
                        first_item = data[0]
                        if isinstance(first_item, dict):
                            return first_item.get('bfeNummer')
                        elif isinstance(first_item, int):
                            return first_item
                    elif isinstance(data, int):
                        # Response is directly an integer
                        return data
                    elif isinstance(data, dict):
                        # Response is a single object
                        return data.get('bfeNummer')
            except requests.RequestException as e:
                print(f"API call to adresseTilEnhedBfe failed: {e}")

        # 2. Fallback (for houses/buildings)
        if address_info.get('husnummer_id'):
            building_url = "https://services.datafordeler.dk/DAR/DAR_BFE_Public/1/rest/husnummerTilBygningBfe"
            params = {"husnummerid": address_info['husnummer_id'], "username": DATA_FORDELER_USERNAME,
                "password": DATA_FORDELER_PASSWORD
            }
            try:
                resp = requests.get(building_url, params=params, timeout=30)
                if resp.status_code != 200:
                    return None
                
                building_data =resp.json()

                # 4. Extract BFE number from the correct location in response
                if building_data:
                    # Try to get BFE from jordstykkeList first
                    jordstykke_list = building_data.get('jordstykkeList', [])
                    if jordstykke_list and len(jordstykke_list) > 0:
                        bfe_number = jordstykke_list[0].get('samletFastEjendom')
                        if bfe_number:
                            return bfe_number
            except requests.RequestException as e:
                print(f"API call to husnummerTilBygningBfe failed: {e}")

        print("Could not retrieve BFE number for the address.")
        return None

    def _calculate_all_features(self, address_info: Dict[str, Any], bfe_nummer: int) -> Dict[str, Any]:
        """
        Modified to handle properties with no sales history.
        """
        features = {}

        # Get property history (might be empty)
        prop_history = self.main_df[self.main_df['bfe_nummer'] == bfe_nummer].sort_values('dato').copy()
        
        # Define cohorts (these work regardless of sales history)
        postnummer_cohort = self.main_df[self.main_df['postnummer'] == address_info['postnummer']].copy()
        by_cohort = self.main_df[self.main_df['by'] == address_info['by']].copy()

        # Calculate features (now handles empty prop_history)
        self._calculate_core_features(features, prop_history, address_info)
        self._calculate_benchmark_features(features, postnummer_cohort, by_cohort)
        self._calculate_geospatial_features(features, address_info)
        
        # Only calculate historical premiums if we have sales history
        if not prop_history.empty:
            self._calculate_historical_premiums(features, prop_history, postnummer_cohort, by_cohort)
        else:
            # Set premium features to 0 for new properties
            features.update({
                'historical_premium_vs_postnummer': 0,
                'historical_premium_vs_by': 0,
                'historical_premium_vs_postnummer_pct': 0,
                'historical_premium_vs_by_pct': 0,
                'historical_premium_vs_postnummer_btype': 0,
                'historical_premium_vs_postnummer_btype_pct': 0
            })
        
        self._calculate_synthesized_features(features)
        
        return features

    def _calculate_core_features(self, features: Dict, prop_history: pd.DataFrame, address_info: Dict):
        if prop_history.empty:
            print("No sales history found - using BBR data")
            
            # Get building characteristics from BBR
            bbr_data = self._get_bbr_data(address_info)
            
            features['dato'] = pd.Timestamp.now(tz='UTC')
            features.update({
                'købesum': None,
                'prev_købesum': None,  # No previous sale
                'Vær.': bbr_data.get('Vær.', 1) if bbr_data else 1,
                'm2': bbr_data.get('m2', 100) if bbr_data else 100,  # Default to 100m2 if unknown
                'btype': bbr_data.get('btype', 'Villa') if bbr_data else 'Villa',
                'days_since_last_sale': None,  # Never sold before
                'pris_pr_m2_prev': None,       # No previous price
                'pris_pr_m2_mean_postummer_prev': None,
                'pris_pr_m2_mean_postnummer_btype_prev': None
            })
            
        else:
            print("Using sales history")
            last_sale = prop_history.iloc[-1]
            features['dato'] = pd.Timestamp.now(tz='UTC')
            features.update({
                'købesum': None,
                'prev_købesum': last_sale.get('købesum'),
                'Vær.': last_sale.get('Vær.'),
                'm2': last_sale.get('m2'),
                'btype': last_sale.get('btype'),
                'days_since_last_sale': (features['dato'] - last_sale['dato']).days,
                'pris_pr_m2_prev': last_sale.get('pris_pr_m2'),
                'pris_pr_m2_mean_postummer_prev': last_sale.get('pris_pr_m2_mean_365D_postnummer'),
                'pris_pr_m2_mean_postnummer_btype_prev': last_sale.get('pris_pr_m2_mean_365D_postnummer_btype')
            })

            postnummer = address_info.get('postnummer', 0)
            region_features = self._get_region_from_postnummer(postnummer)
            features.update(region_features)
        

    def _get_region_from_postnummer(self, postnr: int) -> Dict[str, int]:
        """
        Maps postal code to one-hot encoded region features.
        Returns a dictionary with all region columns set to 0 or 1.
        """
        # Initialize all regions to 0
        regions = {
            'område_Bornholm': 0,
            'område_Fyn og øer': 0,
            'område_Hovedstaden_København': 0,  # Note: using underscore instead of comma
            'område_Nordjylland': 0,
            'område_Nordsjælland': 0,
            'område_Sydjylland': 0,
            'område_Øst- og Midtjylland': 0
        }
        
        # Map postal code to region
        if 0 <= postnr <= 999:
            # Special case - might not need a region for organizations
            pass
        elif 1000 <= postnr <= 2999:
            regions['område_Hovedstaden_København'] = 1
        elif 3000 <= postnr <= 3699:
            regions['område_Nordsjælland'] = 1
        elif 3700 <= postnr <= 3799:
            regions['område_Bornholm'] = 1
        elif 3800 <= postnr <= 3899:
            # Færøerne - not in your model, might default to no region
            pass
        elif 3900 <= postnr <= 3999:
            # Grønland - not in your model, might default to no region
            pass
        elif 4000 <= postnr <= 4999:
            # Andre øer - might map to a specific region or none
            pass
        elif 5000 <= postnr <= 5999:
            regions['område_Fyn og øer'] = 1
        elif 6000 <= postnr <= 6999:
            regions['område_Sydjylland'] = 1
        elif 7000 <= postnr <= 7999:
            regions['område_Sydjylland'] = 1
        elif 8000 <= postnr <= 8999:
            regions['område_Øst- og Midtjylland'] = 1
        elif 9000 <= postnr <= 9999:
            regions['område_Nordjylland'] = 1
        
        return regions

    def _calculate_benchmark_features(self, features: Dict, postnummer_cohort: pd.DataFrame, by_cohort: pd.DataFrame):
        if postnummer_cohort.empty:
            features['pris_pr_m2_mean_365D_postnummer'] = np.nan
            features['pris_pr_m2_mean_365D_by'] = np.nan
            features['pris_pr_m2_mean_365D_postnummer_btype'] = np.nan
            return

        # Use the same time filtering as geospatial features
        max_data_date = postnummer_cohort['dato'].max()
        one_year_back_from_max = max_data_date - pd.Timedelta(days=365)
        
        postnummer_cohort_recent = postnummer_cohort[postnummer_cohort['dato'] >= one_year_back_from_max]
        by_cohort_recent = by_cohort[by_cohort['dato'] >= one_year_back_from_max]

        # --- Calculate for Postnummer --- (simple mean like in notebook)
        if not postnummer_cohort_recent.empty:
            features['pris_pr_m2_mean_365D_postnummer'] = postnummer_cohort_recent['pris_pr_m2'].mean()
        else:
            features['pris_pr_m2_mean_365D_postnummer'] = np.nan

        # --- Calculate for By (City) --- (simple mean like in notebook)
        if not by_cohort_recent.empty:
            features['pris_pr_m2_mean_365D_by'] = by_cohort_recent['pris_pr_m2'].mean()
        else:
            features['pris_pr_m2_mean_365D_by'] = np.nan

        # --- Calculate for Btype-Specific --- (simple mean like in notebook)
        btype = features.get('btype')
        if btype and not postnummer_cohort_recent.empty:
            btype_cohort = postnummer_cohort_recent[postnummer_cohort_recent['btype'] == btype]
            if not btype_cohort.empty:
                features['pris_pr_m2_mean_365D_postnummer_btype'] = btype_cohort['pris_pr_m2'].mean()
            else:
                features['pris_pr_m2_mean_365D_postnummer_btype'] = np.nan
        else:
            features['pris_pr_m2_mean_365D_postnummer_btype'] = np.nan

        btype = features.get('btype')
        if btype and not by_cohort_recent.empty:
            btype_cohort = by_cohort_recent[by_cohort_recent['btype'] == btype]
            if not btype_cohort.empty:
                features['pris_pr_m2_mean_365D_by_btype'] = btype_cohort['pris_pr_m2'].mean()
            else:
                features['pris_pr_m2_mean_365D_by_btype'] = np.nan
        else:
            features['pris_pr_m2_mean_365D_by_btype'] = np.nan



     
    def _calculate_geospatial_features(self, features: Dict, address_info: Dict):
        target_coords_rad = np.radians([[address_info['y'], address_info['x']]])
        
        distances, indices = self.spatial_index.query(target_coords_rad, k=31)
        
        neighbor_indices = indices[0][1:]  # Exclude the property itself
        neighbors_df = self.main_df.iloc[neighbor_indices]

        # ADD ALL MISSING NEIGHBOR COUNT FEATURES:
        features['num_of_5_neighbors'] = min(5, len(neighbors_df))
        features['num_of_15_neighbors'] = min(15, len(neighbors_df))
        features['num_of_30_neighbors'] = len(neighbors_df)
        
        # Existing price per m2 features
        features['mean_of_5_neighbors_pris_pr_m2'] = neighbors_df.head(5)['pris_pr_m2'].mean()
        features['mean_of_15_neighbors_pris_pr_m2'] = neighbors_df.head(15)['pris_pr_m2'].mean()  # ADD THIS
        features['mean_of_30_neighbors_pris_pr_m2'] = neighbors_df['pris_pr_m2'].mean()
        
        # Actual price features
        neighbors_5 = neighbors_df.head(5)
        neighbors_15 = neighbors_df.head(15)  # ADD THIS
        neighbors_30 = neighbors_df
        
        neighbors_5_prices = neighbors_5['pris_pr_m2'] * neighbors_5['m2']
        neighbors_15_prices = neighbors_15['pris_pr_m2'] * neighbors_15['m2']  # ADD THIS
        neighbors_30_prices = neighbors_30['pris_pr_m2'] * neighbors_30['m2']
        
        features['mean_of_5_neighbors_pris'] = neighbors_5_prices.mean()
        features['mean_of_15_neighbors_pris'] = neighbors_15_prices.mean()  # ADD THIS
        features['mean_of_30_neighbors_pris'] = neighbors_30_prices.mean()
        
        # Same building type neighbor features
        if 'btype' in features and features['btype']:
            target_btype = features['btype']
            samebtype_neighbors_5 = neighbors_5[neighbors_5['btype'] == target_btype]
            samebtype_neighbors_15 = neighbors_15[neighbors_15['btype'] == target_btype]  # ADD THIS
            samebtype_neighbors_30 = neighbors_30[neighbors_30['btype'] == target_btype]
            
            # ADD MISSING SAME-TYPE NEIGHBOR COUNTS:
            features['num_of_5_samebtype_neighbors'] = len(samebtype_neighbors_5)
            features['num_of_15_samebtype_neighbors'] = len(samebtype_neighbors_15)  # ADD THIS
            features['num_of_30_samebtype_neighbors'] = len(samebtype_neighbors_30)
            
            # ADD MISSING 15-neighbor same-type features:
            if not samebtype_neighbors_15.empty:
                features['mean_of_15_samebtype_neighbors_pris_pr_m2'] = samebtype_neighbors_15['pris_pr_m2'].mean()
                samebtype_15_prices = samebtype_neighbors_15['pris_pr_m2'] * samebtype_neighbors_15['m2']
                features['mean_of_15_samebtype_neighbors_pris'] = samebtype_15_prices.mean()
            else:
                features['mean_of_15_samebtype_neighbors_pris_pr_m2'] = np.nan
                features['mean_of_15_samebtype_neighbors_pris'] = np.nan
            
            # Existing 5 and 30 neighbor features...
            if not samebtype_neighbors_5.empty:
                features['mean_of_5_samebtype_neighbors_pris_pr_m2'] = samebtype_neighbors_5['pris_pr_m2'].mean()
                samebtype_5_prices = samebtype_neighbors_5['pris_pr_m2'] * samebtype_neighbors_5['m2']
                features['mean_of_5_samebtype_neighbors_pris'] = samebtype_5_prices.mean()
            else:
                features['mean_of_5_samebtype_neighbors_pris_pr_m2'] = np.nan
                features['mean_of_5_samebtype_neighbors_pris'] = np.nan
                
            if not samebtype_neighbors_30.empty:
                features['mean_of_30_samebtype_neighbors_pris_pr_m2'] = samebtype_neighbors_30['pris_pr_m2'].mean()
                samebtype_30_prices = samebtype_neighbors_30['pris_pr_m2'] * samebtype_neighbors_30['m2']
                features['mean_of_30_samebtype_neighbors_pris'] = samebtype_30_prices.mean()
            else:
                features['mean_of_30_samebtype_neighbors_pris_pr_m2'] = np.nan
                features['mean_of_30_samebtype_neighbors_pris'] = np.nan
        else:
            # Set all same-type features to NaN if no building type
            for k in [5, 15, 30]:
                features[f'num_of_{k}_samebtype_neighbors'] = 0
                features[f'mean_of_{k}_samebtype_neighbors_pris_pr_m2'] = np.nan
                features[f'mean_of_{k}_samebtype_neighbors_pris'] = np.nan

    def _calculate_historical_premiums(self, features: Dict, prop_history: pd.DataFrame, postnummer_cohort: pd.DataFrame, by_cohort: pd.DataFrame):
        post_rolling_mean = postnummer_cohort.sort_values('dato').set_index('dato')['pris_pr_m2'].rolling('365D', min_periods=30).mean()
        by_rolling_mean = by_cohort.sort_values('dato').set_index('dato')['pris_pr_m2'].rolling('365D', min_periods=30).mean()

        premiums_post = []
        premiums_by = []

        for _, sale in prop_history.iterrows():
            sale_price_m2 = sale['pris_pr_m2']
            sale_date = sale['dato']

            benchmark_post = post_rolling_mean.asof(sale_date)
            if pd.notna(benchmark_post) and benchmark_post > 0:
                premiums_post.append(sale_price_m2 - benchmark_post)

            benchmark_by = by_rolling_mean.asof(sale_date)
            if pd.notna(benchmark_by) and benchmark_by > 0:
                premiums_by.append(sale_price_m2 - benchmark_by)

        features['historical_premium_vs_postnummer'] = np.mean(premiums_post) if premiums_post else 0
        features['historical_premium_vs_by'] = np.mean(premiums_by) if premiums_by else 0
        
        premiums_post_pct = []
        premiums_by_pct = []
        for _, sale in prop_history.iterrows():
            sale_price_m2 = sale['pris_pr_m2']
            sale_date = sale['dato']
            benchmark_post = post_rolling_mean.asof(sale_date)
            if pd.notna(benchmark_post) and benchmark_post > 0:
                premiums_post_pct.append((sale_price_m2 - benchmark_post) / benchmark_post)
            benchmark_by = by_rolling_mean.asof(sale_date)
            if pd.notna(benchmark_by) and benchmark_by > 0:
                premiums_by_pct.append((sale_price_m2 - benchmark_by) / benchmark_by)

        features['historical_premium_vs_postnummer_pct'] = np.mean(premiums_post_pct) * 100 if premiums_post_pct else 0
        features['historical_premium_vs_by_pct'] = np.mean(premiums_by_pct) * 100 if premiums_by_pct else 0
        btype = features.get('btype')
        if btype and not postnummer_cohort.empty:
            btype_cohort = postnummer_cohort[postnummer_cohort['btype'] == btype]
            if not btype_cohort.empty:
                btype_rolling_mean = btype_cohort.sort_values('dato').set_index('dato')['pris_pr_m2'].rolling('365D', min_periods=10).mean()
                
                premiums_btype = []
                premiums_btype_pct = []
                
                for _, sale in prop_history.iterrows():
                    sale_price_m2 = sale['pris_pr_m2']
                    sale_date = sale['dato']
                    benchmark_btype = btype_rolling_mean.asof(sale_date)
                    
                    if pd.notna(benchmark_btype) and benchmark_btype > 0:
                        premiums_btype.append(sale_price_m2 - benchmark_btype)
                        premiums_btype_pct.append((sale_price_m2 - benchmark_btype) / benchmark_btype)
                
                features['historical_premium_vs_postnummer_btype'] = np.mean(premiums_btype) if premiums_btype else 0
                features['historical_premium_vs_postnummer_btype_pct'] = np.mean(premiums_btype_pct) * 100 if premiums_btype_pct else 0
            else:
                features['historical_premium_vs_postnummer_btype'] = 0
                features['historical_premium_vs_postnummer_btype_pct'] = 0
        else:
            features['historical_premium_vs_postnummer_btype'] = 0
            features['historical_premium_vs_postnummer_btype_pct'] = 0

    def _calculate_synthesized_features(self, features: Dict):
        prop_m2 = features.get('m2', 0)
        if not prop_m2:
            keys = ['postnummer_pris_estimate', 'by_pris_estimate', 'postnummer_pris_premium_adjusted', 'by_pris_premium_adjusted']
            for k in keys: features[k] = None
            return

        features['postnummer_pris_estimate'] = features.get('pris_pr_m2_mean_365D_postnummer', 0) * prop_m2
        features['by_pris_estimate'] = features.get('pris_pr_m2_mean_365D_by', 0) * prop_m2

        adj_post_price_m2 = features.get('pris_pr_m2_mean_365D_postnummer', 0) + features.get('historical_premium_vs_postnummer', 0)
        features['postnummer_pris_premium_adjusted'] = adj_post_price_m2 * prop_m2

        adj_by_price_m2 = features.get('pris_pr_m2_mean_365D_by', 0) + features.get('historical_premium_vs_by', 0)
        features['by_pris_premium_adjusted'] = adj_by_price_m2 * prop_m2

    def generate_for_address(self, full_address_query: str) -> Optional[Dict[str, Any]]:
        """
        The main public method to generate a complete feature vector for a single address.

        Args:
            full_address_query (str): The address to look up (e.g., "Rådhuspladsen 1, 1550 København V").

        Returns:
            A dictionary containing the full feature vector, or None if the process fails.
        """
        print(f"\n--- Starting feature generation for: {full_address_query} ---")
        address_info = self._get_dawa_data(full_address_query)
        print(address_info)
        if not address_info:
            return None
    
        print(f"DAWA lookup successful: {address_info}")

        bfe_nummer = self._get_bfe_number(address_info)
        if not bfe_nummer:
            print("could not get bfe number")
            return None
        print(f"BFE number retrieved: {bfe_nummer}")

        feature_vector = self._calculate_all_features(address_info, bfe_nummer)
        print("--- Feature generation complete ---")
        return feature_vector


# --- Example Usage ---
if __name__ == '__main__':
    DATA_FILE_PATH = 'dataexplor/cleaned_data_with_bfe_coords.csv'

    if not os.path.exists(DATA_FILE_PATH):
        print(f"ERROR: Data file not found at '{DATA_FILE_PATH}'.")
    elif not DATA_FORDELER_USERNAME or DATA_FORDELER_USERNAME == 'your_username':
        print("ERROR: Datafordeleren credentials not set.")
    else:
        feature_service = FeatureGenerator(data_path=DATA_FILE_PATH)
        
        test_address = "bolbro sidevej 6 2960 Rungsted Kyst"
        
        features = feature_service.generate_for_address(test_address)

        if features:
            print("\nGenerated Features:")
            for key, value in features.items():
                print(f"  {key}: {value}")

        test_address = "Kronprinsensgade 57, st., 6700 Esbjerg"
        
        features = feature_service.generate_for_address(test_address)

        if features:
            print("\nGenerated Features:")
            for key, value in features.items():
                print(f"  {key}: {value}")        
        else:
            print(f"\nCould not generate features for '{test_address}'. Check logs for details.")