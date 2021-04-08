import pickle
import sklearn

uid_to_table_mapping: dict = {
    "7dbbccad-a746-4f3d-ac3a-e22327e1bcf9": "vectors",
    "6dbbccad-a746-4f3d-ac3a-e22327e1ybg8": "vectors_from_vkclube",
    "6dbbccad-a746-4f3d-ac3a-e22327e1ybg9": "vectors_high_resolution_low_jitter",
    "lolo": "lolo",
    "test-clusters": "vectors_and_clusters",
    "test-clusters-100": "vectors_and_clusters_100"
}

with open('cache/model_100_c.pickle', 'rb') as f:
    model: sklearn.cluster.k_means_ = pickle.load(f)
