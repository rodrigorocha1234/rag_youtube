# Regra: dataframe_vetorial

Prioridade: vetorização → Series.str/dt/cat → assign/where/mask → numpy.where/select → groupby.agg/transform → merge/join → isin/between → fillna/replace/clip. Evitar iterrows, itertuples e apply(axis=1).
