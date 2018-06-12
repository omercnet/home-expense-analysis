
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.shortcuts import render
from .models import Expense, Category, Names
from django.db.models import Sum, Case, When, F, FloatField
from django.conf import settings


def _top_of_months_ago(months):
    return datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=months)


def details(request):
    return render(request, 'details/details.html',
                  {'details': (Expense.objects.filter(date__gte=_top_of_months_ago(int(request.GET['monthsback'])),
                                                      name__cat__id=int(request.GET['cat'])).order_by('date')
                                              .exclude(name__cat__id=-1))
                   })


def missing(request):
    if request.method == "POST":

        # build a dict from POST
        ex = dict()
        for k in request.POST.keys():
            if "_" in k:
                id = k.split('_')[0]
                key = k.split('_')[1]
                ex.setdefault(id, dict())
                ex[id][key] = request.POST[k]

        for k, v in ex.items():
            print(v)
            if v['cat'] == 0:
                continue

            ex = Expense.objects.get(pk=k)

            if v['cat'] == "-1":
                namesuff = "IGNORE"
            else:
                namesuff = v['name']
            if namesuff:
                new_name = "{}_{}".format(ex.name.name, namesuff)
            else:
                new_name = ex.name.name
            name, created = Names.objects.get_or_create(name=new_name)
            name.cat = Category.objects.get(pk=v['cat'])
            name.save()

            ex.name = name
            ex.save()

    last_month_list = Expense.objects.filter(name__cat__pk=0)

    return render(request, 'missing/missing.html',
                  {'missing': last_month_list,
                   'total': sum(map(lambda ex: ex.charge, last_month_list)),
                   'categories': Category.objects.all()})


def report(request):
    sums = Category.objects.filter(pk__gt=0).annotate(
        lastMonth=Sum(Case(When(names__expense__date__gte=_top_of_months_ago(1),
                                names__expense__charge_number=1,
                                then=F('names__expense__charge') * F('names__expense__total_charges')),
                           output_field=FloatField())),

        lastQuarter=Sum(Case(When(names__expense__date__gte=_top_of_months_ago(3),
                                  names__expense__charge_number=1,
                                  then=F('names__expense__charge') * F('names__expense__total_charges')),
                             output_field=FloatField())),

        lastHalf=Sum(Case(When(names__expense__date__gte=_top_of_months_ago(6),
                               names__expense__charge_number=1,
                               then=F('names__expense__charge') * F('names__expense__total_charges')),
                          output_field=FloatField())),

        lastYear=Sum(Case(When(names__expense__date__gte=_top_of_months_ago(12),
                               names__expense__charge_number=1,
                               then=F('names__expense__charge') * F('names__expense__total_charges')),
                          output_field=FloatField()))
    )

    totals = Expense.objects.all().aggregate(
        lastMonth=Sum(Case(When(date__gte=_top_of_months_ago(1),
                                charge_number=1,
                                then=F('charge') * F('total_charges')), output_field=FloatField())),
        lastQuarter=Sum(Case(When(date__gte=_top_of_months_ago(3),
                                  charge_number=1,
                                  then=F('charge') * F('total_charges')), output_field=FloatField())),
        lastHalf=Sum(Case(When(date__gte=_top_of_months_ago(6),
                               charge_number=1,
                               then=F('charge') * F('total_charges')), output_field=FloatField())),
        lastYear=Sum(Case(When(date__gte=_top_of_months_ago(12),
                               charge_number=1,
                               then=F('charge') * F('total_charges')), output_field=FloatField())))

    not_categorized = Expense.objects.filter(name__cat__pk=0).aggregate(
        lastMonth=totals['lastMonth'] - Sum(Case(When(date__gte=_top_of_months_ago(1),
                                                      charge_number=1,
                                                      name__cat__isnull=False,
                                                      then=F('charge') * F('total_charges')),
                                                 output_field=FloatField())),

        lastQuarter=totals['lastQuarter'] - Sum(Case(When(date__gte=_top_of_months_ago(3),
                                                          charge_number=1,
                                                          name__cat__isnull=False,
                                                          then=F('charge') * F('total_charges')),
                                                     output_field=FloatField())),

        lastHalf=totals['lastHalf'] - Sum(Case(When(date__gte=_top_of_months_ago(6),
                                                    charge_number=1,
                                                    name__cat__isnull=False,
                                                    then=F('charge') * F('total_charges')),
                                               output_field=FloatField())),

        lastYear=totals['lastYear'] - Sum(Case(When(date__gte=_top_of_months_ago(12),
                                                    charge_number=1,
                                                    name__cat__isnull=False,
                                                    then=F('charge') * F('total_charges')),
                                               output_field=FloatField())),
    )

    return render(request, 'report/report.html',
                  {'sums': sums,
                   'not_categorized': not_categorized,
                   'totals': totals,
                   'income': settings.MONTHLY_INCOME,
                   })
