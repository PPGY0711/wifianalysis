import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.datasets.samples_generator import make_blobs
from sklearn.preprocessing import MinMaxScaler


def dummy_data(size, center_size):
    # 制造一批数据。
    x, y = make_blobs(n_samples=size, centers=center_size, n_features=2, random_state=1)
    print(x)
    scaler = MinMaxScaler()
    # MinMaxScaler：归一到 [ 0，1 ]
    scaler.fit(x)
    x = scaler.transform(x)

    plt.scatter(x[:, 0], x[:, 1], c=y)
    plt.grid()
    plt.show()

    return x, y


if __name__ == '__main__':
    row = 4000
    x, y = dummy_data(row, 1)
    dates = pd.date_range('20190101', periods=row)
    df = pd.DataFrame(x, index=dates, columns=['X', 'Y'])  # 生成row行4列位置

    fig = px.density_heatmap(df, x="X", y="Y",
                             # rug(细条)、box(箱图)、violin(小提琴图)、histogram(直方图)。该参数用于在主图上方，绘制一个水平子图，以便对x分布，进行可视化.
                             marginal_x="rug",
                             marginal_y="histogram",
                             )
    fig.show()