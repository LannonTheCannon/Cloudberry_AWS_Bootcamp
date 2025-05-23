import pandas as pd
from ai_data_science_team import DataCleaningAgent, FeatureEngineeringAgent



def run_clean_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    try:
        # Step 1: Clean
        cleaning_agent = DataCleaningAgent()
        cleaning_agent.ivoke_agent(data_raw=df, user_interaction='Use default cleaning steps.')
        df_cleaned = cleaning_agent.get_data_cleaned()

        # Step 2: Feature Engineer
        fe_agent = FeatureEngineeringAgent()
        fe_agent.ivoke_agent(data_raw=df_cleaned, user_interaction='Use default feature engineering steps')
        df_final = fe_agent.get_data_engineered()

        return df_final

    except Exception as e:
        print(f'AI Pipeline failed: {e}')
        raise




# -------------------------------------------------------------------#