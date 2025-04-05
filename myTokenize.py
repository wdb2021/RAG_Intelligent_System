import os
import nltk
from nltk import downloader
nltk.download('punkt_tab')
nltk.set_proxy('https://mirrors.tuna.tsinghua.edu.cn/nltk_data/')  # 清华镜像
nltk.download('punkt_tab', download_dir=os.path.expanduser('~/nltk_data'))
nltk.download('averaged_perceptron_tagger')