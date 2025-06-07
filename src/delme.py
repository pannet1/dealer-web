
    """
        to be removed 
    """

    def merge_ticks_df(self):
        try:
            merged_df = None
            df = self._df_fm_positions()
            # subscribe to new tokens
            symbol_token = (
                df.dropna(subset=["token"])
                .set_index("token")["tradingsymbol"]
                .to_dict()
            )
            token_list = {"exchangeType": 2, "tokens": list(symbol_token.values())}
            self.symbol_token.update(symbol_token)

            flattened_ticks = self._flatten_askbid()
            if not any(flattened_ticks):
                return

            flattened_df = pd.DataFrame(flattened_ticks)
            print(flattened_ticks)
            merged_df = pd.merge(df, flattened_df, on="tradingsymbol", how="inner")
        except Exception as e:
            print(f"{e} while cover")
        finally:
            return merged_df

    def match_df_with_actions(self, df, actions):
        try:
            matching_df = None
            for action_item in actions:
                prefix = split(action_item["tradingsymbol"])
                matching_df = df[
                    df["tradingsymbol"].str.startswith(prefix)
                    & df["tradingsymbol"].str.contains(action_item["action"])
                    & (df["is_trade"] == True)
                ]
                if not matching_df.empty:
                    print(matching_df)
                    matching_df.apply(self.cover_positions, axis=1)
        except Exception as e:
            logging.error(f"{e} in match df with actions")
            print_exc()

    """
        end of removed
    """
