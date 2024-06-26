# -*- coding: utf-8 -*-
"""Ultimo desafio - Bruno Carvalho

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11gAr-HJt2MHhXr8gzvGgMfKTFqV7lzqG
"""

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# %pip install sidetable

import numpy as np
import pandas as pd
import sidetable

import seaborn as sns
import plotly.express as px
import matplotlib.pyplot as plt

from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans, DBSCAN, MeanShift, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler, scale

from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster

from yellowbrick.cluster import kelbow_visualizer

# https://matplotlib.org/stable/tutorials/introductory/customizing.html
sns.set_theme(
    context='talk',
    style='ticks',
    font_scale=.8,
    palette='tab10',
    rc={
        'figure.figsize': (12,8),
        'axes.grid': True,
        'grid.alpha': .2,
        'axes.titlesize': 'x-large',
        'axes.titleweight': 'bold',
        'axes.titlepad': 20,
    }
)

df = pd.read_csv('/content/data (2).csv', encoding='latin1')
print(df.shape)
df.head()

df.info()

df.InvoiceNo.sort_values()

df[['Description','Country']].nunique()

df['Country'].value_counts(normalize=True, ascending=True).plot.barh(figsize=(12,10))

df[['Quantity','UnitPrice']].describe()

df.stb.freq(['Country'])

df.head()

df.isna().sum().sort_values(ascending=False)

df.duplicated().sum()

df.stb.missing()

df = df.dropna(subset=['CustomerID'])
df.stb.missing()

# Commented out IPython magic to ensure Python compatibility.
# %%timeit
# pd.to_datetime(df.InvoiceDate)

# Commented out IPython magic to ensure Python compatibility.
# %%timeit
# pd.to_datetime(df.InvoiceDate, format='%m/%d/%Y %H:%M')

df['InvoiceDate'] = pd.to_datetime(df.InvoiceDate, format='%m/%d/%Y %H:%M')

df['CustomerID'] = df['CustomerID'].astype(int)
df['Country'] = df['Country'].astype('category')

df = df.copy()
df.info()

df.InvoiceDate.agg(['min','max'])

below0 = df[['Quantity','UnitPrice']].le(0).any(axis=1)
df = df[~below0].copy()

df[['Quantity','UnitPrice']].plot.box()

df.query('Quantity>10_000')

df.query('Quantity<10_000')[['Quantity','UnitPrice']].plot.box()

df.query('UnitPrice>8_000')

df = df.query('Quantity<10_000 & UnitPrice<8_000').copy()

df['price_total'] = df.Quantity * df.UnitPrice
df

pd.Timestamp.today()

pd.Timestamp('2012-01-01')

df_rfm = (
  df.groupby('CustomerID')
  .agg(
      R = ('InvoiceDate', lambda x: (pd.Timestamp('2012-01-01') - x.max()).days),
      F = ('InvoiceNo', 'nunique'),
      M = ('price_total', 'mean')
  )
)

df_rfm

df_rfm.apply(scale).plot.box()

df_rfm.apply(scale).query('M>40')

df.query('CustomerID==15098')

df_rfm.apply(scale).plot.box()

from sklearn.preprocessing import PowerTransformer

scaler = PowerTransformer()

df_rfm_scaled = pd.DataFrame(scaler.fit_transform(df_rfm), index=df_rfm.index, columns=df_rfm.columns)
df_rfm_scaled

df_rfm_scaled.plot.box()

scaler.inverse_transform(df_rfm_scaled)

df_rfm.describe()

df_rfm_clip = df_rfm.apply(lambda x: x.clip(upper=x.quantile(.95)))
df_rfm_clip.describe()

df_rfm_clip_scaled = df_rfm_clip.apply(scale)

# KMEANS
kelbow_visualizer(KMeans(), df_rfm_clip_scaled, k=10, timings=False)

cluster_metrics = silhouette_score, davies_bouldin_score, calinski_harabasz_score
cluster_metrics_results = []
X = df_rfm_clip_scaled.copy()

for k in range(2,11):
  model = KMeans(n_clusters=k, random_state=0)
  labels = model.fit_predict(X)
  cluster_results_dict = {'k': k}
  cluster_results_dict['inertia'] = model.inertia_
  for metric in cluster_metrics:
    cluster_results_dict[metric.__name__] = metric(X, labels)
  cluster_metrics_results.append(cluster_results_dict)

pd.DataFrame(cluster_metrics_results).set_index('k').style.background_gradient()

kmeans = KMeans(4)
kmeans_labels = kmeans.fit_predict(df_rfm_clip_scaled)

px.scatter_3d(df_rfm_clip, x='R', y='F', z='M', color=kmeans_labels.astype(str), template='plotly_dark')

