from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from advertisements.filters import AdvertisementFilter
from advertisements.models import Advertisement, Favorite
from advertisements.serializers import AdvertisementSerializer, FavoriteSerializer
from api_with_restrictions.permissions import IsOwnerOrReadOnly


class AdvertisementViewSet(ModelViewSet):
	"""ViewSet для объявлений."""

	# TODO: настройте ViewSet, укажите атрибуты для кверисета,
	#   сериализаторов и фильтров
	queryset = Advertisement.objects.all()
	serializer_class = AdvertisementSerializer
	filter_backends = [DjangoFilterBackend]
	permission_classes = [IsOwnerOrReadOnly]
	filterset_fields = ['creator', 'status']
	filterset_class = AdvertisementFilter

	def get_permissions(self):
		"""Получение прав для действий."""
		if self.action == "create":
			return [IsAuthenticated()]
		if self.action in ["update", "destroy", "partial_update"]:
			return [IsAuthenticated(), IsOwnerOrReadOnly()]
		return []

	def get_queryset(self):
		queryset = super().get_queryset()
		user = self.request.user

		if not user.is_authenticated:
			return queryset.none()

		draft_param = self.request.query_params.get("draft", "").lower()
		if draft_param in ("true", "false"):
			is_draft = draft_param == "true"
			return queryset.filter(creator = user, draft = is_draft)

		if self.action == "create":
			return queryset.filter(draft = False)

		return queryset

	@action(detail = False, methods = ['post'])
	def set_favorite(self, request):
		user = request.user

		if not user.is_authenticated:
			return Response({'detail':'Требуется авторизация'}, status = status.HTTP_403_FORBIDDEN)

		try:
			advertisement_id = request.data['id']
		except KeyError:
			return Response({'detail':'Не указан ID объявления'}, status = status.HTTP_400_BAD_REQUEST)

		try:
			advertisement = Advertisement.objects.get(id = advertisement_id)
		except Advertisement.DoesNotExist:
			return Response({'detail':'Объявление не найдено'}, status = status.HTTP_404_NOT_FOUND)

		if advertisement.creator == user:
			return Response(
				{'detail':'Нельзя добавлять в избранное свои объявления'},
				status = status.HTTP_403_FORBIDDEN
			)

		favorite, created = Favorite.objects.get_or_create(
			user = user,
			advertisement = advertisement
		)

		if not created:
			return Response(
				{'detail':'Объявление уже в избранном'},
				status = status.HTTP_200_OK
			)

		return Response(
			{'detail':'Объявление добавлено в избранное'},
			status = status.HTTP_201_CREATED
		)


class FavoriteViewSet(ModelViewSet):
	queryset = Favorite.objects.all()
	serializer_class = FavoriteSerializer
	filter_backends = [DjangoFilterBackend]
	permission_classes = [IsOwnerOrReadOnly]