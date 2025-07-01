from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from advertisements.filters import AdvertisementFilter
from advertisements.models import Advertisement, FavoriteAdvertisement
from advertisements.serializers import AdvertisementSerializer
from api_with_restrictions.permissions import IsOwnerOrReadOnly


class AdvertisementViewSet(ModelViewSet):
	"""ViewSet для объявлений."""

	# TODO: настройте ViewSet, укажите атрибуты для кверисета,
	#   сериализаторов и фильтров
	queryset = Advertisement.objects.all()
	serializer_class = AdvertisementSerializer
	permission_classes = [IsOwnerOrReadOnly]
	filter_backends = [DjangoFilterBackend]
	filterset_fields = ['creator']
	filterset_class = AdvertisementFilter

	def get_permissions(self):
		"""Получение прав для действий."""
		if self.action in ["create", "update", "partial_update", ]:
			return [IsAuthenticated()]
		return []

	def get_queryset(self):
		if self.action == "create":
			return super().get_queryset().filter(draft = False)
		return super().get_queryset()

	@action(detail = False, methods = ['get'])
	def get_draft(self, request):
		user = request.user

		if not user.is_authenticated:
			return Response({'detail':'Требуется авторизация'}, status = 403)

		queryset = self.queryset.filter(creator = user, draft = "True")

		if not queryset.exists():
			return Response({'detail':'Черновиков не найдено'}, status = 200)

		serializer = self.get_serializer(queryset, many = True)
		return Response(serializer.data)

	@action(detail = False, methods = ['post'])
	def set_favorite(self, request):
		user = request.user

		if not user.is_authenticated:
			return Response({'detail':'Требуется авторизация'}, status = 403)

		try:
			advertisement_id = request.data['id']
		except KeyError:
			return Response({'detail':'Не указан ID объявления'}, status = 400)

		try:
			advertisement = Advertisement.objects.get(id = advertisement_id)
		except Advertisement.DoesNotExist:
			return Response({'detail':'Объявление не найдено'}, status = 404)

		if advertisement.creator == user:
			return Response(
				{'detail':'Нельзя добавлять в избранное свои объявления'},
				status = status.HTTP_403_FORBIDDEN
			)

		favorite, created = FavoriteAdvertisement.objects.get_or_create(
			user = user,
			advertisement = advertisement
		)

		if not created:
			return Response(
				{'detail':'Объявление уже в избранном'},
				status = 200
			)

		return Response(
			{'detail':'Объявление добавлено в избранное'},
			status = 201
		)