import uuid
import logging
from django.db import models
from django.db.models import SET_NULL
from django.contrib.auth.models import User
from .fileds import JSONField
from .utils import SearchService

# Setup logging
logger = logging.getLogger(__name__)

#=========================
#  Integration
#=========================

class Food(models.Model):
    uuid = models.CharField('UUID', max_length=36, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='foods', null=True, blank=True, on_delete=SET_NULL)
    name = models.CharField('Name', max_length=128, blank=False, null=False)
    main_ingredients = JSONField('Main ingredients', blank=False, null=False)
    typical_serving = models.IntegerField('Typical serving', blank=True, null=True)
    small_serving = models.IntegerField('Small serving', blank=True, null=True)
    medium_serving = models.IntegerField('Medium serving', blank=True, null=True)
    large_serving = models.IntegerField('Large serving', blank=True, null=True)
    small_piece = models.IntegerField('Small piece', blank=True, null=True)
    medium_piece = models.IntegerField('Medium piece', blank=True, null=True)
    large_piece = models.IntegerField('Large piece', blank=True, null=True)

    def __str__(self):
        return str('Food "{}"'.format(self.name))

    def save(self, *args, search_service=None, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())

        if not self.id:
            if not search_service:
                search_service = SearchService()

            item = {"uuid": self.uuid ,
                    "description": self.name,
                    "ingredients": self.main_ingredients}

            search_service.add(item, variant=None)

            if self.small_serving or self.medium_serving or self.large_serving:
                search_service.add(item, variant='servings')

            if self.small_piece or self.medium_piece or self.large_piece:
                search_service.add(item, variant='pieces')

        else:
            raise Exception('Cannot edit food yet. Delete and re-create if you need to.')

        super(Food, self).save(*args, **kwargs)

    def delete(self, *args, search_service=None, **kwargs):
        if not search_service:
            search_service = SearchService()
        item = {'uuid':self.uuid, 'description': self.name, 'ingredients': self.main_ingredients}
        search_service.delete(item)

        # Remove variants as well (if none present no harm is done)
        search_service.delete(item, variant='servings')
        search_service.delete(item, variant='pieces')

        super(Food, self).delete(*args, **kwargs)

    @property
    def total_observations(self):
        return self.observations.count()

    @classmethod
    def query(cls, q, variant=None, search_service=None):
        if not search_service:
            search_service = SearchService()
        food_objects = []
        for entry in search_service.query(q, variant):
            try:
                food_objects.append(Food.objects.get(uuid=entry['_id']))
            except Exception as e:
                logger.error('{} @ {}'.format(e,entry))
        return food_objects


class FoodObservation(models.Model):
    uuid = models.CharField('UUID', max_length=36, blank=True, null=True)
    food = models.ForeignKey(Food, related_name='observations', on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, related_name='food_observations', null=True, blank=True, on_delete=SET_NULL)
    cho_ratio = models.FloatField('CHO ratio', blank=True, null=True)
    protein_ratio = models.FloatField('Protein ratio', blank=True, null=True)
    fiber_ratio = models.FloatField('Fiber ratio', blank=True, null=True)
    fat_ratio = models.FloatField('Fat ratio', blank=True, null=True)

    def __str__(self):
        return str('Food observation for "{}"'.format(self.food.name))

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        super(FoodObservation, self).save(*args, **kwargs)

    @property
    def cho(self):
        if self.cho_ratio:
            return int(round(self.cho_ratio * 100))
        else:
            return None

    @property
    def proteins(self):
        if self.protein_ratio:
            return int(round(self.protein_ratio * 100))
        else:
            return None

    @property
    def fibers(self):
        if self.fiber_ratio:
            return int(round(self.fiber_ratio * 100))
        else:
            return None

    @property
    def fat(self):
        if self.fat_ratio:
            return int(round(self.fat_ratio * 100))
        else:
            return None

