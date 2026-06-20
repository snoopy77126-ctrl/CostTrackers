class CategoryImportResult:

    def __init__(self):
        self.new_categories = []
        self.existing_categories = []

        self.invalid_rows = []

        self.total_rows = 0
        self.importable_count = 0


class CategoryImportRow:

    def __init__(self):
        self.row_index = 0

        self.raw_data = {}
        self.cleaned_data = {}

        self.exists = False
        self.match = None

        self.errors = []
        self.warnings = []

