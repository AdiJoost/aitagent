from pydantic import BaseModel


class ConfusionMatrix(BaseModel):
    true_positiv: int
    true_negativ: int
    false_positive: int
    false_negative: int
    precision: float = 0
    recall: float = 0
    f_one_score: float = 0

    def calculate_metrics(self) -> None:
        self.precision = self.get_precison()
        self.recall = self.get_recall()
        self.f_one_score = self.get_f_one_score()

    def get_precison(self) -> float:
        if self.true_positiv == 0 and self.false_positive == 0:
            return 0
        return float(self.true_positiv) / float(self.true_positiv + self.false_positive)

    def get_recall(self) -> float:
        if self.true_positiv == 0 and self.false_negative == 0:
            return 0
        return float(self.true_positiv) / float(self.true_positiv + self.false_negative)

    def get_f_one_score(self) -> float:
        if (
            self.true_positiv == 0
            and self.false_positive == 0
            and self.false_negative == 0
        ):
            return 0
        return (2 * float(self.true_positiv)) / (
            2 * float(self.true_positiv)
            + float(self.false_positive)
            + float(self.false_negative)
        )
