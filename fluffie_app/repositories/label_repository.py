


class LabelRepository():
    def __init__(self, db):
        self.db = db
        self.positive_labels = db["positive_labels"]
        self.positive_labels = db["product_label_summaries"]
