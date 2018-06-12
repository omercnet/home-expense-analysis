from django.db import models
from expense.models import Expense


class CalUser(models.Model):
    # TODO: Encrypt these fields
    username = models.CharField(max_length=250)
    password = models.CharField(max_length=250)
    token = models.CharField(max_length=500, null=True)

    def __str__(self):
        return self.username


class CalCard(models.Model):
    user = models.ForeignKey(CalUser, on_delete=models.CASCADE)
    cal_id = models.CharField(max_length=10)
    last_4 = models.CharField(max_length=4)
    card_type = models.CharField(max_length=250)
    debit_date = models.IntegerField()
    owner_name = models.CharField(max_length=250)
    is_effective = models.BooleanField()

    bank_code = models.IntegerField()
    bank_branch = models.IntegerField()
    bank_account = models.IntegerField()
    bank_description = models.CharField(max_length=250)

    def __str__(self):
        return "{}: {} ({}) {}-{}-{}".format(self.user, self.last_4, self.card_type,
                                             self.bank_code, self.bank_branch, self.bank_account)


class CalExpense(models.Model):
    expense = models.OneToOneField(Expense, on_delete=models.CASCADE, primary_key=True)
    id = models.IntegerField()
