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
        for col in self.columns:
            col_widths[col] = len(str(col))
        row_indices = list(self._data.keys())
        for row in row_indices:
            for col in self.columns:
                val = self._data.get(row, {}).get(col, '')
                col_widths[col] = max(col_widths[col], len(str(val)))
        header = ' '.join((f'{col:>{col_widths[col]}}' for col in self.columns))
        lines = [f"{'':<8} {header}"]
        for row in row_indices:
            cells = []
            for col in self.columns:
                val = self._data[row].get(col, '')
                cells.append(f'{val:>{col_widths[col]}}')
            line = f"{row:<8} {' '.join(cells)}"
            lines.append(line)
        return '\n'.join(lines)

    def __repr__(self):
        return self.__str__()

    def to_pickle(self, filepath):
        """
        将当前 Dataframe 对象序列化保存到文件
        """
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self, f)
        except Exception as e:
            return None

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