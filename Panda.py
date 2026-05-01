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
        if key in self.columns:
            return {row: self._data[row].get(key, None) for row in self._data}
        else:
            raise KeyError(f"Column '{key}' not found")

class _Loc:

    def __init__(self, df):
        self.df = df

    def __getitem__(self, key):
        if isinstance(key, tuple):
            row, col = key
            return self.df._data.get(row, {}).get(col, None)
        else:
            return self.df._data.get(key, {}).copy()

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            row, col = key
            if row not in self.df._data:
                self.df._data[row] = {}
            self.df._data[row][col] = value
            if col not in self.df.columns:
                self.df.columns.append(col)
        else:
            self.df._data[key] = value.copy() if hasattr(value, 'copy') else value

def read_pickle(filepath):
    """
    从文件加载并返回一个 DataFrame 对象
    """
    try:
        with open(filepath, 'rb') as f:
            obj = pickle.load(f)
        if isinstance(obj, DataFrame):
            return obj
        else:
            raise TypeError('File does not contain a DataFrame object')
    except FileNotFoundError:
        return None
    except Exception as e:
        return None