class ExtKwargs(dict):
    def alias(self, alias_array):
        for norm_k, alias_ks in alias_array.items():
            if norm_k not in self:
                if not isinstance(alias_ks, (tuple, list)):
                    alias_ks = (alias_ks,)

                for alias_k in alias_ks:
                    if alias_k in self:
                        self[norm_k] = self[alias_k]
                        del self[alias_k]

                        break

        return self

    def rename(self, rename_array):
        for k, new_k in rename_array.items():
            if k in self:
                v = self[k]
                del self[k]

                self[new_k] = v

        return self

    def extract(self, *names):
        new_kwargs = ExtKwargs()

        for k, v in self.items():
            if k in names:
                new_kwargs[k] = v

        return new_kwargs
