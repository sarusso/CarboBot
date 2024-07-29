import uuid
import logging
from django.db import models
from django.contrib.auth.models import User
from .fileds import JSONField

# Setup logging
logger = logging.getLogger(__name__) 

#=========================
#  Integration
#=========================

class Food(models.Model):
    uuid = models.CharField('UUID', max_length=36, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='foods', on_delete=models.CASCADE) # TODO: _not_ this!
    name = models.CharField('Name', max_length=128, blank=False, null=False)
    main_ingredients = JSONField('Main ingredients', blank=False, null=False)
    typical_weight = models.IntegerField('Typical weight', blank=True, null=True)

    def __str__(self):
        return str('Food "{}"'.format(self.name))

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        super(Food, self).save(*args, **kwargs)

    @property
    def total_observations(self):
        return self.observations.count()

class FoodObservation(models.Model):
    uuid = models.CharField('UUID', max_length=36, blank=True, null=True)
    food = models.ForeignKey(Food, related_name='observations', on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, related_name='food_observations', on_delete=models.CASCADE) # TODO: _not_ this!
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

