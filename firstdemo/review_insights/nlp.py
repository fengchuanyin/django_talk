import re
from collections import Counter

STOPWORDS = set([
    '的','了','和','与','为','在','是','就','也','都','很','不','没有','非常','真的','这个','那个','我们','你们','他们','以及','但是','还是','如果','因为','所以','而且','呢','啊','吗','吧','哦','还','也许','可能','比较','感觉','觉得','有点','有些'
])

SYNONYMS = {
    '客服': '售后',
    '客服态度': '售后',
    '质保': '售后',
    '运输': '物流',
    '配送': '物流',
    '发货': '物流',
    '快递': '物流',
    '外观': '颜值',
    '做工': '质量',
    '材质': '质量',
    '稳定性': '质量',
    '便宜': '价格',
    '贵': '价格',
    '性价比': '价格',
    '包装盒': '包装',
}

def _safe_tokenize(text):
    try:
        import jieba
        return [w for w in jieba.cut(text or '')]
    except Exception:
        return re.findall(r"[\w\-]+", text or '')

def _normalize_token(t):
    t = t.strip().lower()
    if not t or t in STOPWORDS:
        return ''
    if re.match(r"^[0-9]+$", t):
        return ''
    return SYNONYMS.get(t, t)

def _clean_tokens(tokens):
    out = []
    for t in tokens:
        nt = _normalize_token(t)
        if nt:
            out.append(nt)
    return out

def extract_product_clusters(reviews, n_clusters=5, top_tokens=3):
    texts = []
    sentiments = []
    for r in reviews:
        texts.append(r.content or '')
        sentiments.append(r.sentiment)
    if not texts:
        return []
    docs = [' '.join(_clean_tokens(_safe_tokenize(t))) for t in texts]
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans
        k = max(1, min(n_clusters, len(docs)))
        vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
        X = vec.fit_transform(docs)
        km = KMeans(n_clusters=k, n_init=10)
        km.fit(X)
        labels = km.labels_.tolist()
        terms = vec.get_feature_names_out()
        order_centroids = km.cluster_centers_.argsort()[:, ::-1]
        clusters = []
        for i in range(k):
            top = [terms[ind] for ind in order_centroids[i, :top_tokens]]
            label = '·'.join(top)
            pos = 0
            neg = 0
            neu = 0
            for idx, c in enumerate(labels):
                if c == i:
                    s = sentiments[idx]
                    if s == 'positive':
                        pos += 1
                    elif s == 'negative':
                        neg += 1
                    else:
                        neu += 1
            total = max(1, pos + neg + neu)
            score = int(round((pos / total) * 100 - (neg / total) * 100 * 0.5))
            clusters.append({'label': label, 'positive': pos, 'negative': neg, 'neutral': neu, 'score': score})
        clusters.sort(key=lambda x: x['score'], reverse=True)
        return clusters
    except Exception:
        token_lists = [ _clean_tokens(_safe_tokenize(t)) for t in texts ]
        flat = []
        for tl in token_lists:
            flat.extend(tl)
        common = [w for w,_ in Counter(flat).most_common(n_clusters)]
        clusters = []
        for cw in common:
            pos = 0
            neg = 0
            neu = 0
            for i, tl in enumerate(token_lists):
                if cw in tl:
                    s = sentiments[i]
                    if s == 'positive':
                        pos += 1
                    elif s == 'negative':
                        neg += 1
                    else:
                        neu += 1
            total = max(1, pos + neg + neu)
            score = int(round((pos / total) * 100 - (neg / total) * 100 * 0.5))
            clusters.append({'label': cw, 'positive': pos, 'negative': neg, 'neutral': neu, 'score': score})
        clusters.sort(key=lambda x: x['score'], reverse=True)
        return clusters

def pros_cons_from_clusters(clusters, top_n=3):
    pros = []
    cons = []
    for c in clusters:
        total = max(1, c['positive'] + c['negative'] + c['neutral'])
        pr = c['positive'] / total
        nr = c['negative'] / total
        if pr >= 0.5 and len(pros) < top_n:
            pros.append(c['label'])
        if nr >= 0.3 and len(cons) < top_n:
            cons.append(c['label'])
        if len(pros) >= top_n and len(cons) >= top_n:
            break
    return pros, cons

def build_global_clusters(reviews, n_clusters=8, top_tokens=3, evidence_per_cluster=2):
    texts = []
    sentiments = []
    objs = []
    for r in reviews:
        texts.append(r.content or '')
        sentiments.append(r.sentiment)
        objs.append(r)
    if not texts:
        return []
    docs = [' '.join(_clean_tokens(_safe_tokenize(t))) for t in texts]
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans
        k = max(1, min(n_clusters, len(docs)))
        vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
        X = vec.fit_transform(docs)
        km = KMeans(n_clusters=k, n_init=10)
        km.fit(X)
        labels = km.labels_.tolist()
        terms = vec.get_feature_names_out()
        order_centroids = km.cluster_centers_.argsort()[:, ::-1]
        clusters = []
        for i in range(k):
            top = [terms[ind] for ind in order_centroids[i, :top_tokens]]
            label = '·'.join([SYNONYMS.get(t, t) for t in top])
            pos = 0
            neg = 0
            neu = 0
            samples = []
            for idx, c in enumerate(labels):
                if c == i:
                    s = sentiments[idx]
                    if s == 'positive':
                        pos += 1
                    elif s == 'negative':
                        neg += 1
                    else:
                        neu += 1
                    if len(samples) < evidence_per_cluster:
                        samples.append(objs[idx].content[:200])
            total = max(1, pos + neg + neu)
            clusters.append({'label': label, 'positive': pos, 'negative': neg, 'neutral': neu, 'samples': samples})
        return clusters
    except Exception:
        token_lists = [ _clean_tokens(_safe_tokenize(t)) for t in texts ]
        flat = []
        for tl in token_lists:
            flat.extend(tl)
        common = [w for w,_ in Counter(flat).most_common(n_clusters)]
        clusters = []
        for cw in common:
            pos = 0
            neg = 0
            neu = 0
            samples = []
            for i, tl in enumerate(token_lists):
                if cw in tl:
                    s = sentiments[i]
                    if s == 'positive':
                        pos += 1
                    elif s == 'negative':
                        neg += 1
                    else:
                        neu += 1
                    if len(samples) < evidence_per_cluster:
                        samples.append(texts[i][:200])
            clusters.append({'label': cw, 'positive': pos, 'negative': neg, 'neutral': neu, 'samples': samples})
        return clusters