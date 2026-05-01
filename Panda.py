import pickle
import copy
class DataFrame:
    def __init__(self, columns=None):
        self._data = {}  # 刚开始是空字典，没有行 ✅
        self.columns = list(columns) if columns is not None else []

    @property
    def loc(self):
        return _Loc(self)

    def __str__(self):
        if not self.columns and not self._data:
            return "<Empty DataFrame>"

        # 计算每列宽度（至少为列名长度）
        col_widths = {}
        for col in self.columns:
            col_widths[col] = len(str(col))

        # 收集所有行索引
        row_indices = list(self._data.keys())

        # 更新列宽：考虑每行每个单元格的内容长度
        for row in row_indices:
            for col in self.columns:
                val = self._data.get(row, {}).get(col, '')
                col_widths[col] = max(col_widths[col], len(str(val)))

        # 构造表头
        header = " ".join(f"{col:>{col_widths[col]}}" for col in self.columns)
        lines = [f"{'':<8} {header}"]  # 第一列空出来放行名

        # 构造每一行
        for row in row_indices:
            cells = []
            for col in self.columns:
                val = self._data[row].get(col, '')
                cells.append(f"{val:>{col_widths[col]}}")
            line = f"{row:<8} {' '.join(cells)}"
            lines.append(line)

        return "\n".join(lines)

    def __repr__(self):
        return self.__str__()  # 简单起见，repr 和 str 一样
    
    def to_pickle(self, filepath):
        """
        将当前 Dataframe 对象序列化保存到文件
        """
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self, f)
            # print(f"Dataframe saved to {filepath}")
        except Exception as e:
            # print(f"Failed to save: {e}")
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

            # 可选：将新列加入 columns
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
            raise TypeError("File does not contain a DataFrame object")
    except FileNotFoundError:
        # print(f"❌ File not found: {filepath}")
        return None
    except Exception as e:
        # print(f"❌ Failed to load: {e}")
        return None

