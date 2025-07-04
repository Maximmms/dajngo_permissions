from django.contrib.auth.models import User
from rest_framework import serializers

from advertisements.models import Advertisement, Favorite


class UserSerializer(serializers.ModelSerializer):
	"""Serializer для пользователя."""

	class Meta:
		model = User
		fields = ('id', 'username', 'first_name',
				  'last_name',)


class AdvertisementSerializer(serializers.ModelSerializer):
	"""Serializer для объявления."""

	creator = UserSerializer(
		read_only = True,
	)

	class Meta:
		model = Advertisement
		fields = ('id', 'title', 'description', 'creator',
				  'status', 'created_at', 'draft')

	def create(self, validated_data):
		"""Метод для создания"""

		# Простановка значения поля создатель по-умолчанию.
		# Текущий пользователь является создателем объявления
		# изменить или переопределить его через API нельзя.
		# обратите внимание на `context` – он выставляется автоматически
		# через методы ViewSet.
		# само поле при этом объявляется как `read_only=True`
		validated_data["creator"] = self.context["request"].user
		return super().create(validated_data)

	def validate(self, data):
		"""Метод для валидации. Вызывается при создании и обновлении."""

		user = self.context["request"].user

		if self.instance is None:
			open_advs_count = Advertisement.objects.filter(
				creator = user,
				status = "OPEN",
				draft = False
			).count()

			if open_advs_count >= 10:
				raise serializers.ValidationError("У пользователя не может быть более 10 активных объявлений")

		else:
			if 'status' in data and data['status'] != "CLOSED" or \
					'draft' in data and data['draft'] is False:
				open_advs_count = Advertisement.objects.filter(
					creator = user,
					status = "OPEN",
					draft = False
				).count()

			if self.instance.status == 'CLOSED' or self.instance.draft:
				open_advs_count += 1

			if open_advs_count > 10:
				raise serializers.ValidationError("У пользователя не может быть более 10 активных объявлений")

		return data


class FavoriteSerializer(serializers.ModelSerializer):
	class Meta:
		model = Favorite
		fields = ['advertisement', 'created_at']

	def create(self, validated_data):
		user = self.context["request"].user
		advertisement = validated_data["advertisement"]

		validated_data["user"] = self.context["request"].user

		if advertisement.creator == user:

			raise serializers.ValidationError("Пользователь не может добавить свое объявление в избранное")

		if Favorite.objects.filter(user = user, advertisement = advertisement).exists():
			raise serializers.ValidationError("Пользователь уже добавил данное объявление в избранное")

		validated_data["user"] = user
		return super().create(validated_data)