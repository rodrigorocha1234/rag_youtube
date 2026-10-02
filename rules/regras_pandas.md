# Pandas
Proibidos quando houver alternativa vetorial: `iterrows`, loops por linha/coluna/grupo, atribuição célula a célula, `apply(axis=1)`, `itertuples` sem justificativa e conversões para listas/dicts para processamento linha a linha.
Prioridade: vetorização → `.str/.dt/.cat` → `assign/where/mask` → NumPy → `groupby.agg/transform` → `merge/join` → `isin/between` → `fillna/replace/clip`.
