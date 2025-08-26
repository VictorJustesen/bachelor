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