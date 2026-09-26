def correlation_clusters(df, threshold=0.85):
    cols = list(df.select_dtypes("number").columns)
    if not cols:
        return []
    corr = df[cols].corr().abs()
    groups, seen = [], set()
    for c in cols:
        if c in seen:
            continue
        group = [x for x in cols if corr.loc[c, x] >= threshold]
        seen.update(group)
        groups.append(group)
    return groups