# Análise dos Clusters
centers = pd.DataFrame(kmeans.cluster_centers_, columns=df_rfm_clip_scaled.columns)
fig,axes = plt.subplots(nrows=4, figsize=(14,12), sharex=True)

for i,ax in enumerate(axes):
  center = centers.loc[i,:]
  maxPC = 1.01 * center.abs().max()
  colors = ['pink' if l > 0 else 'blue' for l in center]
  center.plot.bar(ax=ax, color=colors)
  ax.set_ylabel(f'Cluster {i+1}')
  ax.set_ylim(-maxPC, maxPC)
  ax.axhline(color='black')
  ax.xaxis.set_ticks_position('none')

plt.xticks(rotation=60, ha='right')
plt.tight_layout()
plt.show()

(
  df_rfm_clip.assign(cluster=kmeans_labels)
  .groupby('cluster')
  .mean()
  .transpose()
  .style.background_gradient(cmap='YlOrRd', axis=1)
)

"""Ao analisar numericamente os valores dos centróides e das observações em cada cluster, podemos identificar os seguintes perfis:

Cluster 1:

Ticket médio: Médio

Frequência: Muito Baixo

Recência: Muito Alta

Esse perfil sugere clientes inativos ou em churn, os quais não efetuam compras há muito tempo, tiveram poucos pedidos no passado e apresentam um valor médio baixo.

Cluster 2:

Ticket médio: Baixo

Frequência: Baixo

Recência: Muito Baixa

Este grupo consiste em novos clientes ou clientes ocasionais, cujo comportamento nas três variáveis é mediano, sem destacar-se em nenhuma.

Cluster 3:

Ticket médio: Muito Alto

Frequência: Média

Recência: Alta

Representando clientes VIP, este grupo realiza pedidos de alto valor, embora com uma frequência média e há algum tempo.

Cluster 4:

Ticket médio: Médio

Frequência: Alta

Recência: Baixa

Esses são clientes frequentes, que realizam muitos pedidos com um ticket médio razoável e compram com regularidade.

A segmentação de clientes através de técnicas de clusterização é altamente benéfica no contexto do comércio eletrônico. Ao compreender detalhadamente o perfil, comportamento e necessidades de cada grupo de clientes, é possível desenvolver estratégias de marketing, vendas, serviços e relacionamento personalizadas.

Essa abordagem não apenas contribui para aumentar a receita e a frequência de compras, mas também para reduzir os custos associados à aquisição e retenção de clientes. Dessa forma, a análise de dados por meio da clusterização apresenta um potencial significativo para agregar valor a uma operação de e-commerce.

Com base na análise de agrupamento de clientes, é possível recomendar ações e estratégias diferenciadas para cada cluster:

Clientes VIP (Cluster 1):

Investigue os motivos para a evasão e desenvolva estratégias para trazê-los de volta.

Ofereça incentivos para a primeira compra após um longo período de inatividade.

Implemente um serviço de atendimento ao cliente com pesquisa de satisfação para entender e resolver suas necessidades.

Clientes Frequentes (Cluster 2):

Ofereça descontos e frete grátis para suas primeiras compras, incentivando assim novas transações.

Estimule a indicação e compartilhamento nas redes sociais para expandir sua base de clientes.

Concentre-se em aprimorar a experiência do usuário em seu site e aplicativos para garantir a fidelidade desses clientes.

Clientes Inativos (Cluster 3):

Mantenha um programa de fidelidade e ofereça atendimento personalizado para reconquistá-los.

Crie ofertas exclusivas e serviços premium para incentivar sua reativação.

Garanta um estoque e variedade de produtos de maior valor para atender às suas necessidades específicas.

Novos Clientes (Cluster 4):

Forneça ofertas por volume com descontos progressivos para incentivar compras repetidas.

Utilize o marketing por notificação push para informar sobre novas coleções e produtos.

Simplifique o processo de compra e pagamento para melhorar a experiência de compra desses novos clientes.

Essas recomendações podem ser ajustadas e expandidas de acordo com os objetivos e estratégias específicas de cada empresa. O importante é reconhecer a importância da clusterização para proporcionar uma experiência personalizada, maximizando resultados e fidelização, em vez de adotar uma abordagem genérica de "tamanho único".

Conclusão:

A segmentação de clientes por meio de técnicas de clusterização é fundamental para o sucesso do comércio eletrônico. Ao entender os diferentes perfis, comportamentos e necessidades de cada grupo, é possível desenvolver estratégias eficazes de marketing, vendas e relacionamento. Essa abordagem não apenas aumenta a receita e a frequência de compras, mas também reduz os custos associados à aquisição e retenção de clientes, proporcionando assim um valor significativo para as operações de comércio eletrônico.
"""