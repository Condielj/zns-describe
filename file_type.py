import pandas as pd


class FileType(object):
    def __init__(self, data: pd.DataFrame):

        self.data = data

    def missing_cols(self) -> list[str]:

        return list(set(self.item_cols) - set(self.data.columns.tolist()))

    def fits_type(self) -> bool:
        return len(self.missing_cols()) == 0

    @property
    def item_cols(self) -> list[str]:
        raise (NotImplementedError)

    @property
    def unnamed_cols(self) -> list[str]:
        raise (NotImplementedError)

    @property
    def named_cols(self) -> list[str]:
        raise (NotImplementedError)

    def get_hs_code_name(self) -> str:
        raise (NotImplementedError)


class BulkClassifyOutput(FileType):
    @property
    def item_cols(self):
        return self.unnamed_cols + self.named_cols

    @property
    def unnamed_cols(self):
        return ["Description", "Detailed Description"]

    @property
    def named_cols(self):
        return ["Category", "Brand", "Material/Composition"]

    def get_hs_code_name(self):

        # Loop over columns
        for col in self.data.columns:

            # Does it start with "hs_code"
            if col.startswith("hs_code"):

                # That's the one
                return col

        # You didn't find any
        return None


class ColinaBoardOutput(FileType):
    @property
    def item_cols(self):
        return self.unnamed_cols + self.named_cols

    @property
    def unnamed_cols(self):
        return ["description", "detailedDescription"]

    @property
    def named_cols(self):
        return ["category"]

    def get_hs_code_name(self):

        # Loop over columns
        for col in self.data:

            # Does it start with "hs_code"
            if col.startswith("hs_code"):

                # That's the one
                return col

        # You didn't find any
        return None


def infer_file_type(data: pd.DataFrame) -> FileType:

    file_types = [BulkClassifyOutput, ColinaBoardOutput]

    for ft in file_types:
        candidate = ft(data)
        if candidate.fits_type():
            return candidate
