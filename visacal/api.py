
import logging
from datetime import datetime

import requests
from attr import attrs, attrib

from .models import CalCard, CalUser, CalExpense
from expense.models import Expense, Names

logger = logging.getLogger(__name__)


@attrs
class CalApi:
    user = attrib(type=CalUser)

    api_url = 'https://cal4u.cal-online.co.il/Cal4U'
    login_url = 'https://connect.cal-online.co.il/api/authentication/login'
    settings_url = 'https://cal4u.cal-online.co.il/digitalwallet/settings.json'

    s = None
    params = dict()

    def __attrs_post_init__(self):
        self.s = requests.Session()
        self.s.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 '
                          '(KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
        }
        self.default_params = {'OperatingSystem': 'Android'}

    def get(self, endpoint, params={}, retry=False):
        r = self.s.get('{}/{}'.format(self.api_url, endpoint), params={**self.default_params, **params})
        if r.status_code == 401 and not retry:
            self.login()
            return self.get(endpoint=endpoint, params=params, retry=True)

        r.raise_for_status()
        return r.json()

    def login(self):
        settings = self.s.get(self.settings_url).json()
        self.s.headers.update({'X-Site-Id': settings['siteId']})
        self.default_params.update({'CurrentVersion': settings['version']})
        login = self.s.post(self.login_url, json={'username': self.user.username,
                                                  'password': self.user.password,
                                                  'rememberMe': None})
        login.raise_for_status()
        self.s.headers.update({'Authorization': 'CALAuthScheme {}'.format(login.json()['token'])})

    def refresh_cards(self):
        bank_accounts = self.get('CardsByAccounts')
        for b in bank_accounts['BankAccounts']:
            logger.debug(b)
            for card in b['Cards']:
                logger.debug(b)
                data = {
                    'user': self.user,
                    'cal_id': card['Id'],
                    'last_4': card['LastFourDigits'],
                    'card_type': card['CardType'],
                    'debit_date': card['DebitDate'],
                    'owner_name': '{} {}'.format(card['OwnerFirstName'], card['OwnerLastName']),
                    'is_effective': card['IsEffectiveInd'],
                    'bank_code': b['BankCode'],
                    'bank_branch': b['BankBranchNumber'],
                    'bank_account': b['AccountNumber'],
                    'bank_description': b['BankCodeDescription'],
                }
                cal_card, created = CalCard.objects.get_or_create(cal_id=card['Id'], defaults=data)
                if created:
                    logger.info('Created new Cal Card: %s', data)

    def get_expenses(self, card, from_date=None, to_date=None):
        if not to_date:
            to_date = datetime.now()
        to_date = to_date.strftime('%d/%m/%Y')

        if not from_date:
            from_date = datetime.now().replace(day=1)
        from_date = from_date.strftime('%d/%m/%Y')

        expenses = self.get('CalTransactions/{}'.format(card.cal_id), {'FromDate': from_date, 'ToDate': to_date})

        if not expenses['Transactions']:
            return

        for cal_ex in expenses['Transactions']:
            try:
                CalExpense.objects.get(id=cal_ex['Id'])
            except CalExpense.DoesNotExist:
                name, created = Names.objects.get_or_create(name=cal_ex['MerchantDetails']['Name'])
                # d = self.get('CalTransDetails/{}'.format(cal_ex['Id'], {'Numerator': 2}))
                if not int(cal_ex['CurrentPayment']):
                    cal_ex['CurrentPayment'] = 1
                if not int(cal_ex['TotalPayments']):
                    cal_ex['TotalPayments'] = 1
                ex = Expense(date=datetime.strptime(cal_ex['Date'], '%d/%m/%Y'),
                             name=name,
                             total=cal_ex['Amount']['Value'],
                             charge=cal_ex['DebitAmount']['Value'],
                             notes=cal_ex['Notes'],
                             charge_number=cal_ex['CurrentPayment'],
                             total_charges=cal_ex['TotalPayments'])
                ex.save()
                calexpense = CalExpense(id=cal_ex['Id'], expense=ex, card=card)
                calexpense.save()
