from django_filters import rest_framework as filters

from advertisements.models import Advertisement


class AdvertisementFilter(filters.FilterSet):
	"""Фильтры для объявлений."""

	created_at_before = filters.DateFilter(field_name = 'created_at', lookup_expr = 'gte')

	class Meta:
		model = Advertisement
		fields = ['created_at']