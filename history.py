import tiktoken
import pandas as pd

class History:
    def __init__(self, history):
        self.history = history

    def add(self, role, content):
        self.history.append({"role": role, "content": content})

    def len(self):
        return len(self.history)

    def all(self):
        return self.history

    def as_dataframe(self):
        tokenizer = tiktoken.get_encoding("cl100k_base")
        data = []
        for h in self.history:
            chars = len(h["content"])
            tokens = len(tokenizer.encode(h["content"]))
            s = h["content"]
            if len(s) > 10:
                s = s[:10] + "..."
            data.append([h['role'], chars, tokens, s])
        return pd.DataFrame(
            data,
            columns = ["role", "chars", "tokens", "content"],
            index = range(len(self.history)),
        )
