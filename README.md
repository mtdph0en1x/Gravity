An end-to-end data mining and machine learning project that scrapes, parses, and analyzes custom community level files from the physics game Gravity Defied.

Rather than relying on pre-cleaned tabular data, this project implements a complete ETL pipeline—from raw file extraction and coordinate geometry decoding to feature engineering, Principal Component Analysis (PCA), and K-Means clustering evaluated via Silhouette Score analysis.

Project Overview
Data Harvesting: Automated scraping and downloading of community-created level packages.
Custom Parsing: Decoded raw coordinate arrays and track boundaries into a structured tabular dataset.
Feature Engineering: Extracted geometric and physics-based metrics (actual_track_length, track_efficiency, elevation delta, curvature complexity).
Dimensionality Reduction & Clustering: Applied PCA to reduce multicollinearity, then tuned K-Means (
𝑘
∈
[
5
,
15
]
k∈[5,15]) using Silhouette Coefficient optimization to identify natural track archetypes.
Visualization: Mapped behavioral clusters using Seaborn to categorize tracks by architectural difficulty.
Architecture & Pipeline

 Cluster Distribution
<img width="567" height="433" alt="image" src="https://github.com/user-attachments/assets/3cfaf619-ffe1-4c5b-bd3b-01169c2cc63e" />


Plot Insight: Clusters reveal distinct separation between track length and overall efficiency, identifying distinct design philosophies across community-created tracks.

Tech Stack
Language: Python
Data Processing & ETL: Pandas, NumPy
Machine Learning: Scikit-learn (KMeans, PCA, silhouette_score, StandardScaler)
Visualization: Seaborn, Matplotlib
