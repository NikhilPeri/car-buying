import re
import pickle
import copy
from sklearn.base import TransformerMixin

TMP_CITIES='tmp/cities.pickle'
TMP_PROVINCES='tmp/provinces.pickle'
ADDRESS_TEMPLATE={
    'postal': None,
    'city': None,
    'province': None,
    'street': None,
    'country': 'Canada',
}

class KjijiAddressNormalizer(object):
    def __init__(self):
        try:
            with open(TMP_PROVINCES, 'r') as province_file:
                self.provinces = pickle.load(province_file)
            with open(TMP_CITIES, 'r') as cities_file:
                self.cities = pickle.load(cities_file)
        except:
            self.cities = set()
            self.provinces = set()

    def postal_matcher(self, postal):
        postal = postal.upper()
        matches = re.search('[ABCEGHJKLMNPRSTVXY][0-9][ABCEGHJKLMNPRSTVWXYZ] ?[0-9][ABCEGHJKLMNPRSTVWXYZ][0-9]', postal)
        if matches is not None:
            return matches.group()
        matches = re.search('[0-9][ABCEGHJKLMNPRSTVWXYZ][0-9]', postal)
        if matches is not None:
            return matches.group()

    def city_matcher(self, city):
        city = city.capitalize()
        return city if city in self.cities else None

    def province_matcher(self, province):
        provinces = province.upper()
        provinces = [p.strip() for p in provinces.split(' ')]
        for p in self.provinces:
            if p in provinces:
                return p

    def street_matcher(self, street):
        STREET_KEYWORDS=[
            ' Ave',
            ' Avenue',
            ' Rd',
            ' Road',
            ' Street',
            ' St',
            ' Drive',
            ' Dr',
            ' Court',
            ' Crt',
            ' Crescent',
            ' Ct',
            ' Boulevard',
            ' Blvd',
            ' Terrace'
        ]
        for skw in STREET_KEYWORDS:
            if skw in street:
                return street

    def country_matcher(self, country):
        if 'Canada' in country:
            return 'Canada'


    def transform_address(self, address):
        blocks = address.split(',')
        normalized_address=copy.copy(ADDRESS_TEMPLATE)
        # Machine Matching
        for block in copy.copy(blocks):
            b = block.strip()

            matches = {
                'postal': self.postal_matcher(b),
                'city': self.city_matcher(b),
                'province': self.province_matcher(b),
                'street': self.street_matcher(b),
                'country': self.country_matcher(b),
            }
            matches = {k: v for k, v in matches.iteritems() if v is not None}
            if len(matches) > 0:
                blocks.remove(block)
                normalized_address.update(matches)

        missing_attrubutes = [k for k, v in normalized_address.iteritems() if v is None]
        if len(blocks) == 0:
            return normalized_address
        elif len(missing_attrubutes) == 1 and len(blocks) == 1:
            normalized_address[missing_attrubutes[0]] = blocks[0]
            return normalized_address


        # Human Assisted Matching
        for attribute in missing_attrubutes:
            answer = raw_input('what is the {}:'.format(attribute))
            if answer == '':
                continue
            elif attribute == 'city':
                    answer = answer.capitalize()
                    self.cities.add(answer)
                    self.save()
            elif attribute == 'province':
                answer = answer.upper()
                self.provinces.add(answer)
                self.save()
            normalized_address[attribute] = answer

        return normalized_address

    def fit_transform(self, addresses):
        res = []
        for a in addresses:
            print a
            try:
                a = self.transform_address(a)
            except:
                print 'ERROR'
                a = ADDRESS_TEMPLATE
            res.append(a)
            print res[-1]
            if len(res) % 10 == 0:
                print 'Completed: {}'.format(len(res))
        return res

    def save(self):
        with open(TMP_PROVINCES, 'w+') as province_file:
            pickle.dump(self.provinces, province_file)
        with open(TMP_CITIES, 'w+') as cities_file:
            pickle.dump(self.cities, cities_file)

if __name__ == '__main__':
    import sys
    import pandas as pd

    data = pd.read_csv(sys.argv[1])
    normalizer = KjijiAddressNormalizer()
    addresses = normalizer.fit_transform(data['location'])
    data = data.join(pd.DataFrame(addresses))
    data.to_csv('data/toronto_addresses.csv')
