import pickle
import copy

class DataFrame:

    def __init__(self, columns=None):
        self._data = {}
        self.columns = list(columns) if columns is not None else []

    @property
    def loc(self):
        return _Loc(self)

    def __str__(self):
        if not self.columns and (not self._data):
            return '<Empty DataFrame>'
        col_widths = {}

    def __repr__(self):
        pass

    def to_pickle(self, filepath):
        """
        将当前 Dataframe 对象序列化保存到文件
        """
        pass

    def __getitem__(self, key):
        """
        支持 df['column_name'] 获取某一列
        返回一个 dict: {row_index: value}
        """
        pass

class _Loc:

    def __init__(self, df):
        pass

    def __getitem__(self, key):
        pass

    def __setitem__(self, key, value):
        pass

def read_pickle(filepath):
    """
    从文件加载并返回一个 DataFrame 对象
    """
    pass